import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ["EXELLENTI_TESTING"] = "1"
os.environ["EXELLENTI_SKIP_ML"] = "1"
os.environ["EXELLENTI_SECRET"] = "test-secret-exellenti"
tmp = Path(tempfile.gettempdir()) / "exellenti_pytest.db"
if tmp.exists():
    tmp.unlink()
os.environ["EXELLENTI_DATABASE_URL"] = f"sqlite:///{tmp.as_posix()}"
sys.path.insert(0, str(ROOT))

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        yield test_client
