"""Server-rendered pages: landing page, dashboard, screenings, shortlist and tools."""
from __future__ import annotations

from pathlib import Path

from flask import (Blueprint, abort, flash, jsonify, redirect, render_template, request, send_from_directory,
                   url_for)
from flask_login import current_user, login_required
from sqlalchemy import text

from resume_screening import __version__, config
from resume_screening.catalog import ROLES
from resume_screening.engine import load_metrics
from resume_screening.skills import SKILLS

from .api import SAMPLE_EXTS, list_samples, screening_counts, screening_summary
from .extensions import db
from .models import (Candidate, Screening, STATUS_PENDING, STATUS_REJECTED, STATUS_SHORTLISTED)

bp = Blueprint("main", __name__)

MAX_MB = config.MAX_FILE_BYTES // (1024 * 1024)


@bp.get("/")
def index():
    return render_template("index.html", metrics=load_metrics() or {}, roles=ROLES, n_samples=len(list_samples()),
                           n_skills=len(SKILLS))


@bp.get("/health")
def health():
    """Liveness/readiness probe used by Render: 200 when the app and its database respond."""
    try:
        db.session.execute(text("SELECT 1"))
        database = "ok"
    except Exception:  # pragma: no cover - exercised only when the DB is down
        db.session.rollback()
        database = "error"
    body = {"status": "ok" if database == "ok" else "degraded", "version": __version__, "model_loaded": True,
            "database": database, "persistent_database": db.engine.dialect.name != "sqlite"}
    return jsonify(body), (200 if database == "ok" else 503)


# ---------------------------------------------------------------- dashboard
@bp.get("/dashboard")
@login_required
def dashboard():
    uid = current_user.id
    by_status = {STATUS_PENDING: 0, STATUS_SHORTLISTED: 0, STATUS_REJECTED: 0}
    for status, n in db.session.execute(
            db.select(Candidate.status, db.func.count(Candidate.id)).where(Candidate.user_id == uid)
            .group_by(Candidate.status)):
        by_status[status] = n
    total_candidates = sum(by_status.values())
    avg_score = db.session.scalar(db.select(db.func.avg(Candidate.score)).where(Candidate.user_id == uid))
    n_screenings = db.session.scalar(db.select(db.func.count(Screening.id)).where(Screening.user_id == uid)) or 0

    recent = db.session.execute(db.select(Screening).where(Screening.user_id == uid)
                                .order_by(Screening.created_at.desc(), Screening.id.desc()).limit(5)).scalars().all()
    counts = screening_counts(uid, [s.id for s in recent])
    shortlisted = db.session.execute(
        db.select(Candidate).where(Candidate.user_id == uid, Candidate.status == STATUS_SHORTLISTED)
        .order_by(Candidate.shortlisted_at.desc(), Candidate.id.desc()).limit(6)).scalars().all()

    grades = {"Strong match": 0, "Good match": 0, "Partial match": 0, "Weak match": 0}
    for grade, n in db.session.execute(
            db.select(Candidate.grade, db.func.count(Candidate.id)).where(Candidate.user_id == uid)
            .group_by(Candidate.grade)):
        grades[grade] = n

    return render_template(
        "dashboard.html", n_screenings=n_screenings, total_candidates=total_candidates, by_status=by_status,
        avg_score=round(avg_score, 1) if avg_score is not None else None, grades=grades,
        recent=[screening_summary(s, counts.get(s.id)) for s in recent],
        shortlisted=[c.to_dict() for c in shortlisted])


# --------------------------------------------------------------- screenings
@bp.get("/screenings/new")
@login_required
def screening_new():
    return render_template("screening_new.html", roles=ROLES, n_samples=len(list_samples()),
                           max_files=config.MAX_FILES, max_mb=MAX_MB)


@bp.get("/screen")  # legacy URL from the public version of the app
@login_required
def legacy_screen():
    return redirect(url_for("main.screening_new"), code=301)


@bp.get("/screenings")
@login_required
def screenings():
    uid = current_user.id
    page = max(1, request.args.get("page", 1, type=int))
    q = (request.args.get("q") or "").strip()
    stmt = db.select(Screening).where(Screening.user_id == uid)
    if q:
        esc = q.lower().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        stmt = stmt.where(db.func.lower(Screening.job_title).like(f"%{esc}%", escape="\\"))
    page_obj = db.paginate(stmt.order_by(Screening.created_at.desc(), Screening.id.desc()),
                           page=page, per_page=15, error_out=False)
    counts = screening_counts(uid, [s.id for s in page_obj.items])
    return render_template("screenings.html", page=page_obj, q=q,
                           items=[screening_summary(s, counts.get(s.id)) for s in page_obj.items])


@bp.get("/screenings/<int:screening_id>")
@login_required
def screening_detail(screening_id: int):
    s = db.session.get(Screening, screening_id)
    if s is None or s.user_id != current_user.id:
        abort(404)
    counts = screening_counts(current_user.id, [s.id]).get(s.id, {})
    return render_template("screening_detail.html", s=s, summary=screening_summary(s, counts),
                           job=s.job_info or {}, errors=s.errors or [])


@bp.post("/screenings/<int:screening_id>/delete")
@login_required
def screening_delete(screening_id: int):
    s = db.session.get(Screening, screening_id)
    if s is None or s.user_id != current_user.id:
        abort(404)
    title = s.job_title
    db.session.delete(s)
    db.session.commit()
    flash(f"Deleted the screening “{title}” and its candidates.", "success")
    return redirect(url_for("main.screenings"))


@bp.get("/shortlist")
@login_required
def shortlist():
    runs = db.session.execute(db.select(Screening.id, Screening.job_title).where(Screening.user_id == current_user.id)
                              .order_by(Screening.created_at.desc())).all()
    return render_template("shortlist.html", runs=[{"id": r.id, "title": r.job_title} for r in runs])


# ------------------------------------------------------------------- tools
@bp.get("/match")
@login_required
def match():
    return render_template("match.html", n_samples=len(list_samples()), max_mb=MAX_MB)


@bp.get("/insights")
@login_required
def insights():
    return render_template("insights.html", metrics=load_metrics())


@bp.get("/samples/<path:name>")
@login_required
def sample_file(name):
    if Path(name).suffix.lower() not in SAMPLE_EXTS:
        abort(404)
    return send_from_directory(config.SAMPLES_DIR, name, as_attachment=True)
