"""Streamlit AppTest smoke — shell + offline UX paths without real Groq."""

from __future__ import annotations

from pathlib import Path

import pytest
from persona_bot.rag.embeddings import FakeEmbedder

ROOT = Path(__file__).resolve().parents[1]


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
    """Keep AppTest offline — never download ONNX via FastEmbedder."""

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


def _click_label(at, label: str) -> None:  # noqa: ANN001
    for btn in at.button:
        if btn.label == label:
            btn.click().run()
            return
    labels = [b.label for b in at.button]
    raise AssertionError(f"button with label {label!r} not found; have {labels}")


def _enter_knowledge_only(at) -> None:  # noqa: ANN001
    at.run()
    assert not at.exception, at.exception
    at.button("welcome_knowledge_only").click().run()
    assert not at.exception, at.exception
    if "privacy_ack_btn" in _button_keys(at):
        at.button("privacy_ack_btn").click().run()
        assert not at.exception, at.exception


def test_streamlit_app_loads(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _configure_env(monkeypatch, tmp_path)
    at = _apptest()
    at.run()
    # Welcome / shell should render without an uncaught exception.
    assert not at.exception, at.exception


def test_apptest_knowledge_only_ready_path(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Welcome → knowledge-only → privacy → chat shell (no Groq)."""
    _configure_env(monkeypatch, tmp_path)
    _patch_fake_embedder(monkeypatch)
    at = _apptest()
    _enter_knowledge_only(at)
    assert at.session_state["knowledge_only_mode"] is True
    assert at.session_state["wizard_done"] is True
    assert at.session_state["privacy_ack"] is True
    assert at.chat_input, "expected chat input after knowledge-only continue"


def test_apptest_clear_chat_confirm(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    data = _configure_env(monkeypatch, tmp_path)
    _patch_fake_embedder(monkeypatch)
    from persona_bot.chat_store import ChatStore

    store = ChatStore(data / "chat.sqlite3")
    thread = store.create_thread(persona_id="study-buddy", title="seed")
    store.add_message(thread_id=thread.id, role="user", content="hello seed")
    store.add_message(thread_id=thread.id, role="assistant", content="hi back")
    store.close()

    (data / "privacy_ack").write_text("1", encoding="utf-8")
    at = _apptest()
    at.session_state["wizard_done"] = True
    at.session_state["knowledge_only_mode"] = True
    at.session_state["privacy_ack"] = True
    at.session_state["locale"] = "en"
    at.session_state["persona_id"] = "study-buddy"
    at.session_state["thread_id"] = thread.id
    at.run()
    assert not at.exception, at.exception
    assert len(list(at.chat_message)) >= 2

    _click_label(at, "Clear chat")
    assert not at.exception, at.exception
    assert at.session_state["confirm_clear_chat"] is True
    at.button("confirm_clear_chat_btn").click().run()
    assert not at.exception, at.exception
    assert at.session_state["confirm_clear_chat"] is False

    from persona_bot.chat_store import ChatStore as CS

    verify = CS(data / "chat.sqlite3")
    assert verify.list_messages(thread.id) == []
    verify.close()


def test_apptest_editor_create_persona(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    data = _configure_env(monkeypatch, tmp_path)
    _patch_fake_embedder(monkeypatch)
    (data / "privacy_ack").write_text("1", encoding="utf-8")
    at = _apptest()
    at.session_state["wizard_done"] = True
    at.session_state["knowledge_only_mode"] = True
    at.session_state["privacy_ack"] = True
    at.session_state["locale"] = "en"
    at.run()
    assert not at.exception, at.exception

    at.text_input("create_persona_id").set_value("notes-home").run()
    at.text_input("create_persona_name").set_value("Home Notes").run()
    at.text_area("create_persona_prompt").set_value("Answer from my notes only.").run()
    at.button("create_persona_btn").click().run()
    assert not at.exception, at.exception
    assert at.session_state["persona_id"] == "notes-home"
    assert (data / "personas" / "notes-home" / "persona.yaml").is_file()


def test_apptest_make_knowledge_ready_paste(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """User pack paste →「บันทึกความรู้ให้พร้อมใช้」with FakeEmbedder (no Groq)."""
    data = _configure_env(monkeypatch, tmp_path)
    _patch_fake_embedder(monkeypatch)
    from persona_bot.config import clear_settings_cache, get_settings
    from persona_bot.persona_editor import build_persona_config, create_user_persona

    clear_settings_cache()
    settings = get_settings()
    create_user_persona(
        personas_dir=settings.personas_dir,
        persona_id="kb-demo",
        name="KB Demo",
        description="offline paste demo",
        system_prompt="Use knowledge.",
        config=build_persona_config(
            answer_mode="strict",
            temperature=0.2,
            max_tokens=512,
            embedding_preset="lite",
        ),
    )

    (data / "privacy_ack").write_text("1", encoding="utf-8")
    at = _apptest()
    at.session_state["wizard_done"] = True
    at.session_state["knowledge_only_mode"] = True
    at.session_state["privacy_ack"] = True
    at.session_state["locale"] = "en"
    at.session_state["persona_id"] = "kb-demo"
    at.run()
    assert not at.exception, at.exception

    paste_key = "knowledge_paste_kb-demo"
    at.text_area(paste_key).set_value(
        "# Notes\n\nThe wifi password for home lab is maple-42.\n"
    ).run()
    at.button("knowledge_paste_btn_kb-demo").click().run()
    assert not at.exception, at.exception
    saved = list((data / "personas" / "kb-demo" / "knowledge").glob("*.md"))
    assert saved, "expected pasted knowledge file on disk"
