"""Database models: users, screening runs and the candidates they produce.

Resume *files* are never stored. A candidate row keeps only what the ML
pipeline extracted (contact details, skills, education, experience) and the
scores it computed, so recruiters can manage shortlists later.
"""
from __future__ import annotations

import json
import secrets
from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db

STATUS_PENDING, STATUS_SHORTLISTED, STATUS_REJECTED = "pending", "shortlisted", "rejected"
STATUSES = (STATUS_PENDING, STATUS_SHORTLISTED, STATUS_REJECTED)

# A constant hash so unknown e-mails cost the same time as a wrong password.
_DUMMY_HASH = generate_password_hash("not-a-real-password")


def utcnow() -> datetime:
    """Naive UTC timestamp (portable across SQLite and PostgreSQL)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def iso(dt: datetime | None) -> str | None:
    return dt.isoformat(timespec="seconds") + "Z" if dt else None


def jsonable(value):
    """Round-trip through JSON so numpy scalars etc. become plain Python types."""
    return json.loads(json.dumps(value, default=lambda o: o.item() if hasattr(o, "item") else str(o)))


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(254), unique=True, nullable=False, index=True)
    name = db.Column(db.String(80), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    # Rotated on password change so every other session/remember-me cookie stops working.
    session_token = db.Column(db.String(64), nullable=False, default=lambda: secrets.token_hex(16))
    active = db.Column(db.Boolean, nullable=False, default=True)
    failed_logins = db.Column(db.Integer, nullable=False, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    last_login_at = db.Column(db.DateTime, nullable=True)

    screenings = db.relationship("Screening", back_populates="user", cascade="all, delete-orphan",
                                 passive_deletes=False)

    # -- passwords
    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def burn_password_check(password: str) -> None:
        check_password_hash(_DUMMY_HASH, password)

    def rotate_session_token(self) -> None:
        self.session_token = secrets.token_hex(16)

    # -- flask-login
    def get_id(self) -> str:
        return f"{self.id}:{self.session_token}"

    @property
    def is_active(self) -> bool:  # type: ignore[override]
        return bool(self.active)

    @property
    def initials(self) -> str:
        parts = [p for p in (self.name or "").split() if p]
        return ("".join(p[0] for p in parts[:2]) or self.email[:1]).upper()

    def is_locked(self, now: datetime | None = None) -> bool:
        return bool(self.locked_until and self.locked_until > (now or utcnow()))


class Screening(db.Model):
    """One screening run: a job description plus the resumes scored against it."""

    __tablename__ = "screenings"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    job_title = db.Column(db.String(200), nullable=False)
    job_description = db.Column(db.Text, nullable=False)
    job_info = db.Column(db.JSON, nullable=False, default=dict)   # skills, years, education, detected role
    top_n = db.Column(db.Integer, nullable=False, default=5)
    total = db.Column(db.Integer, nullable=False, default=0)
    errors = db.Column(db.JSON, nullable=False, default=list)     # files that could not be read
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)

    user = db.relationship("User", back_populates="screenings")
    candidates = db.relationship("Candidate", back_populates="screening", cascade="all, delete-orphan",
                                 order_by="Candidate.rank")


class Candidate(db.Model):
    __tablename__ = "candidates"

    id = db.Column(db.Integer, primary_key=True)
    screening_id = db.Column(db.Integer, db.ForeignKey("screenings.id", ondelete="CASCADE"),
                             nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    rank = db.Column(db.Integer, nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(254), nullable=True)
    phone = db.Column(db.String(60), nullable=True)
    score = db.Column(db.Float, nullable=False, index=True)
    grade = db.Column(db.String(30), nullable=False)
    recommended = db.Column(db.Boolean, nullable=False, default=False)   # in the ML top-N
    status = db.Column(db.String(20), nullable=False, default=STATUS_PENDING, index=True)
    notes = db.Column(db.Text, nullable=False, default="")
    experience_years = db.Column(db.Float, nullable=False, default=0)
    education_label = db.Column(db.String(60), nullable=True)
    predicted_role = db.Column(db.String(80), nullable=True)
    search_text = db.Column(db.Text, nullable=False, default="")
    data = db.Column(db.JSON, nullable=False, default=dict)               # full engine output for this resume
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    shortlisted_at = db.Column(db.DateTime, nullable=True)

    screening = db.relationship("Screening", back_populates="candidates")

    @classmethod
    def from_engine(cls, screening: "Screening", user_id: int, c: dict) -> "Candidate":
        """Build a row from one candidate dict produced by ``ScreeningEngine.screen``."""
        data = jsonable(c)
        skills = " ".join(data.get("skills", []))
        return cls(
            screening=screening, user_id=user_id, rank=int(c["rank"]), filename=c["filename"][:255],
            name=(c["name"] or "Unknown candidate")[:200], email=(c.get("email") or None),
            phone=(c.get("phone") or None), score=float(c["score"]), grade=c["grade"],
            recommended=bool(c.get("shortlisted")), experience_years=float(c.get("experience_years") or 0),
            education_label=(c.get("education") or {}).get("label"),
            predicted_role=(c.get("predicted_role") or {}).get("title"),
            search_text=" ".join([c["name"] or "", c.get("email") or "", c["filename"],
                                  (c.get("predicted_role") or {}).get("title", ""), skills]).lower(),
            data=data,
        )

    def set_status(self, status: str) -> None:
        self.status = status
        self.shortlisted_at = utcnow() if status == STATUS_SHORTLISTED else None

    def to_dict(self) -> dict:
        d = self.data or {}
        return {
            "id": self.id, "screening_id": self.screening_id,
            "screening_title": self.screening.job_title if self.screening else None,
            "screened_at": iso(self.created_at), "shortlisted_at": iso(self.shortlisted_at),
            "rank": self.rank, "filename": self.filename, "name": self.name, "email": self.email,
            "phone": self.phone, "score": self.score, "grade": self.grade, "recommended": self.recommended,
            "status": self.status, "notes": self.notes or "", "experience_years": self.experience_years,
            "education": d.get("education") or {"label": self.education_label, "detail": ""},
            "predicted_role": d.get("predicted_role"), "skills": d.get("skills", []),
            "matched_skills": d.get("matched_skills", []), "related_skills": d.get("related_skills", []),
            "missing_skills": d.get("missing_skills", []), "extra_skills": d.get("extra_skills", []),
            "components": d.get("components", {}), "weights_used": d.get("weights_used", {}),
            "naive_bayes_role": d.get("naive_bayes_role"), "svm_role": d.get("svm_role"),
            "top_roles": d.get("top_roles", []), "text_similarity": d.get("text_similarity"),
        }
