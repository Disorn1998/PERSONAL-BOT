"""First-run guided tour — coach card + step state (no real 3D)."""

from __future__ import annotations

from pathlib import Path
from typing import Final, Literal

import streamlit as st

from persona_bot.i18n import t
from persona_bot.ui.assets import icon_data_uri, welcome_hero_data_uri

TourStep = Literal["welcome", "path", "persona", "knowledge", "chat", "done"]

TOUR_DONE_FILENAME: Final[str] = "tour_done"
TOUR_STEPS: Final[tuple[TourStep, ...]] = (
    "welcome",
    "path",
    "persona",
    "knowledge",
    "chat",
    "done",
)

_STEP_BODY_KEYS: Final[dict[TourStep, str]] = {
    "welcome": "tour.step.welcome",
    "path": "tour.step.path",
    "persona": "tour.step.persona",
    "knowledge": "tour.step.knowledge",
    "chat": "tour.step.chat",
    "done": "tour.step.done",
}


def tour_done_file(data_dir: Path) -> Path:
    return Path(data_dir) / TOUR_DONE_FILENAME


def is_tour_done(data_dir: Path) -> bool:
    return tour_done_file(data_dir).is_file()


def _sync_session_tour_done(*, active: bool) -> None:
    """Best-effort session update (no-op outside a Streamlit script run)."""
    try:
        st.session_state.tour_done = not active
        st.session_state.tour_active = active
    except Exception:  # noqa: BLE001 — unit tests may lack a script context
        return


def mark_tour_done(data_dir: Path) -> None:
    path = tour_done_file(data_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("1", encoding="utf-8")
    _sync_session_tour_done(active=False)


def clear_tour_done(data_dir: Path) -> None:
    path = tour_done_file(data_dir)
    if path.is_file():
        path.unlink()
    try:
        st.session_state.tour_done = False
    except Exception:  # noqa: BLE001
        return


def _step_index(step: TourStep) -> int:
    return TOUR_STEPS.index(step)


def _coerce_step(raw: object) -> TourStep:
    if isinstance(raw, str) and raw in TOUR_STEPS:
        return raw  # type: ignore[return-value]
    return "welcome"


def init_tour_state(data_dir: Path, *, wizard_done: bool) -> None:
    """Hydrate tour flags from ``data/tour_done`` + session."""
    ss = st.session_state
    done = is_tour_done(data_dir)
    ss.setdefault("tour_done", done)
    if done:
        ss["tour_done"] = True
        ss["tour_active"] = False
        ss.setdefault("tour_step", "done")
        return
    ss.setdefault("tour_active", True)
    if "tour_step" not in ss:
        # Returning users who already finished welcome skip gate steps.
        ss["tour_step"] = "persona" if wizard_done else "welcome"
    else:
        ss["tour_step"] = _coerce_step(ss["tour_step"])
    if ss.get("tour_active"):
        ss["tour_done"] = False


def current_tour_step() -> TourStep | None:
    if not st.session_state.get("tour_active"):
        return None
    if st.session_state.get("tour_done"):
        return None
    return _coerce_step(st.session_state.get("tour_step"))


def advance_tour(data_dir: Path) -> None:
    step = current_tour_step()
    if step is None:
        return
    idx = _step_index(step)
    if idx >= len(TOUR_STEPS) - 1:
        mark_tour_done(data_dir)
        return
    st.session_state.tour_step = TOUR_STEPS[idx + 1]


def skip_tour(data_dir: Path) -> None:
    mark_tour_done(data_dir)


def restart_tour(data_dir: Path, *, wizard_done: bool) -> None:
    clear_tour_done(data_dir)
    st.session_state.tour_active = True
    st.session_state.tour_done = False
    st.session_state.tour_step = "persona" if wizard_done else "welcome"


def coach_mascot_uri() -> str | None:
    """Prefer chat icon; fall back to welcome hero thumbnail."""
    uri = icon_data_uri("chat")
    if uri:
        return uri
    return welcome_hero_data_uri()


def tour_anchor_markup(step: TourStep) -> str:
    """Invisible marker so CSS can spotlight the nearby target."""
    return (
        f'<div class="pb-tour-anchor pb-tour-anchor-{step}" '
        f'data-tour-anchor="{step}" aria-hidden="true"></div>'
    )


def coach_card_markup(step: TourStep) -> str:
    """HTML coach bubble (mascot + short copy). Buttons stay as Streamlit widgets."""
    n = _step_index(step) + 1
    total = len(TOUR_STEPS)
    body = t(_STEP_BODY_KEYS[step])
    mascot = coach_mascot_uri()
    img = ""
    if mascot:
        img = f'<img class="pb-tour-mascot" src="{mascot}" alt="" width="56" height="56" />'
    return f"""
<div class="pb-tour-coach" data-tour-step="{step}" role="dialog" aria-label="{t("tour.title")}">
  <div class="pb-tour-coach-row">
    {img}
    <div class="pb-tour-coach-copy">
      <p class="pb-tour-progress">{t("tour.progress", n=n, total=total)}</p>
      <p class="pb-tour-body">{body}</p>
    </div>
  </div>
</div>
"""


def render_tour_coach(data_dir: Path) -> None:
    """Render coach card + Next/Skip (or Start using on the last step)."""
    step = current_tour_step()
    if step is None:
        return
    st.markdown(coach_card_markup(step), unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    if step == "done":
        with c1:
            if st.button(
                t("action.tour_start"),
                key="tour_finish_btn",
                type="primary",
                use_container_width=True,
            ):
                mark_tour_done(data_dir)
                st.rerun()
        with c2:
            if st.button(
                t("action.tour_skip"),
                key="tour_skip_btn",
                use_container_width=True,
            ):
                skip_tour(data_dir)
                st.rerun()
        return
    with c1:
        if st.button(
            t("action.tour_next"),
            key="tour_next_btn",
            type="primary",
            use_container_width=True,
        ):
            advance_tour(data_dir)
            st.rerun()
    with c2:
        if st.button(
            t("action.tour_skip"),
            key="tour_skip_btn",
            use_container_width=True,
        ):
            skip_tour(data_dir)
            st.rerun()
