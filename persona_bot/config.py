"""Application settings and shared embedding presets (single source of truth)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Final, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

EmbeddingPresetId = Literal["lite", "multilingual", "quality"]

# One table only (§6 / Appendix A). Values verified against fastembed 0.9.1 metadata
# in Phase 0; Thai char→token ratio remains TODO(verify).
EMBEDDING_PRESETS: Final[dict[str, dict[str, Any]]] = {
    "lite": {
        "model": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        "dim": 384,
        "max_input_tokens": 128,
        "query_prefix": "",
        "passage_prefix": "",
        "chunk_chars": 400,
        "chunk_overlap_chars": 60,
        "top_k": 4,
        "min_score": 0.35,
    },
    "multilingual": {
        "model": "intfloat/multilingual-e5-large",
        "dim": 1024,
        "max_input_tokens": 512,
        "query_prefix": "query: ",
        "passage_prefix": "passage: ",
        "chunk_chars": 900,
        "chunk_overlap_chars": 120,
        "top_k": 6,
        "min_score": 0.30,
    },
    "quality": {
        "model": "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        "dim": 768,
        "max_input_tokens": 512,
        "query_prefix": "",
        "passage_prefix": "",
        "chunk_chars": 700,
        "chunk_overlap_chars": 100,
        "top_k": 6,
        "min_score": 0.32,
    },
}


class Settings(BaseSettings):
    """Runtime settings loaded from environment / ``.env`` (never commit secrets)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    groq_api_key: str = Field(default="", alias="GROQ_API_KEY")
    groq_base_url: str = Field(
        default="https://api.groq.com/openai/v1",
        alias="GROQ_BASE_URL",
    )
    # No Python-side hardcoded model fallbacks (F8). Empty → setup error at use site.
    groq_model_primary: str = Field(default="", alias="GROQ_MODEL_PRIMARY")
    groq_model_fallback: str = Field(default="", alias="GROQ_MODEL_FALLBACK")

    app_password: str = Field(default="", alias="APP_PASSWORD")
    examples_dir: Path = Field(default=Path("personas/examples"), alias="EXAMPLES_DIR")
    personas_dir: Path = Field(default=Path("data/personas"), alias="PERSONAS_DIR")
    data_dir: Path = Field(default=Path("data"), alias="DATA_DIR")
    max_knowledge_mb: int = Field(default=50, alias="MAX_KNOWLEDGE_MB")
    llm_timeout_seconds: float = Field(default=60.0, alias="LLM_TIMEOUT_SECONDS")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    # Display-only (F12); does not enforce Groq quota.
    daily_token_limit: int | None = Field(default=None, alias="DAILY_TOKEN_LIMIT")
    embedding_preset: EmbeddingPresetId = Field(default="lite", alias="EMBEDDING_PRESET")

    @field_validator("daily_token_limit", mode="before")
    @classmethod
    def _empty_daily_limit(cls, value: Any) -> Any:
        if value == "" or value is None:
            return None
        return value

    @field_validator("examples_dir", "personas_dir", "data_dir", mode="before")
    @classmethod
    def _as_path(cls, value: Any) -> Path:
        return Path(value)

    def embedding_config(self) -> dict[str, Any]:
        return dict(EMBEDDING_PRESETS[self.embedding_preset])

    def require_models(self) -> tuple[str, str]:
        """Return (primary, fallback) or raise if primary is unset."""
        primary = self.groq_model_primary.strip()
        fallback = self.groq_model_fallback.strip()
        if not primary:
            msg = "GROQ_MODEL_PRIMARY is unset"
            raise ValueError(msg)
        return primary, fallback


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def clear_settings_cache() -> None:
    get_settings.cache_clear()
