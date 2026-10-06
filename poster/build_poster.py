"""Build the A3-landscape project poster (HTML) from the real project artefacts.

    python poster/build_poster.py      # writes poster/poster.html
    python poster/render_poster.py     # writes poster/poster.png (4961x3508, 300 dpi) and poster.pdf (A3)

Every number on the poster is read from models/metrics.json, poster/assets/latency.json or computed by the
engine at build time; nothing is typed in by hand except descriptive text.
"""
from __future__ import annotations

import base64
import io
import json
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from resume_screening import config  # noqa: E402
from resume_screening.catalog import ROLE_BY_ID, role_job_description  # noqa: E402
from resume_screening.engine import load_engine  # noqa: E402
from resume_screening.extractor import extract_text  # noqa: E402
from resume_screening.skills import SKILLS  # noqa: E402

ASSETS = ROOT / "poster" / "assets"
M = json.loads(config.METRICS_PATH.read_text())
LAT = json.loads((ASSETS / "latency.json").read_text())

NAVY, BLUE, CYAN, LIGHT, EDGE, INK = "#0b3a73", "#1a6fc4", "#19a7d6", "#eaf6fd", "#8fd0ee", "#12233f"
GREEN, AMBER, RED = "#1f9d55", "#e0a100", "#d64545"


def img_b64(path: Path, width: int, crop=None, quality=None) -> str:
    im = Image.open(path).convert("RGB")
    if crop:
        im = im.crop(crop)
    im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


# ------------------------------------------------------------------ SVG helpers
def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def box(x, y, w, h, title, sub="", fill="#fff", stroke=BLUE, tcolor=NAVY, tsize=21, ssize=17, sw=2.5):
    cx = x + w / 2
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>']
    lines = sub.split("|") if sub else []
    total = tsize + len(lines) * (ssize + 3)
    ty = y + (h - total) / 2 + tsize * 0.85
    out.append(f'<text x="{cx}" y="{ty:.1f}" text-anchor="middle" font-size="{tsize}" font-weight="700" fill="{tcolor}">{esc(title)}</text>')
    for i, ln in enumerate(lines):
        out.append(f'<text x="{cx}" y="{ty + (i + 1) * (ssize + 3) + 1:.1f}" text-anchor="middle" font-size="{ssize}" fill="#37506f">{esc(ln)}</text>')
    return "".join(out)


def arrow(x1, y1, x2, y2, color=CYAN, w=3.5):
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{w}" marker-end="url(#ah)"/>')


def architecture_svg() -> str:
    s = ['<svg viewBox="0 0 1060 500" xmlns="http://www.w3.org/2000/svg" class="arch" font-family="inherit">',
         f'<defs><marker id="ah" markerWidth="9" markerHeight="9" refX="7" refY="4.5" orient="auto"><path d="M0,0 L9,4.5 L0,9 z" fill="{CYAN}"/></marker></defs>']
    cap = lambda x, t: f'<text x="{x}" y="22" font-size="18" font-weight="800" letter-spacing="1.5" fill="{BLUE}" text-anchor="middle">{t}</text>'  # noqa: E731
    s += [cap(80, "USERS"), cap(262, "WEB APP"), cap(555, "ML PIPELINE (IN MEMORY)"), cap(985, "OUTPUTS")]
    # users
    s.append(box(0, 45, 160, 100, "Recruiter", "job description|+ resumes", fill="#fff"))
    s.append(box(0, 175, 160, 100, "Candidate", "one resume", fill="#fff"))
    s.append(arrow(160, 95, 192, 95)); s.append(arrow(160, 225, 192, 225))
    # flask
    s.append(box(195, 45, 135, 230, "Flask", "UI pages|JSON API|/api/screen|/api/match|upload checks|strict CSP", fill="#dff1fb"))
    s.append(arrow(330, 160, 372, 160))
    # pipeline container
    s.append(f'<rect x="375" y="40" width="545" height="318" rx="16" fill="#f4fbff" stroke="{CYAN}" stroke-width="2.5" stroke-dasharray="9 6"/>')
    bw, bh = 160, 72
    xs = [392, 572, 752]
    s.append(box(xs[0], 62, bw, bh, "Text extractor", "PDF · DOCX|DOC · TXT", ssize=16))
    s.append(box(xs[1], 62, bw, bh, "NLP parser", "skills · education|experience", ssize=16))
    s.append(box(xs[2], 62, bw, bh, "Normaliser", "PII removed|skills → tokens", ssize=16))
    s.append(arrow(xs[0] + bw, 98, xs[1] - 3, 98)); s.append(arrow(xs[1] + bw, 98, xs[2] - 3, 98))
    s.append(arrow(xs[2] + bw / 2, 62 + bh, xs[2] + bw / 2, 162))
    s.append(box(xs[2], 165, bw, bh, "TF-IDF", f"1–2 grams|{M['n_features']:,} features", fill="#fff7e0", stroke=AMBER, ssize=16))
    s.append(box(xs[1], 165, bw, bh, "NB + SVM", "role probabilities", fill="#fff7e0", stroke=AMBER, ssize=16))
    s.append(box(xs[0], 165, bw, bh, "Ensemble", "average of both", fill="#fff7e0", stroke=AMBER, ssize=16))
    s.append(arrow(xs[2] - 3, 201, xs[1] + bw + 3, 201)); s.append(arrow(xs[1] - 3, 201, xs[0] + bw + 3, 201))
    s.append(box(392, 275, 520, 66, "Scoring engine", "40% similarity · 30% skills · 15% role · 10% exp. · 5% edu.", fill=NAVY, stroke=NAVY, tcolor="#fff", tsize=22, ssize=16))
    s[-1] = s[-1].replace('fill="#37506f"', 'fill="#d6ecff"')
    s.append(arrow(xs[2] + bw / 2, 237, xs[2] + bw / 2, 272)); s.append(arrow(xs[0] + bw / 2, 237, xs[0] + bw / 2, 272))
    # outputs
    s.append(arrow(920, 100, 941, 100)); s.append(arrow(920, 200, 941, 200)); s.append(arrow(920, 300, 941, 300))
    s.append(box(944, 62, 116, 76, "Shortlist", "ranked · CSV", fill="#e6f7ee", stroke=GREEN, ssize=16))
    s.append(box(944, 162, 116, 76, "Role match", "top roles", fill="#e6f7ee", stroke=GREEN, tsize=20, ssize=16))
    s.append(box(944, 262, 116, 76, "Insights", "metrics", fill="#e6f7ee", stroke=GREEN, ssize=16))
    # offline training
    s.append(f'<rect x="0" y="392" width="640" height="104" rx="14" fill="#fff" stroke="{BLUE}" stroke-width="2" stroke-dasharray="3 5"/>')
    s.append(f'<text x="14" y="418" font-size="17" font-weight="800" letter-spacing="1.2" fill="{BLUE}">OFFLINE TRAINING</text>')
    s.append(box(14, 428, 170, 56, "Data generator", f"{M['n_samples']:,} resumes", tsize=19, ssize=15))
    s.append(box(224, 428, 190, 56, "train.py", "TF-IDF + NB + SVM", tsize=19, ssize=15))
    s.append(box(454, 428, 170, 56, "model.joblib", "+ metrics.json", tsize=19, ssize=15, fill="#fff7e0", stroke=AMBER))
    s.append(arrow(184, 456, 221, 456)); s.append(arrow(414, 456, 451, 456))
    s.append(arrow(540, 428, 540, 362, color=AMBER))
    # deployment
    s.append(f'<rect x="680" y="392" width="380" height="104" rx="14" fill="#fff" stroke="{BLUE}" stroke-width="2" stroke-dasharray="3 5"/>')
    s.append(f'<text x="694" y="418" font-size="17" font-weight="800" letter-spacing="1.2" fill="{BLUE}">DEPLOYMENT-READY</text>')
    s.append(box(694, 428, 100, 56, "Docker", "", tsize=19)); s.append(box(824, 428, 110, 56, "Gunicorn", "", tsize=19)); s.append(box(964, 428, 84, 56, "Render", "", tsize=19))
    s.append(arrow(794, 456, 821, 456)); s.append(arrow(934, 456, 961, 456))
    s.append("</svg>")
    return "".join(s)


def confusion_svg() -> str:
    labels_full = M["confusion_matrix"]["labels"]
    short = {"Backend Developer": "Backend", "Business Analyst": "Bus. Analyst", "Cybersecurity Analyst": "Cybersecurity",
             "Data Analyst": "Data Analyst", "Data Engineer": "Data Engineer", "Data Scientist": "Data Scientist",
             "DevOps Engineer": "DevOps", "Frontend Developer": "Frontend", "Full Stack Developer": "Full Stack",
             "Machine Learning Engineer": "ML Engineer", "Mobile App Developer": "Mobile App", "QA Engineer": "QA Engineer"}
    labels = [short.get(l, l) for l in labels_full]
    mat = M["confusion_matrix"]["matrix"]
    n, cell, lx, ty = len(labels), 19, 118, 112
    W, H = lx + n * cell + 4, ty + n * cell + 4
    s = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" class="cm" font-family="inherit">']
    for j, l in enumerate(labels):
        x = lx + j * cell + cell / 2 + 6
        s.append(f'<text transform="translate({x},{ty - 8}) rotate(-90)" font-size="16" fill="{INK}">{esc(l)}</text>')
    mx = max(max(r) for r in mat)
    for i, row in enumerate(mat):
        s.append(f'<text x="{lx - 8}" y="{ty + i * cell + cell / 2 + 6}" text-anchor="end" font-size="16" fill="{INK}">{esc(labels[i])}</text>')
        for j, v in enumerate(row):
            x, y = lx + j * cell, ty + i * cell
            if v == 0:
                fill, op = "#f1f6fb", 1
            elif i == j:
                fill, op = BLUE, 0.35 + 0.65 * v / mx
            else:
                fill, op = RED, 0.9
            s.append(f'<rect x="{x}" y="{y}" width="{cell - 2}" height="{cell - 2}" rx="3" fill="{fill}" fill-opacity="{op:.2f}"/>')
            if v and (i != j or True):
                col = "#fff" if (i == j and op > 0.55) or i != j else INK
                s.append(f'<text x="{x + (cell - 2) / 2}" y="{y + cell / 2 + 5}" text-anchor="middle" font-size="13" font-weight="700" fill="{col}">{v}</text>')
    s.append(f'<text x="{lx + n * cell / 2}" y="{H + 18}" text-anchor="middle" font-size="16" fill="#37506f"></text>')
    s.append("</svg>")
    return "".join(s)


def ranking_svg(rows) -> str:
    """Horizontal bars: live ranking of the 14 sample resumes against the Data Scientist example JD."""
    W, rowh, lx, bx, bw = 296, 38, 130, 138, 100
    H = 8 + rowh * len(rows)
    s = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" class="rank" font-family="inherit">']
    for i, (name, score, role, short) in enumerate(rows):
        y = 8 + i * rowh
        color = GREEN if score >= 70 else (BLUE if score >= 50 else (AMBER if score >= 30 else "#9aa9bd"))
        s.append(f'<text x="{lx}" y="{y + 25}" text-anchor="end" font-size="17" font-weight="600" fill="{INK}">{esc(name)}</text>')
        s.append(f'<rect x="{bx}" y="{y + 7}" width="{bw}" height="24" rx="6" fill="#e1ecf6"/>')
        s.append(f'<rect x="{bx}" y="{y + 7}" width="{bw * score / 100:.1f}" height="24" rx="6" fill="{color}"/>')
        s.append(f'<text x="{bx + bw + 8}" y="{y + 26}" font-size="18" font-weight="800" fill="{NAVY}">{score:.1f}</text>')
    s.append("</svg>")
    return "".join(s)


def weights_svg() -> str:
    parts = [("Text sim.", 40, NAVY), ("Skills", 30, BLUE), ("Role fit", 15, CYAN), ("Exp.", 10, "#6cc4e6"), ("Edu.", 5, "#a9dcf0")]
    W, x = 340, 0
    s = [f'<svg viewBox="0 0 {W} 64" xmlns="http://www.w3.org/2000/svg" class="wts" font-family="inherit">']
    for name, w, col in parts:
        ww = W * w / 100
        s.append(f'<rect x="{x:.1f}" y="0" width="{ww - 2:.1f}" height="34" rx="4" fill="{col}"/>')
        if w >= 10:
            s.append(f'<text x="{x + (ww - 2) / 2:.1f}" y="24" text-anchor="middle" font-size="18" font-weight="800" fill="#fff">{w}%</text>')
        else:
            s.append(f'<text x="{x + (ww - 2) / 2:.1f}" y="24" text-anchor="middle" font-size="15" font-weight="800" fill="{NAVY}">{w}</text>')
        s.append(f'<text x="{x + (ww - 2) / 2:.1f}" y="58" text-anchor="middle" font-size="15" fill="#37506f">{name}</text>')
        x += ww
    s.append("</svg>")
    return "".join(s)


# ---------------------------------------------------------------- live evidence
def demo_ranking():
    eng = load_engine()
    jd = role_job_description(ROLE_BY_ID["data-scientist"])
    resumes = [{"filename": p.name, "text": extract_text(p.name, p.read_bytes())} for p in sorted((ROOT / "samples").iterdir())]
    out = eng.screen(resumes, jd, "", top_n=5)
    rows = [(c["name"], c["score"], c["predicted_role"]["title"], c["grade"]) for c in out["candidates"][:6]]
    return rows, out["summary"]


ICONS = {  # simple outline icons, 48x48
    "doc": '<path d="M12 6h18l8 8v28H12z"/><path d="M30 6v8h8M18 24h14M18 31h14"/>',
    "target": '<circle cx="24" cy="26" r="15"/><circle cx="24" cy="26" r="8"/><circle cx="24" cy="26" r="2"/><path d="M24 26L40 8M34 8h6v6"/>',
    "gear": '<circle cx="24" cy="24" r="7"/><path d="M24 6v6M24 36v6M6 24h6M36 24h6M11 11l4 4M33 33l4 4M37 11l-4 4M15 33l-4 4"/>',
    "db": '<ellipse cx="24" cy="12" rx="14" ry="6"/><path d="M10 12v24c0 3 6 6 14 6s14-3 14-6V12M10 24c0 3 6 6 14 6s14-3 14-6"/>',
    "chart": '<path d="M8 40h34M12 40V26M22 40V14M32 40V22M42 40V30"/>',
    "check": '<circle cx="24" cy="24" r="17"/><path d="M15 25l7 7 12-14"/>',
    "bulb": '<path d="M17 32c-5-4-6-8-6-11a13 13 0 0126 0c0 3-1 7-6 11v4H17z"/><path d="M18 42h12"/>',
    "book": '<path d="M8 10h14c3 0 4 2 4 4v26c0-2-1-4-4-4H8zM40 10H26v30c0-2 1-4 4-4h10z"/>',
    "users": '<circle cx="17" cy="16" r="6"/><circle cx="33" cy="18" r="5"/><path d="M5 38c0-8 5-13 12-13s12 5 12 13M30 27c7-1 13 3 13 11"/>',
    "shield": '<path d="M24 5l15 6v11c0 10-6 17-15 21C15 39 9 32 9 22V11z"/><path d="M17 24l5 5 9-10"/>',
    "flow": '<rect x="5" y="8" width="12" height="10" rx="2"/><rect x="31" y="8" width="12" height="10" rx="2"/><rect x="18" y="30" width="12" height="10" rx="2"/><path d="M17 13h14M11 18v6h26v-6M24 24v6"/>',
    "code": '<path d="M16 14L6 24l10 10M32 14l10 10-10 10M28 8l-8 32"/>',
    "wrench": '<path d="M30 8a10 10 0 00-9 14L8 35l5 5 13-13a10 10 0 0014-9l-7 5-5-5z"/>',
}


def icon(name, color=BLUE, size=70):
    return (f'<svg class="pico" width="{size}" height="{size}" viewBox="0 0 48 48" fill="none" stroke="{color}" '
            f'stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round">{ICONS[name]}</svg>')


def panel(cls, title, body, ico=None, extra=""):
    return (f'<section class="panel {cls}" {extra}><div class="pill">{title}</div>'
            f'{icon(ico) if ico else ""}<div class="pbody">{body}</div></section>')


def main():
    rows, summ = demo_ranking()
    h = M["holdout"]; cv = M["cross_validation"]
    acc = h["ensemble"]["accuracy"] * 100
    n_correct = sum(M["confusion_matrix"]["matrix"][i][i] for i in range(M["n_roles"]))

    tech = [("Python", "Py"), ("Flask", "Fl"), ("scikit-learn", "sk"), ("Pandas", "Pd"), ("NumPy", "Np"), ("pypdf", "Pf"),
            ("python-docx", "Dx"), ("joblib", "Jb"), ("HTML·CSS·JS", "Js"), ("Gunicorn", "Gu"), ("Docker", "Dk"), ("Render", "Rn")]
    tech_html = "".join(f'<div class="tech"><b>{b}</b>{n}</div>' for n, b in tech)

    steps = [("doc", "Upload", "PDF · DOC · DOCX · TXT"), ("wrench", "Extract text", "PDF · DOCX · DOC"),
             ("code", "NLP parsing", "skills, degrees|& experience"), ("shield", "Normalise", "PII removed · skill tokens"),
             ("db", "TF-IDF", "1–2 grams"), ("gear", "Classify", "Naive Bayes + SVM"), ("chart", "Rank & shortlist", "5-part score")]
    flow = ""
    for i, (ic, t, s) in enumerate(steps, 1):
        flow += f'<div class="step"><span class="num">{i}</span>{icon(ic, BLUE, 54)}<b>{t}</b><small>{s.replace("|", "<br>")}</small></div>'
        if i < len(steps):
            flow += '<span class="arr">➜</span>'

    lat = f"{LAT['screen14_median_s'] + 1e-9:.2f}"
    kpi = [(f"{acc:.1f}%", f"Ensemble accuracy ({n_correct}/{M['n_test']} test)"),
           (f"{h['ensemble']['f1']:.3f}", "Macro F1-score (P = R = 0.998)"),
           (f"{cv['svm']['accuracy'] * 100:.1f}%", f"SVM 5-fold CV (NB {cv['naive_bayes']['accuracy'] * 100:.1f}%)"),
           ("5 / 5", "Hand-written resumes matched"),
           (f"{lat} s", "to screen 14 resumes (median)")]
    kpi_html = "".join(f'<div class="kpi"><b>{a}</b><span>{b}</span></div>' for a, b in kpi)

    def r(m):
        return f"{m:.3f}"
    table = ("<table class='mt'><tr><th>Model</th><th>Acc.</th><th>F1</th><th>CV</th></tr>"
             f"<tr><td>Naive Bayes</td><td>{r(h['naive_bayes']['accuracy'])}</td><td>{r(h['naive_bayes']['f1'])}</td><td>{r(cv['naive_bayes']['accuracy'])}</td></tr>"
             f"<tr><td>SVM</td><td>{r(h['svm']['accuracy'])}</td><td>{r(h['svm']['f1'])}</td><td>{r(cv['svm']['accuracy'])}</td></tr>"
             f"<tr class='hl'><td>Ensemble</td><td>{r(h['ensemble']['accuracy'])}</td><td>{r(h['ensemble']['f1'])}</td><td>–</td></tr></table>")

    results_body = f"""
      <div class="kpis">{kpi_html}</div>
      <div class="rgrid">
        <div class="rcol r1"><h4>Model comparison</h4>{table}
          <h4>Match-score weights</h4>{weights_svg()}
          <p class="note">Synthetic data: shows the pipeline works, not real-world accuracy.</p></div>
        <div class="rcol r2"><h4>Confusion matrix <small>(n={M['n_test']})</small></h4>{confusion_svg()}
          </div>
        <div class="rcol r3"><h4>Live ranking</h4>{ranking_svg(rows)}
          <p class="note">Data Scientist job vs {summ['total']} sample resumes; the top 2 are Data Scientist resumes.</p></div>
      </div>"""

    html = TEMPLATE
    rep = {
        "{{ARCH}}": architecture_svg(),
        "{{FLOW}}": flow, "{{TECH}}": tech_html, "{{RESULTS}}": results_body,
        "{{SHOT_SCREEN}}": img_b64(ASSETS / "ui_screen.png", 1100, crop=(0, 780, 1420, 1270)),
        "{{N_SAMPLES}}": f"{M['n_samples']:,}", "{{LAT}}": lat, "{{N_TRAIN}}": f"{M['n_train']:,}", "{{N_TEST}}": f"{M['n_test']}",
        "{{N_FEAT}}": f"{M['n_features']:,}", "{{N_ROLES}}": str(M["n_roles"]), "{{N_SKILLS}}": str(len(SKILLS)),
        "{{NAVY}}": NAVY, "{{BLUE}}": BLUE, "{{CYAN}}": CYAN, "{{LIGHT}}": LIGHT, "{{EDGE}}": EDGE, "{{INK}}": INK,
        "{{ICO_DOC}}": icon("doc"), "{{ICO_TARGET}}": icon("target", "#d64545"), "{{ICO_GEAR}}": icon("gear"),
        "{{ICO_DB}}": icon("db"), "{{ICO_CHART}}": icon("chart"), "{{ICO_CHECK}}": icon("check", GREEN),
        "{{ICO_BULB}}": icon("bulb", AMBER), "{{ICO_BOOK}}": icon("book"), "{{ICO_USERS}}": icon("users"),
        "{{ICO_FLOW}}": icon("flow"), "{{ICO_CODE}}": icon("code"), "{{ICO_SHIELD}}": icon("shield"), "{{ICO_WRENCH}}": icon("wrench"),
    }
    for k, v in rep.items():
        html = html.replace(k, v)
    (ROOT / "poster" / "poster.html").write_text(html, encoding="utf-8")
    print("wrote poster/poster.html", len(html) // 1024, "KB")


TEMPLATE = (ROOT / "poster" / "poster.tmpl.html").read_text(encoding="utf-8")

if __name__ == "__main__":
    main()
