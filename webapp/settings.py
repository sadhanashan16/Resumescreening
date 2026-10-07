"""Environment-driven web configuration.

Nothing secret lives in the repository: SECRET_KEY, DATABASE_URL and the rest
are read from environment variables (see ``.env.example``).
"""
from __future__ import annotations

import logging
import os
import secrets
from datetime import timedelta
from pathlib import Path

from resume_screening import config as ml_config

log = logging.getLogger("resumeiq.settings")

BASE_DIR = Path(__file__).resolve().parent.parent
_TRUE = {"1", "true", "yes", "on"}


def env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    return default if value is None else value.strip().lower() in _TRUE


def is_production() -> bool:
    """True on Render (it sets RENDER) or when APP_ENV=production."""
    return os.environ.get("APP_ENV", "").strip().lower() == "production" or bool(os.environ.get("RENDER"))


def normalize_database_url(url: str) -> str:
    """Render/Heroku style ``postgres://`` URLs -> SQLAlchemy ``postgresql+psycopg2://``."""
    url = url.strip()
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg2://" + url[len("postgresql://"):]
    return url


def build_config(overrides: dict | None = None) -> dict:
    """Assemble the Flask config from the environment (``overrides`` win, used by tests)."""
    env = os.environ
    production = is_production()

    secret = env.get("SECRET_KEY", "").strip()
    if not secret:
        if production:
            raise RuntimeError("SECRET_KEY is not set. Set a long random value in the environment "
                               "(on Render the blueprint generates one).")
        secret = secrets.token_hex(32)
        log.warning("SECRET_KEY not set: using a random development key (sessions reset on restart).")

    database_url = env.get("DATABASE_URL", "").strip()
    if database_url:
        database_url = normalize_database_url(database_url)
    else:
        if production and env_bool("REQUIRE_PERSISTENT_DB"):
            raise RuntimeError("DATABASE_URL is not set but REQUIRE_PERSISTENT_DB is enabled.")
        data_dir = Path(env.get("APP_DATA_DIR") or BASE_DIR / "instance")
        data_dir.mkdir(parents=True, exist_ok=True)
        database_url = f"sqlite:///{(data_dir / 'resumeiq.db').resolve()}"
        if production:
            log.warning("DATABASE_URL is not set: falling back to a local SQLite file. On Render this is "
                        "wiped on every deploy - attach a Postgres database (see README).")

    secure_cookies = env_bool("SESSION_COOKIE_SECURE", production)
    cfg = {
        "SECRET_KEY": secret,
        "SQLALCHEMY_DATABASE_URI": database_url,
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "SQLALCHEMY_ENGINE_OPTIONS": {"pool_pre_ping": True},
        "MAX_CONTENT_LENGTH": ml_config.MAX_REQUEST_BYTES,
        "JSON_SORT_KEYS": False,
        # sessions / cookies
        "SESSION_COOKIE_NAME": "resumeiq_session",
        "SESSION_COOKIE_HTTPONLY": True,
        "SESSION_COOKIE_SAMESITE": "Lax",
        "SESSION_COOKIE_SECURE": secure_cookies,
        "REMEMBER_COOKIE_HTTPONLY": True,
        "REMEMBER_COOKIE_SAMESITE": "Lax",
        "REMEMBER_COOKIE_SECURE": secure_cookies,
        "REMEMBER_COOKIE_DURATION": timedelta(days=int(env.get("REMEMBER_DAYS", 14))),
        "PERMANENT_SESSION_LIFETIME": timedelta(hours=int(env.get("SESSION_HOURS", 12))),
        # CSRF (Flask-WTF)
        "WTF_CSRF_TIME_LIMIT": None,
        # rate limiting (Flask-Limiter): memory:// is per-process, fine for one worker
        "RATELIMIT_STORAGE_URI": env.get("RATELIMIT_STORAGE_URI", "memory://"),
        "RATELIMIT_ENABLED": env_bool("RATELIMIT_ENABLED", True),
        "RATELIMIT_HEADERS_ENABLED": True,
        # app behaviour
        "PRODUCTION": production,
        "TRUST_PROXY": env_bool("TRUST_PROXY", production),
        "PREFERRED_URL_SCHEME": "https" if production else "http",
        "MAX_FAILED_LOGINS": int(env.get("MAX_FAILED_LOGINS", 5)),
        "LOCKOUT_MINUTES": int(env.get("LOCKOUT_MINUTES", 15)),
        "ALLOW_SIGNUP": env_bool("ALLOW_SIGNUP", True),
    }
    if overrides:
        cfg.update(overrides)
    return cfg
