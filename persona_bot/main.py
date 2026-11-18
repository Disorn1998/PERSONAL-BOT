"""Streamlit chat shell for persona-bot (Phase 1b–4)."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any, cast

import streamlit as st

from persona_bot.backup import create_backup, delete_all_data, restore_backup
from persona_bot.budget import fit_prompt
from persona_bot.chat_store import ChatStore
from persona_bot.config import clear_settings_cache, get_settings
from persona_bot.errors import (
    AppError,
    KnowledgeNotFoundError,
    MissingApiKeyError,
    MissingModelConfigError,
)
from persona_bot.healthcheck import run_health_check
from persona_bot.i18n import SUPPORTED_LOCALES, get_locale, set_locale, t
from persona_bot.keyring_store import delete_api_key, load_api_key, remember_enabled, save_api_key
from persona_bot.llm import LlmClient, StreamResult
from persona_bot.logging_setup import setup_logging
from persona_bot.persona_pack_io import (
    delete_user_persona,
    export_persona_zip,
    import_persona_zip,
    preview_persona_zip,
)
from persona_bot.prompt import build_messages, not_found_reply_th, strip_context_from_content
from persona_bot.rag.citations import format_sources_markdown, validate_citations
from persona_bot.rag.embeddings import FakeEmbedder
from persona_bot.rag.prompt_inspector import inspect_messages
from persona_bot.rag.retrieve import retrieve
from persona_bot.rag.runtime import build_embedder, get_or_build_store
from persona_bot.rag.search_lab import run_search_lab
from persona_bot.rag.store import VectorStore
from persona_bot.security import password_ok
from persona_bot.services import (
    chat_db_path,
    is_user_persona,
    load_available_personas,
    persona_dir_for,
    usage_path,
)
from persona_bot.ui.errors import error_from_exception, format_error_card
from persona_bot.ui.theme import custom_css
from persona_bot.usage import UsageTracker
from persona_bot.versioning import ensure_data_version, get_app_version


def _init_state() -> None:
    ss = st.session_state
    ss.setdefault("api_key", "")
    ss.setdefault("password_ok", False)
    ss.setdefault("persona_id", "study-buddy")
    ss.setdefault("thread_id", "")
    ss.setdefault("privacy_ack", False)
    ss.setdefault("last_error", None)
    ss.setdefault("wizard_done", False)
    ss.setdefault("locale", "th")
    ss.setdefault("import_preview", None)
    ss.setdefault("import_bytes", None)
    ss.setdefault("confirm_delete_all", False)
    ss.setdefault("confirm_delete_persona", False)
    set_locale(str(ss["locale"]))
    if not ss["api_key"] and remember_enabled():
        stored = load_api_key()
        if stored:
            ss["api_key"] = stored


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


def _wipe_persona_index(persona_id: str) -> None:
    settings = get_settings()
    # Best-effort wipe without requiring a live ONNX embedder.
    VectorStore(
        data_dir=settings.data_dir,
        embedder=FakeEmbedder(dim=8, model_name="fake:wipe"),
    ).wipe_persona(persona_id)


def _sidebar(personas: list) -> None:
    settings = get_settings()
    store = _store()
    usage = _usage()
    by_id = {p.id: p for p in personas}

    st.sidebar.markdown(f"### {t('app.title')}")
    st.sidebar.caption(t("app.tagline"))

    lang = st.sidebar.selectbox(
        t("label.language"),
        options=list(SUPPORTED_LOCALES),
        index=list(SUPPORTED_LOCALES).index(get_locale())
        if get_locale() in SUPPORTED_LOCALES
        else 0,
        format_func=lambda code: "ไทย" if code == "th" else "English",
        key="locale_select",
    )
    if lang != st.session_state.locale:
        st.session_state.locale = lang
        set_locale(lang)
        st.rerun()
    else:
        set_locale(str(st.session_state.locale))

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
        icon = f"{persona.icon} " if persona.icon else ""
        st.sidebar.caption(f"{icon}{persona.description}")

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

    if persona is not None:
        with st.sidebar.expander(t("label.knowledge"), expanded=False):
            try:
                cache_key = f"rag::{persona.id}::{persona.config.embedding_preset}"
                if cache_key not in st.session_state:
                    embedder = build_embedder(settings, persona=persona, fake=False)
                    st.session_state[cache_key] = {
                        "embedder": embedder,
                        "bundle": get_or_build_store(
                            settings=settings,
                            persona=persona,
                            embedder=embedder,
                            force=False,
                        ),
                    }
                embedder = st.session_state[cache_key]["embedder"]
                vstore, manifest, kdir, health = st.session_state[cache_key]["bundle"]
                st.caption(f"{t('label.knowledge_health')}: {health.file_count} files")
                st.caption(
                    t("status.index_ready")
                    if not health.needs_rebuild
                    else ", ".join(health.notes) or t("label.rebuild_index")
                )
                st.caption(f"chunks={manifest.chunk_count}")
                st.caption(str(kdir))
                if st.button(t("label.rebuild_index"), key="rebuild_idx"):
                    st.session_state[cache_key]["bundle"] = get_or_build_store(
                        settings=settings,
                        persona=persona,
                        embedder=embedder,
                        force=True,
                    )
                    st.success(t("status.index_rebuilt"))
                    st.rerun()
                q = st.text_input(t("label.search_query"), key="search_lab_q")
                if st.button(t("action.run_search"), key="search_lab_go") and q.strip():
                    hits = run_search_lab(
                        vstore,
                        persona_id=persona.id,
                        query=q.strip(),
                        top_k=persona.config.resolved_top_k(),
                        min_score=0.0,
                    )
                    for hit in hits:
                        st.write(
                            f"{float(hit['score']):.3f} · {hit.get('source')} — "
                            f"{str(hit.get('text', ''))[:120]}"
                        )
            except Exception as exc:  # noqa: BLE001
                _render_error(exc)

    st.sidebar.caption(f"{t('label.version')}: {get_app_version()}")

    with st.sidebar.expander(t("label.data_tools"), expanded=False):
        # Export current persona (examples or user packs).
        pack_dir = persona_dir_for(st.session_state.persona_id, settings)
        if pack_dir is not None and st.button(t("action.export_persona"), key="export_persona_btn"):
            try:
                payload = export_persona_zip(
                    pack_dir,
                    api_key=st.session_state.api_key or settings.groq_api_key,
                )
                st.download_button(
                    label=f"{st.session_state.persona_id}.zip",
                    data=payload,
                    file_name=f"{st.session_state.persona_id}.zip",
                    mime="application/zip",
                    key="export_download",
                )
                st.success(t("status.export_ok"))
            except Exception as exc:  # noqa: BLE001
                _render_error(exc)

        uploaded = st.file_uploader(
            t("action.import_persona"),
            type=["zip"],
            key="import_persona_upload",
        )
        conflict = st.selectbox(
            t("label.conflict_policy"),
            options=["reject", "rename", "overwrite"],
            format_func=lambda v: t(f"label.conflict.{v}"),
            key="import_conflict",
        )
        if uploaded is not None and st.button(t("action.preview_import"), key="preview_import_btn"):
            try:
                raw = uploaded.getvalue()
                st.session_state.import_bytes = raw
                st.session_state.import_preview = preview_persona_zip(
                    raw,
                    personas_dir=settings.personas_dir,
                ).to_dict()
            except Exception as exc:  # noqa: BLE001
                st.session_state.import_preview = None
                st.session_state.import_bytes = None
                _render_error(exc)
        if st.session_state.import_preview:
            st.markdown(f"**{t('label.import_preview')}**")
            st.json(st.session_state.import_preview)
            if st.button(t("action.confirm_import"), key="confirm_import_btn"):
                try:
                    pack = import_persona_zip(
                        cast(bytes, st.session_state.import_bytes),
                        personas_dir=settings.personas_dir,
                        conflict=cast(Any, conflict),
                    )
                    st.session_state.persona_id = pack.id
                    st.session_state.import_preview = None
                    st.session_state.import_bytes = None
                    st.success(t("status.import_ok"))
                    st.rerun()
                except Exception as exc:  # noqa: BLE001
                    _render_error(exc)

        if is_user_persona(st.session_state.persona_id, settings):
            st.caption(t("warn.delete_persona"))
            if st.button(t("action.delete_persona"), key="delete_persona_btn"):
                st.session_state.confirm_delete_persona = True
            if st.session_state.confirm_delete_persona and st.button(
                t("action.confirm_delete"), key="confirm_delete_persona_btn"
            ):
                try:
                    pid = str(st.session_state.persona_id)
                    delete_user_persona(personas_dir=settings.personas_dir, persona_id=pid)
                    _wipe_persona_index(pid)
                    st.session_state.persona_id = "study-buddy"
                    st.session_state.thread_id = ""
                    st.session_state.confirm_delete_persona = False
                    st.success(t("status.delete_persona_ok"))
                    st.rerun()
                except Exception as exc:  # noqa: BLE001
                    _render_error(exc)
        else:
            st.caption(t("status.example_persona_readonly"))

        if st.button(t("action.backup"), key="backup_btn"):
            try:
                payload, summary = create_backup(
                    settings.data_dir,
                    api_key=st.session_state.api_key or settings.groq_api_key,
                )
                st.download_button(
                    label="persona-bot-backup.zip",
                    data=payload,
                    file_name="persona-bot-backup.zip",
                    mime="application/zip",
                    key="backup_download",
                )
                st.success(f"{t('status.backup_ok')} ({summary.member_count})")
            except Exception as exc:  # noqa: BLE001
                _render_error(exc)

        restore_file = st.file_uploader(
            t("action.restore"),
            type=["zip"],
            key="restore_upload",
        )
        if restore_file is not None and st.button(t("action.restore"), key="restore_btn"):
            try:
                restore_backup(restore_file.getvalue(), data_dir=settings.data_dir)
                st.session_state.chat_store = ChatStore(chat_db_path())
                st.session_state.usage_tracker = UsageTracker(usage_path())
                st.session_state.thread_id = ""
                st.success(t("status.restore_ok"))
                st.rerun()
            except Exception as exc:  # noqa: BLE001
                _render_error(exc)

        st.warning(t("warn.delete_all"))
        if st.button(t("action.delete_all_data"), key="delete_all_btn"):
            st.session_state.confirm_delete_all = True
        if st.session_state.confirm_delete_all and st.button(
            t("action.confirm_delete"), key="confirm_delete_all_btn"
        ):
            try:
                delete_all_data(settings.data_dir, keep_version=True)
                st.session_state.chat_store = ChatStore(chat_db_path())
                st.session_state.usage_tracker = UsageTracker(usage_path())
                st.session_state.thread_id = ""
                st.session_state.confirm_delete_all = False
                st.success(t("status.delete_all_ok"))
                st.rerun()
            except Exception as exc:  # noqa: BLE001
                _render_error(exc)

    with st.sidebar.expander(t("label.health")):
        report = run_health_check(
            settings,
            api_key=st.session_state.api_key or settings.groq_api_key,
        )
        st.write(t("status.health_ok") if report.ok else t("status.health_issues"))
        st.json(report.to_dict())

    with st.sidebar.expander(t("label.advanced")):
        key_val = st.text_input(
            t("label.api_key"),
            value=st.session_state.api_key,
            type="password",
            help=t("error.hint.add_api_key"),
        )
        remember = st.checkbox(
            t("label.remember_key"),
            value=remember_enabled(),
            key="remember_key_box",
        )
        if st.button(t("action.save_key"), key="save_key_btn"):
            st.session_state.api_key = key_val.strip()
            if remember and key_val.strip():
                save_api_key(key_val.strip())
            st.rerun()
        if st.button(t("action.forget_key"), key="forget_key_btn"):
            st.session_state.api_key = ""
            delete_api_key()
            st.rerun()
        st.caption(t("privacy.notice"))


def _welcome() -> None:
    settings = get_settings()
    report = run_health_check(
        settings,
        api_key=st.session_state.api_key or settings.groq_api_key,
    )
    st.markdown(
        f"""
<div class="pb-welcome">
  <h1>{t("app.title")}</h1>
  <p>{t("label.first_run")}</p>
  <p>{t("first_run.body")}</p>
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
    st.info(t("status.health_ok") if report.ok else t("status.health_issues"))
    with st.expander(t("label.health")):
        st.json(report.to_dict())
    key_val = st.text_input(t("label.api_key"), type="password", key="welcome_key")
    remember = st.checkbox(
        t("label.remember_key"),
        value=remember_enabled(),
        key="welcome_remember",
    )
    if st.button(t("action.save_key"), key="welcome_save"):
        st.session_state.api_key = key_val.strip()
        if remember and key_val.strip():
            save_api_key(key_val.strip())
        st.session_state.wizard_done = True
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

    context_chunks: list[dict[str, Any]] = []
    try:
        cache_key = f"rag::{persona.id}::{persona.config.embedding_preset}"
        if cache_key not in st.session_state:
            embedder = build_embedder(settings, persona=persona, fake=False)
            st.session_state[cache_key] = {
                "embedder": embedder,
                "bundle": get_or_build_store(
                    settings=settings,
                    persona=persona,
                    embedder=embedder,
                    force=False,
                ),
            }
        vstore = st.session_state[cache_key]["bundle"][0]
        context_chunks = retrieve(
            vstore,
            persona_id=persona.id,
            latest=user_text,
            history=history,
            top_k=persona.config.resolved_top_k(),
            min_score=persona.config.resolved_min_score(),
        )
    except AppError as exc:
        with st.chat_message("assistant"):
            _render_error(exc)
        return
    except Exception as exc:  # noqa: BLE001
        with st.chat_message("assistant"):
            _render_error(exc)
        return

    try:
        messages = build_messages(
            persona,
            history=history,
            user_text=user_text,
            context_chunks=context_chunks,
            min_score=persona.config.resolved_min_score(),
        )
    except KnowledgeNotFoundError as exc:
        # Strict + no passing chunks → no LLM call (DoD 2).
        reply = not_found_reply_th()
        store.add_message(thread_id=thread_id, role="assistant", content=reply)
        with st.chat_message("assistant"):
            st.markdown(reply)
            _render_error(exc)
        return

    messages = fit_prompt(messages)
    inspector = inspect_messages(messages)
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
            cite = validate_citations(final_text, context_chunks)
            store.update_message(
                assistant_id,
                content=final_text,
                partial=False,
                meta={
                    "model": result.model,
                    "used_fallback": result.used_fallback,
                    "tokens": result.usage.total_tokens,
                    "sources": [
                        {"source": c.get("source"), "score": c.get("score")} for c in context_chunks
                    ],
                    "citations": cite,
                    "prompt_inspector": inspector,
                },
            )
            placeholder.markdown(final_text)
            _render_meta(result)
            if context_chunks:
                with st.expander(t("label.sources")):
                    st.markdown(format_sources_markdown(context_chunks))
            if not cite["ok"]:
                st.warning(t("status.citations_invalid"))
            with st.expander(t("label.prompt_inspector")):
                st.json(inspector)
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
    ensure_data_version(settings.data_dir)
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
    health = run_health_check(
        settings,
        api_key=st.session_state.api_key or settings.groq_api_key,
    )
    if not has_key or (not health.models_configured and not st.session_state.wizard_done):
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
    persona = next((p for p in personas if p.id == st.session_state.persona_id), None)
    if not messages:
        if persona and persona.greeting:
            icon = f"{persona.icon} " if persona.icon else ""
            st.info(f"{icon}{persona.greeting}")
        else:
            st.caption(t("chat.empty"))
        if persona and persona.starter_questions:
            st.caption(t("label.starter_questions"))
            cols = st.columns(min(3, len(persona.starter_questions)))
            for idx, question in enumerate(persona.starter_questions[:3]):
                if cols[idx].button(question, key=f"starter_{persona.id}_{idx}"):
                    _handle_user_message(question.strip(), personas)
                    return
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
