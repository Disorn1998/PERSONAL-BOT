"""Retrieval — query = latest user message + previous user message (§7.9)."""

from __future__ import annotations

from typing import Any

from app.rag.store import VectorStore


def build_retrieval_query(*, latest: str, previous_user: str | None) -> str:
    latest_clean = latest.strip()
    prev = (previous_user or "").strip()
    if prev:
        return f"{prev}\n{latest_clean}"
    return latest_clean


def previous_user_message(history: list[dict[str, str]]) -> str | None:
    """History is prior turns only (excluding the current user message)."""
    for turn in reversed(history):
        if turn.get("role") == "user":
            return turn.get("content")
    return None


def retrieve(
    store: VectorStore,
    *,
    persona_id: str,
    latest: str,
    history: list[dict[str, str]],
    top_k: int,
    min_score: float,
) -> list[dict[str, Any]]:
    query = build_retrieval_query(
        latest=latest,
        previous_user=previous_user_message(history),
    )
    if not query:
        return []
    hits = store.query(persona_id=persona_id, query_text=query, top_k=top_k)
    return [h for h in hits if float(h.get("score", 0.0)) >= min_score]


def filter_by_min_score(
    hits: list[dict[str, Any]],
    *,
    min_score: float,
) -> list[dict[str, Any]]:
    return [h for h in hits if float(h.get("score", 0.0)) >= min_score]
