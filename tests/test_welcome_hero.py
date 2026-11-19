"""Welcome hero asset + soft CSS motion wiring."""

from __future__ import annotations

from pathlib import Path

import pytest
from persona_bot.ui.assets import welcome_hero_data_uri, welcome_hero_path
from persona_bot.ui.theme import custom_css

ROOT = Path(__file__).resolve().parents[1]


def test_welcome_hero_asset_exists() -> None:
    path = welcome_hero_path()
    assert path.is_file(), path
    assert path.suffix.lower() == ".jpg"
    assert path.stat().st_size > 10_000


def test_welcome_hero_data_uri() -> None:
    uri = welcome_hero_data_uri()
    assert uri is not None
    assert uri.startswith("data:image/jpeg;base64,")
    assert len(uri) > 1000


def test_welcome_hero_motion_css() -> None:
    css = custom_css()
    assert "@keyframes pb-welcome-float" in css
    assert "@keyframes pb-welcome-shadow-pulse" in css
    assert "prefers-reduced-motion: reduce" in css
    assert ".pb-welcome-hero" in css
    # Gentle 4–6s float window
    assert "5s ease-in-out infinite" in css


def _configure_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    data = tmp_path / "data"
    data.mkdir()
    monkeypatch.setenv("DATA_DIR", str(data))
    monkeypatch.setenv("PERSONAS_DIR", str(data / "personas"))
    monkeypatch.setenv("EXAMPLES_DIR", str(ROOT / "personas" / "examples"))
    monkeypatch.setenv("GROQ_API_KEY", "")
    monkeypatch.setenv("APP_PASSWORD", "")
    monkeypatch.setenv("PERSONA_BOT_REMEMBER_KEY", "0")
    return data


def test_apptest_welcome_gate_embeds_hero(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _configure_env(monkeypatch, tmp_path)
    pytest.importorskip("streamlit")
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(str(ROOT / "persona_bot" / "main.py"), default_timeout=60)
    at.run()
    assert not at.exception, at.exception
    # Hero markup must use the motion class (not a bare st.image).
    joined = "\n".join(m.value for m in at.markdown if isinstance(m.value, str))
    assert 'class="pb-welcome-hero"' in joined
    assert "data:image/jpeg;base64," in joined
