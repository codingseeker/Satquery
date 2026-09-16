"""
Database initialization behaviour.

Startup uses ``Base.metadata.create_all`` which must be idempotent and
non-destructive: it creates missing tables but never drops or wipes existing
data, so application state survives re-initialization.
"""

from conftest import restart_database


def test_create_all_is_idempotent():
    """Re-running schema creation must not duplicate or drop anything."""
    from sqlalchemy import create_engine, inspect

    from app.database import Base
    import app.database as dbmod

    url = dbmod.engine.url
    connect_args = {"check_same_thread": False} if url.drivername == "sqlite" else {}
    engine = create_engine(url, connect_args=connect_args)

    before = set(inspect(engine).get_table_names())
    Base.metadata.create_all(bind=engine)
    after = set(inspect(engine).get_table_names())
    assert after == before


def test_restart_does_not_wipe_existing_records(client):
    """A DB with existing rows must keep those rows after re-init + restart."""
    import app.database as dbmod

    from sqlalchemy import create_engine

    url = dbmod.engine.url
    connect_args = {"check_same_thread": False} if url.drivername == "sqlite" else {}
    engine = create_engine(url, connect_args=connect_args)

    r = client.post("/api/auth/register", json={"email": "keepme@example.com", "password": "supersecret1"})
    assert r.status_code == 201
    registered = r.json()["user"]["id"]

    # Re-run init on the same file — nothing should be wiped.
    from app.database import Base

    Base.metadata.create_all(bind=engine)
    _assert_user_count_at_least(engine, 1)

    # Full app restart simulation (new engine + init on the same file).
    restart_database()

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {r.json()['access_token']}"})
    assert me.status_code == 200
    assert me.json()["id"] == registered


def _assert_user_count_at_least(engine, n: int):
    from sqlalchemy import inspect

    tables = inspect(engine).get_table_names()
    assert "users" in tables
    with engine.connect() as conn:
        count = conn.exec_driver_sql("SELECT COUNT(*) FROM users").scalar()
    assert count >= n


def test_sqlite_parent_directory_is_created():
    """Startup creates the parent directory of a file-based SQLite DB so that
    ``create_all`` does not fail on a fresh checkout."""
    import tempfile
    from pathlib import Path

    from sqlalchemy import create_engine

    import app.main as main_module
    from app.database import Base

    with tempfile.TemporaryDirectory() as tmp:
        nested = Path(tmp) / "a" / "b" / "db.sqlite"
        assert not nested.parent.exists()

        settings = main_module.settings.model_copy(
            update={"DATABASE_URL": f"sqlite:///{nested}"}
        )
        original = main_module.settings
        main_module.settings = settings
        try:
            main_module._ensure_database_dir()
            assert nested.parent.is_dir(), "sqlite parent dir must be created at startup"

            engine = create_engine(f"sqlite:///{nested}", connect_args={"check_same_thread": False})
            Base.metadata.create_all(bind=engine)
            with engine.connect() as conn:
                tables = conn.exec_driver_sql(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            assert tables, "schema should be created after ensure_database_dir"
        finally:
            main_module.settings = original


def test_startup_code_has_no_destructive_init():
    """Guard: startup/runtime code must never drop tables or delete the DB."""
    from pathlib import Path

    root = Path(__file__).resolve().parents[1] / "app"
    greps = {
        "drop_all": "drop_all",
        "Base.metadata.drop": "drop",
        "os.remove(database": "remove",
    }
    for path in (root / "main.py", root / "database.py", root / "config.py"):
        text = path.read_text()
        assert "drop_all" not in text, f"destructive drop_all found in {path}"
        assert "DROP TABLE" not in text.upper(), f"destructive DROP TABLE found in {path}"