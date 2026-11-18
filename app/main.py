"""Streamlit chat shell for persona-bot (Phase 1b)."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import cast

import streamlit as st

from app.budget import fit_prompt
from app.chat_store import ChatStore
from app.config import clear_settings_cache, get_settings
from app.errors import AppError, KnowledgeNotFoundError, MissingApiKeyError, MissingModelConfigError
from app.i18n import t
from app.llm import LlmClient, StreamResult
from app.logging_setup import setup_logging
from app.prompt import build_messages, not_found_reply_th, strip_context_from_content
from app.security import password_ok
from app.services import chat_db_path, load_available_personas, usage_path
from app.ui.errors import error_from_exception, format_error_card
from app.ui.theme import custom_css
from app.usage import UsageTracker


def _init_state() -> None:
    ss = st.session_state
    ss.setdefault("api_key", "")
    ss.setdefault("password_ok", False)
    ss.setdefault("persona_id", "study-buddy")
    ss.setdefault("thread_id", "")
    ss.setdefault("privacy_ack", False)
    ss.setdefault("last_error", None)


def _store() -> ChatStore:
    if "chat_store" not in st.session_state:
        st.session_state.chat_store = ChatStore(chat_db_path())
    return cast(ChatStore, st.session_state.chat_store)


def _usage() -> UsageTracker:
    if "usage_tracker" not in st.session_state:
        st.session_state.usage_tracker = UsageTracker(usage_path())
    return cast(UsageTracker, st.session_state.usage_tracker)


def _render_error(exc: BaseException) -> None:
    info = error_from_exception(exc)
    title, hint = format_error_card(info)
    hint_html = f'<div class="hint">{hint}</div>' if hint else ""
    st.markdown(
        f'<div class="pb-error"><strong>{title}</strong>{hint_html}</div>',
        unsafe_allow_html=True,
    )


def _ensure_thread(store: ChatStore, persona_id: str) -> str:
    thread_id = cast(str, st.session_state.thread_id)
    if thread_id:
        existing = store.get_thread(thread_id)
        if existing and existing.persona_id == persona_id:
            return thread_id
    thread = store.create_thread(persona_id=persona_id, title=t("action.new_chat"))
    st.session_state.thread_id = thread.id
    return thread.id


def _sidebar(personas: list) -> None:
    settings = get_settings()
    store = _store()
    usage = _usage()
    by_id = {p.id: p for p in personas}

    st.sidebar.markdown(f"### {t('app.title')}")
    st.sidebar.caption(t("app.tagline"))

    if settings.app_password and not st.session_state.password_ok:
        pwd = st.sidebar.text_input(t("label.password"), type="password")
        if st.sidebar.button(t("action.save_key"), key="pwd_btn"):
            if password_ok(settings.app_password, pwd):
                st.session_state.password_ok = True
                st.rerun()
            st.sidebar.error(t("error.app_password"))
        return

    persona_ids = [p.id for p in personas]
    labels = {p.id: p.name for p in personas}
    current = st.session_state.persona_id
    if current not in persona_ids and persona_ids:
        current = persona_ids[0]
        st.session_state.persona_id = current
    selected = st.sidebar.selectbox(
        t("label.persona"),
        options=persona_ids,
        format_func=lambda i: labels.get(i, i),
        index=persona_ids.index(current) if current in persona_ids else 0,
    )
    if selected != st.session_state.persona_id:
        st.session_state.persona_id = selected
        st.session_state.thread_id = ""
        st.rerun()

    persona = by_id.get(st.session_state.persona_id)
    if persona:
        st.sidebar.caption(persona.description)

    st.sidebar.divider()
    c1, c2 = st.sidebar.columns(2)
    if c1.button(t("action.new_chat"), use_container_width=True):
        thread = store.create_thread(
            persona_id=st.session_state.persona_id, title=t("action.new_chat")
        )
        st.session_state.thread_id = thread.id
        st.rerun()
    if c2.button(t("action.clear_chat"), use_container_width=True):
        tid = _ensure_thread(store, st.session_state.persona_id)
        store.clear_thread_messages(tid)
        st.rerun()

    threads = store.list_threads(persona_id=st.session_state.persona_id)
    if threads:
        thread_ids = [th.id for th in threads]
        titles = {th.id: th.title for th in threads}
        tid = st.session_state.thread_id or thread_ids[0]
        if tid not in thread_ids:
            tid = thread_ids[0]

        def _thread_label(thread_key: str) -> str:
            return titles.get(thread_key, thread_key)[:40]

        chosen = st.sidebar.selectbox(
            t("label.thread"),
            options=thread_ids,
            format_func=_thread_label,
            index=thread_ids.index(tid),
        )
        if chosen is not None:
            st.session_state.thread_id = str(chosen)

    st.sidebar.divider()
    snap = usage.snapshot
    st.sidebar.markdown(f"**{t('label.usage_today')}**")
    st.sidebar.markdown(
        f'<div class="pb-meta">{t("label.tokens")}: {snap.total_tokens} · '
        f"n={snap.request_count}</div>",
        unsafe_allow_html=True,
    )

    with st.sidebar.expander(t("label.advanced")):
        key_val = st.text_input(
            t("label.api_key"),
            value=st.session_state.api_key,
            type="password",
            help=t("error.hint.add_api_key"),
        )
        if st.button(t("action.save_key"), key="save_key_btn"):
            st.session_state.api_key = key_val.strip()
            st.rerun()
        if st.button(t("action.forget_key"), key="forget_key_btn"):
            st.session_state.api_key = ""
            st.rerun()
        st.caption(t("privacy.notice"))


def _welcome() -> None:
    st.markdown(
        f"""
<div class="pb-welcome">
  <h1>{t("app.title")}</h1>
  <p>{t("app.welcome")}</p>
  <p>{t("app.welcome.body")}</p>
  <ol>
    <li>{t("app.onboarding.step1")}</li>
    <li>{t("app.onboarding.step2")}</li>
    <li>{t("app.onboarding.step3")}</li>
  </ol>
</div>
""",
        unsafe_allow_html=True,
    )
    key_val = st.text_input(t("label.api_key"), type="password", key="welcome_key")
    if st.button(t("action.save_key"), key="welcome_save"):
        st.session_state.api_key = key_val.strip()
        st.rerun()


def _render_meta(result: StreamResult) -> None:
    badge_cls = "pb-badge fallback" if result.used_fallback else "pb-badge"
    label = t("label.fallback") if result.used_fallback else t("label.model")
    st.markdown(
        f'<span class="{badge_cls}">{label}: {result.model or "-"}</span>'
        f'<span class="pb-badge">{t("label.tokens")}: '
        f"{result.usage.total_tokens}</span>",
        unsafe_allow_html=True,
    )


def _handle_user_message(user_text: str, personas: list) -> None:
    settings = get_settings()
    store = _store()
    usage = _usage()
    by_id = {p.id: p for p in personas}
    persona = by_id[st.session_state.persona_id]
    thread_id = _ensure_thread(store, persona.id)

    store.add_message(thread_id=thread_id, role="user", content=user_text)
    current_thread = store.get_thread(thread_id)
    if current_thread is not None and current_thread.title == t("action.new_chat"):
        store.touch_thread(thread_id, title=user_text[:40])

    history = store.history_for_prompt(thread_id)
    # Drop the just-added user message from history for build_messages (it passes user_text).
    history = history[:-1]

    with st.chat_message("user"):
        st.markdown(user_text)

    # Phase 1b: no RAG yet — empty context. Strict personas short-circuit cleanly.
    try:
        messages = build_messages(
            persona,
            history=history,
            user_text=user_text,
            context_chunks=[],
        )
    except KnowledgeNotFoundError as exc:
        reply = not_found_reply_th()
        store.add_message(thread_id=thread_id, role="assistant", content=reply)
        with st.chat_message("assistant"):
            st.markdown(reply)
            _render_error(exc)
        return

    messages = fit_prompt(messages)
    assistant_id = str(uuid.uuid4())
    store.add_message(
        thread_id=thread_id,
        role="assistant",
        content="",
        partial=True,
        message_id=assistant_id,
    )

    api_key = st.session_state.api_key or settings.groq_api_key
    result = StreamResult()
    try:
        if not api_key:
            raise MissingApiKeyError()
        if not settings.groq_model_primary.strip():
            raise MissingModelConfigError()
        client = LlmClient(settings=settings, api_key=api_key)
        with st.chat_message("assistant"):
            placeholder = st.empty()
            parts: list[str] = []
            for chunk in client.stream_chat(
                messages,
                temperature=persona.config.temperature,
                max_tokens=persona.config.max_tokens,
                result=result,
            ):
                parts.append(chunk)
                text = "".join(parts)
                placeholder.markdown(text)
                # Persist partials so Stop/rerun never loses text (F9).
                store.update_message(assistant_id, content=text, partial=True)
            final_text = "".join(parts) or result.text
            store.update_message(
                assistant_id,
                content=final_text,
                partial=False,
                meta={
                    "model": result.model,
                    "used_fallback": result.used_fallback,
                    "tokens": result.usage.total_tokens,
                },
            )
            placeholder.markdown(final_text)
            _render_meta(result)
        usage.record(result)
    except AppError as exc:
        store.update_message(
            assistant_id,
            content=result.text or "",
            partial=bool(result.text),
        )
        with st.chat_message("assistant"):
            if result.text:
                st.markdown(result.text)
                st.caption(t("status.partial_saved"))
            _render_error(exc)
    except Exception as exc:  # noqa: BLE001 — show Thai card, never traceback
        store.update_message(
            assistant_id,
            content=result.text or "",
            partial=bool(result.text),
        )
        with st.chat_message("assistant"):
            if result.text:
                st.markdown(result.text)
                st.caption(t("status.partial_saved"))
            _render_error(exc)


def run() -> None:
    st.set_page_config(
        page_title=t("app.title"),
        layout="centered",
        initial_sidebar_state="expanded",
    )
    st.markdown(custom_css(), unsafe_allow_html=True)
    _init_state()

    clear_settings_cache()
    settings = get_settings()
    setup_logging(settings.log_level, api_key=st.session_state.api_key or settings.groq_api_key)

    try:
        personas = load_available_personas(settings)
    except Exception as exc:  # noqa: BLE001
        _render_error(exc)
        return
    if not personas:
        st.warning(t("error.persona_load"))
        return

    _sidebar(personas)

    settings = get_settings()
    if settings.app_password and not st.session_state.password_ok:
        st.info(t("error.hint.password"))
        return

    has_key = bool(st.session_state.api_key or settings.groq_api_key)
    if not has_key:
        _welcome()
        return

    if not st.session_state.privacy_ack:
        st.info(t("privacy.notice"))
        if st.button(t("action.got_it"), key="privacy_ack_btn"):
            st.session_state.privacy_ack = True
            # Persist flag under data/
            flag = Path(settings.data_dir) / "privacy_ack"
            flag.parent.mkdir(parents=True, exist_ok=True)
            flag.write_text("1", encoding="utf-8")
            st.rerun()
        # Allow chat after ack file exists from a prior session
        flag = Path(settings.data_dir) / "privacy_ack"
        if flag.exists():
            st.session_state.privacy_ack = True
        else:
            return

    store = _store()
    thread_id = _ensure_thread(store, st.session_state.persona_id)
    messages = store.list_messages(thread_id)
    if not messages:
        st.caption(t("chat.empty"))
    for msg in messages:
        if msg.role not in {"user", "assistant"}:
            continue
        with st.chat_message(msg.role):
            content = strip_context_from_content(msg.content) if msg.role == "user" else msg.content
            st.markdown(content or "…")
            if msg.partial:
                st.caption(t("status.partial_saved"))
            if msg.meta and msg.role == "assistant":
                fake = StreamResult(
                    model=str(msg.meta.get("model") or ""),
                    used_fallback=bool(msg.meta.get("used_fallback")),
                )
                fake.usage.total_tokens = int(msg.meta.get("tokens") or 0)
                _render_meta(fake)

    prompt = st.chat_input(t("chat.placeholder"))
    if prompt:
        _handle_user_message(prompt.strip(), personas)


def main() -> None:
    run()


if __name__ == "__main__":
    main()
