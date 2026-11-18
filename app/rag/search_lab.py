"""Search-lab helper — run a retrieval query and return scored hits for inspection."""

from __future__ import annotations

from typing import Any

from app.rag.store import VectorStore


def run_search_lab(
    store: VectorStore,
    *,
    persona_id: str,
    query: str,
    top_k: int = 6,
    min_score: float = 0.0,
) -> list[dict[str, Any]]:
    hits = store.query(persona_id=persona_id, query_text=query, top_k=top_k)
    return [h for h in hits if float(h.get("score", 0.0)) >= min_score]
