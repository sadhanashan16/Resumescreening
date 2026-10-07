FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# antiword extracts text from legacy .doc resumes
RUN apt-get update \
 && apt-get install -y --no-install-recommends antiword \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
# Train the models at build time so the container starts instantly and the
# deployed model is reproducible (deterministic seed).
RUN python -m resume_screening.train

RUN useradd --create-home appuser && chown -R appuser /app && chmod +x /app/start.sh
USER appuser

# Render injects $PORT, SECRET_KEY and DATABASE_URL (see render.yaml). start.sh runs migrations, then gunicorn.
CMD ["./start.sh"]
