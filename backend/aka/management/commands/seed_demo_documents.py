from __future__ import annotations

import uuid

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from aka.ingestion.chunker import ChunkingService
from aka.ingestion.embeddings import EmbeddingService
from aka.models import Department, Document
from aka.qdrant.service import ChunkVector, QdrantService


DEMO_DOCS = [
    {
        "name": "healthaera_architecture.txt",
        "department_slug": "ai-team",
        "uploader": "alice",
        "sensitivity": "internal",
        "text": (
            "HealthAera technical architecture used a retrieval-first monolith with Django, Qdrant, "
            "and a governed RBAC layer. We chose all-mpnet-base-v2 because it produced stable semantic "
            "retrieval for internal documents and aligned well with our chunk-based search design. "
            "The system filters by department and sensitivity before search, ensuring unauthorized chunks never reach the model."
        ),
    },
    {
        "name": "agent_architecture_notes.txt",
        "department_slug": "ai-team",
        "uploader": "alice",
        "sensitivity": "internal",
        "text": (
            "During the agent architecture phase, the main design decisions were to keep the application monolithic, "
            "enforce RBAC at the backend, store knowledge in one Qdrant collection, and use document-level metadata "
            "to govern access. We also chose a service layer pattern so business logic stays out of views."
        ),
    },
    {
        "name": "healthaera_outcome_summary.txt",
        "department_slug": "ai-team",
        "uploader": "alice",
        "sensitivity": "open",
        "text": (
            "The HealthAera project outcome was a successful internal knowledge pilot that reduced search time, "
            "improved document reuse, and gave the team a governed way to find architecture decisions with sources attached."
        ),
    },
    {
        "name": "ai_healthcare_case_study.txt",
        "department_slug": "ai-showcases",
        "uploader": "alice",
        "sensitivity": "open",
        "text": (
            "Antier built AI assistants for healthcare clients and the results were strong: faster information retrieval, "
            "better document discovery, and clearer handoff between teams. The case study shows practical gains in response time "
            "and team productivity."
        ),
    },
    {
        "name": "rag_capabilities_deck.txt",
        "department_slug": "ai-showcases",
        "uploader": "alice",
        "sensitivity": "open",
        "text": (
            "Antier's RAG capabilities include document ingestion, role-based filtering, chunked retrieval, grounded answers, "
            "and governed access requests. The team can search internal knowledge, cite sources, and prevent unauthorized retrieval."
        ),
    },
    {
        "name": "sales_capability_deck.txt",
        "department_slug": "sales",
        "uploader": "bob",
        "sensitivity": "open",
        "text": (
            "Antier's sales capability deck summarizes our offerings across blockchain, AI, and enterprise software delivery. "
            "We highlight proven delivery, dedicated teams, and a consultative engagement model that helps clients scope and ship quickly."
        ),
    },
    {
        "name": "sales_past_wins.txt",
        "department_slug": "sales",
        "uploader": "bob",
        "sensitivity": "open",
        "text": (
            "Recent sales wins include multi-quarter engagements in fintech and healthcare. The past wins summary shows strong "
            "renewal rates, expanding scope with existing clients, and successful handoffs from proposal to delivery."
        ),
    },
    {
        "name": "sales_pricing_guidelines.txt",
        "department_slug": "sales",
        "uploader": "bob",
        "sensitivity": "restricted",
        "text": (
            "Antier pricing guidelines. The standard blended engineering day rate is 850 USD. "
            "Volume discounts apply at 10 percent for engagements above 20 resources and 15 percent above 50 resources. "
            "Discount approval authority for anything beyond 15 percent sits with the Sales lead. "
            "Annual retainer contracts receive a further 5 percent loyalty adjustment."
        ),
    },
    {
        "name": "cefi_capabilities.txt",
        "department_slug": "cefi",
        "uploader": "alice",
        "sensitivity": "open",
        "text": (
            "Antier's CeFi (Centralized Finance) capabilities cover centralized crypto exchange platforms, custodial wallet "
            "and custody solutions, KYC and AML compliance workflows, fiat on-ramp and off-ramp integration, and order-matching "
            "engines. The team builds regulated, high-throughput trading systems for centralized finance clients."
        ),
    },
    {
        "name": "defi_capabilities.txt",
        "department_slug": "defi",
        "uploader": "alice",
        "sensitivity": "open",
        "text": (
            "Antier's DeFi (Decentralized Finance) capabilities include automated market maker (AMM) and DEX development, "
            "liquidity pools, yield farming and staking protocols, lending and borrowing platforms, and smart contract security "
            "audits. The team delivers decentralized, non-custodial financial protocols on multiple chains."
        ),
    },
]


class Command(BaseCommand):
    help = "Seed a demo knowledge corpus for the acceptance scenarios."

    def handle(self, *args, **options):
        User = get_user_model()
        chunking = ChunkingService()
        embedder = EmbeddingService()
        qdrant = QdrantService()
        qdrant.create_collection()

        for demo_doc in DEMO_DOCS:
            department = Department.objects.get(slug=demo_doc["department_slug"])
            uploader = User.objects.get(username=demo_doc["uploader"])
            document, created = Document.objects.get_or_create(
                name=demo_doc["name"],
                department=department,
                defaults={
                    "uploader": uploader,
                    "sensitivity": demo_doc["sensitivity"],
                    "version": 1,
                    "status": Document.Status.ACTIVE,
                    "file_size": len(demo_doc["text"].encode("utf-8")),
                    "mime_type": "text/plain",
                    "chunk_count": 0,
                },
            )
            if not created:
                continue
            chunks = chunking.split(demo_doc["text"])
            vectors = []
            for chunk in chunks:
                vectors.append(
                    ChunkVector(
                        id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"{document.id}:{chunk.chunk_id}")),
                        vector=embedder.embed_text(chunk.text),
                        payload={
                            "namespace": department.slug,
                            "doc_id": str(document.id),
                            "doc_name": document.name,
                            "chunk_id": chunk.chunk_id,
                            "version": document.version,
                            "sensitivity": document.sensitivity,
                            "uploader": str(uploader.id),
                            "timestamp": timezone.now().isoformat(),
                            "text": chunk.text,
                        },
                    )
                )
            qdrant.upsert_chunks(vectors)
            document.chunk_count = len(chunks)
            document.save(update_fields=["chunk_count", "updated_at"])

        self.stdout.write(self.style.SUCCESS("Seeded demo documents."))
