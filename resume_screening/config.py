"""Central configuration (overridable through environment variables)."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = Path(os.environ.get("MODEL_DIR", BASE_DIR / "models"))
SAMPLES_DIR = BASE_DIR / "samples"
MODEL_PATH = MODEL_DIR / "model.joblib"
METRICS_PATH = MODEL_DIR / "metrics.json"

ALLOWED_EXTENSIONS = {"pdf", "doc", "docx", "txt"}
MAX_FILES = int(os.environ.get("MAX_FILES", 30))
MAX_FILE_BYTES = int(os.environ.get("MAX_FILE_BYTES", 5 * 1024 * 1024))
MAX_REQUEST_BYTES = MAX_FILES * MAX_FILE_BYTES + 1024 * 1024
MAX_JD_CHARS = 20_000

RANDOM_STATE = 42

# Resume <-> job description scoring weights. Components that cannot be
# computed (e.g. the JD states no experience requirement) are dropped and the
# remaining weights are re-normalised.
SCORE_WEIGHTS = {
    "text_similarity": 0.40,   # TF-IDF cosine similarity
    "skills": 0.30,            # share of the JD's skills the resume covers
    "role_fit": 0.15,          # NB + SVM role agreement with the JD (neighbouring roles earn partial credit)
    "experience": 0.10,
    "education": 0.05,
}
# TF-IDF cosine similarity between a resume and a JD rarely exceeds ~0.5, so it
# is rescaled against this ceiling to land on a 0-1 scale.
SIMILARITY_CEILING = 0.45

# Resume <-> job-role recommendation weights.
ROLE_WEIGHTS = {"text_similarity": 0.30, "skills": 0.35, "classifier": 0.35}
