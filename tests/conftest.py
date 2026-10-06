import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


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


@pytest.fixture()
def client(trained_model):
    from app import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()
