from __future__ import annotations

from dataclasses import dataclass

import google.generativeai as genai
from django.conf import settings

from aka.services.query_rewrite import QueryRewriteService
from aka.services.retrieval import RetrievedChunk, RetrieverService


INSUFFICIENT_ANSWER = "I do not have enough information to answer that question."


@dataclass(slots=True)
class RAGResult:
    answer: str
    sources: list[dict[str, str]]
    department: str


class RAGService:
    def __init__(
        self,
        *,
        retriever_service: RetrieverService | None = None,
        query_rewrite_service: QueryRewriteService | None = None,
    ) -> None:
        self.retriever_service = retriever_service or RetrieverService()
        self.query_rewrite_service = query_rewrite_service or QueryRewriteService()

    # Chunks passed to the LLM. Slightly wider than the spec's 5 so a single
    # relevant chunk in a small document isn't crowded out by large documents.
    CONTEXT_CHUNKS = 8

    def _prompt(self, question: str, chunks: list[RetrievedChunk]) -> str:
        context_lines = []
        for chunk in chunks:
            context_lines.append(f"[Source: {chunk.doc_name} | {chunk.sensitivity}]\n{chunk.text or ''}")
        return (
            "You are a knowledge assistant for Antier Solutions. Answer the user's question using ONLY the "
            "document excerpts provided below. You must NOT use any outside or general knowledge, even if you "
            "know the answer. If the answer is not explicitly contained in these excerpts — or the excerpts are "
            "unrelated to the question — you MUST respond with EXACTLY this sentence and nothing else: "
            f'"{INSUFFICIENT_ANSWER}"\n\n'
            f"Question: {question}\n\n"
            "Excerpts:\n"
            + "\n\n".join(context_lines)
        )

    def answer(self, *, question: str, aka_filter: dict[str, list[str]], department: str) -> RAGResult:
        # Scope retrieval to the selected department's namespace (the doc's
        # department-context model); document grants apply regardless of namespace.
        scopes = aka_filter.get("scopes", [])
        if department:
            scopes = [scope for scope in scopes if scope.get("namespace") == department]
        scoped_filter = {"scopes": scopes, "extra_doc_ids": aka_filter.get("extra_doc_ids", [])}

        # Relevance gate on the RAW question (an honest similarity signal — query
        # rewriting can inflate weak matches). If the best chunk is too weak, the
        # question is out of scope for the permitted documents, so answer
        # "insufficient" without consulting the LLM (prevents general-knowledge
        # answers like "name four colours" that aren't grounded in any document).
        gate_chunks = self.retriever_service.retrieve(question, scoped_filter)
        min_score = getattr(settings, "RETRIEVAL_MIN_SCORE", 0.25)
        if not gate_chunks or gate_chunks[0].score < min_score:
            return RAGResult(answer=INSUFFICIENT_ANSWER, sources=[], department=department)

        # In scope: merge the raw-question hits (already fetched for the gate) with
        # the rewritten-query hits, so a relevant chunk surfaced by either phrasing
        # reaches the LLM. Dedupe by chunk, keep the best score, take the top N.
        rewritten = self.query_rewrite_service.rewrite(question)
        retrieved = self.retriever_service.retrieve(rewritten, scoped_filter)
        merged: dict[tuple[str, str], RetrievedChunk] = {}
        for chunk in [*gate_chunks, *retrieved]:
            key = (chunk.doc_id, chunk.chunk_id)
            if key not in merged or chunk.score > merged[key].score:
                merged[key] = chunk
        context = sorted(merged.values(), key=lambda c: c.score, reverse=True)[: self.CONTEXT_CHUNKS]

        if settings.GEMINI_API_KEY:
            # Let the LLM judge sufficiency from the supplied excerpts (its system
            # prompt returns the exact insufficient sentence when context is thin).
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel(settings.GEMINI_MODEL)
            response = model.generate_content(
                self._prompt(question, context),
                generation_config={"max_output_tokens": 1000, "temperature": 0.0},
            )
            answer = (response.text or "").strip() or INSUFFICIENT_ANSWER
        else:
            answer = self._extractive_answer(question, context)

        # Only attach sources when we actually answered, so the UI can show the
        # "Request this information" affordance on an insufficient response.
        is_insufficient = answer.strip().rstrip(".") == INSUFFICIENT_ANSWER.rstrip(".")
        sources: list[dict[str, str]] = []
        if not is_insufficient:
            seen: set[str] = set()
            for chunk in context:
                if chunk.doc_name in seen:
                    continue
                seen.add(chunk.doc_name)
                sources.append(
                    {"doc_name": chunk.doc_name, "sensitivity": chunk.sensitivity, "department": chunk.namespace}
                )
        return RAGResult(answer=answer, sources=sources, department=department)

    def _extractive_answer(self, question: str, chunks: list[RetrievedChunk]) -> str:
        import re

        question_terms = {term.lower() for term in re.findall(r"[a-zA-Z0-9]+", question) if len(term) > 2}
        sentences: list[str] = []
        for chunk in chunks:
            for sentence in re.split(r"(?<=[.!?])\s+", chunk.text or ""):
                normalized = sentence.lower()
                if any(term in normalized for term in question_terms):
                    sentences.append(sentence.strip())
                if len(sentences) >= 3:
                    break
            if len(sentences) >= 3:
                break
        if sentences:
            return " ".join(sentences)
        return (chunks[0].text or "I do not have enough information to answer that question.").strip()[:1200]
