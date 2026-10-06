# ResumeIQ: AI Resume Screening & Job Matching

An end-to-end machine-learning web application that reads resumes (PDF / DOC / DOCX / TXT), extracts skills, education and experience with NLP, matches them to a job description and produces a ranked, explainable shortlist. It can also take a single resume and recommend the job roles it fits best.

**Stack:** Python · Flask · scikit-learn (TF-IDF, Multinomial Naive Bayes, linear SVM) · Pandas · NumPy · pypdf · python-docx · Gunicorn · Docker · Render

## Features

| | |
|---|---|
| **Recruiter mode** (`/screen`) | Paste a job description, upload up to 30 resumes, get a top-N shortlist with score breakdown, matched / related / missing skills, CSV export |
| **Candidate mode** (`/match`) | Upload one resume, see the best-fit roles (of 12), how Naive Bayes and SVM each classify it, and which skills to learn |
| **Model insights** (`/insights`) | Hold-out + cross-validated metrics, per-role F1, confusion matrix, top predictive terms |
| **JSON API** | `POST /api/screen`, `POST /api/match`, `GET /api/roles`, `GET /api/model`, `GET /health` |
| **Bias-aware** | Name, e-mail, phone and URLs are removed from the text before scoring |
| **Private** | Files are processed in memory and never written to disk or stored |

## How it works

```
resume file ──► text extraction ──► NLP parsing ──► normalisation ──► TF-IDF (1-2 grams)
(pdf/doc/docx/txt)  (pypdf, python-docx,   (sections, skills,   (skills → canonical   │
                     antiword)              education, years)    tokens, no PII)       ├─► cosine similarity vs. job description
                                                                                      ├─► Multinomial Naive Bayes ─┐
                                                                                      └─► Calibrated linear SVM ───┴─► role probabilities
```

**Match score (0-100)** = weighted sum, re-normalised when the job description omits a requirement:

| Weight | Component | Source |
|---|---|---|
| 40% | Text similarity | TF-IDF cosine similarity between resume and JD |
| 30% | Skill coverage | Share of JD skills found in the resume; related skills (MySQL ↔ PostgreSQL) earn ½ credit |
| 15% | Role fit | Agreement between the NB+SVM role distributions of the resume and the JD |
| 10% | Experience | Years estimated from date ranges / stated experience vs. years requested |
| 5% | Education | Highest degree detected vs. level requested |

Grades: ≥70 strong · ≥50 good · ≥30 partial · otherwise weak. The shortlist is the top-N by score.

## Run locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
python -m resume_screening.train      # trains the models (~10 s) -> models/
python app.py                          # http://localhost:5000
pytest -q                              # 34 tests
```

If `models/` is missing the app trains itself on first start.
For `.doc` (Word 97-2003) files install `antiword` (`apt install antiword`); without it a best-effort fallback reader is used.

## Deploy to Render

The repo contains a [Render Blueprint](render.yaml) and a `Dockerfile` (installs `antiword`, trains the model at build time, serves with Gunicorn).

1. Push this repo to GitHub (already done if you are reading this there).
2. In Render: **New + → Blueprint** → connect the GitHub repo → pick the branch to deploy → **Apply**.
   (Or **New + → Web Service → Docker**, health check path `/health`.)
3. Wait for the build (~5 min on first deploy). Your site is live at `https://<service-name>.onrender.com`.

Notes for the free plan: the service sleeps after ~15 min idle (first request after that takes ~30-60 s), and there is 512 MB RAM. The app is configured for it (1 Gunicorn worker + 4 threads, ~180 MB resident).

## Training on your own data

```bash
python -m resume_screening.train --csv resumes.csv --text-col text --label-col role
```

Labels must be role ids or titles from `resume_screening/catalog.py`; add or edit roles there to change the role set. Skill vocabulary lives in `resume_screening/skills.py`.

## Important limitations (please read)

* **The shipped model is trained on synthetic resumes.** Real resume corpora are personal data, so none is bundled. Synthetic data is much more regular than real resumes, so the ~99% hold-out accuracy shown on `/insights` is **not** a real-world accuracy estimate. As a sanity check the test-suite includes hand-written resumes that the generator never produced. For production use, retrain on your own labelled data.
* Skill/education/experience extraction is rule-based (regex + a 160-skill taxonomy), not a trained NER model, so unusual phrasing and skills outside the taxonomy are missed.
* Scanned / image-only PDFs have no text layer and are rejected (no OCR).
* Automated screening can encode bias. Use scores as a decision aid and keep a human in the loop; check local regulations on automated hiring tools.

## Project layout

```
app.py                     Flask app (pages + JSON API, security headers)
resume_screening/
  extractor.py             PDF / DOCX / DOC / TXT → text
  parser.py                sections, contact info, experience, education, JD parsing
  skills.py                skill taxonomy + extractor
  text_utils.py            normalisation (PII removal, skill canonicalisation)
  catalog.py               job roles
  dataset.py               synthetic training-data generator
  train.py                 TF-IDF + Naive Bayes + SVM training & evaluation
  engine.py                scoring / ranking / role recommendation
templates/ static/         UI (no build step, strict CSP)
samples/                   14 fictional demo resumes (PDF, DOCX, DOC, TXT)
tests/                     pytest suite
Dockerfile render.yaml     deployment
.github/workflows/ci.yml   tests + Docker build/health check
```
