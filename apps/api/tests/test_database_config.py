from app.db.database import DEFAULT_SQLITE_DATABASE_URL, build_engine_options, resolve_database_url


def test_resolve_database_url_defaults_to_sqlite():
    assert resolve_database_url(None) == DEFAULT_SQLITE_DATABASE_URL
    assert resolve_database_url("") == DEFAULT_SQLITE_DATABASE_URL


def test_build_engine_options_uses_sqlite_connect_args():
    options = build_engine_options("sqlite:///./taskgenie.db")
    assert options["connect_args"] == {"check_same_thread": False}


def test_build_engine_options_skips_sqlite_specific_args_for_postgres():
    options = build_engine_options("postgresql://taskgenie:secret@localhost:5432/taskgenie")
    assert options == {}
