from collections import Counter
from http.cookiejar import CookieJar
from urllib.parse import urlencode
from urllib.request import HTTPCookieProcessor, Request, build_opener
import re

from app.domain.enums import StudentStatus
from app.infrastructure.database import ModelRun, Prediction, SchoolGrade, SessionLocal, Student, User

db = SessionLocal()
print("salones", db.query(SchoolGrade).count())
print(
    "activos",
    db.query(Student).filter(Student.es_historico.is_(False), Student.estado == StudentStatus.ACTIVO.value).count(),
)
print("historicos", db.query(Student).filter(Student.es_historico.is_(True)).count())
print("=== MODELOS ===")
for row in db.query(ModelRun).order_by(ModelRun.selected.desc(), ModelRun.f1.desc()).all():
    print(
        f"{row.algoritmo}|sel={row.selected}|rec={row.recall:.3f}±{row.recall_std:.3f}"
        f"|f1={row.f1:.3f}|prauc={row.pr_auc:.3f}|acc={row.accuracy:.3f}|folds={row.cv_folds}"
    )
preds = db.query(Prediction).filter(Prediction.vigente.is_(True)).all()
print("pred", len(preds))
print("atencion", dict(Counter(p.nivel_riesgo for p in preds)))
print("modelo", dict(Counter(p.nivel_modelo for p in preds)))
print(
    "clave_temporal vacias",
    db.query(User).filter(User.clave_temporal == "").count(),
    "/",
    db.query(User).count(),
)
db.close()

BASE = "http://127.0.0.1:3939"
opener = build_opener(HTTPCookieProcessor(CookieJar()))
html = opener.open(BASE + "/login").read().decode()
assert "Dir#Ex26" not in html
csrf = re.search(r'name="csrf" value="([^"]+)"', html).group(1)
data = urlencode({"username": "directora", "password": "Dir#Ex26", "csrf": csrf}).encode()
opener.open(Request(BASE + "/login", data=data, method="POST"))
body = opener.open(BASE + "/").read().decode()
assert "Panel de dirección" in body
modelo = opener.open(BASE + "/modelo").read().decode()
assert "entorno sintético" in modelo.lower() or "Validación cruzada" in modelo
csv_body = opener.open(BASE + "/riesgo/exportar").read().decode("utf-8-sig")
assert "prioridad" in csv_body and "nivel_modelo" in csv_body
print("HTTP director+modelo+csv OK")
