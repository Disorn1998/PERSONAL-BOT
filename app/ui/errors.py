"""Thai error card rendering helpers (copy from strings.py only)."""

from __future__ import annotations

from app.errors import AppError, ErrorInfo, to_error_info
from app.i18n import t


def format_error_card(info: ErrorInfo) -> tuple[str, str | None]:
    """Return (title, hint) resolved through i18n."""
    title = t(info.string_key)
    hint = t(info.hint_key) if info.hint_key else None
    return title, hint


def error_from_exception(exc: BaseException) -> ErrorInfo:
    if isinstance(exc, AppError):
        return exc.to_info()
    return to_error_info(exc)
