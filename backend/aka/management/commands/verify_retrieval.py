from __future__ import annotations

from django.core.management.base import BaseCommand

from aka.services.retrieval import RetrieverService


class Command(BaseCommand):
    help = "Verify retrieval returns chunks under RBAC filter."

    def handle(self, *args, **options):
        filter_data = {"scopes": [{"namespace": "sales", "allowed_sensitivity": ["open"]}], "extra_doc_ids": []}
        chunks = RetrieverService().retrieve("what is inside the sales docs?", filter_data)
        self.stdout.write(str(len(chunks)))

