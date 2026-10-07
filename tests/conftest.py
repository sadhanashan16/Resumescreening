import os
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Importing app.py builds the module-level WSGI app, so give it a throwaway data dir first.
_DATA = tempfile.mkdtemp(prefix="resumeiq-tests-")
os.environ.setdefault("APP_DATA_DIR", _DATA)
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-used-anywhere-else")
os.environ.pop("DATABASE_URL", None) if os.environ.get("TEST_DATABASE_URL") is None else None


@pytest.fixture(scope="session", autouse=True)
def trained_model():
    """Make sure a trained model exists (trains once, ~10 s, if missing)."""
    from resume_screening import config
    if not config.MODEL_PATH.exists():
        from resume_screening.train import main
        main([])


@pytest.fixture(scope="session")
def engine(trained_model):
    from resume_screening.engine import load_engine
    return load_engine()


def make_app(**overrides):
    from app import create_app
    from webapp.extensions import db
    url = os.environ.get("TEST_DATABASE_URL", "sqlite://")
    if "test" not in url.rsplit("/", 1)[-1].lower() and not url.startswith("sqlite"):
        raise RuntimeError("TEST_DATABASE_URL is dropped and recreated by the tests; its database name must contain 'test'.")
    cfg = {"TESTING": True, "RATELIMIT_ENABLED": False, "WTF_CSRF_ENABLED": False,
           "SQLALCHEMY_DATABASE_URI": os.environ.get("TEST_DATABASE_URL", "sqlite://"),
           "SQLALCHEMY_ENGINE_OPTIONS": {"pool_pre_ping": True}, "SECRET_KEY": "test"}
    cfg.update(overrides)
    app = create_app(cfg)
    with app.app_context():
        db.drop_all()
        db.create_all()
    return app


@pytest.fixture()
def app(trained_model):
    app = make_app()
    yield app
    from webapp.extensions import db
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def register(client, email="alex@example.com", name="Alex Morgan", password="Sup3rSecret99", follow=True):
    return client.post("/register", data={"name": name, "email": email, "password": password, "confirm": password},
                       follow_redirects=follow)


@pytest.fixture()
def auth_client(client):
    """A client with a freshly registered, logged-in user."""
    register(client)
    return client


@pytest.fixture()
def other_client(app):
    """A second, independent logged-in user (for isolation tests)."""
    c = app.test_client()
    register(c, email="blake@example.com", name="Blake Rivera")
    return c
