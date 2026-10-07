"""JSON API: run screenings, browse results, manage the shortlist.

Every route requires a logged-in user and only ever touches that user's rows
(someone else's id answers 404, never 403). All screening results come from
``resume_screening.engine`` - this module only stores and serves them.
"""
from __future__ import annotations

import csv
import io
import os
from pathlib import Path

from flask import Blueprint, Response, jsonify, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.orm import joinedload
from werkzeug.utils import secure_filename

from resume_screening import config
from resume_screening.catalog import ROLES, role_job_description
from resume_screening.engine import GRADES, load_engine, load_metrics
from resume_screening.extractor import MIN_TEXT_CHARS, ExtractionError, extension, extract_text

from .errors import ApiError
from .extensions import db, limiter, user_or_ip
from .models import (Candidate, STATUSES, STATUS_PENDING, STATUS_SHORTLISTED, Screening, iso, jsonable)

bp = Blueprint("api", __name__, url_prefix="/api")

SAMPLE_EXTS = tuple("." + e for e in config.ALLOWED_EXTENSIONS)
GRADE_KEYS = {"strong": "Strong match", "good": "Good match", "partial": "Partial match", "weak": "Weak match"}
SORTS = {
    "score": Candidate.score, "rank": Candidate.rank, "name": db.func.lower(Candidate.name),
    "experience": Candidate.experience_years, "recent": Candidate.created_at, "status": Candidate.status,
}


# ----------------------------------------------------------- shared helpers
def list_samples() -> list[Path]:
    if not config.SAMPLES_DIR.is_dir():
        return []
    return sorted(p for p in config.SAMPLES_DIR.iterdir() if p.suffix.lower() in SAMPLE_EXTS)


def read_resume(filename: str, data: bytes) -> dict:
    return {"filename": filename, "text": extract_text(filename, data)}


def read_uploads(files, limit: int) -> tuple[list[dict], list[dict]]:
    """Validate and extract text from uploaded files. Returns (resumes, errors)."""
    files = [f for f in files if f and f.filename]
    if len(files) > limit:
        raise ApiError(f"Too many files: upload at most {limit} resumes at a time.")
    resumes, errors, seen = [], [], set()
    for f in files:
        name = secure_filename(f.filename) or "resume"
        if name in seen:  # keep names unique so results are not ambiguous
            stem, ext = os.path.splitext(name)
            name = f"{stem}-{len(seen)}{ext}"
        seen.add(name)
        if extension(name) not in config.ALLOWED_EXTENSIONS:
            errors.append({"filename": name, "error": "Unsupported file type. Use PDF, DOC, DOCX or TXT."})
            continue
        data = f.stream.read(config.MAX_FILE_BYTES + 1)
        if len(data) > config.MAX_FILE_BYTES:
            errors.append({"filename": name, "error": f"File is larger than {config.MAX_FILE_BYTES // (1024 * 1024)} MB."})
            continue
        try:
            resumes.append(read_resume(name, data))
        except ExtractionError as exc:
            errors.append({"filename": name, "error": str(exc)})
    return resumes, errors


def owned(model, row_id: int):
    """Fetch a row that belongs to the current user or answer 404."""
    row = db.session.get(model, row_id)
    if row is None or row.user_id != current_user.id:
        raise ApiError("Not found.", 404)
    return row


def json_body() -> dict:
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ApiError("Send a JSON object.")
    return data


def screening_summary(s: Screening, counts: dict | None = None) -> dict:
    """Scalar summary of a run (counts come from one grouped query when listing)."""
    c = counts or {}
    return {
        "id": s.id, "job_title": s.job_title, "created_at": iso(s.created_at), "total": s.total,
        "top_n": s.top_n, "url": url_for("main.screening_detail", screening_id=s.id),
        "shortlisted": c.get("shortlisted", 0), "rejected": c.get("rejected", 0), "pending": c.get("pending", 0),
        "avg_score": round(c["avg"], 1) if c.get("avg") is not None else None,
        "top_score": round(c["top"], 1) if c.get("top") is not None else None,
    }


def screening_counts(user_id: int, ids: list[int] | None = None) -> dict[int, dict]:
    stmt = (db.select(Candidate.screening_id, Candidate.status, db.func.count(Candidate.id),
                      db.func.avg(Candidate.score), db.func.max(Candidate.score))
            .where(Candidate.user_id == user_id).group_by(Candidate.screening_id, Candidate.status))
    if ids is not None:
        stmt = stmt.where(Candidate.screening_id.in_(ids))
    out: dict[int, dict] = {}
    for sid, status, n, avg, top in db.session.execute(stmt):
        d = out.setdefault(sid, {"n": 0, "sum": 0.0, "top": 0.0})
        d[status] = n
        d["n"] += n
        d["sum"] += (avg or 0) * n
        d["top"] = max(d["top"], top or 0)
    for d in out.values():
        d["avg"] = d["sum"] / d["n"] if d["n"] else None
    return out


def candidate_filters(args, with_status: bool = True):
    """WHERE clauses for the candidate list, shared by listing, counting and CSV export."""
    clauses = [Candidate.user_id == current_user.id]
    sid = args.get("screening_id", type=int)
    if sid:
        clauses.append(Candidate.screening_id == sid)
    if with_status:
        status = args.get("status", "all")
        if status in STATUSES:
            clauses.append(Candidate.status == status)
        elif status != "all":
            raise ApiError("Unknown status filter.")
    grade = args.get("grade", "all")
    if grade != "all":
        if grade not in GRADE_KEYS:
            raise ApiError("Unknown grade filter.")
        clauses.append(Candidate.grade == GRADE_KEYS[grade])
    if args.get("recommended") in ("1", "true"):
        clauses.append(Candidate.recommended.is_(True))
    min_score = args.get("min_score", type=float)
    if min_score:
        clauses.append(Candidate.score >= min_score)
    for token in (args.get("q") or "").lower().split()[:6]:
        esc = token.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        clauses.append(Candidate.search_text.like(f"%{esc}%", escape="\\"))
    return clauses


def sort_clause(args):
    key = args.get("sort", "score")
    if key not in SORTS:
        raise ApiError("Unknown sort option.")
    col = SORTS[key]
    desc = args.get("order", "asc" if key in ("rank", "name") else "desc") != "asc"
    return [col.desc() if desc else col.asc(), Candidate.id.asc()]


# ---------------------------------------------------------------- screening
@bp.post("/screen")
@login_required
@limiter.limit("60 per hour", key_func=user_or_ip)
def screen():
    """Run the ML screening pipeline on uploaded resumes and save the results for this user."""
    jd = (request.form.get("job_description") or "").strip()
    if len(jd) < 30:
        raise ApiError("Please paste a job description (at least a couple of sentences).")
    if len(jd) > config.MAX_JD_CHARS:
        raise ApiError(f"The job description is too long (max {config.MAX_JD_CHARS:,} characters).")
    try:
        top_n = int(request.form.get("top_n", 5))
    except ValueError:
        raise ApiError("Shortlist size must be a number.")
    top_n = max(1, min(top_n, config.MAX_FILES))

    resumes, errors = read_uploads(request.files.getlist("resumes"), config.MAX_FILES)
    if request.form.get("use_samples") in ("1", "true", "on"):
        for p in list_samples():
            try:
                resumes.append(read_resume(p.name, p.read_bytes()))
            except ExtractionError as exc:  # pragma: no cover - samples are curated
                errors.append({"filename": p.name, "error": str(exc)})
    if len(resumes) > config.MAX_FILES:
        raise ApiError(f"Too many resumes: at most {config.MAX_FILES} per run.")
    if not resumes:
        msg = "No readable resumes were provided."
        if errors:
            msg += " " + errors[0]["filename"] + ": " + errors[0]["error"]
        raise ApiError(msg)

    title = (request.form.get("job_title") or "").strip()[:200]
    result = load_engine().screen(resumes, jd, title, top_n)      # <- the existing ML pipeline

    screening = Screening(
        user_id=current_user.id, job_title=(result["job"]["title"] or "Untitled screening")[:200],
        job_description=jd, job_info=jsonable(result["job"]), top_n=result["shortlist_size"],
        total=len(result["candidates"]), errors=errors)
    db.session.add(screening)
    for c in result["candidates"]:
        db.session.add(Candidate.from_engine(screening, current_user.id, c))
    db.session.commit()

    return jsonify(screening_detail_payload(screening, errors=errors)), 201


def screening_detail_payload(s: Screening, errors=None) -> dict:
    rows = db.session.execute(
        db.select(Candidate).options(joinedload(Candidate.screening))
        .where(Candidate.screening_id == s.id).order_by(Candidate.rank)).scalars().all()
    counts = screening_counts(current_user.id, [s.id]).get(s.id, {})
    out = screening_summary(s, counts)
    out.update(job=s.job_info, errors=errors if errors is not None else (s.errors or []),
               recommended=sum(1 for r in rows if r.recommended), candidates=[r.to_dict() for r in rows],
               summary={"total": s.total, "average_score": out["avg_score"] or 0,
                        "strong_matches": sum(1 for r in rows if r.score >= GRADES[0][0])})
    return out


@bp.get("/screenings")
@login_required
def screenings():
    page = max(1, request.args.get("page", 1, type=int))
    per_page = min(50, max(1, request.args.get("per_page", 20, type=int)))
    stmt = db.select(Screening).where(Screening.user_id == current_user.id)
    q = (request.args.get("q") or "").strip()
    if q:
        esc = q.lower().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        stmt = stmt.where(db.func.lower(Screening.job_title).like(f"%{esc}%", escape="\\"))
    page_obj = db.paginate(stmt.order_by(Screening.created_at.desc(), Screening.id.desc()),
                           page=page, per_page=per_page, error_out=False)
    counts = screening_counts(current_user.id, [s.id for s in page_obj.items])
    return jsonify(items=[screening_summary(s, counts.get(s.id)) for s in page_obj.items],
                   page=page_obj.page, pages=page_obj.pages, total=page_obj.total)


@bp.get("/screenings/<int:screening_id>")
@login_required
def screening_detail(screening_id: int):
    return jsonify(screening_detail_payload(owned(Screening, screening_id)))


@bp.delete("/screenings/<int:screening_id>")
@login_required
def delete_screening(screening_id: int):
    db.session.delete(owned(Screening, screening_id))
    db.session.commit()
    return jsonify(ok=True)


@bp.get("/screenings/<int:screening_id>/export.csv")
@login_required
def export_screening(screening_id: int):
    s = owned(Screening, screening_id)
    return export_candidates(forced={"screening_id": s.id}, filename=f"screening-{s.id}.csv")


# --------------------------------------------------------------- candidates
@bp.get("/candidates")
@login_required
def candidates():
    args = request.args
    page = max(1, args.get("page", 1, type=int))
    per_page = min(100, max(1, args.get("per_page", 25, type=int)))
    stmt = (db.select(Candidate).options(joinedload(Candidate.screening))
            .where(*candidate_filters(args)).order_by(*sort_clause(args)))
    page_obj = db.paginate(stmt, page=page, per_page=per_page, error_out=False)

    counts = {s: 0 for s in STATUSES}
    for status, n in db.session.execute(
            db.select(Candidate.status, db.func.count(Candidate.id))
            .where(*candidate_filters(args, with_status=False)).group_by(Candidate.status)):
        counts[status] = n
    counts["all"] = sum(counts.values())
    return jsonify(items=[c.to_dict() for c in page_obj.items], page=page_obj.page, pages=page_obj.pages,
                   total=page_obj.total, per_page=per_page, counts=counts)


@bp.get("/candidates/<int:candidate_id>")
@login_required
def candidate(candidate_id: int):
    return jsonify(owned(Candidate, candidate_id).to_dict())


@bp.patch("/candidates/<int:candidate_id>")
@login_required
def update_candidate(candidate_id: int):
    row, body = owned(Candidate, candidate_id), json_body()
    if "status" in body:
        if body["status"] not in STATUSES:
            raise ApiError("Status must be pending, shortlisted or rejected.")
        if body["status"] != row.status:
            row.set_status(body["status"])
    if "notes" in body:
        if not isinstance(body["notes"], str):
            raise ApiError("Notes must be text.")
        if len(body["notes"]) > 5000:
            raise ApiError("Notes are limited to 5,000 characters.")
        row.notes = body["notes"].strip()
    db.session.commit()
    return jsonify(row.to_dict())


@bp.delete("/candidates/<int:candidate_id>")
@login_required
def delete_candidate(candidate_id: int):
    row = owned(Candidate, candidate_id)
    db.session.delete(row)
    db.session.commit()
    return jsonify(ok=True)


@bp.post("/candidates/bulk")
@login_required
def bulk_update():
    """Set the status of many candidates: either explicit ``ids`` or a whole ``screening_id`` scope."""
    body = json_body()
    status = body.get("status")
    if status not in STATUSES:
        raise ApiError("Status must be pending, shortlisted or rejected.")
    stmt = db.select(Candidate).where(Candidate.user_id == current_user.id)
    if isinstance(body.get("ids"), list):
        try:
            ids = {int(i) for i in body["ids"]}
        except (TypeError, ValueError):
            raise ApiError("ids must be numbers.")
        if not ids or len(ids) > 500:
            raise ApiError("Select between 1 and 500 candidates.")
        stmt = stmt.where(Candidate.id.in_(ids))
    elif isinstance(body.get("screening_id"), int):
        owned(Screening, body["screening_id"])
        stmt = stmt.where(Candidate.screening_id == body["screening_id"])
        if body.get("scope") == "recommended":
            stmt = stmt.where(Candidate.recommended.is_(True))
        elif body.get("scope") != "all":
            raise ApiError("scope must be 'recommended' or 'all'.")
    else:
        raise ApiError("Provide ids or a screening_id.")
    rows = db.session.execute(stmt).scalars().all()
    for row in rows:
        if row.status != status:
            row.set_status(status)
    db.session.commit()
    return jsonify(updated=len(rows), status=status)


@bp.get("/candidates/export.csv")
@login_required
def export_candidates(forced: dict | None = None, filename: str | None = None):
    args = request.args.copy()
    for k, v in (forced or {}).items():
        args[k] = v
    rows = db.session.execute(
        db.select(Candidate).options(joinedload(Candidate.screening))
        .where(*candidate_filters(args)).order_by(*sort_clause(args))).scalars().all()
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["Rank", "Name", "Email", "Phone", "Score", "Grade", "Status", "AI recommended", "Experience (yrs)",
                "Education", "Predicted role", "Matched skills", "Related skills", "Missing skills", "Job",
                "Screened at", "Notes"])
    for r in rows:
        d = r.to_dict()
        w.writerow([csv_safe(x) for x in [
            r.rank, r.name, r.email or "", r.phone or "", f"{r.score:.1f}", r.grade, r.status,
            "yes" if r.recommended else "no", r.experience_years, r.education_label or "",
            r.predicted_role or "", "; ".join(d["matched_skills"]),
            "; ".join(f"{x['has']}~{x['required']}" for x in d["related_skills"]),
            "; ".join(d["missing_skills"]), r.screening.job_title, iso(r.created_at), r.notes or ""]])
    name = filename or ("shortlist.csv" if args.get("status") == STATUS_SHORTLISTED else "candidates.csv")
    return Response("﻿" + buf.getvalue(), mimetype="text/csv; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="{name}"'})


def csv_safe(value) -> str:
    """Neutralise spreadsheet formula injection (cells that start with = + - @ or control chars)."""
    s = "" if value is None else str(value)
    if s and (s[0] in "=@\t\r" or (s[0] in "+-" and not s[1:2].isdigit())):
        return "'" + s
    return s


# -------------------------------------------------------- existing helpers
@bp.get("/roles")
@login_required
def roles():
    return jsonify([{"id": r["id"], "title": r["title"], "description": r["description"],
                     "example_job_description": role_job_description(r)} for r in ROLES])


@bp.get("/samples")
@login_required
def samples():
    return jsonify([{"filename": p.name, "size": p.stat().st_size, "url": f"/samples/{p.name}"}
                    for p in list_samples()])


@bp.post("/match")
@login_required
@limiter.limit("120 per hour", key_func=user_or_ip)
def match():
    resumes, errors = read_uploads(request.files.getlist("resume"), 1)
    sample = request.form.get("sample")
    pasted = (request.form.get("resume_text") or "").strip()
    if not resumes and sample:
        path = next((p for p in list_samples() if p.name == sample), None)
        if not path:
            raise ApiError("Unknown sample resume.", 404)
        resumes = [read_resume(path.name, path.read_bytes())]
    if not resumes and pasted:
        if len(pasted) < MIN_TEXT_CHARS:
            raise ApiError("The pasted resume text is too short.")
        resumes = [{"filename": "pasted-resume.txt", "text": pasted[:100_000]}]
    if not resumes:
        raise ApiError(errors[0]["error"] if errors else "Upload a resume, paste its text or choose a sample.")
    return jsonify(load_engine().recommend_roles(resumes[0]["text"], resumes[0]["filename"]))


@bp.get("/model")
@login_required
def model():
    return jsonify(load_metrics() or {})
