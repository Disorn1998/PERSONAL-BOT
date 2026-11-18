"""Ingest knowledge dirs into the vector store (fingerprint + atomic rebuild)."""

from __future__ import annotations

from pathlib import Path

from app.config import EMBEDDING_PRESETS, EmbeddingPresetId
from app.persona import PersonaPack
from app.rag.chunking import Chunk, chunk_text
from app.rag.embeddings import Embedder
from app.rag.fingerprint import build_index_fingerprint
from app.rag.loaders import iter_knowledge_files, load_text_file
from app.rag.store import IndexManifest, VectorStore


def knowledge_dir_for_persona(
    *,
    examples_dir: Path,
    personas_dir: Path,
    persona_id: str,
) -> Path:
    """Prefer user persona pack, else examples/<id>/knowledge."""
    user = personas_dir / persona_id / "knowledge"
    example = examples_dir / persona_id / "knowledge"
    if user.exists():
        return user
    return example


def collect_chunks(
    knowledge_dir: Path,
    *,
    chunk_chars: int,
    overlap_chars: int,
) -> list[Chunk]:
    chunks: list[Chunk] = []
    for path in iter_knowledge_files(knowledge_dir):
        rel = str(path.relative_to(knowledge_dir)).replace("\\", "/")
        text = load_text_file(path)
        chunks.extend(
            chunk_text(
                text,
                source=rel,
                chunk_chars=chunk_chars,
                overlap_chars=overlap_chars,
            )
        )
    return chunks


def ensure_index(
    store: VectorStore,
    *,
    persona: PersonaPack,
    knowledge_dir: Path,
    preset: EmbeddingPresetId | None = None,
    force: bool = False,
) -> IndexManifest:
    """Rebuild when fingerprint mismatches; otherwise return existing manifest."""
    preset_id = preset or persona.config.embedding_preset
    preset_cfg = EMBEDDING_PRESETS[preset_id]
    chunk_chars = persona.config.resolved_chunk_chars()
    overlap = int(preset_cfg["chunk_overlap_chars"])
    fingerprint = build_index_fingerprint(
        knowledge_dir,
        embedding_model=store.embedder.model_name,
        chunk_chars=chunk_chars,
        overlap_chars=overlap,
        extra={"preset": preset_id},
    )
    existing = store.load_manifest(persona.id)
    if (
        not force
        and existing is not None
        and existing.fingerprint == fingerprint
        and existing.embedding_model == store.embedder.model_name
        and existing.chunk_chars == chunk_chars
    ):
        return existing

    chunks = collect_chunks(
        knowledge_dir,
        chunk_chars=chunk_chars,
        overlap_chars=overlap,
    )
    return store.rebuild(
        persona_id=persona.id,
        chunks=chunks,
        fingerprint=fingerprint,
        chunk_chars=chunk_chars,
        overlap_chars=overlap,
    )


def ensure_persona_index(
    *,
    data_dir: Path,
    examples_dir: Path,
    personas_dir: Path,
    persona: PersonaPack,
    embedder: Embedder,
    force: bool = False,
) -> tuple[VectorStore, IndexManifest, Path]:
    store = VectorStore(data_dir=data_dir, embedder=embedder)
    kdir = knowledge_dir_for_persona(
        examples_dir=examples_dir,
        personas_dir=personas_dir,
        persona_id=persona.id,
    )
    manifest = ensure_index(
        store,
        persona=persona,
        knowledge_dir=kdir,
        force=force,
    )
    return store, manifest, kdir
