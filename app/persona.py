"""Persona Pack schema and YAML load/save (Phase 1a — schema + examples metadata)."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field, field_validator

from app.config import EMBEDDING_PRESETS, EmbeddingPresetId
from app.errors import PersonaLoadError

AnswerMode = Literal["strict", "balanced", "open"]


class AnswerModeEnum(StrEnum):
    STRICT = "strict"
    BALANCED = "balanced"
    OPEN = "open"


class PersonaConfig(BaseModel):
    """Tuning + retrieval knobs stored with a Persona Pack."""

    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1024, ge=16, le=8192)
    answer_mode: AnswerMode = "balanced"
    embedding_preset: EmbeddingPresetId = "lite"
    top_k: int | None = Field(default=None, ge=1, le=32)
    min_score: float | None = Field(default=None, ge=0.0, le=1.0)
    chunk_chars: int | None = Field(default=None, ge=100, le=4000)

    def resolved_top_k(self) -> int:
        if self.top_k is not None:
            return self.top_k
        return int(EMBEDDING_PRESETS[self.embedding_preset]["top_k"])

    def resolved_min_score(self) -> float:
        if self.min_score is not None:
            return self.min_score
        return float(EMBEDDING_PRESETS[self.embedding_preset]["min_score"])

    def resolved_chunk_chars(self) -> int:
        if self.chunk_chars is not None:
            return self.chunk_chars
        return int(EMBEDDING_PRESETS[self.embedding_preset]["chunk_chars"])


class PersonaPack(BaseModel):
    """Persona Pack = role + knowledge refs + tuning (§1 / §0.2)."""

    id: str = Field(min_length=2, max_length=64, pattern=r"^[a-z0-9][a-z0-9_-]*$")
    name: str = Field(min_length=1, max_length=120)
    description: str = ""
    system_prompt: str = Field(min_length=1)
    config: PersonaConfig = Field(default_factory=PersonaConfig)
    knowledge_files: list[str] = Field(default_factory=list)
    avatar: str | None = None
    version: int = 1

    @field_validator("id")
    @classmethod
    def _slug_id(cls, value: str) -> str:
        return value.strip().lower()


def load_persona_yaml(path: Path) -> PersonaPack:
    """Load a Persona Pack from ``persona.yaml`` (UTF-8)."""
    try:
        text = path.read_text(encoding="utf-8")
        data = yaml.safe_load(text)
    except OSError as exc:
        raise PersonaLoadError(str(exc), details={"path": str(path)}) from exc
    except yaml.YAMLError as exc:
        raise PersonaLoadError(str(exc), details={"path": str(path)}) from exc
    if not isinstance(data, dict):
        raise PersonaLoadError("persona.yaml must be a mapping", details={"path": str(path)})
    try:
        return PersonaPack.model_validate(_normalize_persona_dict(data))
    except Exception as exc:  # pydantic ValidationError
        raise PersonaLoadError(str(exc), details={"path": str(path)}) from exc


def save_persona_yaml(pack: PersonaPack, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = pack.model_dump(mode="python")
    text = yaml.safe_dump(payload, allow_unicode=True, sort_keys=False)
    path.write_text(text, encoding="utf-8")


def _normalize_persona_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Accept flat or nested ``config`` blocks from example YAML."""
    known_config = {
        "temperature",
        "max_tokens",
        "answer_mode",
        "embedding_preset",
        "top_k",
        "min_score",
        "chunk_chars",
    }
    out = dict(data)
    config = dict(out.get("config") or {})
    for key in list(out.keys()):
        if key in known_config and key not in config:
            config[key] = out.pop(key)
    out["config"] = config
    return out


def list_example_persona_dirs(examples_dir: Path) -> list[Path]:
    if not examples_dir.exists():
        return []
    return sorted(p for p in examples_dir.iterdir() if p.is_dir() and (p / "persona.yaml").exists())
