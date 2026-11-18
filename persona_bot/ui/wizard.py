"""First-run wizard helpers (progress copy + markup)."""

from __future__ import annotations

from typing import Any

from persona_bot.i18n import t


def wizard_step(*, has_key: bool, privacy_ack: bool) -> int:
    """1 = API key, 2 = privacy ack, 3 = ready to chat."""
    if not has_key:
        return 1
    if not privacy_ack:
        return 2
    return 3


def overwrite_confirm_required(conflict: str, preview: dict[str, Any] | None) -> bool:
    """True when import would overwrite an existing user pack id."""
    if conflict != "overwrite" or not preview:
        return False
    return bool(preview.get("duplicate_of"))


def progress_labels() -> tuple[str, str, str]:
    return (
        t("wizard.step1"),
        t("wizard.step2"),
        t("wizard.step3"),
    )


def progress_markup(current: int) -> str:
    """HTML progress row for steps 1–3 (current is 1-based)."""
    labels = progress_labels()
    parts: list[str] = []
    for idx, label in enumerate(labels, start=1):
        cls = "pb-wizard-step"
        if idx < current:
            cls += " done"
        elif idx == current:
            cls += " active"
        parts.append(f'<span class="{cls}"><span class="n">{idx}</span> {label}</span>')
    return (
        f'<div class="pb-wizard" role="list" aria-label="{t("label.first_run")}">'
        + "".join(parts)
        + "</div>"
    )
