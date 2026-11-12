import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent
ROOT_DIR = BACKEND_DIR.parent
FRONTEND_DIR = ROOT_DIR / "frontend"
DATA_DIR = ROOT_DIR / "data"
ML_DIR = ROOT_DIR / "ml"
load_dotenv(ROOT_DIR / ".env")

DATA_DIR.mkdir(exist_ok=True)
ML_DIR.mkdir(exist_ok=True)

def _flag(name: str, default: str = "") -> bool:
    return os.getenv(name, default).lower() in {"1", "true", "yes"}


def normalize_database_url(raw: str) -> str:
    """Railway entrega postgres://; SQLAlchemy usa el driver psycopg 3."""
    if raw.startswith("postgres://"):
        raw = "postgresql://" + raw[len("postgres://") :]
    if raw.startswith("postgresql://"):
        raw = "postgresql+psycopg://" + raw[len("postgresql://") :]
    return raw


ON_RAILWAY = bool(os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RAILWAY_PROJECT_ID"))
SECRET_KEY = os.getenv("EXELLENTI_SECRET", "exellenti-dev-local-only")
_WEAK_SECRETS = {
    "",
    "exellenti-dev-local-only",
    "cambiar-esta-clave-en-cualquier-despliegue",
    "test-secret-exellenti",
}
if ON_RAILWAY and SECRET_KEY in _WEAK_SECRETS:
    raise RuntimeError(
        "Defina EXELLENTI_SECRET en Railway con una clave larga propia. "
        "No use la clave de desarrollo."
    )

_raw_database = os.getenv("DATABASE_URL") or os.getenv("EXELLENTI_DATABASE_URL")
if not _raw_database:
    _raw_database = f"sqlite:///{(DATA_DIR / 'exellenti.db').as_posix()}"
DATABASE_URL = normalize_database_url(_raw_database)
MODEL_PATH = Path(os.getenv("EXELLENTI_MODEL_PATH", str(ML_DIR / "modelo_desercion.joblib")))
HOST = os.getenv("EXELLENTI_HOST", "0.0.0.0" if ON_RAILWAY else "127.0.0.1")
PORT = int(os.getenv("PORT") or os.getenv("EXELLENTI_PORT") or "3939")
ANIO_LECTIVO = 2026
INSTITUCION = "Institución Educativa Exellenti"
DISTRITO = "El Tambo"
PROVINCIA = "Huancayo"
SKIP_ML = _flag("EXELLENTI_SKIP_ML")
TESTING = _flag("EXELLENTI_TESTING")
HTTPS_ONLY = _flag("EXELLENTI_HTTPS", "1" if ON_RAILWAY else "0")
SCHEMA_VERSION = "2026-9"
