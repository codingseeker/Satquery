"""
Shared pytest fixtures.

Important: the environment below MUST be set before any ``app.*`` module is
imported, because the database engine and settings are created at import time.
The whole test session runs against an isolated SQLite file on disk so tests
can cheaply exercise "restart" behaviour without touching a real PostgreSQL.
"""

import os
import sys
import tempfile
from pathlib import Path

import pytest

_BACKEND_DIR = Path(__file__).resolve().parents[1]
_ROOT_DIR = _BACKEND_DIR.parent

# Make `app` and `ai_service` importable from any invocation directory.
for _p in (_BACKEND_DIR, _ROOT_DIR):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

# Isolated, persistent-on-disk SQLite database for the whole session. From the
# backend's point of view this is a normal file-backed database, so restarting
# the application (new engine, same file) must keep registered users.
_TESTS_TMP = Path(tempfile.mkdtemp(prefix="satquery-tests-"))
os.environ["DATABASE_URL"] = f"sqlite:///{_TESTS_TMP / 'test_app.db'}"
os.environ["UPLOAD_DIR"] = str(_TESTS_TMP / "uploads")
os.environ["MAX_UPLOAD_SIZE_MB"] = "2"
os.environ["AI_MODE"] = "mock"
os.environ["JWT_SECRET_KEY"] = "test-secret"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "60"

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.database import Base  # noqa: E402
import app.database as dbmod  # noqa: E402
from app.main import app  # noqa: E402

TEST_DB_FILE = _TESTS_TMP / "test_app.db"
TEST_MAX_UPLOAD_SIZE_MB = 2
TEST_MAX_UPLOAD_SIZE = TEST_MAX_UPLOAD_SIZE_MB * 1024 * 1024


def restart_database():
    """Simulate a backend restart: dispose the pool, open the SAME database
    file with a brand-new engine and session factory, and re-run the
    non-destructive schema init exactly like startup does."""
    dbmod.engine.dispose()
    url = dbmod.engine.url
    connect_args = {"check_same_thread": False} if url.drivername == "sqlite" else {}
    engine = create_engine(url, connect_args=connect_args)
    Base.metadata.create_all(bind=engine)
    dbmod.engine = engine
    dbmod.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def db_path():
    return TEST_DB_FILE


@pytest.fixture()
def register_user():
    """Register a unique user and return (email, password, auth headers)."""

    def _register(index: int = 0):
        from datetime import datetime

        email = f"user{datetime.now().timestamp()}{index}@example.com"
        password = "supersecret1"
        payload = {"email": email, "password": password}
        with TestClient(app) as c:
            r = c.post("/api/auth/register", json=payload)
            assert r.status_code == 201, r.text
            token = r.json()["access_token"]
        return email, password, {"Authorization": f"Bearer {token}"}

    return _register