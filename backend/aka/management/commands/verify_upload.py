from __future__ import annotations

from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from aka.services.documents import DocumentService


class Command(BaseCommand):
    help = "Verify document upload end to end."

    def handle(self, *args, **options):
        User = get_user_model()
        user = User.objects.get(username="alice")
        upload = SimpleUploadedFile("verify.txt", b"upload verification test content")
        result = DocumentService().upload(uploaded_file=upload, department_slug="ai-team", sensitivity="internal", user=user)
        self.stdout.write(f"{result.document.id} {result.chunk_count}")
