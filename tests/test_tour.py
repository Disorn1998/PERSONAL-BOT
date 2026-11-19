"""Guided tour state machine + persist + AppTest smoke."""

from __future__ import annotations

from pathlib import Path

import pytest
from persona_bot.i18n import set_locale, t
from persona_bot.rag.embeddings import FakeEmbedder
from persona_bot.ui.theme import custom_css
from persona_bot.ui.tour import (
    TOUR_STEPS,
    clear_tour_done,
    coach_card_markup,
    is_tour_done,
    mark_tour_done,
)

ROOT = Path(__file__).resolve().parents[1]


def test_tour_persist_roundtrip(tmp_path: Path) -> None:
    assert not is_tour_done(tmp_path)
    mark_tour_done(tmp_path)
    assert is_tour_done(tmp_path)
    clear_tour_done(tmp_path)
    assert not is_tour_done(tmp_path)


def test_tour_strings_th_en() -> None:
    set_locale("th")
    assert "คีย์" in t("tour.step.welcome") or "ความรู้" in t("tour.step.welcome")
    assert t("action.tour_next") == "ถัดไป"
    assert t("action.tour_skip") == "ข้าม"
    assert t("action.tour_start") == "เริ่มใช้"
    set_locale("en")
    body = t("tour.step.welcome").lower()
    assert "api key" in body or "knowledge" in body
    assert t("action.tour_next") == "Next"
    assert t("action.tour_skip") == "Skip"
    assert t("action.tour_start") == "Start using"


def test_coach_card_markup_contains_step() -> None:
    set_locale("en")
    html = coach_card_markup("welcome")
    assert 'data-tour-step="welcome"' in html
    assert "pb-tour-coach" in html
    assert "Step 1/6" in html


def test_tour_css_spotlight_present() -> None:
    css = custom_css()
    assert "pb-tour-coach" in css
    assert "pb-tour-mascot" in css
    assert "data-tour-step" in css


def _configure_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    data = tmp_path / "data"
    data.mkdir()
    monkeypatch.setenv("DATA_DIR", str(data))
    monkeypatch.setenv("PERSONAS_DIR", str(data / "personas"))
    monkeypatch.setenv("EXAMPLES_DIR", str(ROOT / "personas" / "examples"))
    monkeypatch.setenv("GROQ_API_KEY", "")
    monkeypatch.setenv("GROQ_MODEL_PRIMARY", "openai/gpt-oss-120b")
    monkeypatch.setenv("GROQ_MODEL_FALLBACK", "openai/gpt-oss-20b")
    monkeypatch.setenv("APP_PASSWORD", "")
    monkeypatch.setenv("PERSONA_BOT_REMEMBER_KEY", "0")
    return data


def _patch_fake_embedder(monkeypatch: pytest.MonkeyPatch) -> None:
    def _fake_build(settings, *, persona, fake: bool = False):  # noqa: ANN001
        del settings, fake
        return FakeEmbedder(dim=32, model_name=f"fake:{persona.config.embedding_preset}")

    monkeypatch.setattr("persona_bot.main.build_embedder", _fake_build)
    monkeypatch.setattr("persona_bot.rag.runtime.build_embedder", _fake_build)


def _apptest(timeout: int = 60):
    pytest.importorskip("streamlit")
    from streamlit.testing.v1 import AppTest

    return AppTest.from_file(str(ROOT / "persona_bot" / "main.py"), default_timeout=timeout)


def _button_keys(at) -> set[str]:  # noqa: ANN001
    return {getattr(b, "key", None) for b in at.button if getattr(b, "key", None)}


def test_apptest_tour_shows_first_run(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    data = _configure_env(monkeypatch, tmp_path)
    _patch_fake_embedder(monkeypatch)
    at = _apptest()
    at.session_state["locale"] = "en"
    at.run()
    assert not at.exception, at.exception
    assert at.session_state.get("tour_active") is True
    assert at.session_state.get("tour_step") == "welcome"
    assert "tour_next_btn" in _button_keys(at)
    assert "tour_skip_btn" in _button_keys(at)
    markdown_blobs = [getattr(m, "value", "") or "" for m in at.markdown]
    assert any("pb-tour-coach" in str(blob) for blob in markdown_blobs)
    assert not (data / "tour_done").exists()


def test_apptest_tour_skip_persists(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    data = _configure_env(monkeypatch, tmp_path)
    _patch_fake_embedder(monkeypatch)
    at = _apptest()
    at.session_state["locale"] = "en"
    at.run()
    assert "tour_skip_btn" in _button_keys(at)
    at.button("tour_skip_btn").click().run()
    assert not at.exception, at.exception
    assert at.session_state.get("tour_active") is False
    assert at.session_state.get("tour_done") is True
    assert (data / "tour_done").read_text(encoding="utf-8").strip() == "1"
    assert "tour_next_btn" not in _button_keys(at)
    # Reload: tour stays hidden
    at2 = _apptest()
    at2.session_state["locale"] = "en"
    at2.run()
    assert not at2.exception, at2.exception
    assert at2.session_state.get("tour_active") is False
    assert "tour_next_btn" not in _button_keys(at2)


def test_apptest_tour_next_reaches_done(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    data = _configure_env(monkeypatch, tmp_path)
    _patch_fake_embedder(monkeypatch)
    (data / "privacy_ack").write_text("1", encoding="utf-8")
    (data / "entry_path").write_text("knowledge", encoding="utf-8")
    at = _apptest()
    at.session_state["locale"] = "en"
    at.session_state["wizard_done"] = True
    at.session_state["knowledge_only_mode"] = True
    at.session_state["privacy_ack"] = True
    at.session_state["entry_path"] = "knowledge"
    at.run()
    assert not at.exception, at.exception
    # Wizard already done → start at persona
    assert at.session_state.get("tour_step") == "persona"
    for _ in range(len(TOUR_STEPS)):
        keys = _button_keys(at)
        if "tour_finish_btn" in keys:
            at.button("tour_finish_btn").click().run()
            break
        assert "tour_next_btn" in keys
        at.button("tour_next_btn").click().run()
        assert not at.exception, at.exception
    assert at.session_state.get("tour_done") is True
    assert (data / "tour_done").is_file()


def test_apptest_tour_restart_from_more_settings(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    data = _configure_env(monkeypatch, tmp_path)
    _patch_fake_embedder(monkeypatch)
    (data / "privacy_ack").write_text("1", encoding="utf-8")
    (data / "tour_done").write_text("1", encoding="utf-8")
    (data / "entry_path").write_text("knowledge", encoding="utf-8")
    at = _apptest()
    at.session_state["locale"] = "en"
    at.session_state["wizard_done"] = True
    at.session_state["knowledge_only_mode"] = True
    at.session_state["privacy_ack"] = True
    at.session_state["entry_path"] = "knowledge"
    at.run()
    assert not at.exception, at.exception
    assert "tour_next_btn" not in _button_keys(at)
    assert "tour_restart_btn" in _button_keys(at)
    at.button("tour_restart_btn").click().run()
    assert not at.exception, at.exception
    assert at.session_state.get("tour_active") is True
    assert at.session_state.get("tour_step") == "persona"
    assert not (data / "tour_done").exists()
    assert "tour_next_btn" in _button_keys(at)
