"""
Authentication persistence across backend restarts.

Users are stored in the file-backed database (never in process memory), so a
backend restart or re-initialization must not lose registered accounts and they
must still be able to log in with the same (hashed) password.
"""

import os
import subprocess
import sys
from pathlib import Path

from conftest import TEST_DB_FILE, restart_database

_BACKEND_DIR = Path(__file__).resolve().parents[1]
_ROOT_DIR = _BACKEND_DIR.parent


def _register(client, email):
    r = client.post("/api/auth/register", json={"email": email, "password": "supersecret1"})
    assert r.status_code == 201, r.text
    return r.json()


def test_user_exists_in_database_after_register(client, db_path):
    email, password = "persist@example.com", "supersecret1"
    r = _register(client, email)

    from sqlalchemy.orm import sessionmaker

    from app.utils.security import verify_password
    from app.database import Base
    from sqlalchemy import create_engine

    from app.models.user import User

    url = "sqlite:///" + str(db_path)
    engine = create_engine(url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    with Session() as db:
        user = db.query(User).filter(User.email == email).one()
        assert user.id == r["user"]["id"]
        assert user.password_hash != password, "password must not be stored in plain text"
        assert verify_password(password, user.password_hash), "stored bcrypt hash must verify"


def test_login_works_after_single_restart(client):
    """register -> restart (fresh engine, same DB file) -> login."""
    email, password = "restart1@example.com", "supersecret1"
    _register(client, email)

    restart_database()

    r = client.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200, me.text
    assert me.json()["email"] == email


def test_login_works_after_multiple_restarts(client):
    email, password = "restart_many@example.com", "supersecret1"
    _register(client, email)

    for _ in range(3):
        restart_database()

    r = client.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {r.json()['access_token']}"})
    assert me.status_code == 200 and me.json()["email"] == email


def test_users_accumulate_across_restarts(client):
    """Restarting must never truncate the user table — previously and newly
    registered users all remain."""
    first = "accum1@example.com"
    _register(client, first)
    restart_database()
    second = "accum2@example.com"
    _register(client, second)
    restart_database()

    for email in (first, second):
        r = client.post("/api/auth/login", json={"email": email, "password": "supersecret1"})
        assert r.status_code == 200, f"{email} should still log in via {r.text}"


def test_cross_process_restart_preserves_user(db_path):
    """True process-level restart: a separate Python process registers a user,
    exits, then another process logs in against the same DB file."""
    env = {
        "DATABASE_URL": f"sqlite:///{db_path}",
        "UPLOAD_DIR": str(db_path.parent / "uploads"),
        "MAX_UPLOAD_SIZE_MB": "2",
        "AI_MODE": "mock",
        "JWT_SECRET_KEY": "test-secret",
        "ACCESS_TOKEN_EXPIRE_MINUTES": "60",
    }
    import os

    python_path = os.pathsep.join([str(_BACKEND_DIR), str(_ROOT_DIR)])
    base = {
        "PYTHONPATH": python_path,
        **os.environ,
        **env,
    }

    register_script = (
        "import os\n"
        "from fastapi.testclient import TestClient\n"
        "from app.main import app\n"
        "with TestClient(app) as c:\n"
        "    r = c.post('/api/auth/register', json={'email':'xproc@example.com','password':'supersecret1'})\n"
        "    assert r.status_code == 201, r.text\n"
        "print('registered')"
    )
    login_script = (
        "import os\n"
        "from fastapi.testclient import TestClient\n"
        "from app.main import app\n"
        "with TestClient(app) as c:\n"
        "    r = c.post('/api/auth/login', json={'email':'xproc@example.com','password':'supersecret1'})\n"
        "    assert r.status_code == 200, r.text\n"
        "    assert c.get('/api/auth/me', headers={'Authorization': f\"Bearer {r.json()['access_token']}\"}).status_code == 200\n"
        "print('logged_in')"
    )

    py = sys.executable
    r1 = subprocess.run([py, "-c", register_script], capture_output=True, text=True, env=base, cwd=os.getcwd())
    assert r1.returncode == 0, r1.stderr
    r2 = subprocess.run([py, "-c", login_script], capture_output=True, text=True, env=base, cwd=os.getcwd())
    assert r2.returncode == 0, r2.stderr
    assert "logged_in" in r2.stdout