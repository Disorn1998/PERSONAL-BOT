"""Thai error card rendering helpers (copy from strings.py only)."""

from __future__ import annotations

from typing import Any

from persona_bot.errors import AppError, ErrorInfo, to_error_info
from persona_bot.i18n import t
from persona_bot.ratelimit import parse_reset_to_seconds


def format_error_card(info: ErrorInfo) -> tuple[str, str | None]:
    """Return (title, hint) resolved through i18n."""
    title = t(info.string_key)
    hint = t(info.hint_key) if info.hint_key else None
    retry_line = format_retry_after_line(info.details)
    if retry_line:
        hint = f"{hint}\n{retry_line}" if hint else retry_line
    return title, hint


def format_retry_after_line(details: dict[str, Any] | None) -> str | None:
    """Build a bilingual-friendly countdown / reset hint from 429 ``details``."""
    if not details:
        return None
    parts: list[str] = []
    retry = details.get("retry_after_seconds")
    if isinstance(retry, (int, float)) and retry > 0:
        seconds = int(retry) if float(retry).is_integer() else round(float(retry), 1)
        parts.append(t("error.hint.retry_after").format(seconds=seconds))
    for key, label_key in (
        ("reset_tokens", "error.hint.reset_tokens"),
        ("reset_requests", "error.hint.reset_requests"),
    ):
        raw = details.get(key)
        if not raw:
            continue
        parsed = parse_reset_to_seconds(str(raw))
        if parsed is not None:
            seconds = int(parsed) if float(parsed).is_integer() else round(float(parsed), 1)
            parts.append(t(label_key).format(reset=raw, seconds=seconds))
        else:
            parts.append(t(label_key).format(reset=raw, seconds=raw))
    if not parts:
        return None
    return " · ".join(parts)


def error_from_exception(exc: BaseException) -> ErrorInfo:
    if isinstance(exc, AppError):
        return exc.to_info()
    return to_error_info(exc)
