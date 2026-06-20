#!/bin/sh
# Django API startup: wait for Qdrant, migrate, seed, then serve.
set -e
cd /app

QDRANT_HOST="${QDRANT_HOST:-qdrant}"
QDRANT_PORT="${QDRANT_PORT:-6333}"
QDRANT_COLLECTION="${QDRANT_COLLECTION:-aka_knowledge}"

echo "[backend] waiting for Qdrant at ${QDRANT_HOST}:${QDRANT_PORT} ..."
until curl -sf "http://${QDRANT_HOST}:${QDRANT_PORT}/healthz" >/dev/null 2>&1; do
  sleep 1
done
echo "[backend] Qdrant is ready."

# On a fresh DB, also clear any stale Qdrant collection so SQL metadata and
# the vector store never drift out of sync.
FRESH_DB=0
[ ! -f db.sqlite3 ] && FRESH_DB=1

python manage.py migrate --noinput

if [ "$FRESH_DB" = "1" ]; then
  echo "[backend] fresh database — clearing stale Qdrant collection (if any)."
  curl -s -X DELETE "http://${QDRANT_HOST}:${QDRANT_PORT}/collections/${QDRANT_COLLECTION}" >/dev/null 2>&1 || true
fi

echo "[backend] seeding RBAC users, departments and demo documents ..."
python manage.py seed_data
python manage.py seed_demo_documents

echo "[backend] starting Django on 0.0.0.0:8000"
exec python manage.py runserver --noreload 0.0.0.0:8000
