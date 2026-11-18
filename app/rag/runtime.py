"""Session-facing RAG runtime helpers (embedder + ensure index)."""

from __future__ import annotations

from pathlib import Path

from app.config import EMBEDDING_PRESETS, Settings
from app.persona import PersonaPack
from app.rag.embeddings import Embedder, FakeEmbedder, FastEmbedder
from app.rag.fingerprint import build_index_fingerprint
from app.rag.health import KnowledgeHealth, assess_knowledge_health
from app.rag.ingest import ensure_index, knowledge_dir_for_persona
from app.rag.store import IndexManifest, VectorStore


def build_embedder(settings: Settings, *, persona: PersonaPack, fake: bool = False) -> Embedder:
    preset = persona.config.embedding_preset
    if fake:
        return FakeEmbedder(dim=32, model_name=f"fake:{preset}")
    return FastEmbedder(preset=preset)


def get_or_build_store(
    *,
    settings: Settings,
    persona: PersonaPack,
    embedder: Embedder,
    force: bool = False,
) -> tuple[VectorStore, IndexManifest, Path, KnowledgeHealth]:
    store = VectorStore(data_dir=settings.data_dir, embedder=embedder)
    kdir = knowledge_dir_for_persona(
        examples_dir=settings.examples_dir,
        personas_dir=settings.personas_dir,
        persona_id=persona.id,
    )
    overlap = int(EMBEDDING_PRESETS[persona.config.embedding_preset]["chunk_overlap_chars"])
    expected_fp = build_index_fingerprint(
        kdir,
        embedding_model=embedder.model_name,
        chunk_chars=persona.config.resolved_chunk_chars(),
        overlap_chars=overlap,
        extra={"preset": persona.config.embedding_preset},
    )
    manifest = ensure_index(
        store,
        persona=persona,
        knowledge_dir=kdir,
        force=force,
    )
    health = assess_knowledge_health(
        store,
        persona=persona,
        examples_dir=settings.examples_dir,
        personas_dir=settings.personas_dir,
        expected_fingerprint=expected_fp,
    )
    return store, manifest, kdir, health
