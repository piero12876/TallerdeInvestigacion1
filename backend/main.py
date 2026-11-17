import logging
from urllib.parse import urlparse

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from backend.config import (
    DATABASE_URL,
    FRONTEND_DIR,
    HTTPS_ONLY,
    MODEL_PATH,
    ON_RAILWAY,
    ON_VERCEL,
    SECRET_KEY,
    SKIP_ML,
)
from backend.domain.validate import safe_next
from backend.infrastructure.database import (
    Base,
    ModelRun,
    Prediction,
    SessionLocal,
    init_db,
    ping_db,
    reset_if_stale,
)
from ml.engine import predict_all, train_and_select
from backend.infrastructure.seed import fill_missing_bimesters, seed_if_empty
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

_startup_error = ""

_DB_HELP = {
    "internal": (
        "Vercel tiene la dirección interna de Railway. "
        "En DATABASE_URL pegue DATABASE_PUBLIC_URL, la que usa tramway.proxy.rlwy.net."
    ),
    "auth": (
        "Postgres rechazó la contraseña. En Railway pulse el icono de copiar de "
        "DATABASE_PUBLIC_URL, no seleccione el texto con el mouse: está partido en dos líneas. "
        "Pegue ese valor en Vercel y vuelva a desplegar."
    ),
    "db": (
        "No se pudo conectar. En Vercel, DATABASE_URL debe ser el valor completo de "
        "DATABASE_PUBLIC_URL."
    ),
}


@app.middleware("http")
async def db_guard(request: Request, call_next):
    if _startup_error and request.url.path not in {"/health", "/favicon.ico"}:
        return HTMLResponse(
            "<h1>No se pudo abrir la base</h1><p>"
            + _DB_HELP.get(_startup_error, _DB_HELP["db"])
            + "</p>",
            status_code=503,
        )
    return await call_next(request)


@app.get("/health")
def health():
    if _startup_error:
        return JSONResponse({"ok": False, "db": "down"}, status_code=503)
    ping_db()
    return {"ok": True, "db": "up"}


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
    global _startup_error
    try:
        _startup()
        _startup_error = ""
    except Exception as exc:
        logging.getLogger("exellenti").exception("La base no quedó lista")
        text = str(exc).lower()
        if "railway.internal" in DATABASE_URL:
            _startup_error = "internal"
        elif "password authentication failed" in text:
            _startup_error = "auth"
        else:
            _startup_error = "db"


def _startup() -> None:
    if (ON_RAILWAY or ON_VERCEL) and DATABASE_URL.startswith("sqlite"):
        logging.getLogger("exellenti").warning(
            "La base es SQLite en un disco temporal. En Railway agregue PostgreSQL "
            "para que exista DATABASE_URL. En Vercel los datos no sobreviven al reinicio."
        )
    reset_if_stale()
    init_db()
    logging.getLogger("exellenti").info(
        "Tablas listas (%s): %s",
        "sqlite" if DATABASE_URL.startswith("sqlite") else "postgresql",
        ", ".join(sorted(Base.metadata.tables)),
    )
    db = SessionLocal()
    try:
        seed_if_empty(db)
        fill_missing_bimesters(db)
    finally:
        db.close()
    if SKIP_ML or ON_VERCEL:
        return
    db = SessionLocal()
    try:
        has_model = db.query(ModelRun).filter(ModelRun.selected.is_(True)).first()
        if not has_model or not MODEL_PATH.exists():
            train_and_select(db)
            predict_all(db)
        elif not db.query(Prediction).filter(Prediction.vigente.is_(True)).first():
            predict_all(db)
    except Exception:
        logging.getLogger("exellenti").exception("El modelo no se entrenó; el ingreso sigue disponible")
    finally:
        db.close()
