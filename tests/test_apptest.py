"""Streamlit AppTest smoke — loads the chat shell without real Groq."""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_streamlit_app_loads(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    pytest.importorskip("streamlit")
    from streamlit.testing.v1 import AppTest

    data = tmp_path / "data"
    data.mkdir()
    monkeypatch.setenv("DATA_DIR", str(data))
    monkeypatch.setenv("PERSONAS_DIR", str(data / "personas"))
    monkeypatch.setenv("EXAMPLES_DIR", str(ROOT / "personas" / "examples"))
    monkeypatch.setenv("GROQ_API_KEY", "")
    monkeypatch.setenv("GROQ_MODEL_PRIMARY", "openai/gpt-oss-120b")
    monkeypatch.setenv("GROQ_MODEL_FALLBACK", "openai/gpt-oss-20b")
    monkeypatch.setenv("APP_PASSWORD", "")

    at = AppTest.from_file(str(ROOT / "app" / "main.py"), default_timeout=30)
    at.run()
    # Welcome / shell should render without an uncaught exception.
    assert not at.exception, at.exception
