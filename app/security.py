"""Security helpers — never leak API keys into logs, data, or exception text (DoD 4)."""

from __future__ import annotations

import re
from typing import Any

_KEY_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?i)(api[_-]?key|authorization|bearer)\s*[:=]\s*([^\s,;]+)"),
    re.compile(r"(?i)bearer\s+([a-z0-9\-._~+/]+=*)"),
    re.compile(r"gsk_[A-Za-z0-9]{8,}"),
    re.compile(r"sk-[A-Za-z0-9]{8,}"),
)

REDACTED = "***REDACTED***"


def redact_secrets(text: str, *, extra_secrets: list[str] | None = None) -> str:
    """Return ``text`` with known secret shapes and explicit values scrubbed."""
    if not text:
        return text
    scrubbed = text
    for pattern in _KEY_PATTERNS:
        scrubbed = pattern.sub(REDACTED, scrubbed)
    for secret in extra_secrets or []:
        if secret and secret in scrubbed:
            scrubbed = scrubbed.replace(secret, REDACTED)
    return scrubbed


def safe_exception_message(exc: BaseException, *, api_key: str = "") -> str:
    extras = [api_key] if api_key else None
    return redact_secrets(str(exc), extra_secrets=extras)


def assert_no_secret_in_mapping(data: dict[str, Any], *, forbidden: list[str]) -> None:
    """Raise if any forbidden secret substring appears in string values (export checks)."""
    blob = " ".join(str(v) for v in data.values())
    for secret in forbidden:
        if secret and secret in blob:
            msg = "secret value must not appear in persisted/exported data"
            raise ValueError(msg)


def password_ok(configured: str, provided: str) -> bool:
    """Optional APP_PASSWORD gate (not multi-user login — §16.7)."""
    if not configured:
        return True
    return configured == provided
