from __future__ import annotations

from django.core.management.base import BaseCommand

from aka.ingestion.embeddings import EmbeddingService


class Command(BaseCommand):
    help = "Verify embeddings produce the expected vector shape."

    def handle(self, *args, **options):
        service = EmbeddingService()
        vector = service.embed_text("Embedding verification test.")
        self.stdout.write(str(len(vector)))
        if len(vector) != 768:
            raise SystemExit(1)

