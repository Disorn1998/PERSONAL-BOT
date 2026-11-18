"""Settings and embedding preset table."""

from __future__ import annotations

import pytest
from persona_bot.config import EMBEDDING_PRESETS, Settings, clear_settings_cache


def test_embedding_presets_have_required_keys() -> None:
    required = {
        "model",
        "dim",
        "max_input_tokens",
        "query_prefix",
        "passage_prefix",
        "chunk_chars",
        "top_k",
        "min_score",
    }
    for name, preset in EMBEDDING_PRESETS.items():
        assert required <= set(preset), name


def test_settings_require_models(monkeypatch: pytest.MonkeyPatch) -> None:
    clear_settings_cache()
    monkeypatch.setenv("GROQ_MODEL_PRIMARY", "")
    monkeypatch.setenv("GROQ_MODEL_FALLBACK", "")
    settings = Settings()
    with pytest.raises(ValueError, match="GROQ_MODEL_PRIMARY"):
        settings.require_models()


def test_settings_paths_and_daily_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    clear_settings_cache()
    monkeypatch.setenv("EXAMPLES_DIR", "personas/examples")
    monkeypatch.setenv("DAILY_TOKEN_LIMIT", "")
    settings = Settings()
    assert settings.examples_dir.name == "examples"
    assert settings.daily_token_limit is None
