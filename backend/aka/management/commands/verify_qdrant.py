from __future__ import annotations

import uuid

from django.core.management.base import BaseCommand

from aka.qdrant.service import ChunkVector, QdrantService


class Command(BaseCommand):
    help = "Create the Qdrant collection, insert test vectors, and retrieve them."

    def handle(self, *args, **options):
        service = QdrantService()
        service.create_collection()

        point_a = ChunkVector(
            id=str(uuid.uuid4()),
            vector=[1.0] + [0.0] * 1023,
            payload={
                "namespace": "ai-team",
                "doc_id": "doc-1",
                "doc_name": "Test Document",
                "chunk_id": "chunk-1",
                "version": 1,
                "sensitivity": "open",
                "uploader": "alice",
                "timestamp": "2026-06-18T00:00:00Z",
            },
        )
        point_b = ChunkVector(
            id=str(uuid.uuid4()),
            vector=[0.0, 1.0] + [0.0] * 1022,
            payload={
                "namespace": "sales",
                "doc_id": "doc-2",
                "doc_name": "Sales Notes",
                "chunk_id": "chunk-1",
                "version": 1,
                "sensitivity": "internal",
                "uploader": "bob",
                "timestamp": "2026-06-18T00:00:00Z",
            },
        )

        service.upsert_chunks([point_a, point_b])
        results = service.search([1.0] + [0.0] * 1023, limit=2)

        self.stdout.write(self.style.SUCCESS("Collection ready."))
        self.stdout.write(f"Retrieved {len(results)} vectors.")
        for result in results:
            payload = result.get("payload", {})
            self.stdout.write(
                f"- {payload.get('doc_name')} ({payload.get('doc_id')}) score={result.get('score')}"
            )
