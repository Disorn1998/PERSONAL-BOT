"""Validate citation markers ``[n]`` against supplied sources."""

from __future__ import annotations

import re
from typing import Any

_CITE_RE = re.compile(r"\[(\d+)\]")


def extract_citation_numbers(text: str) -> list[int]:
    return [int(m.group(1)) for m in _CITE_RE.finditer(text)]


def validate_citations(
    answer: str,
    sources: list[dict[str, Any]],
) -> dict[str, Any]:
    """Return validation summary; invalid cites are listed (not silently dropped)."""
    cited = extract_citation_numbers(answer)
    max_n = len(sources)
    valid = sorted({n for n in cited if 1 <= n <= max_n})
    invalid = sorted({n for n in cited if n < 1 or n > max_n})
    return {
        "cited": cited,
        "valid": valid,
        "invalid": invalid,
        "ok": not invalid,
        "source_count": max_n,
    }


def format_sources_markdown(sources: list[dict[str, Any]]) -> str:
    if not sources:
        return ""
    lines: list[str] = []
    for i, src in enumerate(sources, start=1):
        name = str(src.get("source") or "")
        score = src.get("score")
        score_s = f" · score={float(score):.3f}" if score is not None else ""
        preview = str(src.get("text") or "").strip().replace("\n", " ")
        if len(preview) > 160:
            preview = preview[:157] + "…"
        lines.append(f"**[{i}]** `{name}`{score_s}\n{preview}")
    return "\n\n".join(lines)
