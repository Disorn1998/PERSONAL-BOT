"""Chroma-backed vector store with manifest + atomic rebuild."""

from __future__ import annotations

import contextlib
import json
import re
import shutil
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from persona_bot.rag.chunking import Chunk
from persona_bot.rag.embeddings import Embedder


def sanitize_collection_name(persona_id: str) -> str:
    """Chroma-safe name: 3–512 chars, start/end alnum, [a-z0-9._-]."""
    slug = re.sub(r"[^a-z0-9._-]+", "-", persona_id.strip().lower())
    slug = re.sub(r"\.{2,}", ".", slug).strip(".-_")
    if len(slug) < 3:
        slug = f"p-{slug or 'x'}"
    if not slug[0].isalnum():
        slug = f"p{slug}"
    if not slug[-1].isalnum():
        slug = f"{slug}0"
    return slug[:512]


@dataclass(slots=True)
class IndexManifest:
    persona_id: str
    fingerprint: str
    embedding_model: str
    chunk_chars: int
    overlap_chars: int
    chunk_count: int = 0
    sources: list[str] = field(default_factory=list)
    updated_at: float = 0.0

    def to_json(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> IndexManifest:
        return cls(
            persona_id=str(data["persona_id"]),
            fingerprint=str(data["fingerprint"]),
            embedding_model=str(data["embedding_model"]),
            chunk_chars=int(data["chunk_chars"]),
            overlap_chars=int(data["overlap_chars"]),
            chunk_count=int(data.get("chunk_count", 0)),
            sources=[str(s) for s in data.get("sources", [])],
            updated_at=float(data.get("updated_at", 0.0)),
        )


class VectorStore:
    """Persistent Chroma collection under ``data/chroma`` + JSON manifests."""

    def __init__(self, *, data_dir: Path, embedder: Embedder) -> None:
        self.data_dir = Path(data_dir)
        self.chroma_dir = self.data_dir / "chroma"
        self.manifest_dir = self.data_dir / "index"
        self.chroma_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_dir.mkdir(parents=True, exist_ok=True)
        self.embedder = embedder
        self._client: Any | None = None

    def _get_client(self) -> Any:
        if self._client is None:
            import chromadb

            self._client = chromadb.PersistentClient(path=str(self.chroma_dir))
        return self._client

    def manifest_path(self, persona_id: str) -> Path:
        return self.manifest_dir / f"{persona_id}.json"

    def load_manifest(self, persona_id: str) -> IndexManifest | None:
        path = self.manifest_path(persona_id)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return IndexManifest.from_json(data)
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError):
            return None

    def save_manifest(self, manifest: IndexManifest) -> None:
        path = self.manifest_path(manifest.persona_id)
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(
            json.dumps(manifest.to_json(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        tmp.replace(path)

    def collection_name(self, persona_id: str) -> str:
        return sanitize_collection_name(persona_id)

    def rebuild(
        self,
        *,
        persona_id: str,
        chunks: list[Chunk],
        fingerprint: str,
        chunk_chars: int,
        overlap_chars: int,
    ) -> IndexManifest:
        """Atomically replace the persona collection."""
        name = self.collection_name(persona_id)
        client = self._get_client()
        # Drop existing collection if present.
        with contextlib.suppress(Exception):
            client.delete_collection(name)

        collection = client.create_collection(
            name=name,
            metadata={"hnsw:space": "cosine", "persona_id": persona_id},
        )
        if chunks:
            texts = [c.text for c in chunks]
            embeddings = self.embedder.embed_documents(texts)
            ids = [f"{persona_id}-{c.index}-{i}" for i, c in enumerate(chunks)]
            metadatas = [
                {
                    "source": c.source,
                    "chunk_index": c.index,
                    "start_char": c.start_char,
                    "end_char": c.end_char,
                }
                for c in chunks
            ]
            # Batch to keep memory bounded.
            batch = 64
            for start in range(0, len(ids), batch):
                end = start + batch
                collection.add(
                    ids=ids[start:end],
                    embeddings=embeddings[start:end],
                    documents=texts[start:end],
                    metadatas=metadatas[start:end],
                )

        sources = sorted({c.source for c in chunks})
        manifest = IndexManifest(
            persona_id=persona_id,
            fingerprint=fingerprint,
            embedding_model=self.embedder.model_name,
            chunk_chars=chunk_chars,
            overlap_chars=overlap_chars,
            chunk_count=len(chunks),
            sources=sources,
            updated_at=time.time(),
        )
        self.save_manifest(manifest)
        return manifest

    def query(
        self,
        *,
        persona_id: str,
        query_text: str,
        top_k: int,
    ) -> list[dict[str, Any]]:
        name = self.collection_name(persona_id)
        client = self._get_client()
        try:
            collection = client.get_collection(name)
        except Exception:  # noqa: BLE001
            return []
        if collection.count() == 0:
            return []
        qvec = self.embedder.embed_queries([query_text])[0]
        result = collection.query(
            query_embeddings=[qvec],
            n_results=min(top_k, max(1, collection.count())),
            include=["documents", "metadatas", "distances"],
        )
        docs = (result.get("documents") or [[]])[0]
        metas = (result.get("metadatas") or [[]])[0]
        distances = (result.get("distances") or [[]])[0]
        out: list[dict[str, Any]] = []
        for doc, meta, dist in zip(docs, metas, distances, strict=False):
            # score = 1 − cosine distance (when space=cosine)
            score = 1.0 - float(dist)
            out.append(
                {
                    "text": str(doc or ""),
                    "source": str((meta or {}).get("source") or ""),
                    "score": score,
                    "chunk_index": (meta or {}).get("chunk_index"),
                }
            )
        return out

    def wipe_persona(self, persona_id: str) -> None:
        name = self.collection_name(persona_id)
        with contextlib.suppress(Exception):
            self._get_client().delete_collection(name)
        path = self.manifest_path(persona_id)
        if path.exists():
            path.unlink()

    def reset_all(self) -> None:
        self._client = None
        if self.chroma_dir.exists():
            shutil.rmtree(self.chroma_dir)
        if self.manifest_dir.exists():
            shutil.rmtree(self.manifest_dir)
        self.chroma_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_dir.mkdir(parents=True, exist_ok=True)
