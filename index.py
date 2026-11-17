"""Entrada de Vercel. Cada ruta llega a FastAPI con su dirección original."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.main import app  # noqa: E402

__all__ = ["app"]
