import logging
from urllib.parse import urlparse

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from backend.config import (
    DATABASE_URL,
    FRONTEND_DIR,
    HTTPS_ONLY,
    MODEL_PATH,
    ON_RAILWAY,
    SECRET_KEY,
    SKIP_ML,
)
from backend.domain.validate import safe_next
from backend.infrastructure.database import ModelRun, Prediction, SessionLocal, init_db, reset_if_stale
from ml.engine import predict_all, train_and_select
from backend.infrastructure.seed import seed_if_empty
from backend.presentation.web import router

app = FastAPI(title="IE Exellenti — Riesgo de deserción")
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    session_cookie="exellenti_session",
    same_site="lax",
    https_only=HTTPS_ONLY,
    max_age=60 * 60 * 8,
)
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR / "static")), name="static")
app.include_router(router)


@app.get("/health")
def health():
    return {"ok": True}


@app.exception_handler(RequestValidationError)
async def invalid_form(request: Request, _exc: RequestValidationError):
    try:
        request.session["flash"] = "Revise los datos: hay un valor no válido."
    except Exception:
        pass
    referer = request.headers.get("referer") or "/"
    path = urlparse(referer).path or "/"
    return RedirectResponse(safe_next(path), status_code=303)


@app.on_event("startup")
def startup() -> None:
    if ON_RAILWAY and DATABASE_URL.startswith("sqlite"):
        logging.getLogger("exellenti").warning(
            "Railway está usando SQLite. Esos datos se pierden en cada deploy. "
            "Agregue PostgreSQL en el mismo proyecto para que exista DATABASE_URL."
        )
    reset_if_stale()
    init_db()
    db = SessionLocal()
    try:
        seed_if_empty(db)
        if SKIP_ML:
            return
        has_model = db.query(ModelRun).filter(ModelRun.selected.is_(True)).first()
        # El archivo del modelo no viaja en git y el disco de Railway se vacía
        # en cada deploy. Si falta, se vuelve a entrenar con los datos de la base.
        if not has_model or not MODEL_PATH.exists():
            train_and_select(db)
            predict_all(db)
        elif not db.query(Prediction).filter(Prediction.vigente.is_(True)).first():
            predict_all(db)
    finally:
        db.close()
