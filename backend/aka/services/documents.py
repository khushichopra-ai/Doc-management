from __future__ import annotations

import logging
import mimetypes
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from django.db import transaction

from aka.ingestion.chunker import Chunk, ChunkingService
from aka.ingestion.embeddings import EmbeddingService
from aka.ingestion.parser import DocumentParser
from aka.models import Department, Document, User
from aka.qdrant.service import ChunkVector, QdrantService

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {"pdf", "docx", "xlsx", "pptx", "txt"}
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024


@dataclass(slots=True)
class UploadResult:
    document: Document
    chunk_count: int


class DocumentService:
    def __init__(
        self,
        *,
        parser: DocumentParser | None = None,
        chunking_service: ChunkingService | None = None,
        embedding_service: EmbeddingService | None = None,
        qdrant_service: QdrantService | None = None,
    ) -> None:
        self.parser = parser or DocumentParser()
        self.chunking_service = chunking_service or ChunkingService()
        self.embedding_service = embedding_service or EmbeddingService()
        self.qdrant_service = qdrant_service or QdrantService()

    def validate(self, uploaded_file) -> None:
        extension = Path(uploaded_file.name).suffix.lower().lstrip(".")
        if extension not in ALLOWED_EXTENSIONS:
            raise ValueError("Unsupported file type.")
        if uploaded_file.size > MAX_FILE_SIZE_BYTES:
            raise ValueError("File size must be under 50MB.")
        logger.info("Antivirus skipped for POC upload: %s", uploaded_file.name)

    def _read_bytes(self, uploaded_file) -> bytes:
        uploaded_file.seek(0)
        return uploaded_file.read()

    def _resolve_department(self, department_slug: str) -> Department:
        return Department.objects.get(slug=department_slug)

    def _current_version(self, department: Department, name: str) -> int:
        latest = (
            Document.objects.filter(department=department, name=name)
            .order_by("-version", "-created_at")
            .first()
        )
        return 1 if latest is None else latest.version + 1

    def _supersede_previous_active(self, department: Department, name: str) -> str | None:
        """Mark the current active version superseded (DB only). Returns its id so
        the caller can purge its Qdrant chunks outside the write transaction."""
        previous = (
            Document.objects.filter(
                department=department,
                name=name,
                status=Document.Status.ACTIVE,
            )
            .order_by("-version", "-created_at")
            .first()
        )
        if previous is None:
            return None
        previous.status = Document.Status.SUPERSEDED
        previous.save(update_fields=["status", "updated_at"])
        return str(previous.id)

    def _build_vectors(
        self,
        *,
        doc_id: uuid.UUID,
        namespace: str,
        doc_name: str,
        version: int,
        sensitivity: str,
        uploader_id: str,
        chunks: list[Chunk],
    ) -> list[ChunkVector]:
        timestamp = datetime.now(timezone.utc).isoformat()
        vectors: list[ChunkVector] = []
        for chunk in chunks:
            embedding = self.embedding_service.embed_text(chunk.text)
            vectors.append(
                ChunkVector(
                    id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"{doc_id}:{chunk.chunk_id}")),
                    vector=embedding,
                    payload={
                        "namespace": namespace,
                        "doc_id": str(doc_id),
                        "doc_name": doc_name,
                        "chunk_id": chunk.chunk_id,
                        "version": version,
                        "sensitivity": sensitivity,
                        "uploader": uploader_id,
                        "timestamp": timestamp,
                        "text": chunk.text,
                    },
                )
            )
        return vectors

    def upload(self, *, uploaded_file, department_slug: str, sensitivity: str, user: User) -> UploadResult:
        # Upload is governed by the account role (Lead/Contributor may upload to
        # any department); no per-department membership is required.
        if user.role not in {User.Role.LEAD, User.Role.CONTRIBUTOR}:
            raise PermissionError("Role does not allow upload.")

        self.validate(uploaded_file)
        department = self._resolve_department(department_slug)
        content = self._read_bytes(uploaded_file)
        parsed = self.parser.parse(uploaded_file.name, content)
        chunks = self.chunking_service.split(parsed.text)
        if not chunks:
            raise ValueError("No content found in uploaded file.")

        # Embed BEFORE opening the write transaction so the slow model call never
        # holds the SQLite write lock. The id is pre-generated to tie vectors to
        # the row that is about to be created.
        doc_id = uuid.uuid4()
        version = self._current_version(department, uploaded_file.name)
        vectors = self._build_vectors(
            doc_id=doc_id,
            namespace=department.slug,
            doc_name=uploaded_file.name,
            version=version,
            sensitivity=sensitivity,
            uploader_id=str(user.id),
            chunks=chunks,
        )

        # Short write transaction: supersede + create only (no network / no embedding).
        with transaction.atomic():
            superseded_id = self._supersede_previous_active(department, uploaded_file.name)
            document = Document.objects.create(
                id=doc_id,
                name=uploaded_file.name,
                department=department,
                uploader=user,
                sensitivity=sensitivity,
                version=version,
                status=Document.Status.ACTIVE,
                file_size=uploaded_file.size,
                mime_type=mimetypes.guess_type(uploaded_file.name)[0] or "",
                chunk_count=len(chunks),
            )

        # Qdrant I/O happens outside the DB transaction (no lock during network calls).
        if superseded_id:
            self.qdrant_service.delete_document(superseded_id)
        self.qdrant_service.upsert_chunks(vectors)
        return UploadResult(document=document, chunk_count=len(chunks))

    def delete_document(self, document: Document) -> None:
        # DB write and Qdrant purge are kept out of a single long transaction so
        # the network call never holds the SQLite write lock.
        document.status = Document.Status.DELETED
        document.save(update_fields=["status", "updated_at"])
        self.qdrant_service.delete_document(str(document.id))
