# ============================================================
# AKA (Antier Knowledge Assistant) — single all-in-one image.
# One image runs BOTH the React SPA (served by nginx) and the Django API,
# managed together by supervisord. Qdrant runs as its official image
# alongside (see docker-compose.yml).
#
#   Build context: repository root
#   Build + run:   docker compose up --build
# ============================================================

# ---- Stage 1: build the React frontend ----
FROM node:20-alpine AS frontend
WORKDIR /fe
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build           # -> /fe/dist

# ---- Stage 2: Django API + nginx (serves the built SPA) ----
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/opt/hf-cache \
    SENTENCE_TRANSFORMERS_HOME=/opt/hf-cache \
    # Sensible defaults (overridden by docker-compose env / .env).
    QDRANT_HOST=qdrant \
    QDRANT_PORT=6333 \
    QDRANT_COLLECTION=aka_knowledge \
    EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2 \
    EMBEDDING_DIM=768 \
    DJANGO_DEBUG=True \
    DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,app \
    GEMINI_MODEL=gemini-2.5-flash

WORKDIR /app

# nginx (serve SPA + reverse proxy), supervisor (run both processes), curl (healthcheck).
RUN apt-get update \
 && apt-get install -y --no-install-recommends nginx supervisor curl \
 && rm -rf /var/lib/apt/lists/*

# Python deps: CPU-only torch FIRST (avoids the multi-GB CUDA wheels), then the rest.
COPY backend/requirements.txt ./
RUN pip install --upgrade pip \
 && pip install "torch>=2.0,<3.0" --index-url https://download.pytorch.org/whl/cpu \
 && pip install -r requirements.txt

# Pre-bake the embedding model so the container runs with no network at runtime.
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-mpnet-base-v2')"

# Backend code + built frontend + process configs.
COPY backend/ /app/
COPY --from=frontend /fe/dist /var/www/aka
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY docker/supervisord.conf /etc/supervisor/supervisord.conf
COPY docker/start-backend.sh /usr/local/bin/start-backend.sh
RUN chmod +x /usr/local/bin/start-backend.sh \
 && rm -f /etc/nginx/sites-enabled/default

EXPOSE 80 8000
CMD ["supervisord", "-c", "/etc/supervisor/supervisord.conf"]
