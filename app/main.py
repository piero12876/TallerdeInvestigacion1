from urllib.parse import urlparse

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.config import BASE_DIR, SECRET_KEY, SKIP_ML
from app.domain.validate import safe_next
from app.infrastructure.database import ModelRun, Prediction, SessionLocal, init_db, reset_if_stale
from app.infrastructure.ml_engine import predict_all, train_and_select
from app.infrastructure.seed import seed_if_empty
from app.presentation.web import router

app = FastAPI(title="IE Exellenti — Riesgo de deserción")
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    session_cookie="exellenti_session",
    same_site="lax",
    https_only=False,
    max_age=60 * 60 * 8,
)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "presentation" / "static")), name="static")
app.include_router(router)


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
    reset_if_stale()
    init_db()
    db = SessionLocal()
    try:
        seed_if_empty(db)
        if SKIP_ML:
            return
        has_model = db.query(ModelRun).filter(ModelRun.selected.is_(True)).first()
        if not has_model:
            train_and_select(db)
            predict_all(db)
        elif not db.query(Prediction).filter(Prediction.vigente.is_(True)).first():
            predict_all(db)
    finally:
        db.close()
