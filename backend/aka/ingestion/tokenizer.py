from __future__ import annotations

import tiktoken


class Tokenizer:
    def __init__(self) -> None:
        try:
            self.encoding = tiktoken.encoding_for_model("text-embedding-3-small")
        except Exception:
            self.encoding = tiktoken.get_encoding("cl100k_base")

    def encode(self, text: str) -> list[int]:
        return self.encoding.encode(text)

    def decode(self, tokens: list[int]) -> str:
        return self.encoding.decode(tokens)

