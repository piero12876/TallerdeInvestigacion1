from collections import Counter

from sqlalchemy.orm import Session, joinedload

from app.domain.enums import Role, StudentStatus, achievement
from app.infrastructure.database import (
    AttendanceRecord,
    Course,
    FollowUp,
    GradeRecord,
    Prediction,
    SchoolGrade,
    Student,
    TeacherAssignment,
    TeacherProfile,
    User,
)


def tutors_by_grade(db: Session) -> dict[int, str]:
    rows = (
        db.query(SchoolGrade)
        .options(joinedload(SchoolGrade.tutor).joinedload(TeacherProfile.user))
        .all()
    )
    return {
        row.id: row.tutor.user.full_name
        for row in rows
        if row.tutor and row.tutor.user
    }


def teachers_of_grade(db: Session, grade_id: int) -> list[dict]:
    rows = (
        db.query(TeacherAssignment)
        .options(
            joinedload(TeacherAssignment.teacher).joinedload(TeacherProfile.user),
            joinedload(TeacherAssignment.course),
        )
        .filter(TeacherAssignment.grade_id == grade_id)
        .all()
    )
    return [
        {
            "docente": row.teacher.user.full_name,
            "curso": row.course.nombre,
            "curso_id": row.course_id,
            "tutor": False,
        }
        for row in rows
        if row.teacher and row.teacher.user and row.course
    ]


def course_teacher_map(db: Session, grade_id: int) -> dict[int, str]:
    return {row["curso_id"]: row["docente"] for row in teachers_of_grade(db, grade_id)}


def institution_snapshot(db: Session) -> dict:
    grades = db.query(SchoolGrade).order_by(SchoolGrade.nivel, SchoolGrade.seccion).all()
    courses = db.query(Course).order_by(Course.id).all()
    teachers = db.query(TeacherProfile).options(joinedload(TeacherProfile.user)).all()
    students = (
        db.query(Student)
        .options(joinedload(Student.grade))
        .filter(Student.es_historico.is_(False))
        .all()
    )
    activos = [s for s in students if s.estado == StudentStatus.ACTIVO.value]
    preds = {
        p.student_id: p
        for p in db.query(Prediction).filter(Prediction.vigente.is_(True)).all()
    }
    tutor_map = tutors_by_grade(db)
    users = db.query(User).filter(User.is_active.is_(True)).all()
    followups = db.query(FollowUp).count()

    aulas = []
    for grade in grades:
        kids = [s for s in activos if s.grade_id == grade.id]
        risk = Counter(preds[s.id].nivel_riesgo for s in kids if s.id in preds)
        aulas.append(
            {
                "id": grade.id,
                "nombre": grade.nombre,
                "nivel": grade.nivel,
                "seccion": grade.seccion,
                "matriculados": len(kids),
                "tutor": tutor_map.get(grade.id, "Sin tutor de aula"),
                "alto": risk.get("alto", 0),
                "medio": risk.get("medio", 0),
                "bajo": risk.get("bajo", 0),
            }
        )

    return {
        "matriculados": len(activos),
        "salones": len(grades),
        "grados": len({g.nivel for g in grades}),
        "secciones": sorted({g.seccion for g in grades}),
        "docentes": len(teachers),
        "areas": len(courses),
        "usuarios": len(users),
        "seguimientos": followups,
        "por_rol": dict(Counter(u.role for u in users)),
        "aulas": aulas,
        "cursos": courses,
        "tutor_map": tutor_map,
        "role_labels": {
            Role.DIRECTORA.value: "Directora",
            Role.DOCENTE.value: "Docentes",
            Role.ESTUDIANTE.value: "Estudiantes con usuario",
        },
        "por_grado": [
            {"label": f"{n}.°", "value": sum(1 for s in activos if s.grade and s.grade.nivel == n), "color": "#1f4454"}
            for n in range(1, 7)
        ],
        "por_seccion": [
            {
                "label": sec,
                "value": sum(1 for s in activos if s.grade and s.grade.seccion == sec),
                "color": "#1b6b93",
            }
            for sec in ("A", "B", "C")
        ],
        "por_rol_bars": [
            {
                "label": {
                    Role.DIRECTORA.value: "Dirección",
                    Role.DOCENTE.value: "Docente",
                    Role.ESTUDIANTE.value: "Alumno",
                }.get(rol, rol),
                "value": n,
                "color": "#1f4454",
            }
            for rol, n in Counter(u.role for u in users).items()
        ],
        "riesgo_global": [
            {"label": "Alto", "value": sum(a["alto"] for a in aulas), "color": "#b42318"},
            {"label": "Medio", "value": sum(a["medio"] for a in aulas), "color": "#b58112"},
            {"label": "Bajo", "value": sum(a["bajo"] for a in aulas), "color": "#1f7a4d"},
        ],
        **_academic_kpis(db, activos),
        "tutores": sum(1 for a in aulas if a["tutor"] != "Sin tutor de aula"),
        "sin_tutor": sum(1 for a in aulas if a["tutor"] == "Sin tutor de aula"),
    }


def _academic_kpis(db: Session, activos: list[Student]) -> dict:
    ids = [s.id for s in activos]
    if not ids:
        return {"promedio_ie": 0, "asistencia_pct": 0, "notas_n": 0, "asistencias_n": 0}
    recs = db.query(GradeRecord).filter(GradeRecord.student_id.in_(ids)).all()
    atts = db.query(AttendanceRecord).filter(AttendanceRecord.student_id.in_(ids)).all()
    presente = sum(1 for a in atts if a.estado in {"presente", "tardanza", "justificada"})
    return {
        "promedio_ie": round(sum(r.nota for r in recs) / len(recs), 1) if recs else 0,
        "asistencia_pct": round(100.0 * presente / len(atts), 1) if atts else 0,
        "notas_n": len(recs),
        "asistencias_n": len(atts),
    }


def teacher_panel(db: Session, assignments: list, students: list[Student], preds: list[Prediction], tutored: list | None = None) -> dict:
    tutored = tutored or []
    salones_dictados = sorted({a.grade.nombre for a in assignments if a.grade})
    salones_tutor = sorted({g.nombre for g in tutored if g})
    salones = sorted(set(salones_dictados) | set(salones_tutor))
    cursos = sorted({a.course.nombre for a in assignments if a.course})
    cargas = [
        {
            "salon": a.grade.nombre if a.grade else "—",
            "curso": a.course.nombre if a.course else "—",
        }
        for a in assignments
        if a.grade
    ]
    cargas.sort(key=lambda row: (row["salon"], row["curso"]))
    pred_map = {p.student_id: p for p in preds}
    risk = Counter(pred_map[s.id].nivel_riesgo for s in students if s.id in pred_map)
    ids = [s.id for s in students]
    recs = db.query(GradeRecord).filter(GradeRecord.student_id.in_(ids or [-1])).all() if ids else []
    by_course: dict[str, list[float]] = {}
    course_names = {c.id: c.nombre for c in db.query(Course).all()}
    for rec in recs:
        by_course.setdefault(course_names.get(rec.course_id, "?"), []).append(rec.nota)
    promedios = [
        {"label": name[:12], "value": round(sum(vals) / len(vals), 1), "color": "#1f4454"}
        for name, vals in sorted(by_course.items())
    ]
    aulas = []
    by_grade: dict[int, list[Student]] = {}
    for student in students:
        by_grade.setdefault(student.grade_id or 0, []).append(student)
    for kids in by_grade.values():
        grade = kids[0].grade if kids else None
        local = Counter(pred_map[s.id].nivel_riesgo for s in kids if s.id in pred_map)
        aulas.append(
            {
                "nombre": grade.nombre if grade else "Sin salón",
                "matriculados": len(kids),
                "alto": local.get("alto", 0),
                "medio": local.get("medio", 0),
                "bajo": local.get("bajo", 0),
            }
        )
    aulas.sort(key=lambda row: row["nombre"])
    return {
        "salones": len(salones),
        "salones_nombres": salones,
        "cursos": len(cursos),
        "cursos_nombres": cursos,
        "es_tutor": bool(tutored),
        "es_aula": bool(assignments) and bool(tutored),
        "cargas": cargas,
        "alumnos": len(students),
        "alto": risk.get("alto", 0),
        "medio": risk.get("medio", 0),
        "bajo": risk.get("bajo", 0),
        "promedios": promedios,
        "aulas": aulas,
        "riesgo_bars": [
            {"label": "Alto", "value": risk.get("alto", 0), "color": "#b42318"},
            {"label": "Medio", "value": risk.get("medio", 0), "color": "#b58112"},
            {"label": "Bajo", "value": risk.get("bajo", 0), "color": "#1f7a4d"},
        ],
    }


def academic_evolution(table: dict, students: list[Student]) -> dict:
    b1 = [table.get((s.id, 1)) for s in students if table.get((s.id, 1)) is not None]
    b2 = [table.get((s.id, 2)) for s in students if table.get((s.id, 2)) is not None]
    avg1 = round(sum(b1) / len(b1), 1) if b1 else 0
    avg2 = round(sum(b2) / len(b2), 1) if b2 else 0
    deltas = []
    for student in students:
        n1, n2 = table.get((student.id, 1)), table.get((student.id, 2))
        if n1 is None or n2 is None:
            continue
        delta = round(n2 - n1, 1)
        deltas.append(
            {
                "nombre": student.full_name,
                "b1": n1,
                "b2": n2,
                "delta": delta,
                "baja": delta <= -1,
            }
        )
    return {
        "prom_b1": avg1,
        "prom_b2": avg2,
        "delta": round(avg2 - avg1, 1) if b1 and b2 else 0,
        "bajan": sum(1 for row in deltas if row["baja"]),
        "suben": sum(1 for row in deltas if row["delta"] >= 1),
        "bars": [
            {"label": "Bimestre 1", "value": avg1, "color": "#1b6b93"},
            {"label": "Bimestre 2", "value": avg2, "color": "#1f4454"},
        ],
        "deltas": deltas,
    }


def attendance_patterns(db: Session, students: list[Student]) -> dict:
    ids = [s.id for s in students]
    recs = (
        db.query(AttendanceRecord)
        .filter(AttendanceRecord.student_id.in_(ids or [-1]))
        .order_by(AttendanceRecord.fecha.asc())
        .all()
        if ids
        else []
    )
    by_student: dict[int, list] = {}
    totals = Counter()
    for rec in recs:
        by_student.setdefault(rec.student_id, []).append(rec)
        totals[rec.estado] += 1
    filas = []
    for student in students:
        att = by_student.get(student.id, [])
        total = len(att)
        falta = sum(1 for a in att if a.estado == "falta")
        tardanza = sum(1 for a in att if a.estado == "tardanza")
        presente = sum(1 for a in att if a.estado in {"presente", "tardanza", "justificada"})
        pct = round(100.0 * presente / total, 1) if total else 0
        racha = 0
        cur = 0
        for rec in att:
            if rec.estado == "falta":
                cur += 1
                racha = max(racha, cur)
            else:
                cur = 0
        trail = 0
        for rec in reversed(att):
            if rec.estado == "falta":
                trail += 1
            else:
                break
        patron = trail >= 3 or racha >= 3 or (total >= 10 and pct < 85)
        filas.append(
            {
                "id": student.id,
                "nombre": student.full_name,
                "dias": total,
                "faltas": falta,
                "tardanzas": tardanza,
                "pct": pct,
                "racha": racha,
                "trail": trail,
                "patron": patron,
            }
        )
    filas.sort(key=lambda row: (not row["patron"], row["pct"]))
    return {
        "filas": filas,
        "patron_n": sum(1 for row in filas if row["patron"]),
        "bars": [
            {"label": "Presente", "value": totals.get("presente", 0), "color": "#1f7a4d"},
            {"label": "Tardanza", "value": totals.get("tardanza", 0), "color": "#b58112"},
            {"label": "Falta", "value": totals.get("falta", 0), "color": "#b42318"},
            {"label": "Justif.", "value": totals.get("justificada", 0), "color": "#1b6b93"},
        ],
    }


def student_progress(student: Student) -> dict:
    recs = student.grades or []
    att = student.attendance or []
    by_course: dict[str, dict[int, float]] = {}
    for rec in recs:
        name = rec.course.nombre if rec.course else "Área"
        by_course.setdefault(name, {})[rec.bimestre] = rec.nota
    filas = []
    bien, mal, proceso = [], [], []
    b1_all, b2_all = [], []
    for name, bims in sorted(by_course.items()):
        vals = [bims[k] for k in sorted(bims)]
        avg = round(sum(vals) / len(vals), 1) if vals else 0
        nivel = achievement(avg)
        n1, n2 = bims.get(1), bims.get(2)
        if n1 is not None:
            b1_all.append(n1)
        if n2 is not None:
            b2_all.append(n2)
        filas.append({"area": name, "promedio": avg, "logro": nivel, "b1": n1, "b2": n2})
        if nivel in {"AD", "A"}:
            bien.append(name)
        elif nivel == "B":
            proceso.append(name)
        else:
            mal.append(name)
    presente = sum(1 for a in att if a.estado == "presente")
    falta = sum(1 for a in att if a.estado == "falta")
    tardanza = sum(1 for a in att if a.estado == "tardanza")
    just = sum(1 for a in att if a.estado == "justificada")
    avg1 = round(sum(b1_all) / len(b1_all), 1) if b1_all else 0
    avg2 = round(sum(b2_all) / len(b2_all), 1) if b2_all else 0
    return {
        "filas": filas,
        "bien": bien,
        "mal": mal,
        "proceso": proceso,
        "prom_b1": avg1,
        "prom_b2": avg2,
        "delta": round(avg2 - avg1, 1) if b1_all and b2_all else 0,
        "notas_bars": [{"label": f["area"][:10], "value": f["promedio"], "color": "#1f4454"} for f in filas],
        "evo_bars": [
            {"label": "Bimestre 1", "value": avg1, "color": "#1b6b93"},
            {"label": "Bimestre 2", "value": avg2, "color": "#1f4454"},
        ],
        "asistencia_bars": [
            {"label": "Presente", "value": presente, "color": "#1f7a4d"},
            {"label": "Tardanza", "value": tardanza, "color": "#b58112"},
            {"label": "Falta", "value": falta, "color": "#b42318"},
            {"label": "Justif.", "value": just, "color": "#1b6b93"},
        ],
    }
