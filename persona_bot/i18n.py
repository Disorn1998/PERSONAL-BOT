"""UI i18n helpers — Thai default, English secondary (§2 / Phase 4)."""

from __future__ import annotations

from typing import Any, Literal

from persona_bot.ui import strings

Locale = Literal["th", "en"]

DEFAULT_LOCALE: Locale = "th"
SUPPORTED_LOCALES: tuple[Locale, ...] = ("th", "en")

_current_locale: Locale = DEFAULT_LOCALE


def get_locale() -> Locale:
    return _current_locale


def set_locale(locale: str) -> Locale:
    """Set process-local UI locale (Streamlit stores the choice in session_state)."""
    global _current_locale
    _current_locale = locale if locale in SUPPORTED_LOCALES else DEFAULT_LOCALE  # type: ignore[assignment]
    return _current_locale


def t(key: str, *, locale: str | None = None, **kwargs: Any) -> str:
    """Resolve a UI string by key.

    Falls back to Thai, then to the key itself when missing so missing copy is visible.
    """
    loc = locale or _current_locale
    table = strings.STRINGS.get(loc) or strings.STRINGS[DEFAULT_LOCALE]
    template = table.get(key)
    if template is None and loc != DEFAULT_LOCALE:
        template = strings.STRINGS[DEFAULT_LOCALE].get(key)
    if template is None:
        template = key
    if kwargs:
        return template.format(**kwargs)
    return template
