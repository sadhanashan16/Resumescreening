# ResumeIQ: AI Resume Screening & Shortlisting Platform

A multi-user web application for recruiters, HR teams and hiring managers. Create an account, upload resumes (PDF / DOC / DOCX / TXT), paste a job description, and a machine-learning pipeline ranks every candidate, explains the score, and lets you shortlist and manage the people you want to move forward with.

**Stack:** Python · Flask · scikit-learn (TF-IDF, Multinomial Naive Bayes, linear SVM) · SQLAlchemy + Alembic · PostgreSQL (SQLite for local development) · Flask-Login / Flask-WTF · Gunicorn · Docker · Render

## The workflow

```
create account → log in → upload resumes + job description → AI screening → review ranked results
      → shortlist / reject / add notes → manage the shortlist (filter, export CSV) → log out
```

| Area | What you get |
|---|---|
| **Accounts** | Sign up, log in, log out, "keep me signed in", change password (signs out other devices), delete account and all data. Passwords are hashed (scrypt); sessions are signed, `HttpOnly`, `SameSite=Lax` and `Secure` in production; CSRF protection on every form and API call; login rate limiting and temporary account lockout. |
| **Dashboard** | Totals (screenings, candidates, shortlisted, average score), pipeline and match-quality charts, recent screenings, latest shortlisted candidates, and a getting-started guide for new users. |
| **New screening** | Job description (or one of 12 example roles) plus many resumes, with drag-and-drop, per-file error reporting and a "try with sample resumes" option. Results are saved to your account. |
| **Results** | Table and card views; search (name, skill, e-mail, role); filter by match quality and status; sort by score, AI rank, name, experience; per-candidate drawer with score breakdown, matched / related / missing skills and Naive Bayes / SVM predictions; notes. |
| **Shortlist management** | Shortlist / reject / reset one candidate or many (bulk select), "shortlist the AI's top N", a shortlist page across all screenings, notes, CSV export. |
| **Job match** | Upload one resume and see which of 12 roles fits best and which skills to learn. |
| **Model insights** | Training data, hold-out and cross-validated metrics, confusion matrix. |

**Every score, grade, skill list and recommendation comes from the ML pipeline in `resume_screening/` and is stored unchanged.** The web layer only stores and displays it (`tests/test_screenings.py::test_stored_results_are_exactly_the_ml_engine_output` asserts this).

## How the machine learning works

```
resume file ─► text extraction ─► NLP parsing ─► normalisation ─► TF-IDF (1-2 grams)
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

Grades: ≥70 strong · ≥50 good · ≥30 partial · otherwise weak. Names, e-mails, phone numbers and links are removed before scoring.

## Project layout

```
app.py                      Application factory (`create_app`) + WSGI entry point (`gunicorn app:app`)
webapp/                     Accounts, persistence, pages and API
  settings.py               Environment-driven configuration (no secrets in the repo)
  models.py                 User, Screening, Candidate (SQLAlchemy)
  auth.py  forms.py         Sign up / log in / log out / account, validation
  views.py                  Server-rendered pages (dashboard, screenings, shortlist, tools)
  api.py                    JSON API: screen, list, filter, shortlist, export
  errors.py extensions.py   Error handling, Flask extensions
resume_screening/           ML pipeline (extraction, parsing, TF-IDF, NB, SVM, scoring), unchanged by the web layer
migrations/                 Alembic migrations (`flask --app app db upgrade`)
templates/ static/          UI (no build step, strict Content-Security-Policy)
samples/                    14 fictional demo resumes (PDF, DOCX, DOC, TXT)
tests/                      pytest suite (SQLite and PostgreSQL)
Dockerfile start.sh         Container: trains the model at build time; start.sh migrates then serves
render.yaml                 Render Blueprint: web service + PostgreSQL
.env.example                Every environment variable, documented
.github/workflows/ci.yml    Tests on SQLite + PostgreSQL, Docker build and boot check
```

## Run locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env                       # edit SECRET_KEY (see below); leave DATABASE_URL empty for SQLite
python -m resume_screening.train           # trains the models (~10 s) -> models/
flask --app app db upgrade                 # creates the database tables
python app.py                              # http://localhost:5000
pytest -q                                  # 78 tests
```

Generate a secret key with `python -c "import secrets; print(secrets.token_hex(32))"`.
For `.doc` (Word 97-2003) files install `antiword` (`apt install antiword`); without it a best-effort fallback reader is used.

## Configuration (environment variables)

Nothing secret is stored in the repository. See [`.env.example`](.env.example) for the annotated list.

| Variable | Required | Purpose |
|---|---|---|
| `SECRET_KEY` | **production** | Signs sessions and CSRF tokens. The app refuses to start in production without it. On Render the blueprint generates one. |
| `DATABASE_URL` | **production** | PostgreSQL URL (`postgres://` and `postgresql://` both work). Empty → SQLite file in `instance/` (development only). |
| `APP_ENV` | no | `production` enables secure cookies, HSTS and proxy-header trust. Render also sets `RENDER=true`, which implies it. |
| `REQUIRE_PERSISTENT_DB` | no | In production, refuse to start without `DATABASE_URL` (set by `render.yaml`). |
| `ALLOW_SIGNUP` | no | `false` closes registration (e.g. once your team has accounts). |
| `MAX_FAILED_LOGINS`, `LOCKOUT_MINUTES` | no | Account lockout (default 5 failures → 15 minutes). |
| `SESSION_HOURS`, `REMEMBER_DAYS` | no | Session lifetime (12 h) and "keep me signed in" duration (14 d). |
| `SESSION_COOKIE_SECURE`, `TRUST_PROXY` | no | Default to true in production. |
| `RATELIMIT_STORAGE_URI` | no | `memory://` by default; use `redis://…` if you run more than one worker. |
| `MAX_FILES`, `MAX_FILE_BYTES` | no | Upload limits (30 files, 5 MB each). |
| `MODEL_DIR`, `APP_DATA_DIR`, `LOG_LEVEL`, `PORT` | no | Model location, SQLite directory, logging, port. |

## Deploy to Render

The repo contains a [Render Blueprint](render.yaml) (web service from the `Dockerfile` **and** a PostgreSQL database, wired together) plus `start.sh`, which applies database migrations and then starts Gunicorn.

### Option A: new deployment (Blueprint)
1. Push/merge this code to the branch Render should deploy.
2. In Render: **New + → Blueprint**, connect the GitHub repo, choose the branch, **Apply**.
3. Render creates the `resumeiq-db` database, generates `SECRET_KEY`, injects `DATABASE_URL`, builds the image (which trains the model) and starts the service. The first build takes ~5 minutes. Your site is at `https://<service-name>.onrender.com`; open it and **Sign up**.

### Option B: you already have a Render web service for this repo
1. **New + → PostgreSQL** (same region as the web service). Copy its **Internal Database URL**.
2. Web service → **Environment**, add:
   - `DATABASE_URL` = the internal URL
   - `SECRET_KEY` = a long random value (e.g. from the command above)
   - `APP_ENV` = `production`, and optionally `REQUIRE_PERSISTENT_DB` = `true`
3. Set the **Health Check Path** to `/health`, then **Manual Deploy → Deploy latest commit**. The container migrates the database automatically on start.

### Things to know about Render
* **Free PostgreSQL databases expire after about 30 days** (Render deletes them). For a permanent site choose a paid plan: change `plan: free` under `databases` in `render.yaml` (or pick a paid instance in the dashboard).
* The free web service sleeps after ~15 minutes idle (first request afterwards takes 30-60 s) and has 512 MB RAM. The app is configured for it: one Gunicorn worker with four threads, ~190 MB resident.
* Without `DATABASE_URL` the app falls back to a SQLite file inside the container, which **Render wipes on every deploy**. A warning is logged, `/health` reports `"persistent_database": false`, and `REQUIRE_PERSISTENT_DB=true` turns the situation into a startup error.
* `/health` returns 503 if the database is unreachable.

## Database and migrations

Schema changes are managed with Alembic (via Flask-Migrate); the initial migration is `migrations/versions/0001_initial_schema.py`.

```bash
flask --app app db upgrade                         # apply migrations (start.sh does this on every deploy)
flask --app app db migrate -m "describe change"    # create a migration after editing webapp/models.py
flask --app app db downgrade                       # roll back one revision
```

Tables: `users`, `screenings` (one per screening run: job title, description, extracted job requirements) and `candidates` (extracted details, scores, status, notes). **Resume files are never stored**: only what the ML pipeline extracted from them and the scores it produced. Deleting a screening or an account cascades to its candidates.

## Security design

* Passwords: scrypt hashes (Werkzeug), policy of ≥ 8 characters with a letter and a number, a common-password blocklist.
* Sessions: signed cookies, `HttpOnly`, `SameSite=Lax`, `Secure` in production; changing the password rotates a per-user token that signs out every other device.
* CSRF: Flask-WTF tokens on all forms; the JavaScript sends `X-CSRFToken` on every API write. `Referrer-Policy: same-origin` is required for the HTTPS referer check.
* Brute force: per-IP rate limits on login (15/min), sign-up (30/h) and password changes, plus account lockout. Wrong e-mail and wrong password are indistinguishable (message and timing).
* Data isolation: every query is scoped to the logged-in user; other users' ids answer 404.
* Uploads: extension and content-signature checks, size and count limits, in-memory processing.
* Browser: strict CSP (no inline scripts or styles), `X-Frame-Options: DENY`, `nosniff`, HSTS in production, `no-store` on all non-static responses; CSV exports neutralise spreadsheet formulas; open redirects after login are blocked.

## API

All routes require a logged-in session and (for writes) the CSRF header; errors are JSON `{"error": "..."}`.

| Method | Route | Purpose |
|---|---|---|
| POST | `/api/screen` | Run the ML screening on uploaded resumes + job description; saves and returns the screening |
| GET | `/api/screenings`, `/api/screenings/<id>` | List / fetch screenings (with candidates) |
| DELETE | `/api/screenings/<id>` | Delete a screening and its candidates |
| GET | `/api/candidates` | Filter/sort/search/paginate (`status`, `screening_id`, `grade`, `q`, `sort`, `order`, `page`, `per_page`) with per-status counts |
| GET / PATCH / DELETE | `/api/candidates/<id>` | Fetch; set `status` (`pending`/`shortlisted`/`rejected`) and `notes`; delete |
| POST | `/api/candidates/bulk` | Set status for `ids`, or for a `screening_id` with `scope` `recommended` / `all` |
| GET | `/api/candidates/export.csv`, `/api/screenings/<id>/export.csv` | CSV export honouring the same filters |
| POST | `/api/match` | Job-role recommendations for one resume |
| GET | `/api/roles`, `/api/samples`, `/api/model`, `/health` | Example job descriptions, sample resumes, training metrics, health check (public) |

## Training on your own data

```bash
python -m resume_screening.train --csv resumes.csv --text-col text --label-col role
```

Labels must be role ids or titles from `resume_screening/catalog.py`; edit that file to change the role set. The skill vocabulary lives in `resume_screening/skills.py`.

## Testing

```bash
pytest -q                                                       # SQLite (in memory)
TEST_DATABASE_URL=postgresql+psycopg2://user:pw@localhost/resumeiq_test pytest -q   # PostgreSQL (database is dropped and recreated!)
```

The suite covers authentication (validation, lockout, CSRF, rate limits, session rotation, safe redirects), data isolation between users, the screening/shortlist API, CSV export, migrations vs. models, configuration, and the ML pipeline. CI runs it on SQLite and PostgreSQL and boots the Docker image against a throwaway database.

## Limitations (please read)

* **The shipped model is trained on synthetic resumes.** Real resume corpora are personal data, so none is bundled; the ~99% hold-out accuracy on `/insights` is **not** a real-world accuracy estimate. Retrain on your own labelled data for production decisions.
* Skill / education / experience extraction is rule-based (regex + a 164-skill taxonomy), not a trained NER model; scanned or image-only PDFs have no text layer and are rejected (no OCR).
* **Automated screening can encode bias.** Scores are a decision aid; keep a human in the loop and check local regulations on automated hiring tools.
* There is **no e-mail based password reset** (it needs an SMTP provider; users can change their password while logged in). Sign-up reveals whether an e-mail is already registered. Rate limits are in memory, so they are per process (fine for the single-worker deployment; use `RATELIMIT_STORAGE_URI=redis://…` before scaling out).
* There are no organisations or roles: every account is an independent workspace.
