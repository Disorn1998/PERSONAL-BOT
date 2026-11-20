"""First-run onboarding gate — full-screen until chat-ready (no sidebar)."""

from __future__ import annotations

import html
import re
from typing import Any, Literal

import streamlit as st

from persona_bot.config import clear_settings_cache, get_settings
from persona_bot.env_store import upsert_groq_api_key
from persona_bot.i18n import SUPPORTED_LOCALES, get_locale, set_locale, t
from persona_bot.keyring_store import (
    delete_api_key,
    env_remember_enabled,
    remember_enabled,
    remember_status_key,
    save_api_key,
    set_ui_remember_preference,
)
from persona_bot.persona import PersonaPack
from persona_bot.persona_editor import (
    add_knowledge_bytes,
    add_knowledge_paste,
    create_user_persona,
)
from persona_bot.rag.runtime import build_embedder, get_or_build_store
from persona_bot.services import is_user_persona, load_available_personas
from persona_bot.ui.assets import welcome_hero_data_uri, welcome_hero_path
from persona_bot.ui.errors import error_from_exception, format_error_card
from persona_bot.ui.tour import is_tour_done
from persona_bot.ui.wizard import (
    EntryPath,
    clear_entry_path,
    load_entry_path,
    save_entry_path,
)

WelcomeStage = Literal["gate", "api", "knowledge", "role"]
PENDING_FILES_KEY = "onboarding_pending_files"
_ID_SAFE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
_UPLOAD_TYPES = ["txt", "md", "pdf", "docx", "xlsx", "xls", "png", "jpg", "jpeg", "webp"]


def is_chat_ready() -> bool:
    """True when the first-run wizard finished (sidebar + chat may show)."""
    return bool(st.session_state.get("wizard_done"))


def user_personas(personas: list[PersonaPack], settings: Any) -> list[PersonaPack]:
    return [p for p in personas if is_user_persona(p.id, settings)]


def can_show_continue(personas: list[PersonaPack], settings: Any) -> bool:
    """Continue CTA when a user pack exists or ``data/entry_path`` is already set."""
    if user_personas(personas, settings):
        return True
    return load_entry_path(settings.data_dir) is not None


def _render_error(exc: BaseException) -> None:
    info = error_from_exception(exc)
    title, hint = format_error_card(info)
    hint_html = ""
    if hint:
        safe = hint.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        safe = safe.replace("\n", "<br/>")
        hint_html = f'<div class="hint">{safe}</div>'
    st.markdown(
        f'<div class="pb-error"><strong>{title}</strong>{hint_html}</div>',
        unsafe_allow_html=True,
    )


def _clear_rag_cache(persona_id: str | None = None) -> None:
    prefix = f"rag::{persona_id}::" if persona_id else "rag::"
    for key in list(st.session_state.keys()):
        if isinstance(key, str) and key.startswith(prefix):
            del st.session_state[key]


def _rebuild_persona_index(persona: PersonaPack) -> None:
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


def _apply_remember_choice(remember: bool, key_val: str) -> None:
    key = key_val.strip()
    st.session_state.api_key = key
    should_remember = bool(remember) or env_remember_enabled()
    set_ui_remember_preference(bool(remember) or env_remember_enabled())
    if should_remember and key:
        save_api_key(key)
        st.session_state.remember_loaded = True
    elif not remember and not env_remember_enabled():
        delete_api_key()
        st.session_state.remember_loaded = False


def _persist_key_to_env(key_val: str) -> None:
    """Upsert ``GROQ_API_KEY`` into ``.env`` — never log the secret."""
    key = key_val.strip()
    if not key:
        return
    try:
        upsert_groq_api_key(key)
        clear_settings_cache()
    except Exception as exc:  # noqa: BLE001 — UI still has session key
        _render_error(exc)


def set_welcome_stage(stage: WelcomeStage) -> None:
    st.session_state.welcome_stage = stage


def apply_entry_path(entry: EntryPath, *, finish: bool = False) -> None:
    """Set session path; persist + mark wizard done only when finishing."""
    st.session_state.entry_path = entry
    st.session_state.settings_entry_path = entry
    if entry == "knowledge":
        st.session_state.knowledge_only_mode = True
    else:
        st.session_state.knowledge_only_mode = False
    if finish:
        save_entry_path(get_settings().data_dir, entry)
        st.session_state.wizard_done = True
        _maybe_start_tour()
    else:
        set_welcome_stage(entry)  # type: ignore[arg-type]


def _maybe_start_tour() -> None:
    """Tour starts only after chat-ready."""
    settings = get_settings()
    if is_tour_done(settings.data_dir):
        st.session_state.tour_active = False
        st.session_state.tour_done = True
        return
    st.session_state.tour_active = True
    st.session_state.tour_done = False
    st.session_state.tour_step = "persona"


def finish_to_chat(*, entry: EntryPath) -> None:
    apply_entry_path(entry, finish=True)


def go_to_role(*, entry: EntryPath) -> None:
    """After API or knowledge step — role before chat."""
    st.session_state.entry_path = entry
    st.session_state.settings_entry_path = entry
    if entry == "knowledge":
        st.session_state.knowledge_only_mode = True
    else:
        st.session_state.knowledge_only_mode = False
    set_welcome_stage("role")


def back_to_gate() -> None:
    settings = get_settings()
    clear_entry_path(settings.data_dir)
    st.session_state.entry_path = None
    st.session_state.welcome_stage = "gate"
    st.session_state.wizard_done = False
    st.session_state.knowledge_only_mode = False


def _pending_files() -> list[dict[str, Any]]:
    raw = st.session_state.get(PENDING_FILES_KEY)
    if not isinstance(raw, list):
        st.session_state[PENDING_FILES_KEY] = []
        return []
    return raw


def _stage_file(filename: str, data: bytes) -> None:
    pending = _pending_files()
    pending.append({"filename": filename, "data": data})
    st.session_state[PENDING_FILES_KEY] = pending


def _flush_pending_to_persona(persona_id: str) -> int:
    settings = get_settings()
    pending = list(_pending_files())
    if not pending:
        return 0
    count = 0
    for item in pending:
        name = str(item.get("filename") or "note.txt")
        data = item.get("data") or b""
        if not isinstance(data, (bytes, bytearray)) or not data:
            continue
        add_knowledge_bytes(
            settings=settings,
            persona_id=persona_id,
            filename=name,
            data=bytes(data),
        )
        count += 1
    st.session_state[PENDING_FILES_KEY] = []
    return count


def _slug_from_name(name: str) -> str:
    raw = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    if not raw:
        raw = "my-persona"
    if not _ID_SAFE.match(raw):
        raw = "my-persona"
    return raw[:48]


def _tone_to_prompt(name: str, tone: str) -> str:
    tone_clean = tone.strip() or t("onboarding.tone_default")
    return (
        f"You are {name.strip() or 'a helpful assistant'}. "
        f"Tone: {tone_clean}. "
        "Answer clearly. Prefer the user's knowledge files when available."
    )


def _parse_starters(raw: str) -> list[str]:
    return [line.strip() for line in str(raw).splitlines() if line.strip()][:8]


def _brand_header(title_key: str, sub_key: str) -> None:
    st.markdown(
        f"""
<div class="pb-welcome">
  <p class="pb-welcome-brand">{t("app.title")}</p>
  <h1>{t(title_key)}</h1>
  <p class="pb-welcome-sub">{t(sub_key)}</p>
</div>
""",
        unsafe_allow_html=True,
    )


def _locale_row() -> None:
    lang = st.selectbox(
        t("label.language"),
        options=list(SUPPORTED_LOCALES),
        index=list(SUPPORTED_LOCALES).index(get_locale())
        if get_locale() in SUPPORTED_LOCALES
        else 0,
        format_func=lambda code: "ไทย" if code == "th" else "English",
        key="onboarding_locale_select",
    )
    if lang != st.session_state.locale:
        st.session_state.locale = lang
        set_locale(lang)
        st.rerun()
    else:
        set_locale(str(st.session_state.locale))


def render_gate(personas: list[PersonaPack]) -> None:
    """Full-screen gate: API / Upload / Continue (when eligible)."""
    settings = get_settings()
    _locale_row()
    hero_uri = welcome_hero_data_uri()
    hero_block = ""
    if hero_uri:
        alt = html.escape(t("app.title"))
        hero_block = (
            f'<div class="pb-welcome-hero"><img src="{hero_uri}" alt="{alt}" width="100%" /></div>'
        )
    st.markdown(
        f"""
<div class="pb-welcome">
  <p class="pb-welcome-brand">{t("app.title")}</p>
  <h1>{t("app.welcome.headline")}</h1>
  <p class="pb-welcome-sub">{t("app.welcome.sub")}</p>
  {hero_block}
</div>
""",
        unsafe_allow_html=True,
    )
    if not hero_uri and welcome_hero_path().is_file():
        st.image(str(welcome_hero_path()), width="stretch")

    show_continue = can_show_continue(personas, settings)
    if show_continue:
        c1, c2, c3 = st.columns(3)
    else:
        c1, c2 = st.columns(2)
        c3 = None

    with c1:
        if st.button(
            t("action.choose_api"),
            key="welcome_choose_api",
            type="primary",
            use_container_width=True,
        ):
            apply_entry_path("api", finish=False)
            st.rerun()
    with c2:
        if st.button(
            t("action.choose_knowledge"),
            key="welcome_choose_knowledge",
            use_container_width=True,
        ):
            apply_entry_path("knowledge", finish=False)
            st.rerun()
    if c3 is not None:
        with c3:
            if st.button(
                t("action.continue_existing"),
                key="welcome_continue",
                use_container_width=True,
            ):
                has_key = bool(st.session_state.api_key or settings.groq_api_key)
                entry: EntryPath = "api" if has_key else "knowledge"
                finish_to_chat(entry=entry)
                st.rerun()
    st.caption(t("welcome.change_later"))


def render_api_path() -> None:
    """Path A — paste Groq key (writes ``.env``) then role."""
    settings = get_settings()
    env_key = (settings.groq_api_key or "").strip()
    _locale_row()
    _brand_header("action.choose_api", "welcome.api_hint")

    if env_key and not st.session_state.api_key:
        st.success(t("welcome.env_key_found"))
        if st.button(t("action.continue_to_role"), key="welcome_start_env", type="primary"):
            st.session_state.api_key = env_key
            go_to_role(entry="api")
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
        _persist_key_to_env(key_val)
        go_to_role(entry="api")
        st.rerun()
    if st.button(t("action.back_welcome"), key="welcome_back_api"):
        back_to_gate()
        st.rerun()
    st.caption(t("welcome.change_later"))


def render_knowledge_path(personas: list[PersonaPack]) -> None:
    """Path B — stage uploads/paste then continue to role."""
    settings = get_settings()
    _locale_row()
    _brand_header("action.choose_knowledge", "welcome.knowledge_hint")

    users = user_personas(personas, settings)
    if users:
        labels = {p.id: p.name for p in users}
        ids = [p.id for p in users]
        current = st.session_state.persona_id
        if current not in ids:
            current = ids[0]
            st.session_state.persona_id = current
        selected = st.selectbox(
            t("label.persona"),
            options=ids,
            format_func=lambda i: labels.get(i, i),
            index=ids.index(current) if current in ids else 0,
            key="welcome_persona",
        )
        if selected != st.session_state.persona_id:
            st.session_state.persona_id = selected
        persona = next((p for p in users if p.id == st.session_state.persona_id), None)
    else:
        persona = None
        st.caption(t("welcome.knowledge_stage_hint"))

    uploaded = st.file_uploader(
        t("action.upload_knowledge"),
        type=_UPLOAD_TYPES,
        key="welcome_knowledge_upload",
        accept_multiple_files=True,
    )
    paste_text = st.text_area(
        t("label.knowledge_paste"),
        key="welcome_knowledge_paste",
        height=100,
    )

    if st.button(t("action.make_knowledge_ready"), key="welcome_knowledge_upload_btn"):
        try:
            saved = 0
            if uploaded:
                files = uploaded if isinstance(uploaded, list) else [uploaded]
                for item in files:
                    data = item.getvalue()
                    if persona is not None:
                        add_knowledge_bytes(
                            settings=settings,
                            persona_id=persona.id,
                            filename=item.name,
                            data=data,
                        )
                        saved += 1
                    else:
                        _stage_file(item.name, data)
                        saved += 1
            if paste_text.strip():
                if persona is not None:
                    add_knowledge_paste(
                        settings=settings,
                        persona_id=persona.id,
                        text=paste_text,
                        filename="welcome-notes.md",
                    )
                else:
                    _stage_file("welcome-notes.md", paste_text.strip().encode("utf-8"))
                saved += 1
            if persona is not None and saved:
                _clear_rag_cache(persona.id)
                _rebuild_persona_index(persona)
            if saved:
                st.success(t("status.knowledge_ready_after_save"))
            else:
                st.warning(t("welcome.knowledge_empty_save"))
        except Exception as exc:  # noqa: BLE001
            _render_error(exc)

    pending_n = len(_pending_files())
    if pending_n:
        st.caption(t("welcome.pending_files", n=pending_n))

    if st.button(
        t("action.continue_to_role"),
        key="welcome_knowledge_only",
        type="primary",
    ):
        go_to_role(entry="knowledge")
        st.rerun()
    if st.button(t("action.back_welcome"), key="welcome_back_knowledge"):
        st.session_state[PENDING_FILES_KEY] = []
        back_to_gate()
        st.rerun()
    st.caption(t("welcome.change_later"))


def render_role_step(personas: list[PersonaPack]) -> None:
    """Create or select a persona, then open chat + sidebar."""
    settings = get_settings()
    _locale_row()
    _brand_header("onboarding.role_title", "onboarding.role_hint")

    users = user_personas(personas, settings)
    mode = st.radio(
        t("onboarding.role_mode"),
        options=["create", "select"] if users else ["create"],
        format_func=lambda m: (
            t("onboarding.role_create") if m == "create" else t("onboarding.role_select")
        ),
        key="onboarding_role_mode",
        horizontal=True,
    )

    entry: EntryPath = "api" if st.session_state.get("entry_path") == "api" else "knowledge"

    if mode == "select" and users:
        labels = {p.id: p.name for p in users}
        ids = [p.id for p in users]
        current = st.session_state.persona_id
        if current not in ids:
            current = ids[0]
        selected = st.selectbox(
            t("label.persona"),
            options=ids,
            format_func=lambda i: labels.get(i, i),
            index=ids.index(current) if current in ids else 0,
            key="onboarding_role_select",
        )
        if st.button(t("action.start_chat"), key="onboarding_role_use", type="primary"):
            st.session_state.persona_id = selected
            flushed = _flush_pending_to_persona(selected)
            if flushed:
                selected_pack = next(p for p in users if p.id == selected)
                _clear_rag_cache(selected)
                try:
                    _rebuild_persona_index(selected_pack)
                except Exception as exc:  # noqa: BLE001
                    _render_error(exc)
                    return
            finish_to_chat(entry=entry)
            st.rerun()
    else:
        name = st.text_input(t("label.persona_name"), key="onboarding_role_name")
        tone = st.text_input(
            t("label.persona_tone"),
            value=t("onboarding.tone_default"),
            key="onboarding_role_tone",
            help=t("label.persona_tone_help"),
        )
        starters = st.text_area(
            t("label.starter_questions"),
            key="onboarding_role_starters",
            height=80,
            help=t("label.starter_questions_help"),
        )
        if st.button(t("action.create_persona"), key="onboarding_role_create", type="primary"):
            base_id = _slug_from_name(name or "my-persona")
            display_name = (name or t("onboarding.default_persona_name")).strip()
            prompt = _tone_to_prompt(name, tone)
            starter_list = _parse_starters(starters)
            created: PersonaPack | None = None
            for candidate in [base_id, *(f"{base_id}-{n}" for n in range(2, 100))]:
                try:
                    created = create_user_persona(
                        personas_dir=settings.personas_dir,
                        persona_id=candidate,
                        name=display_name,
                        system_prompt=prompt,
                        description=tone.strip(),
                        starter_questions=starter_list,
                    )
                    break
                except Exception:  # noqa: BLE001 — try next id on collision
                    continue
            if created is None:
                st.error(t("error.persona_editor"))
                return
            st.session_state.persona_id = created.id
            flushed = _flush_pending_to_persona(created.id)
            if flushed:
                _clear_rag_cache(created.id)
                try:
                    refreshed = load_available_personas(settings)
                    target = next((p for p in refreshed if p.id == created.id), created)
                    _rebuild_persona_index(target)
                except Exception as exc:  # noqa: BLE001
                    _render_error(exc)
            finish_to_chat(entry=entry)
            st.rerun()

    if st.button(t("action.back_welcome"), key="welcome_back_role"):
        # Return to the path that led here.
        prev = st.session_state.get("entry_path") or "gate"
        if prev in {"api", "knowledge"}:
            set_welcome_stage(prev)  # type: ignore[arg-type]
        else:
            back_to_gate()
        st.rerun()


def render_onboarding(personas: list[PersonaPack]) -> None:
    """Welcome gate → api | knowledge → role → chat-ready."""
    stage = st.session_state.get("welcome_stage") or "gate"
    entry = st.session_state.get("entry_path")
    if stage == "role":
        render_role_step(personas)
        return
    if entry == "api" or stage == "api":
        render_api_path()
        return
    if entry == "knowledge" or stage == "knowledge":
        render_knowledge_path(personas)
        return
    render_gate(personas)
