"""ResumeIQ - AI resume screening platform (Flask application factory).

``gunicorn app:app`` serves the module-level ``app``; tests and tooling call
``create_app()`` with their own configuration.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

from flask import Flask, request
from werkzeug.middleware.proxy_fix import ProxyFix

try:  # local development convenience: load variables from .env (real environment variables win)
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:  # python-dotenv is a dev-only dependency
    pass

from resume_screening import __version__
from resume_screening.engine import load_engine
from webapp import auth, api, models, views  # noqa: F401  (models import registers the tables)
from webapp.errors import register_error_handlers
from webapp.extensions import csrf, db, limiter, login_manager, migrate
from webapp.settings import build_config

log = logging.getLogger("resumeiq")
STATIC_DIR = Path(__file__).resolve().parent / "static"


def create_app(test_config: dict | None = None, preload: bool = True) -> Flask:
    app = Flask(__name__)
    app.config.update(build_config(test_config))
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))

    if app.config["TRUST_PROXY"]:  # Render terminates TLS: trust one proxy hop for scheme/host/client IP
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    login_manager.init_app(app)
    limiter.init_app(app)

    app.register_blueprint(views.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(api.bp)
    register_error_handlers(app)

    if preload:
        load_engine()  # fail fast / train once at start-up, not on the first request

    @app.context_processor
    def template_globals():
        def static_v(filename: str) -> str:
            """URL of a static file with a cache-busting version from its mtime."""
            from flask import url_for
            try:
                version = int((STATIC_DIR / filename).stat().st_mtime)
            except OSError:
                version = __version__
            return url_for("static", filename=filename, v=version)
        return {"static_v": static_v, "app_version": __version__, "allow_signup": app.config["ALLOW_SIGNUP"]}

    @app.after_request
    def security_headers(resp):
        h = resp.headers
        h.setdefault("X-Content-Type-Options", "nosniff")
        h.setdefault("X-Frame-Options", "DENY")
        # same-origin (not no-referrer): Flask-WTF's HTTPS CSRF check needs the Referer on same-origin posts
        h.setdefault("Referrer-Policy", "same-origin")
        h.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        h.setdefault("Content-Security-Policy",
                     "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; "
                     "base-uri 'self'; form-action 'self'; frame-ancestors 'none'")
        if app.config["PRODUCTION"]:
            h.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        if not request.path.startswith("/static/"):
            h["Cache-Control"] = "no-store"   # never cache pages or API data (shared computers, back button)
        return resp

    return app


app = create_app()  # WSGI entry point: gunicorn app:app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
