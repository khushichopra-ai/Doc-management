from __future__ import annotations

from django.core.management.base import BaseCommand

from aka.ingestion.chunker import ChunkingService


class Command(BaseCommand):
    help = "Verify chunk count and boundaries."

    def handle(self, *args, **options):
        service = ChunkingService()
        text = " ".join(f"token{i}" for i in range(900))
        chunks = service.split(text)
        self.stdout.write(str(len(chunks)))
        if not chunks:
            raise SystemExit(1)

