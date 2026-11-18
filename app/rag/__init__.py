"""RAG package — local embeddings, Chroma store, retrieval, citations."""

from __future__ import annotations

from app.rag.citations import format_sources_markdown, validate_citations
from app.rag.ingest import ensure_persona_index
from app.rag.retrieve import retrieve

__all__ = [
    "ensure_persona_index",
    "format_sources_markdown",
    "retrieve",
    "validate_citations",
]
