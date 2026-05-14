"""Fixed-window + overlap chunking using tiktoken token counts."""

from dataclasses import dataclass

import tiktoken

from core.config import CHUNK_SIZE, CHUNK_OVERLAP

_enc = tiktoken.get_encoding("cl100k_base")

MIN_CHUNK_TOKENS = 16
MAX_CHUNKS_PER_DOC = 1000


@dataclass
class Chunk:
    chunk_index: int
    content: str
    start_char: int
    end_char: int
    token_count: int


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[Chunk]:
    tokens = _enc.encode(text)
    if not tokens:
        return []

    chunks: list[Chunk] = []
    step = chunk_size - overlap
    i = 0

    while i < len(tokens) and len(chunks) < MAX_CHUNKS_PER_DOC:
        token_slice = tokens[i: i + chunk_size]
        content = _enc.decode(token_slice)
        token_count = len(token_slice)

        if token_count < MIN_CHUNK_TOKENS:
            break

        # Approximate char positions by finding the content in the original text
        # starting from where the previous chunk ended
        search_start = chunks[-1].end_char if chunks else 0
        start_char = text.find(content[:40], search_start)
        if start_char == -1:
            start_char = search_start
        end_char = start_char + len(content)

        chunks.append(Chunk(
            chunk_index=len(chunks),
            content=content,
            start_char=start_char,
            end_char=end_char,
            token_count=token_count,
        ))

        i += step

    return chunks
