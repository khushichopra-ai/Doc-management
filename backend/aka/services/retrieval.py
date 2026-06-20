from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aka.ingestion.embeddings import EmbeddingService
from aka.qdrant.service import QdrantService


@dataclass(slots=True)
class RetrievedChunk:
    doc_id: str
    doc_name: str
    chunk_id: str
    namespace: str
    sensitivity: str
    uploader: str
    timestamp: str
    score: float
    text: str | None = None


class RetrieverService:
    def __init__(self, embedding_service: EmbeddingService | None = None, qdrant_service: QdrantService | None = None) -> None:
        self.embedding_service = embedding_service or EmbeddingService()
        self.qdrant_service = qdrant_service or QdrantService()

    def _build_qdrant_filter(self, aka_filter: dict[str, Any]) -> dict[str, Any]:
        scopes = aka_filter.get("scopes", [])
        extra_doc_ids = aka_filter.get("extra_doc_ids", [])

        # One OR-clause per department scope, each gated by that department's own
        # sensitivity levels — so a user's ceiling never crosses departments.
        should: list[dict[str, Any]] = []
        for scope in scopes:
            should.append(
                {
                    "must": [
                        {"key": "namespace", "match": {"any": [scope.get("namespace")]}},
                        {"key": "sensitivity", "match": {"any": scope.get("allowed_sensitivity", [])}},
                    ]
                }
            )
        if extra_doc_ids:
            should.append({"must": [{"key": "doc_id", "match": {"any": extra_doc_ids}}]})

        # No scopes and no grants => match nothing (empty `any` matches nothing),
        # never fall through to an unconstrained search.
        if not should:
            should.append({"must": [{"key": "doc_id", "match": {"any": []}}]})

        return {"should": should, "must_not": []}

    def retrieve(self, question: str, aka_filter: dict[str, list[str]]) -> list[RetrievedChunk]:
        query_vector = self.embedding_service.embed_text(question)
        results = self.qdrant_service.search(
            query_vector,
            limit=10,
            qdrant_filter=self._build_qdrant_filter(aka_filter),
        )
        chunks: list[RetrievedChunk] = []
        for result in results:
            payload = result.get("payload", {})
            chunks.append(
                RetrievedChunk(
                    doc_id=str(payload.get("doc_id", "")),
                    doc_name=str(payload.get("doc_name", "")),
                    chunk_id=str(payload.get("chunk_id", "")),
                    namespace=str(payload.get("namespace", "")),
                    sensitivity=str(payload.get("sensitivity", "")),
                    uploader=str(payload.get("uploader", "")),
                    timestamp=str(payload.get("timestamp", "")),
                    score=float(result.get("score", 0.0)),
                    text=payload.get("text"),
                )
            )
        return chunks

