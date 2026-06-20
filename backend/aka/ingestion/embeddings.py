from __future__ import annotations

import hashlib
import logging
from functools import lru_cache

from django.conf import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self, model_name: str | None = None) -> None:
        self.model_name = model_name or settings.EMBEDDING_MODEL

    @property
    def dimension(self) -> int:
        return settings.EMBEDDING_DIM

    def embed_text(self, text: str) -> list[float]:
        try:
            return self._sentence_transformer_embed(text)
        except Exception as exc:
            # The embedder MUST be identical at ingestion and query time, or
            # similarity scores become meaningless and retrieval silently breaks.
            # Only use the deterministic stub when explicitly opted in (tests/CI);
            # otherwise fail loudly rather than corrupt the index.
            if getattr(settings, "EMBEDDINGS_ALLOW_FALLBACK", False):
                logger.warning("SentenceTransformers unavailable; using deterministic fallback: %s", exc)
                return self._fallback_embed(text)
            logger.error("Embedding model unavailable and fallback disabled: %s", exc)
            raise

    def _sentence_transformer_embed(self, text: str) -> list[float]:
        from sentence_transformers import SentenceTransformer  # type: ignore

        model = self._load_model(self.model_name)
        vector = model.encode(text, normalize_embeddings=True)
        values = [float(value) for value in vector.tolist()]
        if len(values) != self.dimension:
            raise ValueError(f"Expected vector dimension {self.dimension}, got {len(values)}")
        return values

    @lru_cache(maxsize=1)
    def _load_model(self, model_name: str):  # type: ignore[no-untyped-def]
        from sentence_transformers import SentenceTransformer  # type: ignore

        return SentenceTransformer(model_name)

    def _fallback_embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimension
        tokens = text.split()
        for index, token in enumerate(tokens):
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            for offset in range(0, 32, 4):
                bucket = (int.from_bytes(digest[offset : offset + 4], "big") + index + offset) % self.dimension
                vector[bucket] += 1.0
        norm = sum(value * value for value in vector) ** 0.5 or 1.0
        return [value / norm for value in vector]

