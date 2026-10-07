"""Flask extension instances (initialised in ``create_app``)."""
from flask import request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()
login_manager = LoginManager()
limiter = Limiter(key_func=get_remote_address)


def user_or_ip() -> str:
    """Rate-limit key: the logged-in user when known, otherwise the client IP."""
    if current_user and current_user.is_authenticated:
        return f"user:{current_user.id}"
    return get_remote_address() or request.remote_addr or "unknown"
