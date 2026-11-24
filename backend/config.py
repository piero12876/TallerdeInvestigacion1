import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent
ROOT_DIR = BACKEND_DIR.parent
FRONTEND_DIR = ROOT_DIR / "frontend"
load_dotenv(ROOT_DIR / ".env")

ON_RAILWAY = bool(os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RAILWAY_PROJECT_ID"))
ON_VERCEL = os.getenv("VERCEL") == "1" or bool(os.getenv("VERCEL_ENV"))
# En Vercel el disco del proyecto es de solo lectura. SQLite y el modelo van al temporal del sistema.
if ON_VERCEL:
    _scratch = Path(os.getenv("TMPDIR") or os.getenv("TEMP") or (os.sep + "tmp"))
    DATA_DIR = _scratch / "exellenti" / "data"
    ML_DIR = _scratch / "exellenti" / "ml"
else:
    DATA_DIR = ROOT_DIR / "data"
    ML_DIR = ROOT_DIR / "ml"

DATA_DIR.mkdir(parents=True, exist_ok=True)
ML_DIR.mkdir(parents=True, exist_ok=True)

def _flag(name: str, default: str = "") -> bool:
    return os.getenv(name, default).lower() in {"1", "true", "yes"}


def normalize_database_url(raw: str) -> str:
    """Railway entrega postgres://. SQLAlchemy usa psycopg 3.

    La URL interna (postgres.railway.internal) no lleva SSL. La pública sí.
    El panel de Railway parte el valor en dos líneas; un salto al copiar
    deja la contraseña inválida.
    """
    raw = raw.strip().strip('"').strip("'")
    if raw.startswith("postgres"):
        raw = "".join(raw.split())
    if raw.startswith("postgres://"):
        raw = "postgresql://" + raw[len("postgres://") :]
    if raw.startswith("postgresql://"):
        raw = "postgresql+psycopg://" + raw[len("postgresql://") :]
    if raw.startswith("postgresql") and "sslmode=" not in raw:
        host = raw.split("@")[-1].split("/")[0].split(":")[0]
        local = host in {"localhost", "127.0.0.1"} or host.endswith(".railway.internal")
        if not local:
            sep = "&" if "?" in raw else "?"
            raw = f"{raw}{sep}sslmode=require"
    return raw


SECRET_KEY = os.getenv("EXELLENTI_SECRET", "exellenti-dev-local-only")
_WEAK_SECRETS = {
    "",
    "exellenti-dev-local-only",
    "cambiar-esta-clave-en-cualquier-despliegue",
    "test-secret-exellenti",
}
if (ON_RAILWAY or ON_VERCEL) and SECRET_KEY in _WEAK_SECRETS:
    raise RuntimeError(
        "Defina EXELLENTI_SECRET en Railway o Vercel con una clave larga propia. "
        "No use la clave de desarrollo."
    )

_raw_database = os.getenv("DATABASE_URL") or os.getenv("EXELLENTI_DATABASE_URL")
if not _raw_database:
    _raw_database = f"sqlite:///{(DATA_DIR / 'exellenti.db').as_posix()}"
DATABASE_URL = normalize_database_url(_raw_database)
MODEL_PATH = Path(os.getenv("EXELLENTI_MODEL_PATH", str(ML_DIR / "modelo_desercion.joblib")))
HOST = os.getenv("EXELLENTI_HOST", "0.0.0.0" if (ON_RAILWAY or ON_VERCEL) else "127.0.0.1")
PORT = int(os.getenv("PORT") or os.getenv("EXELLENTI_PORT") or "3939")
ANIO_LECTIVO = 2026
INSTITUCION = "Institución Educativa Exellenti"
DISTRITO = "El Tambo"
PROVINCIA = "Huancayo"
SKIP_ML = _flag("EXELLENTI_SKIP_ML")
TESTING = _flag("EXELLENTI_TESTING")
HTTPS_ONLY = _flag("EXELLENTI_HTTPS", "1" if (ON_RAILWAY or ON_VERCEL) else "0")
SCHEMA_VERSION = "2026-9"
