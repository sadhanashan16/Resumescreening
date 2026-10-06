"""Flask web application: AI resume screening and job matching."""
from __future__ import annotations

import logging
import os
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_from_directory
from werkzeug.exceptions import HTTPException, RequestEntityTooLarge
from werkzeug.utils import secure_filename

from resume_screening import __version__, config
from resume_screening.catalog import ROLES, role_job_description
from resume_screening.engine import load_engine, load_metrics
from resume_screening.skills import SKILLS
from resume_screening.extractor import MIN_TEXT_CHARS, ExtractionError, extension, extract_text

log = logging.getLogger("resume_screening")

SAMPLE_EXTS = tuple("." + e for e in config.ALLOWED_EXTENSIONS)


class ApiError(Exception):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.message, self.status = message, status


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


def create_app(preload: bool = True) -> Flask:
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = config.MAX_REQUEST_BYTES
    app.config["JSON_SORT_KEYS"] = False
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
    if preload:
        load_engine()  # fail fast / train once at start-up, not on the first request

    # ------------------------------------------------------------- pages
    @app.get("/")
    def index():
        metrics = load_metrics() or {}
        return render_template("index.html", metrics=metrics, roles=ROLES, n_samples=len(list_samples()),
                               n_skills=len(SKILLS))

    @app.get("/screen")
    def screen_page():
        return render_template("screen.html", roles=ROLES, n_samples=len(list_samples()),
                               max_files=config.MAX_FILES, max_mb=config.MAX_FILE_BYTES // (1024 * 1024))

    @app.get("/match")
    def match_page():
        return render_template("match.html", n_samples=len(list_samples()),
                               max_mb=config.MAX_FILE_BYTES // (1024 * 1024))

    @app.get("/insights")
    def insights_page():
        return render_template("insights.html", metrics=load_metrics())

    @app.get("/health")
    def health():
        return jsonify(status="ok", version=__version__, model_loaded=True)

    # --------------------------------------------------------------- API
    @app.get("/api/roles")
    def api_roles():
        return jsonify([{"id": r["id"], "title": r["title"], "description": r["description"],
                         "example_job_description": role_job_description(r)} for r in ROLES])

    @app.get("/api/samples")
    def api_samples():
        return jsonify([{"filename": p.name, "size": p.stat().st_size, "url": f"/samples/{p.name}"}
                        for p in list_samples()])

    @app.get("/samples/<path:name>")
    def sample_file(name):
        if Path(name).suffix.lower() not in SAMPLE_EXTS:
            raise ApiError("Not found", 404)
        return send_from_directory(config.SAMPLES_DIR, name, as_attachment=True)

    @app.post("/api/screen")
    def api_screen():
        jd = (request.form.get("job_description") or "").strip()
        if len(jd) < 30:
            raise ApiError("Please paste a job description (at least a couple of sentences).")
        if len(jd) > config.MAX_JD_CHARS:
            raise ApiError(f"The job description is too long (max {config.MAX_JD_CHARS:,} characters).")
        try:
            top_n = int(request.form.get("top_n", 5))
        except ValueError:
            raise ApiError("top_n must be a number.")
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

        result = load_engine().screen(resumes, jd, request.form.get("job_title", ""), top_n)
        result["errors"] = errors
        return jsonify(result)

    @app.post("/api/match")
    def api_match():
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
        result = load_engine().recommend_roles(resumes[0]["text"], resumes[0]["filename"])
        return jsonify(result)

    @app.get("/api/model")
    def api_model():
        return jsonify(load_metrics() or {})

    # ---------------------------------------------------- errors / headers
    @app.errorhandler(ApiError)
    def handle_api_error(err: ApiError):
        return jsonify(error=err.message), err.status

    @app.errorhandler(RequestEntityTooLarge)
    def handle_too_large(_):
        return jsonify(error="The upload is too large. Reduce the number or size of files."), 413

    @app.errorhandler(HTTPException)
    def handle_http(err: HTTPException):
        if request.path.startswith("/api/"):
            return jsonify(error=err.description), err.code
        return render_template("error.html", code=err.code, message=err.description), err.code

    @app.errorhandler(Exception)
    def handle_unexpected(err: Exception):
        log.exception("Unhandled error")
        if request.path.startswith("/api/"):
            return jsonify(error="Something went wrong while analysing the resumes."), 500
        return render_template("error.html", code=500, message="Something went wrong."), 500

    @app.after_request
    def security_headers(resp):
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("X-Frame-Options", "DENY")
        resp.headers.setdefault("Referrer-Policy", "no-referrer")
        resp.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; "
            "base-uri 'self'; form-action 'self'; frame-ancestors 'none'")
        if request.path.startswith("/api/"):
            resp.headers["Cache-Control"] = "no-store"
        return resp

    return app


app = create_app()  # WSGI entry point: gunicorn app:app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
