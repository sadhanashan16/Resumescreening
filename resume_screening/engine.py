"""Scoring engine: ranks resumes against a job description and recommends
job roles for a resume, using the trained TF-IDF / Naive Bayes / SVM model."""
from __future__ import annotations

import json
import threading
from datetime import date

import joblib
import numpy as np

from . import config
from .catalog import ROLE_BY_ID, ROLES, role_profile_text
from .parser import parse_job_description, parse_resume
from .skills import SKILL_BY_NAME, related_skills
from .text_utils import normalize_for_model

GRADES = [(70, "Strong match"), (50, "Good match"), (30, "Partial match"), (0, "Weak match")]


def grade_for(score: float) -> str:
    return next(label for threshold, label in GRADES if score >= threshold)


def _cosine(a, b) -> np.ndarray:
    """Rows of a (L2-normalised TF-IDF) against a single row b."""
    return np.asarray(a.dot(b.T).todense()).ravel()


class ScreeningEngine:
    def __init__(self, bundle: dict):
        self.vectorizer = bundle["vectorizer"]
        self.nb = bundle["nb"]
        self.svm = bundle["svm"]
        self.labels: list[str] = [str(x) for x in bundle["labels"]]
        self.titles = [ROLE_BY_ID[r]["title"] for r in self.labels]
        self._profiles = [ROLE_BY_ID[r] for r in self.labels]
        # role affinity: 1 for the same role, 0.4 for neighbouring roles in the catalog
        n = len(self.labels)
        self._affinity = np.eye(n)
        for i, role in enumerate(self._profiles):
            for adj in role["adjacent"]:
                if adj in self.labels:
                    j = self.labels.index(adj)
                    self._affinity[i, j] = self._affinity[j, i] = 0.4
        self._role_matrix = self.vectorizer.transform(
            [normalize_for_model(role_profile_text(r)) for r in self._profiles])

    # ------------------------------------------------------------ classifier
    def _role_proba(self, X) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        p_nb, p_svm = self.nb.predict_proba(X), self.svm.predict_proba(X)
        return p_nb, p_svm, (p_nb + p_svm) / 2

    # ----------------------------------------------------------------- jobs
    def analyse_job(self, text: str, title: str = "") -> dict:
        job = parse_job_description(text, title)
        X = self.vectorizer.transform([normalize_for_model(text)])
        _, _, p = self._role_proba(X)
        job["role_probabilities"] = p[0]
        top = int(p[0].argmax())
        job["predicted_role"] = {"id": self.labels[top], "title": self.titles[top], "confidence": round(float(p[0][top]), 3)}
        job["vector"] = X
        return job

    # -------------------------------------------------------------- scoring
    @staticmethod
    def _skill_overlap(required: list[str], have: list[str]) -> tuple[float | None, list, list, list]:
        """Coverage of ``required`` by ``have``; related skills earn half credit."""
        technical = [s for s in required if SKILL_BY_NAME[s].category != "soft"]
        req = technical or required
        if not req:
            return None, [], [], []
        have_set = set(have)
        matched, partial, missing, credit = [], [], [], 0.0
        for s in req:
            if s in have_set:
                matched.append(s)
                credit += 1
            else:
                near = sorted(related_skills(s) & have_set)
                if near:
                    partial.append({"required": s, "has": near[0]})
                    credit += 0.5
                else:
                    missing.append(s)
        return credit / len(req), matched, partial, missing

    def score_resume(self, profile: dict, job: dict, sim: float, resume_proba: np.ndarray) -> dict:
        w = dict(config.SCORE_WEIGHTS)
        comps: dict[str, float | None] = {}
        comps["text_similarity"] = min(1.0, max(0.0, sim) / config.SIMILARITY_CEILING)

        cov, matched, partial, missing = self._skill_overlap(job["skills"], profile["skills"])
        comps["skills"] = cov

        comps["role_fit"] = float(resume_proba @ self._affinity @ job["role_probabilities"])

        req_years = job["min_years"]
        comps["experience"] = None if req_years is None else min(1.0, profile["experience_years"] / req_years)

        req_edu = job["education_level"]
        if req_edu is None:
            comps["education"] = None
        else:
            have = profile["education"]["level"]
            comps["education"] = 1.0 if have >= req_edu else (have / req_edu if have else 0.25)

        active = {k: v for k, v in comps.items() if v is not None}
        total_w = sum(w[k] for k in active)
        score = 100 * sum(w[k] * v for k, v in active.items()) / total_w
        have_set = set(job["skills"])
        extra = [s for s in profile["skills"]
                 if s not in have_set and SKILL_BY_NAME[s].category != "soft"][:12]
        return {
            "score": round(score, 1),
            "grade": grade_for(score),
            "components": {k: (None if v is None else round(100 * v, 1)) for k, v in comps.items()},
            "weights_used": {k: round(w[k] / total_w, 3) for k in active},
            "matched_skills": matched,
            "related_skills": partial,
            "missing_skills": missing,
            "extra_skills": extra,
        }

    # --------------------------------------------------------------- public
    def screen(self, resumes: list[dict], job_text: str, job_title: str = "", top_n: int = 5) -> dict:
        """``resumes``: ``[{"filename", "text"}]``. Returns ranked candidates."""
        job = self.analyse_job(job_text, job_title)
        profiles = [parse_resume(r["text"], r["filename"]) for r in resumes]
        X = self.vectorizer.transform([normalize_for_model(p["blind_text"]) for p in profiles])
        sims = _cosine(X, job["vector"])
        p_nb, p_svm, p_ens = self._role_proba(X)

        candidates = []
        for i, prof in enumerate(profiles):
            res = self.score_resume(prof, job, float(sims[i]), p_ens[i])
            top = np.argsort(p_ens[i])[::-1][:3]
            candidates.append({
                "filename": prof["filename"], "name": prof["name"], "email": prof["email"], "phone": prof["phone"],
                "experience_years": prof["experience_years"], "education": prof["education"],
                "skills": prof["skills"], "word_count": prof["word_count"],
                "text_similarity": round(float(sims[i]), 3),
                "predicted_role": {"title": self.titles[int(top[0])], "confidence": round(float(p_ens[i][top[0]]), 3)},
                "naive_bayes_role": self.titles[int(p_nb[i].argmax())],
                "svm_role": self.titles[int(p_svm[i].argmax())],
                "top_roles": [{"title": self.titles[int(j)], "probability": round(float(p_ens[i][j]), 3)} for j in top],
                **res,
            })
        candidates.sort(key=lambda c: (-c["score"], -c["text_similarity"], c["filename"]))
        n = max(1, min(top_n, len(candidates))) if candidates else 0
        for rank, c in enumerate(candidates, 1):
            c["rank"] = rank
            c["shortlisted"] = rank <= n
        return {
            "job": {
                "title": job["title"], "skills": job["skills"], "min_years": job["min_years"],
                "education_level": job["education_level"], "predicted_role": job["predicted_role"],
            },
            "shortlist_size": n,
            "candidates": candidates,
            "summary": {
                "total": len(candidates),
                "average_score": round(float(np.mean([c["score"] for c in candidates])), 1) if candidates else 0,
                "strong_matches": sum(c["score"] >= 70 for c in candidates),
            },
        }

    def recommend_roles(self, text: str, filename: str = "", top_k: int = 5) -> dict:
        """Which job roles suit this resume best?"""
        prof = parse_resume(text, filename)
        X = self.vectorizer.transform([normalize_for_model(prof["blind_text"])])
        p_nb, p_svm, p = self._role_proba(X)
        sims = _cosine(self._role_matrix, X)
        have = prof["skills"]
        w = config.ROLE_WEIGHTS
        results = []
        for j, role in enumerate(self._profiles):
            core, secondary = role["core"], role["secondary"]
            c_cov, c_match, c_part, c_miss = self._skill_overlap(core, have)
            s_cov, s_match, _, _ = self._skill_overlap(secondary, have)
            skill_fit = (c_cov or 0) * 0.75 + (s_cov or 0) * 0.25
            sim_norm = min(1.0, float(sims[j]) / config.SIMILARITY_CEILING)
            score = 100 * (w["text_similarity"] * sim_norm + w["skills"] * skill_fit + w["classifier"] * float(p[0][j]))
            results.append({
                "id": role["id"], "title": role["title"], "description": role["description"],
                "score": round(score, 1), "grade": grade_for(score),
                "probability": round(float(p[0][j]), 3),
                "components": {"text_similarity": round(100 * sim_norm, 1), "skills": round(100 * skill_fit, 1),
                               "classifier": round(100 * float(p[0][j]), 1)},
                "matched_skills": c_match + s_match,
                "related_skills": c_part,
                "skills_to_learn": c_miss[:6],
                "typical_min_years": role["min_years"],
            })
        results.sort(key=lambda r: -r["score"])
        return {
            "candidate": {k: prof[k] for k in ("filename", "name", "email", "phone", "skills", "experience_years", "education", "word_count")},
            "naive_bayes_role": self.titles[int(p_nb[0].argmax())],
            "svm_role": self.titles[int(p_svm[0].argmax())],
            "roles": results[:top_k],
        }


# --------------------------------------------------------------- singleton
_engine: ScreeningEngine | None = None
_lock = threading.Lock()


def load_engine(train_if_missing: bool = True) -> ScreeningEngine:
    global _engine
    with _lock:
        if _engine is None:
            if not config.MODEL_PATH.exists():
                if not train_if_missing:
                    raise FileNotFoundError(f"{config.MODEL_PATH} not found - run: python -m resume_screening.train")
                from .train import main as train_main
                train_main([])
            _engine = ScreeningEngine(joblib.load(config.MODEL_PATH))
        return _engine


def load_metrics() -> dict | None:
    try:
        return json.loads(config.METRICS_PATH.read_text())
    except (OSError, ValueError):
        return None
