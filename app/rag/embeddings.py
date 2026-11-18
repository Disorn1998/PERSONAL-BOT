"""Embedding backends — fastembed production + FakeEmbedder for offline tests."""

from __future__ import annotations

import hashlib
import math
import re
from collections.abc import Sequence
from typing import Protocol

from app.config import EMBEDDING_PRESETS, EmbeddingPresetId


class Embedder(Protocol):
    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]: ...

    def embed_queries(self, texts: Sequence[str]) -> list[list[float]]: ...

    @property
    def dim(self) -> int: ...

    @property
    def model_name(self) -> str: ...


class FakeEmbedder:
    """Deterministic bag-of-hashes embedder for unit tests (no ONNX download)."""

    def __init__(self, *, dim: int = 32, model_name: str = "fake-embedder") -> None:
        self._dim = dim
        self._model_name = model_name

    @property
    def dim(self) -> int:
        return self._dim

    @property
    def model_name(self) -> str:
        return self._model_name

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return [self._embed_one(t) for t in texts]

    def embed_queries(self, texts: Sequence[str]) -> list[list[float]]:
        return [self._embed_one(t) for t in texts]

    def _embed_one(self, text: str) -> list[float]:
        tokens = re.findall(r"\w+", text.lower(), flags=re.UNICODE)
        vec = [0.0] * self._dim
        if not tokens:
            vec[0] = 1.0
            return vec
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            idx = digest[0] % self._dim
            sign = 1.0 if digest[1] % 2 == 0 else -1.0
            vec[idx] += sign
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]


class FastEmbedder:
    """Local ONNX embeddings via fastembed."""

    def __init__(
        self,
        *,
        preset: EmbeddingPresetId = "lite",
        model_name: str | None = None,
        query_prefix: str | None = None,
        passage_prefix: str | None = None,
    ) -> None:
        from fastembed import TextEmbedding  # lazy — heavy import

        cfg = EMBEDDING_PRESETS[preset]
        self._model_name = model_name or str(cfg["model"])
        self._query_prefix = query_prefix if query_prefix is not None else str(cfg["query_prefix"])
        self._passage_prefix = (
            passage_prefix if passage_prefix is not None else str(cfg["passage_prefix"])
        )
        self._dim = int(cfg["dim"])
        # TODO(verify): cache_dir placement under data/ for Windows installs
        self._model = TextEmbedding(model_name=self._model_name)

    @property
    def dim(self) -> int:
        return self._dim

    @property
    def model_name(self) -> str:
        return self._model_name

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        prefixed = [self._passage_prefix + t for t in texts]
        return [list(map(float, vec)) for vec in self._model.embed(prefixed)]

    def embed_queries(self, texts: Sequence[str]) -> list[list[float]]:
        prefixed = [self._query_prefix + t for t in texts]
        return [list(map(float, vec)) for vec in self._model.embed(prefixed)]


def get_embedder(preset: EmbeddingPresetId, *, fake: bool = False) -> Embedder:
    if fake:
        dim = int(EMBEDDING_PRESETS[preset]["dim"])
        return FakeEmbedder(dim=min(dim, 64), model_name=f"fake:{preset}")
    return FastEmbedder(preset=preset)
