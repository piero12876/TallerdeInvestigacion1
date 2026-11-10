from __future__ import annotations

from dataclasses import dataclass

import joblib
import numpy as np
from sklearn.base import clone
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold
from sklearn.naive_bayes import GaussianNB
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sqlalchemy.orm import Session, joinedload

from app.config import MODEL_PATH
from app.domain.enums import AttendanceStatus, RiskLevel, StudentStatus
from app.infrastructure.database import ModelRun, Prediction, Student

FEATURE_NAMES = [
    "promedio",
    "nota_minima",
    "cursos_desaprobados",
    "tendencia",
    "asistencia_pct",
    "faltas",
    "tardanzas",
    "justificadas",
    "nivel",
]

FEATURE_LABELS = {
    "promedio": "Promedio académico",
    "nota_minima": "Nota mínima",
    "cursos_desaprobados": "Áreas desaprobadas",
    "tendencia": "Tendencia bim. 2 − bim. 1",
    "asistencia_pct": "Asistencia (%)",
    "faltas": "Faltas no justificadas",
    "tardanzas": "Tardanzas",
    "justificadas": "Inasistencias justificadas",
    "nivel": "Grado",
}


@dataclass
class FeatureRow:
    student_id: int
    values: list[float]
    label: int | None


def _student_features(student: Student) -> list[float]:
    records = student.grades or []
    if records:
        notas = [r.nota for r in records]
        promedio = float(np.mean(notas))
        nota_minima = float(np.min(notas))
        by_course: dict[int, list[float]] = {}
        by_bim: dict[int, list[float]] = {}
        for r in records:
            by_course.setdefault(r.course_id, []).append(r.nota)
            by_bim.setdefault(r.bimestre, []).append(r.nota)
        desaprobados = sum(1 for vals in by_course.values() if np.mean(vals) < 11)
        b1 = float(np.mean(by_bim.get(1, [promedio])))
        b2 = float(np.mean(by_bim.get(2, [promedio])))
        tendencia = b2 - b1
    else:
        promedio = 12.0
        nota_minima = 12.0
        desaprobados = 0
        tendencia = 0.0

    att = student.attendance or []
    total = len(att) or 1
    faltas = sum(1 for a in att if a.estado == AttendanceStatus.FALTA.value)
    tardanzas = sum(1 for a in att if a.estado == AttendanceStatus.TARDANZA.value)
    justificadas = sum(1 for a in att if a.estado == AttendanceStatus.JUSTIFICADA.value)
    presentes = sum(1 for a in att if a.estado == AttendanceStatus.PRESENTE.value)
    asistencia_pct = 100.0 * (presentes + tardanzas + justificadas) / total
    nivel = float(student.grade.nivel) if student.grade else 1.0

    return [
        round(promedio, 2),
        round(nota_minima, 2),
        float(desaprobados),
        round(tendencia, 2),
        round(asistencia_pct, 2),
        float(faltas),
        float(tardanzas),
        float(justificadas),
        nivel,
    ]


def collect_rows(db: Session, labeled_only: bool = False) -> list[FeatureRow]:
    students = (
        db.query(Student)
        .options(joinedload(Student.grades), joinedload(Student.attendance), joinedload(Student.grade))
        .all()
    )
    rows: list[FeatureRow] = []
    for student in students:
        values = _student_features(student)
        label = 1 if student.estado == StudentStatus.DESERTOR.value else 0
        if labeled_only and not student.es_historico and student.estado == StudentStatus.ACTIVO.value:
            continue
        if labeled_only:
            rows.append(FeatureRow(student.id, values, label))
        else:
            rows.append(
                FeatureRow(
                    student.id,
                    values,
                    label if student.es_historico or student.estado == StudentStatus.DESERTOR.value else None,
                )
            )
    return rows


def _metrics(y_true, y_pred, y_proba) -> dict:
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    vn, fp, fn, vp = (int(x) for x in cm.ravel())
    auc = 0.0
    pr_auc = 0.0
    if len(set(y_true)) > 1 and y_proba is not None:
        try:
            auc = float(roc_auc_score(y_true, y_proba))
        except ValueError:
            auc = 0.0
        try:
            pr_auc = float(average_precision_score(y_true, y_proba))
        except ValueError:
            pr_auc = 0.0
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "roc_auc": auc,
        "pr_auc": pr_auc,
        "vp": vp,
        "vn": vn,
        "fp": fp,
        "fn": fn,
    }


def _oversample_minority(X: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Réplica aleatoria del minoritario, solo en el fold de entrenamiento. No es SMOTE."""
    pos = np.where(y == 1)[0]
    neg = np.where(y == 0)[0]
    if len(pos) == 0 or len(neg) == 0 or len(pos) >= len(neg):
        return X, y
    extra = np.random.RandomState(42).choice(pos, size=len(neg) - len(pos), replace=True)
    idx = np.concatenate([neg, pos, extra])
    rng = np.random.RandomState(42)
    rng.shuffle(idx)
    return X[idx], y[idx]


def _candidates():
    return {
        "Regresión logística": Pipeline(
            [
                ("scaler", StandardScaler()),
                ("clf", LogisticRegression(max_iter=400, class_weight="balanced")),
            ]
        ),
        "Naive Bayes": Pipeline(
            [
                ("scaler", StandardScaler()),
                ("clf", GaussianNB()),
            ]
        ),
        "SVM": Pipeline(
            [
                ("scaler", StandardScaler()),
                ("clf", SVC(kernel="rbf", probability=True, class_weight="balanced", random_state=42)),
            ]
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=160,
            max_depth=5,
            min_samples_leaf=3,
            class_weight="balanced",
            random_state=42,
        ),
        "Árboles impulsados": GradientBoostingClassifier(
            n_estimators=80,
            max_depth=3,
            learning_rate=0.08,
            random_state=42,
        ),
    }


def train_and_select(db: Session) -> ModelRun:
    rows = collect_rows(db, labeled_only=True)
    if len(rows) < 20:
        raise RuntimeError("No hay suficientes registros históricos etiquetados para entrenar.")

    X = np.array([r.values for r in rows], dtype=float)
    y = np.array([int(r.label or 0) for r in rows], dtype=int)
    n_pos = int(y.sum())
    folds = max(2, min(5, n_pos, int(len(y) - n_pos)))
    skf = StratifiedKFold(n_splits=folds, shuffle=True, random_state=42)

    best_name = ""
    best_model = None
    best_score = -1.0
    best_run: ModelRun | None = None
    db.query(ModelRun).delete()
    db.flush()

    for name, proto in _candidates().items():
        oof_pred = np.zeros(len(y), dtype=int)
        oof_proba = np.zeros(len(y), dtype=float)
        fold_recall = []
        fold_f1 = []
        for train_idx, test_idx in skf.split(X, y):
            model = clone(proto)
            Xtr, ytr = _oversample_minority(X[train_idx], y[train_idx])
            model.fit(Xtr, ytr)
            pred = model.predict(X[test_idx])
            proba = model.predict_proba(X[test_idx])[:, 1]
            oof_pred[test_idx] = pred
            oof_proba[test_idx] = proba
            fold_recall.append(float(recall_score(y[test_idx], pred, zero_division=0)))
            fold_f1.append(float(f1_score(y[test_idx], pred, zero_division=0)))
        metrics = _metrics(y, oof_pred, oof_proba)
        final = clone(proto)
        Xb, yb = _oversample_minority(X, y)
        final.fit(Xb, yb)
        run = ModelRun(
            algoritmo=name,
            n_train=len(y) - max(1, len(y) // folds),
            n_test=max(1, len(y) // folds),
            selected=False,
            pr_auc=metrics["pr_auc"],
            recall_std=float(np.std(fold_recall)),
            f1_std=float(np.std(fold_f1)),
            cv_folds=folds,
            nota=(
                f"Validación cruzada estratificada {folds}-fold (predicciones OOF). "
                f"n etiquetados={len(y)} (desertores={n_pos}). Entorno sintético de tesis, no padrón real."
            ),
            **{k: metrics[k] for k in ("accuracy", "precision", "recall", "f1", "roc_auc", "vp", "vn", "fp", "fn")},
        )
        db.add(run)
        score = metrics["f1"] * 0.45 + metrics["recall"] * 0.55
        if score > best_score:
            best_score = score
            best_name = name
            best_model = final
            best_run = run

    if best_model is None or best_run is None:
        db.rollback()
        raise RuntimeError("No se pudo seleccionar un modelo")

    payload = {
        "model": best_model,
        "name": best_name,
        "features": FEATURE_NAMES,
        "cv_folds": folds,
        "n_labeled": len(y),
    }
    joblib.dump(payload, MODEL_PATH)
    best_run.selected = True
    db.commit()
    db.refresh(best_run)
    return best_run


def _load_model():
    if not MODEL_PATH.exists():
        return None
    return joblib.load(MODEL_PATH)


def classify(prob: float) -> str:
    if prob >= 0.62:
        return RiskLevel.ALTO.value
    if prob >= 0.35:
        return RiskLevel.MEDIO.value
    return RiskLevel.BAJO.value


def predict_all(db: Session) -> int:
    payload = _load_model()
    if payload is None:
        train_and_select(db)
        payload = _load_model()
    model = payload["model"]
    name = payload["name"]

    db.query(Prediction).filter(Prediction.vigente.is_(True)).update({"vigente": False})
    students = (
        db.query(Student)
        .options(joinedload(Student.grades), joinedload(Student.attendance), joinedload(Student.grade))
        .filter(Student.estado == StudentStatus.ACTIVO.value, Student.es_historico.is_(False))
        .all()
    )
    scored: list[tuple[Student, float]] = []
    for student in students:
        values = np.array([_student_features(student)])
        if hasattr(model, "predict_proba"):
            prob = float(model.predict_proba(values)[0, 1])
        else:
            prob = float(model.predict(values)[0])
        scored.append((student, prob))
    scored.sort(key=lambda item: item[1], reverse=True)

    by_salon: dict[int, list] = {}
    for student, prob in scored:
        by_salon.setdefault(student.grade_id or 0, []).append((student.id, prob))
    cupo_salon: dict[int, str] = {}
    for group in by_salon.values():
        group.sort(key=lambda item: item[1], reverse=True)
        for i, (sid, _prob) in enumerate(group):
            if i == 0:
                cupo_salon[sid] = RiskLevel.ALTO.value
            elif i < 5:
                cupo_salon[sid] = RiskLevel.MEDIO.value
            else:
                cupo_salon[sid] = RiskLevel.BAJO.value

    for index, (student, prob) in enumerate(scored, start=1):
        db.add(
            Prediction(
                student_id=student.id,
                probabilidad=round(prob, 4),
                nivel_modelo=classify(prob),
                nivel_riesgo=cupo_salon.get(student.id, classify(prob)),
                prioridad=index,
                modelo=name,
                vigente=True,
            )
        )
    db.commit()
    return len(scored)


def student_feature_map(student: Student) -> dict[str, float]:
    values = _student_features(student)
    return dict(zip(FEATURE_NAMES, values))
