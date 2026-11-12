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

SECRET_KEY = os.getenv("EXELLENTI_SECRET", "exellenti-dev-local-only")
DATABASE_URL = os.getenv(
    "EXELLENTI_DATABASE_URL",
    f"sqlite:///{(DATA_DIR / 'exellenti.db').as_posix()}",
)
MODEL_PATH = Path(os.getenv("EXELLENTI_MODEL_PATH", str(ML_DIR / "modelo_desercion.joblib")))
HOST = os.getenv("EXELLENTI_HOST", "127.0.0.1")
PORT = int(os.getenv("EXELLENTI_PORT", "3939"))
ANIO_LECTIVO = 2026
INSTITUCION = "Institución Educativa Exellenti"
DISTRITO = "El Tambo"
PROVINCIA = "Huancayo"
SKIP_ML = os.getenv("EXELLENTI_SKIP_ML", "").lower() in {"1", "true", "yes"}
TESTING = os.getenv("EXELLENTI_TESTING", "").lower() in {"1", "true", "yes"}
SCHEMA_VERSION = "2026-7"
