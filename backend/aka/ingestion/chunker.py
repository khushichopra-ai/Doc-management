from __future__ import annotations

from dataclasses import dataclass

from langchain_text_splitters import RecursiveCharacterTextSplitter

from aka.ingestion.tokenizer import Tokenizer


@dataclass(slots=True)
class Chunk:
    chunk_id: str
    text: str


class ChunkingService:
    def __init__(self, chunk_size: int = 400, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.tokenizer = Tokenizer()
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            length_function=self._token_length,
            separators=["\n\n", "\n", " ", ""],
        )

    def _token_length(self, text: str) -> int:
        return len(self.tokenizer.encode(text))

    def split(self, text: str) -> list[Chunk]:
        pieces = self.splitter.split_text(text)
        chunks = [Chunk(chunk_id=f"chunk-{index + 1}", text=piece.strip()) for index, piece in enumerate(pieces) if piece.strip()]
        return chunks

