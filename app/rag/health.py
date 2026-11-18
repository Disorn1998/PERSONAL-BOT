"""Knowledge-health summary for a persona index."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from app.persona import PersonaPack
from app.rag.ingest import knowledge_dir_for_persona
from app.rag.loaders import iter_knowledge_files
from app.rag.store import VectorStore


@dataclass(slots=True)
class KnowledgeHealth:
    persona_id: str
    knowledge_dir: str
    file_count: int
    chunk_count: int
    fingerprint: str | None
    embedding_model: str | None
    chunk_chars: int | None
    sources: list[str]
    needs_rebuild: bool
    notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def assess_knowledge_health(
    store: VectorStore,
    *,
    persona: PersonaPack,
    examples_dir: Path,
    personas_dir: Path,
    expected_fingerprint: str | None = None,
) -> KnowledgeHealth:
    kdir = knowledge_dir_for_persona(
        examples_dir=examples_dir,
        personas_dir=personas_dir,
        persona_id=persona.id,
    )
    files = iter_knowledge_files(kdir)
    manifest = store.load_manifest(persona.id)
    notes: list[str] = []
    needs_rebuild = False
    if not files:
        notes.append("no_knowledge_files")
    if manifest is None:
        notes.append("no_manifest")
        needs_rebuild = bool(files)
    else:
        if expected_fingerprint and manifest.fingerprint != expected_fingerprint:
            notes.append("fingerprint_mismatch")
            needs_rebuild = True
        if manifest.chunk_count == 0 and files:
            notes.append("empty_index_with_files")
            needs_rebuild = True
    return KnowledgeHealth(
        persona_id=persona.id,
        knowledge_dir=str(kdir),
        file_count=len(files),
        chunk_count=manifest.chunk_count if manifest else 0,
        fingerprint=manifest.fingerprint if manifest else None,
        embedding_model=manifest.embedding_model if manifest else None,
        chunk_chars=manifest.chunk_chars if manifest else None,
        sources=list(manifest.sources) if manifest else [],
        needs_rebuild=needs_rebuild,
        notes=notes,
    )
