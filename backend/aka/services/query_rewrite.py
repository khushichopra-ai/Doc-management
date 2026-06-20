from __future__ import annotations

import logging
import re

import google.generativeai as genai
from django.conf import settings

logger = logging.getLogger(__name__)

# If the model ignores instructions and returns a preamble/list, we discard it
# and fall back to the original question (which retrieves well on its own).
_PREAMBLE_PREFIXES = ("here are", "here's", "here is", "sure", "okay", "ok,", "i ", "as an", "option", "rewritten")
_LABEL_RE = re.compile(r"^(rewritten query|query|search query|answer)\s*[:\-]\s*", re.IGNORECASE)


class QueryRewriteService:
    def rewrite(self, question: str) -> str:
        original = question.strip()
        if not settings.GEMINI_API_KEY:
            return original

        try:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel(settings.GEMINI_MODEL)
            response = model.generate_content(
                "Rewrite the user's question into ONE concise, self-contained search query. "
                "Respond with ONLY the query text on a single line — no preamble, no quotes, "
                "no numbering, no options, no explanation.\n\n"
                f"Question: {original}",
                # gemini-2.5 is a thinking model; give enough budget that internal
                # reasoning tokens don't truncate the actual one-line query output.
                generation_config={"max_output_tokens": 512, "temperature": 0.0},
            )
            return self._sanitize((response.text or ""), original)
        except Exception as exc:
            logger.warning("Query rewrite failed; using original question: %s", exc)
            return original

    def _sanitize(self, text: str, original: str) -> str:
        # Use only the first non-empty line, stripped of quotes and any "Query:" label.
        line = next((ln.strip() for ln in text.splitlines() if ln.strip()), "")
        line = _LABEL_RE.sub("", line).strip().strip('"\'')

        lowered = line.lower()
        looks_bad = (
            not line
            or len(line) > 300
            or lowered.startswith(_PREAMBLE_PREFIXES)
        )
        if looks_bad:
            logger.info("Discarding low-quality rewrite %r; using original question.", text[:80])
            return original
        return line
