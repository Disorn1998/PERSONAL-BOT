"""Minimal i18n helpers (Phase 0).

UI language is Thai by default; identifiers stay English (§2).
"""

from __future__ import annotations

from typing import Any

from app.ui import strings

DEFAULT_LOCALE = "th"


def t(key: str, *, locale: str = DEFAULT_LOCALE, **kwargs: Any) -> str:
    """Resolve a UI string by key.

    Falls back to the key itself when missing so missing copy is visible in UI.
    """
    table = strings.STRINGS.get(locale) or strings.STRINGS[DEFAULT_LOCALE]
    template = table.get(key, key)
    if kwargs:
        return template.format(**kwargs)
    return template
