"""
Django settings for the AKA (Antier Knowledge Assistant) project.

Phase 0: project skeleton only. Environment-driven configuration is loaded
from the repository-root .env file via python-dotenv.
"""
from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

# backend/config/settings.py -> BASE_DIR = backend/
BASE_DIR = Path(__file__).resolve().parent.parent
# Repository root holds the shared .env and docker-compose.yml.
REPO_ROOT = BASE_DIR.parent

load_dotenv(REPO_ROOT / ".env")


def env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


def env_bool(key: str, default: bool = False) -> bool:
    return env(key, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def env_list(key: str, default: str = "") -> list[str]:
    return [item.strip() for item in env(key, default).split(",") if item.strip()]


# --- Core ---
SECRET_KEY = env("DJANGO_SECRET_KEY", "dev-insecure-change-me")
DEBUG = env_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")
if DEBUG and "testserver" not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append("testserver")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "corsheaders",
    "rest_framework_simplejwt",
    # Local
    "aka",
]

AUTH_USER_MODEL = "aka.User"

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# --- Database (SQLite, per spec) ---
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
        # Wait up to 30s for a write lock instead of failing instantly; WAL is
        # enabled per-connection in aka.apps so readers and the writer coexist.
        "OPTIONS": {"timeout": 30},
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- I18N ---
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# --- Static ---
STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "aka.authentication.jwt.CookieJWTAuthentication",
    ],
}

# Token lifetimes are kept in sync with the auth-cookie max-age (see api/auth.py)
# so a live cookie never carries an already-expired token.
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
}

# --- CORS (React dev server) ---
CORS_ALLOWED_ORIGINS = env_list("FRONTEND_ORIGIN", "http://localhost:5173")
CORS_ALLOW_CREDENTIALS = True

# --- Project-specific configuration (consumed in later phases) ---
QDRANT_HOST = env("QDRANT_HOST", "localhost")
QDRANT_PORT = int(env("QDRANT_PORT", "6333"))
QDRANT_COLLECTION = env("QDRANT_COLLECTION", "aka_knowledge")

# HuggingFace sentence-transformers embeddings (no external/cloud service).
EMBEDDING_MODEL = env("EMBEDDING_MODEL", "sentence-transformers/all-mpnet-base-v2")
EMBEDDING_DIM = int(env("EMBEDDING_DIM", "768"))
# Only allow the deterministic stub embedder when explicitly enabled (tests/CI).
# In normal operation a missing model must fail loudly, never silently corrupt
# the index with vectors incompatible with query-time embeddings.
EMBEDDINGS_ALLOW_FALLBACK = env_bool("EMBEDDINGS_ALLOW_FALLBACK", False)

# Minimum top-chunk cosine similarity for a question to be considered in-scope.
# Off-topic questions score well below this against the corpus, so they are
# answered with the standard "insufficient" response instead of reaching the LLM.
RETRIEVAL_MIN_SCORE = float(env("RETRIEVAL_MIN_SCORE", "0.25"))

GEMINI_API_KEY = env("GEMINI_API_KEY", "")
GEMINI_MODEL = env("GEMINI_MODEL", "gemini-1.5-flash")
