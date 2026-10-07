"""Measure the numbers quoted in the report (run: python report/measure.py -> report/measurements.json).

Everything is timed through the real Flask app (test client) with a fresh SQLite database, a logged-in user and the
14 sample resumes, so screening time includes text extraction, the ML pipeline AND saving the results to the database.
"""
from __future__ import annotations

import json
import os
import re
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("APP_DATA_DIR", tempfile.mkdtemp(prefix="resumeiq-measure-"))
os.environ.setdefault("SECRET_KEY", "measurement-only-secret-key")

from app import create_app  # noqa: E402
from resume_screening.catalog import ROLE_BY_ID, role_job_description  # noqa: E402
from webapp.extensions import db  # noqa: E402
from webapp.models import User  # noqa: E402

JD = role_job_description(ROLE_BY_ID["data-scientist"])


def rss_mb() -> float:
    m = re.search(r"VmRSS:\s+(\d+) kB", Path("/proc/self/status").read_text())
    return round(int(m.group(1)) / 1024, 1)


def main():
    app = create_app({"TESTING": True, "RATELIMIT_ENABLED": False, "WTF_CSRF_ENABLED": False, "SQLALCHEMY_DATABASE_URI": "sqlite://",
                      "SQLALCHEMY_ENGINE_OPTIONS": {"pool_pre_ping": True}, "SECRET_KEY": "m"})
    with app.app_context():
        db.create_all()
    c = app.test_client()
    pw = "Measure-Pass-42"
    c.post("/register", data={"name": "Measure User", "email": "m@example.com", "password": pw, "confirm": pw})

    def timed(fn, n):
        fn()                                  # warm-up
        t = []
        for _ in range(n):
            s = time.perf_counter(); fn(); t.append(time.perf_counter() - s)
        return statistics.median(t), max(t)

    def screen():
        r = c.post("/api/screen", data={"job_description": JD, "use_samples": "1", "top_n": "5"}, content_type="multipart/form-data")
        assert r.status_code == 201

    screen_med, screen_max = timed(screen, 10)
    list_med, _ = timed(lambda: c.get("/api/candidates?status=all&sort=score&per_page=25"), 20)
    page_med, _ = timed(lambda: c.get("/dashboard"), 20)

    with app.app_context():
        u = db.session.execute(db.select(User)).scalar_one()
        hash_med, _ = timed(lambda: u.check_password(pw), 7)
        scheme = u.password_hash.split("$")[0]

    counts = {}
    out = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider"], cwd=ROOT,
                         capture_output=True, text=True).stdout
    for line in out.splitlines():
        m = re.match(r"tests/(test_\w+\.py)::", line)
        if m:
            counts[m.group(1)] = counts.get(m.group(1), 0) + 1

    res = {"screen14_median_s": round(screen_med, 3), "screen14_max_s": round(screen_max, 3),
           "candidate_list_median_ms": round(list_med * 1000, 1), "dashboard_median_ms": round(page_med * 1000, 1),
           "password_check_median_ms": round(hash_med * 1000, 1), "password_scheme": scheme,
           "process_rss_mb": rss_mb(), "tests_by_file": counts, "tests_total": sum(counts.values())}
    (ROOT / "report" / "measurements.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
