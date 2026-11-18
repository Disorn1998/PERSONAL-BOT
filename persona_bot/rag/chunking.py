"""Character-based chunker (Windows-safe UTF-8). Thai-aware split is best-effort."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Chunk:
    text: str
    source: str
    index: int
    start_char: int
    end_char: int


def chunk_text(
    text: str,
    *,
    source: str,
    chunk_chars: int,
    overlap_chars: int,
) -> list[Chunk]:
    cleaned = text.replace("\r\n", "\n").strip()
    if not cleaned:
        return []
    if chunk_chars < 50:
        chunk_chars = 50
    overlap_chars = max(0, min(overlap_chars, chunk_chars // 2))

    chunks: list[Chunk] = []
    start = 0
    index = 0
    length = len(cleaned)
    while start < length:
        end = min(length, start + chunk_chars)
        if end < length:
            # Prefer breaking at whitespace / newline near the end.
            window = cleaned[start:end]
            break_at = max(window.rfind("\n"), window.rfind(" "), window.rfind("\t"))
            if break_at >= chunk_chars // 3:
                end = start + break_at + 1
        piece = cleaned[start:end].strip()
        if piece:
            chunks.append(
                Chunk(
                    text=piece,
                    source=source,
                    index=index,
                    start_char=start,
                    end_char=end,
                )
            )
            index += 1
        if end >= length:
            break
        start = max(end - overlap_chars, start + 1)
    return chunks
