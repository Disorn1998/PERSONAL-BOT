"""Index fingerprint — rebuild when knowledge or chunk/embed settings change."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from app.rag.loaders import iter_knowledge_files


def file_digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            block = handle.read(1024 * 1024)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def build_index_fingerprint(
    knowledge_dir: Path,
    *,
    embedding_model: str,
    chunk_chars: int,
    overlap_chars: int,
    extra: dict[str, Any] | None = None,
) -> str:
    files = iter_knowledge_files(knowledge_dir)
    payload: dict[str, Any] = {
        "embedding_model": embedding_model,
        "chunk_chars": chunk_chars,
        "overlap_chars": overlap_chars,
        "files": [
            {
                "rel": str(p.relative_to(knowledge_dir)).replace("\\", "/"),
                "sha256": file_digest(p),
                "size": p.stat().st_size,
            }
            for p in files
        ],
    }
    if extra:
        payload["extra"] = extra
    blob = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()
