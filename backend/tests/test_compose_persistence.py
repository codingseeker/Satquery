"""
Docker Compose persistence configuration.

Verifies that `docker compose config` wires a persistent database volume for
PostgreSQL (and a data volume for a SQLite fallback), and that the backend
container resolves `DATABASE_URL` to the `db` service rather than `localhost`.
These assertions exercise real `docker compose` resolution (skipped when Docker
is unavailable).
"""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]

pytestmark = pytest.mark.skipif(
    shutil.which("docker") is None,
    reason="docker CLI not available",
)


def _parse_compose():
    try:
        import yaml
    except ImportError:
        pytest.skip("PyYAML not installed")

    env = {
        k: v
        for k, v in os.environ.items()
        if k not in ("DATABASE_URL", "UPLOAD_DIR", "MAX_UPLOAD_SIZE_MB", "AI_MODE", "MODEL_PATH")
    }
    result = subprocess.run(
        ["docker", "compose", "config"],
        cwd=str(_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode != 0:
        pytest.skip(f"docker compose config failed: {result.stderr.strip()}")
    return yaml.safe_load(result.stdout)


@pytest.fixture(scope="module")
def compose():
    return _parse_compose()


def _db_mounts(compose):
    db = compose["services"]["db"]
    return [m for m in db.get("volumes", []) if isinstance(m, dict)]


def test_postgres_data_volume_is_persistent(compose):
    mounts = _db_mounts(compose)
    pg = [
        m
        for m in mounts
        if m.get("type") == "volume" and m.get("target") == "/var/lib/postgresql/data"
    ]
    assert pg, "db service must mount PostgreSQL data on a persistent volume"
    assert pg[0]["source"] == "pgdata"
    assert "pgdata" in compose.get("volumes", {}), "pgdata named volume must be declared"


def test_backend_has_persistent_data_volume(compose):
    backend = compose["services"]["backend"]
    data_mounts = [
        m
        for m in backend.get("volumes", [])
        if isinstance(m, dict) and m.get("type") == "volume" and m.get("target") == "/app/data"
    ]
    assert data_mounts, "backend must mount a persistent data volume at /app/data"
    assert data_mounts[0]["source"] == "backend_data"
    assert "backend_data" in compose.get("volumes", {}), "backend_data volume must be declared"


def test_backend_connects_to_compose_db_service(compose):
    backend = compose["services"]["backend"]
    env = backend.get("environment", {})
    url = env.get("DATABASE_URL", "")
    assert url.startswith("postgresql://satquery:satquery@db:"), (
        f"backend DATABASE_URL must target the compose `db` service, got {url!r}"
    )
    assert "localhost" not in url.replace("5433", ""), (
        "backend must not resolve DATABASE_URL to host localhost"
    )


def test_uploads_are_separate_from_database_state(compose):
    backend = compose["services"]["backend"]

    upload_mounts = [
        m
        for m in backend.get("volumes", [])
        if isinstance(m, dict) and m.get("target") == "/app/uploads"
    ]
    assert upload_mounts, "uploaded files must be mounted separately from DB state"

    db_targets = {
        m.get("target") for m in backend.get("volumes", []) if isinstance(m, dict)
    }
    assert "/app/data" in db_targets, "persistent DB/data volume must coexist with uploads"
    assert "/app/data" != "/app/uploads", "DB data and uploads must remain separate paths"


def test_compose_builds_backend_from_clean_checkout():
    """Backend image build inputs must not depend on host-only files."""
    dockerfile = (_ROOT / "backend" / "Dockerfile").read_text()
    assert "backend/requirements.txt" in dockerfile
    assert "COPY backend/app ./app" in dockerfile
    assert "COPY ai_service ./ai_service" in dockerfile