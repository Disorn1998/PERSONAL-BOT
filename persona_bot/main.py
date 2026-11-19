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
    MissingModelConfigError,
)
from persona_bot.healthcheck import run_health_check
from persona_bot.i18n import SUPPORTED_LOCALES, get_locale, set_locale, t
from persona_bot.keyring_store import (
    delete_api_key,
    env_remember_enabled,
    load_api_key,
    remember_enabled,
    remember_status_key,
    save_api_key,
    set_ui_remember_preference,
)
from persona_bot.knowledge_answer import (
    resolve_knowledge_only_reply,
    should_fallback_to_knowledge_only,
)
from persona_bot.llm import LlmClient, StreamResult
from persona_bot.logging_setup import setup_logging
from persona_bot.persona import PersonaPack
from persona_bot.persona_editor import (
    add_knowledge_bytes,
    add_knowledge_paste,
    build_persona_config,
    create_user_persona,
    duplicate_persona_to_user,
    index_status_key,
    save_user_persona,
)
from persona_bot.persona_pack_io import (
    delete_user_persona,
    export_persona_zip,
    import_persona_zip,
    preview_persona_zip,
)
from persona_bot.prompt import build_messages, strip_context_from_content
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
from persona_bot.ui.assets import icon_path, welcome_hero_path
from persona_bot.ui.errors import error_from_exception, format_error_card
from persona_bot.ui.theme import custom_css
from persona_bot.ui.wizard import (
    EntryPath,
    clear_entry_path,
    load_entry_path,
    overwrite_confirm_required,
    progress_markup,
    save_entry_path,
    wizard_step,
)
from persona_bot.usage import UsageTracker, format_token_usage
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
    ss.setdefault("confirm_clear_chat", False)
    ss.setdefault("confirm_overwrite_import", False)
    ss.setdefault("remember_loaded", False)
    ss.setdefault("knowledge_only_mode", False)
    ss.setdefault("show_prompt_inspector", False)
    ss.setdefault("entry_path", None)
    ss.setdefault("welcome_stage", "gate")  # gate | api | knowledge
    set_locale(str(ss["locale"]))
    if not ss["api_key"] and remember_enabled():
        stored = load_api_key()
        if stored:
            ss["api_key"] = stored
            ss["remember_loaded"] = True


def _apply_entry_path(entry: EntryPath, *, finish: bool = False) -> None:
    """Set session path; persist + mark wizard done only when finishing."""
    st.session_state.entry_path = entry
    st.session_state.welcome_stage = entry
    # Keep Settings radio in sync so it cannot override the welcome choice.
    st.session_state.settings_entry_path = entry
    if entry == "knowledge":
        st.session_state.knowledge_only_mode = True
    else:
        st.session_state.knowledge_only_mode = False
    if finish:
        save_entry_path(get_settings().data_dir, entry)
        st.session_state.wizard_done = True


def _restore_entry_path_from_disk() -> None:
    """Hydrate welcome path from data/ so returning users skip the gate."""
    if st.session_state.get("entry_path"):
        return
    settings = get_settings()
    stored = load_entry_path(settings.data_dir)
    if stored is None:
        return
    st.session_state.entry_path = stored
    st.session_state.welcome_stage = stored
    if stored == "knowledge":
        st.session_state.knowledge_only_mode = True
    # Prior choice counts as wizard completion for the gate.
    st.session_state.wizard_done = True


def _answer_mode_label(mode: str) -> str:
    key = f"label.answer_mode.{mode}"
    labeled = t(key)
    return labeled if labeled != key else mode


def _rebuild_persona_index(persona: PersonaPack) -> None:
    """Force-rebuild the local index and refresh the session RAG cache."""
    settings = get_settings()
    cache_key = f"rag::{persona.id}::{persona.config.embedding_preset}"
    embedder = build_embedder(settings, persona=persona, fake=False)
    bundle = get_or_build_store(
        settings=settings,
        persona=persona,
        embedder=embedder,
        force=True,
    )
    st.session_state[cache_key] = {"embedder": embedder, "bundle": bundle}


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
    hint_html = ""
    if hint:
        # Preserve newlines from retry-after / reset hints.
        safe = hint.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        safe = safe.replace("\n", "<br/>")
        hint_html = f'<div class="hint">{safe}</div>'
    st.markdown(
        f'<div class="pb-error"><strong>{title}</strong>{hint_html}</div>',
        unsafe_allow_html=True,
    )


def _apply_remember_choice(remember: bool, key_val: str) -> None:
    """Save or skip keyring based on env **or** UI checkbox; persist checkbox opt-in."""
    key = key_val.strip()
    st.session_state.api_key = key
    # Env alone enables remember; checkbox also enables and persists for next load.
    should_remember = bool(remember) or env_remember_enabled()
    set_ui_remember_preference(bool(remember) or env_remember_enabled())
    if should_remember and key:
        save_api_key(key)
        st.session_state.remember_loaded = True
    elif not remember and not env_remember_enabled():
        # User turned opt-in off and env is off — do not keep a stale keyring secret.
        delete_api_key()
        st.session_state.remember_loaded = False


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


def _clear_rag_cache(persona_id: str | None = None) -> None:
    """Drop cached embedder/index bundles so the next chat rebuilds cleanly."""
    prefix = f"rag::{persona_id}::" if persona_id else "rag::"
    for key in list(st.session_state.keys()):
        if isinstance(key, str) and key.startswith(prefix):
            del st.session_state[key]


def _optional_int(raw: str) -> int | None:
    text = raw.strip()
    if not text:
        return None
    return int(text)


def _optional_float(raw: str) -> float | None:
    text = raw.strip()
    if not text:
        return None
    return float(text)


def _render_persona_editor(persona: PersonaPack | None) -> None:
    """Create / edit user packs; examples stay read-only with Duplicate.

    Uses ``st.expander`` (not ``st.sidebar.expander``) so it nests under
    「ตั้งค่าเพิ่มเติม」 instead of floating as a sibling sidebar block.
    """
    settings = get_settings()
    with st.expander(t("label.persona_editor"), expanded=False):
        if persona is not None and st.button(
            t("action.duplicate_persona"),
            key="duplicate_persona_btn",
            use_container_width=True,
        ):
            try:
                pack = duplicate_persona_to_user(settings=settings, source_id=persona.id)
                st.session_state.persona_id = pack.id
                st.session_state.thread_id = ""
                _clear_rag_cache(pack.id)
                st.success(t("status.persona_duplicated"))
                st.rerun()
            except Exception as exc:  # noqa: BLE001
                _render_error(exc)

        user_pack = (
            is_user_persona(st.session_state.persona_id, settings) if persona is not None else False
        )
        if persona is not None and not user_pack:
            st.caption(t("status.example_edit_readonly"))

        if persona is not None and user_pack:
            st.markdown(f"**{t('label.persona_editor')}**")
            name = st.text_input(
                t("label.persona_name"),
                value=persona.name,
                key=f"edit_name_{persona.id}",
            )
            description = st.text_area(
                t("label.persona_description"),
                value=persona.description,
                key=f"edit_desc_{persona.id}",
                height=68,
            )
            system_prompt = st.text_area(
                t("label.system_prompt"),
                value=persona.system_prompt,
                key=f"edit_prompt_{persona.id}",
                height=140,
            )
            answer_mode = st.selectbox(
                t("label.answer_mode"),
                options=["strict", "balanced", "open"],
                index=["strict", "balanced", "open"].index(persona.config.answer_mode),
                format_func=_answer_mode_label,
                key=f"edit_mode_{persona.id}",
            )
            temperature = float(persona.config.temperature)
            max_tokens = int(persona.config.max_tokens)
            embedding_preset = persona.config.embedding_preset
            top_k_raw = "" if persona.config.top_k is None else str(persona.config.top_k)
            min_score_raw = (
                "" if persona.config.min_score is None else str(persona.config.min_score)
            )
            chunk_raw = (
                "" if persona.config.chunk_chars is None else str(persona.config.chunk_chars)
            )
            with st.expander(t("label.advanced"), expanded=False):
                st.caption(t("label.lab_tuning"))
                temperature = st.slider(
                    t("label.temperature"),
                    min_value=0.0,
                    max_value=2.0,
                    value=float(persona.config.temperature),
                    step=0.05,
                    key=f"edit_temp_{persona.id}",
                )
                max_tokens = int(
                    st.number_input(
                        t("label.max_tokens"),
                        min_value=16,
                        max_value=8192,
                        value=int(persona.config.max_tokens),
                        step=64,
                        key=f"edit_max_tokens_{persona.id}",
                    )
                )
                embedding_preset = st.selectbox(
                    t("label.embedding_preset"),
                    options=["lite", "multilingual", "quality"],
                    index=["lite", "multilingual", "quality"].index(
                        persona.config.embedding_preset
                    ),
                    key=f"edit_preset_{persona.id}",
                )
                st.caption(t("label.optional_override"))
                top_k_raw = st.text_input(
                    t("label.top_k"),
                    value="" if persona.config.top_k is None else str(persona.config.top_k),
                    key=f"edit_top_k_{persona.id}",
                )
                min_score_raw = st.text_input(
                    t("label.min_score"),
                    value=(
                        "" if persona.config.min_score is None else str(persona.config.min_score)
                    ),
                    key=f"edit_min_score_{persona.id}",
                )
                chunk_raw = st.text_input(
                    t("label.chunk_chars"),
                    value=(
                        ""
                        if persona.config.chunk_chars is None
                        else str(persona.config.chunk_chars)
                    ),
                    key=f"edit_chunk_{persona.id}",
                )
            if st.button(t("action.save_persona"), key=f"save_persona_{persona.id}"):
                try:
                    updated = persona.model_copy(
                        update={
                            "name": name.strip(),
                            "description": description.strip(),
                            "system_prompt": system_prompt.strip(),
                            "config": build_persona_config(
                                answer_mode=cast(Any, answer_mode),
                                temperature=float(temperature),
                                max_tokens=int(max_tokens),
                                embedding_preset=cast(Any, embedding_preset),
                                top_k=_optional_int(top_k_raw),
                                min_score=_optional_float(min_score_raw),
                                chunk_chars=_optional_int(chunk_raw),
                            ),
                        }
                    )
                    save_user_persona(personas_dir=settings.personas_dir, pack=updated)
                    _clear_rag_cache(persona.id)
                    st.success(t("status.persona_saved"))
                    st.rerun()
                except Exception as exc:  # noqa: BLE001
                    _render_error(exc)

        st.divider()
        st.markdown(f"**{t('label.persona_create')}**")
        new_id = st.text_input(t("label.persona_id"), key="create_persona_id")
        new_name = st.text_input(t("label.persona_name"), key="create_persona_name")
        new_desc = st.text_area(
            t("label.persona_description"),
            key="create_persona_desc",
            height=68,
        )
        new_prompt = st.text_area(
            t("label.system_prompt"),
            key="create_persona_prompt",
            height=120,
            value="คุณเป็นผู้ช่วยที่ตอบจากคลังความรู้ของเพอร์โซนานี้",
        )
        new_mode = st.selectbox(
            t("label.answer_mode"),
            options=["strict", "balanced", "open"],
            index=1,
            format_func=_answer_mode_label,
            key="create_persona_mode",
        )
        new_temp = 0.2
        new_max_tokens = 1024
        new_preset = "lite"
        new_top_k = ""
        new_min_score = ""
        new_chunk = ""
        with st.expander(t("label.advanced"), expanded=False):
            st.caption(t("label.lab_tuning"))
            new_temp = st.slider(
                t("label.temperature"),
                min_value=0.0,
                max_value=2.0,
                value=0.2,
                step=0.05,
                key="create_persona_temp",
            )
            new_max_tokens = int(
                st.number_input(
                    t("label.max_tokens"),
                    min_value=16,
                    max_value=8192,
                    value=1024,
                    step=64,
                    key="create_persona_max_tokens",
                )
            )
            new_preset = st.selectbox(
                t("label.embedding_preset"),
                options=["lite", "multilingual", "quality"],
                index=0,
                key="create_persona_preset",
            )
            st.caption(t("label.optional_override"))
            new_top_k = st.text_input(t("label.top_k"), value="", key="create_persona_top_k")
            new_min_score = st.text_input(
                t("label.min_score"), value="", key="create_persona_min_score"
            )
            new_chunk = st.text_input(t("label.chunk_chars"), value="", key="create_persona_chunk")
        if st.button(t("action.create_persona"), key="create_persona_btn"):
            try:
                pack = create_user_persona(
                    personas_dir=settings.personas_dir,
                    persona_id=new_id,
                    name=new_name,
                    description=new_desc,
                    system_prompt=new_prompt,
                    config=build_persona_config(
                        answer_mode=cast(Any, new_mode),
                        temperature=float(new_temp),
                        max_tokens=int(new_max_tokens),
                        embedding_preset=cast(Any, new_preset),
                        top_k=_optional_int(new_top_k),
                        min_score=_optional_float(new_min_score),
                        chunk_chars=_optional_int(new_chunk),
                    ),
                )
                st.session_state.persona_id = pack.id
                st.session_state.thread_id = ""
                _clear_rag_cache(pack.id)
                st.success(t("status.persona_created"))
                st.rerun()
            except Exception as exc:  # noqa: BLE001
                _render_error(exc)


def _sidebar_knowledge(persona: PersonaPack) -> None:
    """Simple knowledge panel — status + upload/paste only."""
    settings = get_settings()
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
            _vstore, _manifest, _kdir, health = st.session_state[cache_key]["bundle"]
            status_key = index_status_key(
                needs_rebuild=bool(health.needs_rebuild),
                file_count=int(health.file_count),
            )
            files_label = t("label.knowledge_files", n=int(health.file_count))
            st.markdown(f"**{t(status_key)}** · {files_label}")
            if health.needs_rebuild:
                st.warning(t("label.needs_rebuild_banner"))
            if is_user_persona(persona.id, settings):
                uploaded_knowledge = st.file_uploader(
                    t("action.upload_knowledge"),
                    type=["txt", "md", "pdf", "docx"],
                    key=f"knowledge_upload_{persona.id}",
                )
                if uploaded_knowledge is not None and st.button(
                    t("action.make_knowledge_ready"),
                    key=f"knowledge_upload_btn_{persona.id}",
                ):
                    try:
                        dest = add_knowledge_bytes(
                            settings=settings,
                            persona_id=persona.id,
                            filename=uploaded_knowledge.name,
                            data=uploaded_knowledge.getvalue(),
                        )
                        _clear_rag_cache(persona.id)
                        _rebuild_persona_index(persona)
                        st.success(f"{t('status.knowledge_ready_after_save')} ({dest.name})")
                        st.rerun()
                    except Exception as exc:  # noqa: BLE001
                        _render_error(exc)
                paste_name = st.text_input(
                    t("label.knowledge_paste_name"),
                    value="pasted.md",
                    key=f"knowledge_paste_name_{persona.id}",
                )
                paste_text = st.text_area(
                    t("label.knowledge_paste"),
                    key=f"knowledge_paste_{persona.id}",
                    height=100,
                )
                if st.button(
                    t("action.make_knowledge_ready"),
                    key=f"knowledge_paste_btn_{persona.id}",
                ):
                    try:
                        dest = add_knowledge_paste(
                            settings=settings,
                            persona_id=persona.id,
                            text=paste_text,
                            filename=paste_name,
                        )
                        _clear_rag_cache(persona.id)
                        _rebuild_persona_index(persona)
                        st.success(f"{t('status.knowledge_ready_after_save')} ({dest.name})")
                        st.rerun()
                    except Exception as exc:  # noqa: BLE001
                        _render_error(exc)
            else:
                st.caption(t("status.example_edit_readonly"))

            if st.button(t("label.rebuild_index"), key="rebuild_idx"):
                _rebuild_persona_index(persona)
                st.success(t("status.index_rebuilt"))
                st.rerun()
        except Exception as exc:  # noqa: BLE001
            _render_error(exc)


def _sidebar_settings(*, has_key: bool) -> None:
    """Daily settings: entry path + API key (short labels, no help walls)."""
    expanded = not has_key
    with st.sidebar.expander(t("label.settings"), expanded=expanded):
        # Path switcher only after welcome finishes — avoids fighting the gate.
        if st.session_state.get("wizard_done"):
            current_path: EntryPath = (
                "knowledge" if st.session_state.get("knowledge_only_mode") else "api"
            )
            if st.session_state.get("entry_path") in {"api", "knowledge"}:
                current_path = st.session_state.entry_path  # type: ignore[assignment]
            if st.session_state.get("settings_entry_path") not in {"api", "knowledge"}:
                st.session_state.settings_entry_path = current_path
            path_choice = st.radio(
                t("label.entry_path"),
                options=["api", "knowledge"],
                format_func=lambda v: t(f"label.entry_path.{v}"),
                key="settings_entry_path",
            )
            if path_choice != current_path:
                _apply_entry_path(path_choice, finish=True)  # type: ignore[arg-type]
                st.rerun()

        key_suffix = "preauth" if not has_key else "main"
        key_val = st.text_input(
            t("label.api_key"),
            value=st.session_state.api_key,
            type="password",
            key=f"sidebar_key_{key_suffix}",
        )
        remember = st.checkbox(
            t("label.remember_key"),
            value=remember_enabled(),
            key=f"remember_key_box_{key_suffix}",
        )
        if st.button(t("action.save_key"), key=f"save_key_btn_{key_suffix}"):
            _apply_remember_choice(remember, key_val)
            _apply_entry_path("api", finish=True)
            st.rerun()
        if has_key and st.button(t("action.forget_key"), key="forget_key_btn"):
            st.session_state.api_key = ""
            st.session_state.remember_loaded = False
            _apply_entry_path("knowledge", finish=True)
            set_ui_remember_preference(False)
            delete_api_key()
            st.rerun()


def _sidebar_data_tools(settings: Any) -> None:
    """Export / import / backup — power users only."""
    pack_dir = persona_dir_for(st.session_state.persona_id, settings)
    if pack_dir is not None:
        try:
            payload = export_persona_zip(
                pack_dir,
                api_key=st.session_state.api_key or settings.groq_api_key,
            )
            st.download_button(
                label=t("action.export_persona"),
                data=payload,
                file_name=f"{st.session_state.persona_id}.zip",
                mime="application/zip",
                key="export_download",
            )
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
            st.session_state.confirm_overwrite_import = False
        except Exception as exc:  # noqa: BLE001
            st.session_state.import_preview = None
            st.session_state.import_bytes = None
            _render_error(exc)
    if st.session_state.import_preview:
        st.markdown(f"**{t('label.import_preview')}**")
        st.json(st.session_state.import_preview)
        needs_overwrite = overwrite_confirm_required(
            str(conflict),
            cast(dict[str, Any] | None, st.session_state.import_preview),
        )
        overwrite_ok = True
        if needs_overwrite:
            st.warning(t("warn.overwrite_import"))
            overwrite_ok = st.checkbox(
                t("action.confirm_overwrite"),
                key="confirm_overwrite_import",
            )
        if st.button(
            t("action.confirm_import"),
            key="confirm_import_btn",
            disabled=needs_overwrite and not overwrite_ok,
        ):
            try:
                pack = import_persona_zip(
                    cast(bytes, st.session_state.import_bytes),
                    personas_dir=settings.personas_dir,
                    conflict=cast(Any, conflict),
                )
                st.session_state.persona_id = pack.id
                st.session_state.import_preview = None
                st.session_state.import_bytes = None
                st.session_state.confirm_overwrite_import = False
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
            st.session_state.backup_payload = payload
            st.session_state.backup_summary = summary.member_count
        except Exception as exc:  # noqa: BLE001
            st.session_state.backup_payload = None
            _render_error(exc)
    if st.session_state.get("backup_payload"):
        st.download_button(
            label="persona-bot-backup.zip",
            data=cast(bytes, st.session_state.backup_payload),
            file_name="persona-bot-backup.zip",
            mime="application/zip",
            key="backup_download",
        )
        st.success(f"{t('status.backup_ok')} ({st.session_state.get('backup_summary', 0)})")

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


def _sidebar_advanced_labs(persona: PersonaPack | None, settings: Any) -> None:
    """Search lab, prompt inspector, remember-key status details."""
    st.caption(
        t(remember_status_key(loaded_from_keyring=bool(st.session_state.get("remember_loaded"))))
    )
    st.caption(t("label.remember_key_help"))
    st.caption(t("privacy.notice"))
    st.checkbox(
        t("label.prompt_inspector"),
        key="show_prompt_inspector",
    )
    if persona is not None:
        st.markdown(f"**{t('label.search_lab')}**")
        q = st.text_input(t("label.search_query"), key="search_lab_q")
        if st.button(t("action.run_search"), key="search_lab_go") and q.strip():
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


def _sidebar_more(
    *,
    persona: PersonaPack | None,
    settings: Any,
    has_key: bool,
) -> None:
    """Collapsed power panel: usage, version, editor, backup, health, labs."""
    usage = _usage()
    with st.sidebar.expander(t("label.more_settings"), expanded=False):
        snap = usage.snapshot
        token_display = format_token_usage(
            total_tokens=snap.total_tokens,
            daily_limit=settings.daily_token_limit,
        )
        st.markdown(f"**{t('label.usage_today')}**")
        st.caption(f"{t('label.tokens')}: {token_display} · n={snap.request_count}")
        if settings.daily_token_limit is not None and settings.daily_token_limit > 0:
            st.caption(t("label.daily_token_limit"))
        else:
            st.caption(t("status.daily_limit_unset"))

        st.caption(f"{t('label.version')}: {get_app_version()}")

        _render_persona_editor(persona)

        if has_key:
            with st.expander(t("label.data_tools"), expanded=False):
                _sidebar_data_tools(settings)

        with st.expander(t("label.health"), expanded=False):
            report = run_health_check(
                settings,
                api_key=st.session_state.api_key or settings.groq_api_key,
            )
            st.write(t("status.health_ok") if report.ok else t("status.health_issues"))
            st.json(report.to_dict())

        with st.expander(t("label.advanced"), expanded=False):
            _sidebar_advanced_labs(persona, settings)


def _sidebar(personas: list) -> None:
    settings = get_settings()
    store = _store()
    by_id = {p.id: p for p in personas}

    st.sidebar.markdown(f"### {t('app.title')}")

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

    c1, c2 = st.sidebar.columns(2)
    if c1.button(t("action.new_chat"), use_container_width=True):
        st.session_state.confirm_clear_chat = False
        thread = store.create_thread(
            persona_id=st.session_state.persona_id, title=t("action.new_chat")
        )
        st.session_state.thread_id = thread.id
        st.rerun()
    if c2.button(t("action.clear_chat"), use_container_width=True):
        st.session_state.confirm_clear_chat = True
    if st.session_state.confirm_clear_chat:
        st.sidebar.warning(t("warn.clear_chat"))
        if st.sidebar.button(t("action.confirm_clear_chat"), key="confirm_clear_chat_btn"):
            tid = _ensure_thread(store, st.session_state.persona_id)
            store.clear_thread_messages(tid)
            st.session_state.confirm_clear_chat = False
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

    if persona is not None:
        _sidebar_knowledge(persona)

    has_key = bool(st.session_state.api_key or settings.groq_api_key)
    _sidebar_settings(has_key=has_key)
    _sidebar_more(persona=persona, settings=settings, has_key=has_key)


def _welcome_gate() -> None:
    """First viewport: brand + short copy + hero + two path choices."""
    st.markdown(
        f"""
<div class="pb-welcome">
  <p class="pb-welcome-brand">{t("app.title")}</p>
  <h1>{t("app.welcome.headline")}</h1>
  <p class="pb-welcome-sub">{t("app.welcome.sub")}</p>
</div>
""",
        unsafe_allow_html=True,
    )
    hero = welcome_hero_path()
    if hero.is_file():
        st.image(str(hero), width="stretch")
    c1, c2 = st.columns(2)
    with c1:
        if st.button(
            t("action.choose_api"),
            key="welcome_choose_api",
            type="primary",
            use_container_width=True,
        ):
            _apply_entry_path("api", finish=False)
            st.rerun()
    with c2:
        if st.button(
            t("action.choose_knowledge"),
            key="welcome_choose_knowledge",
            use_container_width=True,
        ):
            _apply_entry_path("knowledge", finish=False)
            st.rerun()
    st.caption(t("welcome.change_later"))


def _welcome_api_path() -> None:
    """Path A — paste Groq key or start with .env key."""
    settings = get_settings()
    env_key = (settings.groq_api_key or "").strip()
    st.markdown(
        f"""
<div class="pb-welcome">
  <p class="pb-welcome-brand">{t("app.title")}</p>
  <h1>{t("action.choose_api")}</h1>
  <p class="pb-welcome-sub">{t("welcome.api_hint")}</p>
</div>
""",
        unsafe_allow_html=True,
    )
    if env_key and not st.session_state.api_key:
        st.success(t("welcome.env_key_found"))
        if st.button(t("action.start_chat"), key="welcome_start_env", type="primary"):
            st.session_state.api_key = env_key
            _apply_entry_path("api", finish=True)
            st.rerun()
    key_val = st.text_input(t("label.api_key"), type="password", key="welcome_key")
    remember = st.checkbox(
        t("label.remember_key"),
        value=remember_enabled(),
        key="welcome_remember",
        help=t("label.remember_key_help"),
    )
    st.caption(
        t(remember_status_key(loaded_from_keyring=bool(st.session_state.get("remember_loaded"))))
    )
    if st.button(t("action.save_key"), key="welcome_save", type="primary"):
        _apply_remember_choice(remember, key_val)
        _apply_entry_path("api", finish=True)
        st.rerun()
    if st.button(t("action.back_welcome"), key="welcome_back_api"):
        clear_entry_path(settings.data_dir)
        st.session_state.entry_path = None
        st.session_state.welcome_stage = "gate"
        st.session_state.wizard_done = False
        st.rerun()
    st.caption(t("welcome.change_later"))


def _welcome_knowledge_path(personas: list) -> None:
    """Path B — short upload/paste then Ready (knowledge-only)."""
    settings = get_settings()
    st.markdown(
        f"""
<div class="pb-welcome">
  <p class="pb-welcome-brand">{t("app.title")}</p>
  <h1>{t("action.choose_knowledge")}</h1>
  <p class="pb-welcome-sub">{t("welcome.knowledge_hint")}</p>
</div>
""",
        unsafe_allow_html=True,
    )
    by_id = {p.id: p for p in personas}
    persona_ids = [p.id for p in personas]
    labels = {p.id: p.name for p in personas}
    current = st.session_state.persona_id
    if current not in persona_ids and persona_ids:
        current = persona_ids[0]
        st.session_state.persona_id = current
    selected = st.selectbox(
        t("label.persona"),
        options=persona_ids,
        format_func=lambda i: labels.get(i, i),
        index=persona_ids.index(current) if current in persona_ids else 0,
        key="welcome_persona",
    )
    if selected != st.session_state.persona_id:
        st.session_state.persona_id = selected
    persona = by_id.get(st.session_state.persona_id)
    if persona is not None and is_user_persona(persona.id, settings):
        uploaded = st.file_uploader(
            t("action.upload_knowledge"),
            type=["txt", "md", "pdf", "docx"],
            key="welcome_knowledge_upload",
        )
        paste_text = st.text_area(
            t("label.knowledge_paste"),
            key="welcome_knowledge_paste",
            height=100,
        )
        if uploaded is not None and st.button(
            t("action.make_knowledge_ready"),
            key="welcome_knowledge_upload_btn",
        ):
            try:
                dest = add_knowledge_bytes(
                    settings=settings,
                    persona_id=persona.id,
                    filename=uploaded.name,
                    data=uploaded.getvalue(),
                )
                _clear_rag_cache(persona.id)
                _rebuild_persona_index(persona)
                st.success(f"{t('status.knowledge_ready_after_save')} ({dest.name})")
            except Exception as exc:  # noqa: BLE001
                _render_error(exc)
        elif paste_text.strip() and st.button(
            t("action.make_knowledge_ready"),
            key="welcome_knowledge_paste_btn",
        ):
            try:
                dest = add_knowledge_paste(
                    settings=settings,
                    persona_id=persona.id,
                    text=paste_text,
                    filename="welcome-notes.md",
                )
                _clear_rag_cache(persona.id)
                _rebuild_persona_index(persona)
                st.success(f"{t('status.knowledge_ready_after_save')} ({dest.name})")
            except Exception as exc:  # noqa: BLE001
                _render_error(exc)
    elif persona is not None:
        st.caption(t("status.example_edit_readonly"))

    if st.button(
        t("action.continue_knowledge_only"),
        key="welcome_knowledge_only",
        type="primary",
    ):
        _apply_entry_path("knowledge", finish=True)
        st.rerun()
    if st.button(t("action.back_welcome"), key="welcome_back_knowledge"):
        clear_entry_path(settings.data_dir)
        st.session_state.entry_path = None
        st.session_state.welcome_stage = "gate"
        st.session_state.knowledge_only_mode = False
        st.session_state.wizard_done = False
        st.rerun()
    st.caption(t("welcome.change_later"))


def _welcome(personas: list) -> None:
    """Welcome gate → path A (API) or path B (knowledge)."""
    stage = st.session_state.get("welcome_stage") or "gate"
    entry = st.session_state.get("entry_path")
    if entry in {"api", "knowledge"}:
        stage = entry
    if stage == "api":
        _welcome_api_path()
        return
    if stage == "knowledge":
        _welcome_knowledge_path(personas)
        return
    _welcome_gate()


def _render_chat_empty(persona: PersonaPack | None) -> None:
    """Soft empty state — local icons + short ask-anything copy."""
    cols = st.columns([1, 1, 1, 1, 1])
    for idx, name in enumerate(("chat", "doc", "check")):
        path = icon_path(name)
        if path.is_file():
            cols[idx + 1].image(str(path), width=48)
    if persona and persona.greeting:
        icon = f"{persona.icon} " if persona.icon else ""
        st.info(f"{icon}{persona.greeting}")
    else:
        st.markdown(
            f'<div class="pb-empty"><p>{t("chat.empty")}</p></div>',
            unsafe_allow_html=True,
        )


def _render_meta(result: StreamResult) -> None:
    if not result.model and result.usage.total_tokens <= 0:
        return
    badge_cls = "pb-badge fallback" if result.used_fallback else "pb-badge"
    label = t("label.fallback") if result.used_fallback else t("label.model")
    st.markdown(
        f'<span class="{badge_cls}">{label}: {result.model or "-"}</span>'
        f'<span class="pb-badge">{t("label.tokens")}: '
        f"{result.usage.total_tokens}</span>",
        unsafe_allow_html=True,
    )


def _render_knowledge_only_message(
    *,
    reply: str,
    kept: list[dict[str, Any]],
    has_hits: bool,
    note: str | None = None,
) -> None:
    with st.chat_message("assistant"):
        if has_hits:
            st.markdown(reply)
            st.markdown(
                f'<span class="pb-badge knowledge">{t("label.knowledge_only_badge")}</span>',
                unsafe_allow_html=True,
            )
            if note:
                st.caption(note)
            if kept:
                with st.expander(t("label.sources")):
                    st.markdown(format_sources_markdown(kept))
        else:
            # Calm empty state — no error chrome / model-token badges.
            st.info(reply)


def _emit_knowledge_only(
    *,
    store: ChatStore,
    thread_id: str,
    user_text: str,
    context_chunks: list[dict[str, Any]],
    min_score: float,
    note: str | None = None,
) -> None:
    reply, kept, has_hits = resolve_knowledge_only_reply(
        context_chunks,
        min_score=min_score,
        locale=get_locale(),
        question=user_text,
    )
    store.add_message(
        thread_id=thread_id,
        role="assistant",
        content=reply,
        meta={
            "knowledge_only": True,
            "tokens": 0,
            "model": "",
            "sources": [{"source": c.get("source"), "score": c.get("score")} for c in kept],
        },
    )
    _render_knowledge_only_message(
        reply=reply,
        kept=kept,
        has_hits=has_hits,
        note=note,
    )


def _handle_user_message(user_text: str, personas: list) -> None:
    settings = get_settings()
    store = _store()
    usage = _usage()
    by_id = {p.id: p for p in personas}
    persona = by_id[st.session_state.persona_id]
    thread_id = _ensure_thread(store, persona.id)
    min_score = persona.config.resolved_min_score()

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
        bundle = st.session_state[cache_key]["bundle"]
        health = bundle[3]
        if getattr(health, "needs_rebuild", False):
            st.warning(t("label.needs_rebuild_banner"))
        vstore = bundle[0]
        context_chunks = retrieve(
            vstore,
            persona_id=persona.id,
            latest=user_text,
            history=history,
            top_k=persona.config.resolved_top_k(),
            min_score=min_score,
        )
    except AppError as exc:
        with st.chat_message("assistant"):
            _render_error(exc)
        return
    except Exception as exc:  # noqa: BLE001
        with st.chat_message("assistant"):
            _render_error(exc)
        return

    api_key = (st.session_state.api_key or settings.groq_api_key or "").strip()
    prefer_knowledge_only = bool(st.session_state.get("knowledge_only_mode")) or not api_key

    try:
        messages = build_messages(
            persona,
            history=history,
            user_text=user_text,
            context_chunks=context_chunks,
            min_score=min_score,
        )
    except KnowledgeNotFoundError:
        # Strict + no passing chunks → calm empty state, no LLM / usage chrome.
        reply = t("status.oos_calm")
        store.add_message(thread_id=thread_id, role="assistant", content=reply)
        with st.chat_message("assistant"):
            st.info(reply)
        return

    if prefer_knowledge_only:
        _emit_knowledge_only(
            store=store,
            thread_id=thread_id,
            user_text=user_text,
            context_chunks=context_chunks,
            min_score=min_score,
            note=None if api_key else t("wizard.knowledge_only_hint"),
        )
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

    result = StreamResult()
    try:
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
            if st.session_state.get("show_prompt_inspector"):
                with st.expander(t("label.prompt_inspector")):
                    st.json(inspector)
        usage.record(result)
    except AppError as exc:
        if result.text:
            store.update_message(
                assistant_id,
                content=result.text,
                partial=True,
            )
            with st.chat_message("assistant"):
                st.markdown(result.text)
                st.caption(t("status.partial_saved"))
                _render_error(exc)
            return
        # Auto-fall back to extractive knowledge when key/quota/network fails.
        if should_fallback_to_knowledge_only(exc):
            reply, kept, has_hits = resolve_knowledge_only_reply(
                context_chunks,
                min_score=min_score,
                locale=get_locale(),
                question=user_text,
            )
            store.update_message(
                assistant_id,
                content=reply,
                partial=False,
                meta={
                    "knowledge_only": True,
                    "tokens": 0,
                    "model": "",
                    "sources": [{"source": c.get("source"), "score": c.get("score")} for c in kept],
                    "fallback_from": getattr(exc, "code", type(exc).__name__),
                },
            )
            _render_knowledge_only_message(
                reply=reply,
                kept=kept,
                has_hits=has_hits,
                note=t("status.knowledge_only_fallback"),
            )
            return
        store.update_message(
            assistant_id,
            content="",
            partial=False,
        )
        with st.chat_message("assistant"):
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
    _restore_entry_path_from_disk()

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
    # Gate until the user finishes path A (key) or path B (Ready).
    needs_welcome = not bool(st.session_state.wizard_done)
    if needs_welcome:
        _welcome(personas)
        return
    if not has_key:
        st.session_state.knowledge_only_mode = True

    if not st.session_state.privacy_ack:
        st.markdown(
            progress_markup(wizard_step(has_key=True, privacy_ack=False)),
            unsafe_allow_html=True,
        )
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
        _render_chat_empty(persona)
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
                if msg.meta.get("knowledge_only"):
                    st.markdown(
                        f'<span class="pb-badge knowledge">'
                        f"{t('label.knowledge_only_badge')}</span>",
                        unsafe_allow_html=True,
                    )
                else:
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
