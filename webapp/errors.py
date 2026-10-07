"""Error types and handlers shared by pages and the JSON API."""
from __future__ import annotations

import logging

from flask import jsonify, render_template, request
from flask_wtf.csrf import CSRFError
from werkzeug.exceptions import HTTPException, RequestEntityTooLarge

log = logging.getLogger("resumeiq")


class ApiError(Exception):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.message, self.status = message, status


def wants_json() -> bool:
    return request.path.startswith("/api/")


def register_error_handlers(app) -> None:
    @app.errorhandler(ApiError)
    def api_error(err: ApiError):
        return jsonify(error=err.message), err.status

    @app.errorhandler(CSRFError)
    def csrf_error(err: CSRFError):
        message = "Your session expired or the form was invalid. Please refresh the page and try again."
        if wants_json():
            return jsonify(error=message), 400
        return render_template("error.html", code=400, message=message), 400

    @app.errorhandler(RequestEntityTooLarge)
    def too_large(_):
        message = "The upload is too large. Reduce the number or size of files."
        if wants_json():
            return jsonify(error=message), 413
        return render_template("error.html", code=413, message=message), 413

    @app.errorhandler(HTTPException)
    def http_error(err: HTTPException):
        if wants_json():
            return jsonify(error=err.description), err.code
        return render_template("error.html", code=err.code, message=err.description), err.code

    @app.errorhandler(Exception)
    def unexpected(err: Exception):
        log.exception("Unhandled error")
        try:  # a failed transaction must not poison the next request on this connection
            from .extensions import db
            db.session.rollback()
        except Exception:  # pragma: no cover
            pass
        if wants_json():
            return jsonify(error="Something went wrong on our side. Please try again."), 500
        return render_template("error.html", code=500, message="Something went wrong on our side."), 500
