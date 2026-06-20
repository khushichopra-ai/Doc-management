from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests
from django.conf import settings


@dataclass(slots=True)
class ChunkVector:
    id: str
    vector: list[float]
    payload: dict[str, Any]


class QdrantService:
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = base_url or f"http://{settings.QDRANT_HOST}:{settings.QDRANT_PORT}"

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def create_collection(self) -> None:
        response = requests.get(self._url(f"/collections/{settings.QDRANT_COLLECTION}"), timeout=10)
        if response.status_code == 200:
            vectors = response.json().get("result", {}).get("config", {}).get("params", {}).get("vectors", {})
            current_size = vectors.get("size") if isinstance(vectors, dict) else None
            if current_size == settings.EMBEDDING_DIM:
                return
            requests.delete(self._url(f"/collections/{settings.QDRANT_COLLECTION}"), timeout=10).raise_for_status()

        payload = {
            "vectors": {
                "size": settings.EMBEDDING_DIM,
                "distance": "Cosine",
            }
        }
        response = requests.put(
            self._url(f"/collections/{settings.QDRANT_COLLECTION}"),
            json=payload,
            timeout=10,
        )
        response.raise_for_status()

    def upsert_chunks(self, chunks: list[ChunkVector]) -> None:
        self.create_collection()
        points = [
            {"id": chunk.id, "vector": chunk.vector, "payload": chunk.payload}
            for chunk in chunks
        ]
        response = requests.put(
            self._url(f"/collections/{settings.QDRANT_COLLECTION}/points?wait=true"),
            json={"points": points},
            timeout=30,
        )
        response.raise_for_status()

    def search(
        self,
        query_vector: list[float],
        *,
        limit: int = 10,
        qdrant_filter: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        self.create_collection()
        body: dict[str, Any] = {
            "vector": query_vector,
            "limit": limit,
            "with_payload": True,
            "with_vector": False,
        }
        if qdrant_filter:
            body["filter"] = qdrant_filter
        response = requests.post(
            self._url(f"/collections/{settings.QDRANT_COLLECTION}/points/search"),
            json=body,
            timeout=30,
        )
        response.raise_for_status()
        return response.json().get("result", [])

    def delete_document(self, document_id: str) -> None:
        self.create_collection()
        body = {
            "filter": {
                "must": [
                    {"key": "doc_id", "match": {"value": document_id}},
                ]
            }
        }
        response = requests.post(
            self._url(f"/collections/{settings.QDRANT_COLLECTION}/points/delete?wait=true"),
            json=body,
            timeout=30,
        )
        response.raise_for_status()

    def delete_version(self, document_id: str, version: int) -> None:
        self.create_collection()
        body = {
            "filter": {
                "must": [
                    {"key": "doc_id", "match": {"value": document_id}},
                    {"key": "version", "match": {"value": version}},
                ]
            }
        }
        response = requests.post(
            self._url(f"/collections/{settings.QDRANT_COLLECTION}/points/delete?wait=true"),
            json=body,
            timeout=30,
        )
        response.raise_for_status()
