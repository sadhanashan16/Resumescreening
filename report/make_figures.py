"""Generate the report figures that are not UI screenshots (all values come from real artefacts)."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
FIG = ROOT / "report" / "figures"
from resume_screening import config  # noqa: E402
from resume_screening.catalog import ROLE_BY_ID, role_job_description  # noqa: E402
from resume_screening.engine import load_engine  # noqa: E402
from resume_screening.extractor import extract_text  # noqa: E402

M = json.loads(config.METRICS_PATH.read_text())
NAVY, BLUE, CYAN, ORANGE, GREY = "#0b3a73", "#1a6fc4", "#19a7d6", "#ed7d31", "#8a97a8"
plt.rcParams.update({"font.family": "Liberation Serif", "font.size": 11, "axes.spines.top": False, "axes.spines.right": False})


def html_to_png(html: str, path: Path, width: int, scale=2):
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium", args=["--no-sandbox"])
        pg = b.new_page(viewport={"width": width, "height": 400}, device_scale_factor=scale)
        pg.set_content(html)
        pg.wait_for_timeout(300)
        pg.locator("body > :first-child").screenshot(path=str(path))
        b.close()


# ---------------------------------------------------------------- Figure 4.1
def architecture():
    def box(t, sub, bg="#eaf3fb", bd="#1a6fc4", dark=False, flex=1):
        tc, sc = ("#fff", "#d6ecff") if dark else ("#0b3a73", "#37506f")
        return (f"<div style='flex:{flex};background:{bg};border:2.5px solid {bd};border-radius:12px;padding:10px 12px;text-align:center'>"
                f"<div style='color:{tc};font-size:20px;font-weight:700;line-height:1.15'>{t}</div>"
                f"<div style='font-size:15px;color:{sc};line-height:1.25;margin-top:3px'>{sub}</div></div>")
    def row(*items, gap=14):
        return f"<div style='display:flex;gap:{gap}px'>" + "".join(items) + "</div>"
    amber, ab = "#fff6df", "#e0a100"
    green, gb = "#e6f7ee", "#1f9d55"
    arrow = "<div style='text-align:center;color:#19a7d6;font-size:26px;line-height:1.05;margin:2px 0'>&#8645;</div>"
    cap = lambda t: f"<div style='text-align:center;font-size:14px;color:#37506f;margin:-2px 0 2px'>{t}</div>"
    browser = row(box("Recruiter&rsquo;s browser", "HTML &middot; CSS &middot; JavaScript &middot; session cookie &middot; CSRF token", bg="#f1f4f8", bd="#8a97a8"))
    app = ("<div style='border:3px solid #0b3a73;border-radius:16px;padding:10px 12px;background:#f7fbff'>"
           "<div style='color:#0b3a73;font-weight:800;font-size:19px;text-align:center;margin-bottom:8px'>"
           "Flask application &middot; Gunicorn (1 worker &times; 4 threads) &middot; Docker</div>"
           + row(box("Security layer", "CSP &middot; HSTS &middot; CSRF<br>rate limits &middot; ProxyFix", bg="#fdeceb", bd="#c9534b"),
                 box("Auth blueprint", "register &middot; login &middot; logout<br>Flask-Login &middot; scrypt", bg=amber, bd=ab),
                 box("Pages", "dashboard &middot; screenings<br>shortlist &middot; match &middot; insights"),
                 box("JSON API", "/api/screen &middot; /api/candidates<br>/api/match &middot; /health")) + "</div>")
    lower = row(box("ML engine (resume_screening)", "extractor &rarr; parser &rarr; TF-IDF &rarr; Naive Bayes + SVM &rarr; five-part scorer<br>model.joblib loaded once at start-up", bg="#0b3a73", bd="#0b3a73", dark=True, flex=1.25),
                box("Database", "SQLAlchemy + Alembic migrations<br>users &middot; screenings &middot; candidates", bg=green, bd=gb))
    ops = row(box("Render", "web service + managed PostgreSQL<br>render.yaml blueprint &middot; generated SECRET_KEY", bg="#f1f4f8", bd="#8a97a8"),
              box("GitHub Actions CI", "78 tests on SQLite and PostgreSQL<br>Docker image build", bg="#f1f4f8", bd="#8a97a8"))
    html = ("<html><body style='margin:0;background:#fff'><div style='width:1040px;padding:16px;background:#fff;"
            "font-family:\"Liberation Sans\",Arial,sans-serif'>"
            + browser + cap("HTTPS requests &middot; JSON responses") + arrow + app + arrow
            + lower + "<div style='height:10px'></div>" + ops + "</div></body></html>")
    html_to_png(html, FIG / "fig_architecture.png", 1072)


# ---------------------------------------------------------------- Figure 6.1
def metrics_chart():
    h = M["holdout"]
    models = [("Naive Bayes", "naive_bayes"), ("SVM", "svm"), ("Ensemble", "ensemble")]
    fig, ax = plt.subplots(1, 2, figsize=(9.6, 3.6), gridspec_kw={"width_ratios": [1.15, 1]})
    # (a) final model: four metrics per model
    names = ["Accuracy", "Precision", "Recall", "F1 (macro)"]
    keys = ["accuracy", "precision", "recall", "f1"]
    x = np.arange(len(names)); w = 0.26
    for i, (label, k) in enumerate(models):
        vals = [h[k][m] for m in keys]
        bars = ax[0].bar(x + (i - 1) * w, vals, w, label=label, color=[BLUE, CYAN, NAVY][i])
        for b_, v in zip(bars, vals):
            ax[0].text(b_.get_x() + b_.get_width() / 2, v + 0.0004, f"{v:.3f}", ha="center", va="bottom", fontsize=7.5, rotation=90)
    ax[0].set_xticks(x, names); ax[0].set_ylim(0.98, 1.004); ax[0].set_ylabel("Score (axis starts at 0.98)")
    ax[0].set_title("(a) Hold-out metrics, final model (n = %d)" % M["n_test"], fontsize=10)
    ax[0].legend(fontsize=8, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.12), frameon=False)
    # (b) hold-out accuracy across the three training-data iterations (values recorded during development)
    iters = ["Iteration 1\n(template data)", "Iteration 2a\n(+ noise)", "Iteration 2b\n(final data)"]
    series = {"Naive Bayes": [1.000, 0.996, h["naive_bayes"]["accuracy"]], "SVM": [1.000, 0.992, h["svm"]["accuracy"]],
              "Ensemble": [1.000, 0.996, h["ensemble"]["accuracy"]]}
    x = np.arange(3)
    for i, (label, vals) in enumerate(series.items()):
        ax[1].plot(x, vals, marker="o", label=label, color=[BLUE, CYAN, NAVY][i], linewidth=2)
    ax[1].set_xticks(x, iters, fontsize=8.5); ax[1].set_ylim(0.985, 1.003); ax[1].set_ylabel("Hold-out accuracy")
    ax[1].set_title("(b) Accuracy across data iterations", fontsize=10); ax[1].legend(fontsize=8, frameon=False, loc="lower left")
    ax[1].axhline(1.0, color=GREY, linestyle=":", linewidth=1)
    fig.tight_layout(); fig.savefig(FIG / "fig_metrics.png", dpi=220); plt.close(fig)


# ---------------------------------------------------------------- Figure 6.2
def confusion():
    short = {"Backend Developer": "Backend", "Business Analyst": "Business Analyst", "Cybersecurity Analyst": "Cybersecurity",
             "Data Analyst": "Data Analyst", "Data Engineer": "Data Engineer", "Data Scientist": "Data Scientist",
             "DevOps Engineer": "DevOps", "Frontend Developer": "Frontend", "Full Stack Developer": "Full Stack",
             "Machine Learning Engineer": "ML Engineer", "Mobile App Developer": "Mobile App", "QA Engineer": "QA Engineer"}
    labels = [short[l] for l in M["confusion_matrix"]["labels"]]
    cm = np.array(M["confusion_matrix"]["matrix"])
    fig, ax = plt.subplots(figsize=(6.4, 5.4))
    im = ax.imshow(cm, cmap="Blues", vmin=0, vmax=cm.max())
    ax.set_xticks(range(len(labels)), labels, rotation=60, ha="right", fontsize=8.5)
    ax.set_yticks(range(len(labels)), labels, fontsize=8.5)
    ax.set_xlabel("Predicted role"); ax.set_ylabel("True role")
    for i in range(len(labels)):
        for j in range(len(labels)):
            v = cm[i, j]
            if v:
                ax.text(j, i, str(v), ha="center", va="center", fontsize=8.5, fontweight="bold",
                        color="white" if (i == j and v > cm.max() * 0.5) else ("#b00020" if i != j else NAVY))
    ax.spines[:].set_visible(False)
    fig.tight_layout(); fig.savefig(FIG / "fig_confusion.png", dpi=220); plt.close(fig)


# ---------------------------------------------------------------- Figure 6.3
def ranking():
    eng = load_engine()
    jd = role_job_description(ROLE_BY_ID["data-scientist"])
    resumes = [{"filename": p.name, "text": extract_text(p.name, p.read_bytes())} for p in sorted((ROOT / "samples").iterdir())]
    out = eng.screen(resumes, jd, "Data Scientist", top_n=5)
    cands = out["candidates"]
    json.dump(out, open(ROOT / "report" / "ranking_demo.json", "w"), default=str, indent=1)
    names = [f"{c['name']}  ({c['predicted_role']['title']})" for c in cands][::-1]
    scores = [c["score"] for c in cands][::-1]
    colors = [("#1f9d55" if s >= 70 else BLUE if s >= 50 else ORANGE if s >= 30 else GREY) for s in scores]
    fig, ax = plt.subplots(figsize=(8.2, 4.6))
    bars = ax.barh(names, scores, color=colors)
    for b_, s in zip(bars, scores):
        ax.text(s + 0.8, b_.get_y() + b_.get_height() / 2, f"{s:.1f}", va="center", fontsize=9, fontweight="bold")
    ax.set_xlim(0, 100); ax.set_xlabel("Match score (0–100)")
    for x_, lab in ((70, "strong ≥ 70"), (50, "good ≥ 50"), (30, "partial ≥ 30")):
        ax.axvline(x_, color=GREY, linestyle="--", linewidth=0.8); ax.text(x_ + 0.5, len(names) - 0.35, lab, fontsize=7.5, color=GREY)
    ax.tick_params(axis="y", labelsize=8.5)
    fig.tight_layout(); fig.savefig(FIG / "fig_ranking.png", dpi=220); plt.close(fig)


# ---------------------------------------------------------------- Figure 7.1
def outcomes():
    rows = [
        ("#3f6fa8", "TECHNICAL / ML COMPETENCY", ["Text classification with Naive Bayes and SVM", "TF-IDF features, cosine similarity, probability calibration", "Held-out and cross-validated evaluation"]),
        ("#3c8f5a", "PROBLEM FRAMING & ITERATION", ["Baseline, refinement and final approach (Chapter 4)", "Data too easy at first, so noise was added", "Role-fit and grade thresholds recalibrated"]),
        ("#7a62a8", "TEAMWORK & DIVISION", ["ML / platform and UI / testing split, equal contribution", "Joint review of every milestone", "Reflections in Section 7.1"]),
        ("#c9534b", "ENGINEERING RIGOUR BEYOND THE MODEL", ["78 automated tests, UI verified in a real browser", "Accounts, CSRF, rate limits, strict security headers", "PostgreSQL migrations, Docker image, Render blueprint"]),
        ("#c99a2e", "HONEST SELF-ASSESSMENT", ["Synthetic data stated openly (Chapter 6)", "99.8% is not a real-world accuracy figure", "Rule-based extraction and no OCR acknowledged"]),
    ]
    items = "".join(
        f"<div style='background:{c};color:#fff;border-radius:14px;padding:12px 20px;margin-bottom:10px'>"
        f"<div style='font-weight:800;font-size:19px;letter-spacing:.3px;margin-bottom:4px'>{t}</div>"
        + "".join(f"<div style='font-size:16px;line-height:1.35'>• {b}</div>" for b in bs) + "</div>"
        for c, t, bs in rows)
    html = (f"<html><body style='margin:0;background:#fff'><div style='width:760px;padding:16px;background:#fff;"
            f"font-family:\"Liberation Sans\",Arial,sans-serif'>{items}</div></body></html>")
    html_to_png(html, FIG / "fig_outcomes.png", 800)


def pipeline():
    def box(t, sub="", bg="#eaf3fb", bd="#1a6fc4", w=None, dark=False):
        tc, sc = ("#fff", "#d6ecff") if dark else ("#0b3a73", "#37506f")
        st = f"background:{bg};border:2.5px solid {bd};border-radius:12px;padding:9px 10px;text-align:center;box-sizing:border-box;{'width:%dpx;' % w if w else ''}"
        return f"<div style='{st}'><div style='color:{tc};font-size:20px;font-weight:700;line-height:1.15'>{t}</div>" + (f"<div style='font-size:15px;color:{sc};line-height:1.2;margin-top:2px'>{sub}</div>" if sub else "") + "</div>"
    arr = "<div style='color:#19a7d6;font-size:30px;line-height:1;padding:0 8px;align-self:center'>&#10140;</div>"
    down = "<div style='color:#19a7d6;font-size:30px;text-align:center;line-height:1.1'>&#8595;</div>"
    amber, ab = "#fff6df", "#e0a100"
    def row(*items, gap=0):
        return f"<div style='display:flex;justify-content:center;gap:{gap}px'>" + "".join(items) + "</div>"
    rows = [
        row(box("Resume file", "PDF · DOC · DOCX · TXT", w=210), arr, box("Extract text", "pypdf · python-docx · antiword", w=240), arr, box("NLP parsing", "skills · degree · years", w=200)),
        row(box("Normalise", "remove PII, canonical skills", w=270), arr, box("TF-IDF vector", "unigrams + bigrams", bg=amber, bd=ab, w=240)),
        row(box("Naive Bayes", "P(role | resume)", bg=amber, bd=ab, w=215), box("Calibrated SVM", "P(role | resume)", bg=amber, bd=ab, w=215), box("Cosine similarity", "resume vs. job description", bg=amber, bd=ab, w=250), gap=22),
        row(box("Ensemble", "average → role distribution", bg=amber, bd=ab, w=300), box("Skills · experience · education", "from the parser and the job description", w=380), gap=22),
        row(box("Weighted score 0–100", "40% similarity · 30% skills · 15% role fit · 10% experience · 5% education", bg="#0b3a73", bd="#0b3a73", w=700, dark=True)),
        row(box("Grade · rank · shortlist", "with matched, related and missing skills", bg="#e6f7ee", bd="#1f9d55", w=700)),
    ]
    html = (f"<html><body style='margin:0;background:#fff'><div style='width:760px;padding:14px;background:#fff;font-family:\"Liberation Sans\",Arial,sans-serif'>"
            + down.join(rows) + "</div></body></html>")
    html_to_png(html, FIG / "fig_pipeline.png", 790)


if __name__ == "__main__":
    pipeline(); architecture(); metrics_chart(); confusion(); ranking(); outcomes()
    print(sorted(p.name for p in FIG.iterdir()))
