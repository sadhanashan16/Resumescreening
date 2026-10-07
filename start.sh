#!/bin/sh
# Container entrypoint: apply database migrations, then serve the app.
set -eu

# Configuration mistakes (missing SECRET_KEY, ...) cannot be fixed by retrying: fail immediately and clearly.
python -c "from webapp.settings import build_config; build_config()" || exit 1

echo "Applying database migrations..."
attempt=1
until flask --app app db upgrade; do
  if [ "$attempt" -ge 10 ]; then
    echo "Database migration failed after $attempt attempts; giving up." >&2
    exit 1
  fi
  echo "Database not ready (attempt $attempt/10); retrying in 3s..." >&2
  attempt=$((attempt + 1))
  sleep 3
done

# One worker: the ML model is held in memory (fits Render's 512 MB free tier); threads handle concurrency.
exec gunicorn app:app --bind "0.0.0.0:${PORT:-10000}" --workers 1 --threads 4 --timeout 120 --access-logfile -
