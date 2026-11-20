"""``.env`` upsert helpers — never assert raw secrets in logs."""

from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest
from persona_bot.env_store import default_env_path, upsert_env_var, upsert_groq_api_key


def test_upsert_creates_and_replaces(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    upsert_env_var(env, "FOO", "one")
    assert env.read_text(encoding="utf-8") == "FOO=one\n"
    upsert_env_var(env, "BAR", "two")
    text = env.read_text(encoding="utf-8")
    assert "FOO=one\n" in text
    assert "BAR=two\n" in text
    upsert_env_var(env, "FOO", "three")
    text = env.read_text(encoding="utf-8")
    assert "FOO=three\n" in text
    assert text.count("FOO=") == 1


def test_upsert_groq_api_key_mock_write(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env = tmp_path / "nested" / ".env"
    monkeypatch.setenv("PERSONA_BOT_ENV_FILE", str(env))
    assert default_env_path() == env
    path = upsert_groq_api_key("gsk_test_secret_value")
    assert path == env
    body = env.read_text(encoding="utf-8")
    assert "GROQ_API_KEY=gsk_test_secret_value\n" in body
    # Second write replaces without duplicating.
    upsert_groq_api_key("gsk_test_other")
    body = env.read_text(encoding="utf-8")
    assert body.count("GROQ_API_KEY=") == 1
    assert "gsk_test_other" in body
    # Owner-only bits when the platform supports POSIX modes.
    if os.name == "posix":
        mode = stat.S_IMODE(env.stat().st_mode)
        assert mode == 0o600


def test_upsert_rejects_empty_key(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="empty"):
        upsert_groq_api_key("  ", env_path=tmp_path / ".env")
    with pytest.raises(ValueError, match="invalid"):
        upsert_env_var(tmp_path / ".env", "bad-key", "x")
