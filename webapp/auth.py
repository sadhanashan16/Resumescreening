"""Authentication: sign up, log in, log out and account settings."""
from __future__ import annotations

import hmac
import logging
from datetime import timedelta
from urllib.parse import urlsplit

from flask import (Blueprint, abort, current_app, flash, jsonify, redirect, render_template, request,
                   session, url_for)
from flask_login import current_user, login_required, login_user, logout_user

from .extensions import db, limiter, login_manager
from .forms import ChangePasswordForm, DeleteAccountForm, LoginForm, RegisterForm
from .models import Candidate, Screening, User, STATUS_SHORTLISTED, utcnow

log = logging.getLogger("resumeiq.auth")
bp = Blueprint("auth", __name__)


# ------------------------------------------------------------ login manager
login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to continue."
login_manager.login_message_category = "info"
login_manager.session_protection = "basic"


@login_manager.user_loader
def load_user(session_id: str):
    try:
        raw_id, token = session_id.split(":", 1)
        user = db.session.get(User, int(raw_id))
    except (ValueError, AttributeError):
        return None
    if user and user.is_active and hmac.compare_digest(user.session_token, token):
        return user
    return None


@login_manager.unauthorized_handler
def unauthorized():
    if request.path.startswith("/api/"):
        return jsonify(error="Please log in to continue.", login_url=url_for("auth.login")), 401
    nxt = request.full_path.rstrip("?") if request.method == "GET" else None
    return redirect(url_for("auth.login", next=nxt) if nxt and nxt != "/" else url_for("auth.login"))


def safe_next(target: str | None) -> str | None:
    """Only same-site relative paths may be used as post-login redirect targets."""
    if not target:
        return None
    parts = urlsplit(target)
    if parts.scheme or parts.netloc or not target.startswith("/") or target.startswith("//") or "\\" in target:
        return None
    return target


def _after_login_url() -> str:
    return safe_next(request.args.get("next") or request.form.get("next")) or url_for("main.dashboard")


# --------------------------------------------------------------- sign up
@bp.route("/register", methods=["GET", "POST"])
@limiter.limit("30 per hour", methods=["POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    if not current_app.config["ALLOW_SIGNUP"]:
        abort(404)
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(email=form.email.data, name=form.name.data)
        user.set_password(form.password.data)
        user.last_login_at = utcnow()
        db.session.add(user)
        db.session.commit()
        session.clear()
        login_user(user)
        session.permanent = True
        flash(f"Welcome to ResumeIQ, {user.name.split()[0]}! Your account is ready.", "success")
        return redirect(url_for("main.dashboard"))
    return render_template("auth/register.html", form=form), (400 if form.errors else 200)


# ---------------------------------------------------------------- log in
@bp.route("/login", methods=["GET", "POST"])
@limiter.limit("15 per minute", methods=["POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.execute(db.select(User).filter_by(email=form.email.data)).scalar_one_or_none()
        now = utcnow()
        if user and user.is_locked(now):
            minutes = max(1, int((user.locked_until - now).total_seconds() // 60) + 1)
            flash(f"Too many failed attempts. Try again in about {minutes} minute{'s' if minutes != 1 else ''}.", "error")
            return render_template("auth/login.html", form=form, next=request.args.get("next")), 429
        if user and user.is_active and user.check_password(form.password.data):
            user.failed_logins, user.locked_until, user.last_login_at = 0, None, now
            db.session.commit()
            session.clear()
            login_user(user, remember=form.remember.data)
            session.permanent = True
            return redirect(_after_login_url())
        # Unknown e-mail and wrong password look identical (message and timing).
        if user:
            user.failed_logins += 1
            if user.failed_logins >= current_app.config["MAX_FAILED_LOGINS"]:
                user.locked_until = now + timedelta(minutes=current_app.config["LOCKOUT_MINUTES"])
                user.failed_logins = 0
                log.warning("Account locked after repeated failed logins: user_id=%s", user.id)
            db.session.commit()
        else:
            User.burn_password_check(form.password.data)
        flash("Invalid email or password.", "error")
        return render_template("auth/login.html", form=form, next=request.args.get("next")), 401
    return render_template("auth/login.html", form=form, next=request.args.get("next")), (400 if form.errors else 200)


# --------------------------------------------------------------- log out
@bp.post("/logout")
def logout():
    was_authenticated = current_user.is_authenticated
    logout_user()
    session.clear()
    if was_authenticated:
        flash("You have been logged out.", "success")
    return redirect(url_for("auth.login"))


# --------------------------------------------------------------- account
def _account_context(password_form=None, delete_form=None):
    uid = current_user.id
    stats = {
        "screenings": db.session.scalar(db.select(db.func.count(Screening.id)).filter_by(user_id=uid)) or 0,
        "candidates": db.session.scalar(db.select(db.func.count(Candidate.id)).filter_by(user_id=uid)) or 0,
        "shortlisted": db.session.scalar(
            db.select(db.func.count(Candidate.id)).filter_by(user_id=uid, status=STATUS_SHORTLISTED)) or 0,
    }
    return dict(password_form=password_form or ChangePasswordForm(current_user),
                delete_form=delete_form or DeleteAccountForm(current_user), stats=stats)


@bp.get("/account")
@login_required
def account():
    return render_template("account.html", **_account_context())


@bp.post("/account/password")
@login_required
@limiter.limit("10 per hour")
def change_password():
    form = ChangePasswordForm(current_user)
    if form.validate_on_submit():
        current_user.set_password(form.new_password.data)
        current_user.rotate_session_token()          # signs out every other device
        db.session.commit()
        login_user(current_user, remember=False)      # keep *this* session alive with the new token
        flash("Password updated. Other devices have been signed out.", "success")
        return redirect(url_for("auth.account"))
    return render_template("account.html", **_account_context(password_form=form)), 400


@bp.post("/account/delete")
@login_required
@limiter.limit("5 per hour")
def delete_account():
    form = DeleteAccountForm(current_user)
    if form.validate_on_submit():
        user = db.session.get(User, current_user.id)
        logout_user()
        session.clear()
        db.session.delete(user)                       # cascades to screenings and candidates
        db.session.commit()
        flash("Your account and all of its data have been deleted.", "success")
        return redirect(url_for("main.index"))
    return render_template("account.html", **_account_context(delete_form=form)), 400
