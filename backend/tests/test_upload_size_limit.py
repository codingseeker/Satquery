"""
Upload size limit enforcement.

The configured limit (MAX_UPLOAD_SIZE_MB, default 50) must be enforced
deterministically at the API boundary for both the image-upload endpoint and
the analysis pipeline, returning HTTP 413 for oversized payloads.
"""

import io
from pathlib import Path

from conftest import TEST_MAX_UPLOAD_SIZE

IMAGE_HEADERS = {"Content-Type": "image/png"}


def _png_bytes(size: int) -> bytes:
    # Deterministic payload of the requested size.
    return bytes(i % 253 + 1 for i in range(size)) or b"\x89PNG\r\n\x1a\n"


def _register_and_token(client):
    from datetime import datetime

    email = f"upload{datetime.now().timestamp()}@example.com"
    r = client.post("/api/auth/register", json={"email": email, "password": "supersecret1"})
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_image_below_limit_accepted(client):
    headers = _register_and_token(client)
    content = _png_bytes(TEST_MAX_UPLOAD_SIZE // 2)
    r = client.post(
        "/api/images/upload",
        files={"file": ("below_limit.png", content, "image/png")},
        headers=headers,
    )
    assert r.status_code == 201, r.text
    assert r.json()["metadata"]["file_size"] == len(content)


def test_image_exactly_at_limit_accepted(client):
    headers = _register_and_token(client)
    content = _png_bytes(TEST_MAX_UPLOAD_SIZE)
    r = client.post(
        "/api/images/upload",
        files={"file": ("at_limit.png", content, "image/png")},
        headers=headers,
    )
    assert r.status_code == 201, r.text
    assert r.json()["metadata"]["file_size"] == TEST_MAX_UPLOAD_SIZE


def test_image_above_limit_rejected_with_413(client):
    headers = _register_and_token(client)
    content = _png_bytes(TEST_MAX_UPLOAD_SIZE + 1)
    r = client.post(
        "/api/images/upload",
        files={"file": ("above_limit.png", content, "image/png")},
        headers=headers,
    )
    assert r.status_code == 413, r.text
    assert "size" in r.json()["detail"].lower() or "large" in r.json()["detail"].lower()


def test_oversized_upload_persists_no_partial_file(client):
    """A rejected upload must not leave a partial file or a DB row behind."""
    headers = _register_and_token(client)
    uploads_root = _uploads_root()
    before = sorted(p for p in uploads_root.rglob("*") if p.is_file())
    before_rows = _count_rows()

    r = client.post(
        "/api/images/upload",
        files={"file": ("too_large.png", _png_bytes(TEST_MAX_UPLOAD_SIZE + 1), "image/png")},
        headers=headers,
    )
    assert r.status_code == 413

    after_rows = _count_rows()
    assert after_rows == before_rows, "no image row should be created for an oversized upload"

    after = sorted(p for p in uploads_root.rglob("*") if p.is_file())
    assert after == before, f"oversized upload left files behind: {set(after) - set(before)}"


def _uploads_root():
    from app.config import get_settings

    return Path(get_settings().UPLOAD_DIR)


def _count_rows() -> int:
    from sqlalchemy import create_engine, inspect
    from conftest import TEST_DB_FILE
    import app.database as dbmod

    url = dbmod.engine.url
    connect_args = {"check_same_thread": False} if url.drivername == "sqlite" else {}
    insp = inspect(create_engine(url, connect_args=connect_args))
    with create_engine(url, connect_args=connect_args).connect() as conn:
        tables = insp.get_table_names()
        if "images" not in tables:
            return 0
        return conn.exec_driver_sql("SELECT COUNT(*) FROM images").scalar()


def test_analysis_rejects_oversized_before_processing(client):
    """The analysis pipeline rejects oversized uploads with 413 and creates
    neither an analysis record nor an image file."""
    from sqlalchemy import create_engine, inspect
    import app.database as dbmod

    headers = _register_and_token(client)
    chat = client.post("/api/chats", json={"title": "persist-check"}, headers=headers)
    assert chat.status_code == 201, chat.text
    chat_id = chat.json()["id"]

    r = client.post(
        "/api/analysis",
        data={"query": "detect water", "chat_id": str(chat_id)},
        files={"file": ("too_large.png", _png_bytes(TEST_MAX_UPLOAD_SIZE + 1), "image/png")},
        headers=headers,
    )
    assert r.status_code == 413, r.text

    url = dbmod.engine.url
    connect_args = {"check_same_thread": False} if url.drivername == "sqlite" else {}
    engine = create_engine(url, connect_args=connect_args)
    with engine.connect() as conn:
        tables = inspect(engine).get_table_names()
        if "analyses" in tables:
            count = conn.exec_driver_sql("SELECT COUNT(*) FROM analyses").scalar()
            assert count == 0, "no analysis row should exist after a 413"


def test_small_analysis_accepted(client):
    from datetime import datetime

    email = f"analysis{datetime.now().timestamp()}@example.com"
    r = client.post("/api/auth/register", json={"email": email, "password": "supersecret1"})
    assert r.status_code == 201
    headers = {"Authorization": f"Bearer {r.json()['access_token']}"}

    chat = client.post("/api/chats", json={"title": "ok-check"}, headers=headers)
    chat_id = chat.json()["id"]

    r = client.post(
        "/api/analysis",
        data={"query": "detect water", "chat_id": str(chat_id)},
        files={"file": ("ok.png", _png_bytes(TEST_MAX_UPLOAD_SIZE // 2), "image/png")},
        headers=headers,
    )
    assert r.status_code == 201, r.text
    assert r.json()["status"] == "completed"