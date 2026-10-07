"""Environment-driven configuration and database migrations."""
import pytest
from flask_migrate import check, upgrade
from sqlalchemy import create_engine, inspect

from webapp.settings import build_config, normalize_database_url


def test_database_url_normalisation():
    assert normalize_database_url("postgres://u:p@h:5432/db") == "postgresql+psycopg2://u:p@h:5432/db"
    assert normalize_database_url("postgresql://u:p@h/db") == "postgresql+psycopg2://u:p@h/db"
    assert normalize_database_url("postgresql+psycopg2://u@h/db") == "postgresql+psycopg2://u@h/db"
    assert normalize_database_url("sqlite:///x.db") == "sqlite:///x.db"


def test_production_requires_secret_key(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        build_config()
    monkeypatch.setenv("SECRET_KEY", "a" * 40)
    cfg = build_config()
    assert cfg["SESSION_COOKIE_SECURE"] and cfg["REMEMBER_COOKIE_SECURE"] and cfg["TRUST_PROXY"]
    assert cfg["SESSION_COOKIE_HTTPONLY"] and cfg["SESSION_COOKIE_SAMESITE"] == "Lax" and cfg["PREFERRED_URL_SCHEME"] == "https"


def test_render_environment_counts_as_production(monkeypatch):
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.setenv("RENDER", "true")
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError):
        build_config()


def test_persistent_db_can_be_enforced(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SECRET_KEY", "a" * 40)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("REQUIRE_PERSISTENT_DB", "1")
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        build_config()
    monkeypatch.setenv("DATABASE_URL", "postgres://u:p@h/db")
    assert build_config()["SQLALCHEMY_DATABASE_URI"].startswith("postgresql+psycopg2://")


def test_dev_defaults_are_safe(monkeypatch, tmp_path):
    for k in ("APP_ENV", "RENDER", "SECRET_KEY", "DATABASE_URL", "REQUIRE_PERSISTENT_DB", "SESSION_COOKIE_SECURE"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("APP_DATA_DIR", str(tmp_path))
    cfg = build_config()
    assert len(cfg["SECRET_KEY"]) >= 32 and cfg["SQLALCHEMY_DATABASE_URI"].startswith("sqlite:///")
    assert not cfg["SESSION_COOKIE_SECURE"] and not cfg["TRUST_PROXY"]


def test_migrations_build_the_same_schema_as_the_models(tmp_path):
    """`flask db upgrade` on an empty database must match the ORM models exactly."""
    from conftest import make_app
    from webapp.extensions import db
    url = f"sqlite:///{tmp_path / 'migrated.db'}"
    app = make_app(SQLALCHEMY_DATABASE_URI=url)
    with app.app_context():
        db.drop_all()                      # make_app created tables; start from nothing
        db.engine.dispose()
    with app.app_context():
        engine = create_engine(url)
        assert inspect(engine).get_table_names() == [] or "users" not in inspect(engine).get_table_names()
        upgrade(directory="migrations")
        tables = set(inspect(create_engine(url)).get_table_names())
        assert {"users", "screenings", "candidates", "alembic_version"} <= tables
        check(directory="migrations")      # raises if the models and the migration have drifted apart
