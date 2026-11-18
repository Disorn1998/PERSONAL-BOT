"""Groq / OpenAI-compatible rate-limit header parsing and 429 classification."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from app.errors import RateLimitDayError, RateLimitMinuteError

# Groq docs: *-requests → RPD; *-tokens → TPM. Reset values look like "7.66s" / "2m59s".
_RESET_RE = re.compile(
    r"^(?:(?P<hours>\d+)h)?(?:(?P<minutes>\d+)m)?(?:(?P<seconds>\d+(?:\.\d+)?)s)?$"
)


@dataclass(frozen=True, slots=True)
class RateLimitInfo:
    limit_requests: int | None = None
    remaining_requests: int | None = None
    reset_requests: str | None = None
    limit_tokens: int | None = None
    remaining_tokens: int | None = None
    reset_tokens: str | None = None
    retry_after_seconds: float | None = None

    @property
    def exhausted_daily_requests(self) -> bool:
        return self.remaining_requests is not None and self.remaining_requests <= 0

    @property
    def exhausted_minute_tokens(self) -> bool:
        return self.remaining_tokens is not None and self.remaining_tokens <= 0


def _header(headers: Mapping[str, str], name: str) -> str | None:
    target = name.lower()
    for key, value in headers.items():
        if key.lower() == target:
            return value
    return None


def _as_int(value: str | None) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except ValueError:
        return None


def _as_float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def parse_reset_to_seconds(value: str | None) -> float | None:
    """Parse Groq-style reset strings (``7.66s``, ``2m59.56s``, ``1h``) to seconds."""
    if not value:
        return None
    raw = value.strip().lower()
    # Plain number → seconds
    try:
        return float(raw)
    except ValueError:
        pass
    match = _RESET_RE.match(raw)
    if not match:
        return None
    hours = float(match.group("hours") or 0)
    minutes = float(match.group("minutes") or 0)
    seconds = float(match.group("seconds") or 0)
    total = hours * 3600 + minutes * 60 + seconds
    return total if total > 0 else None


def parse_rate_limit_headers(headers: Mapping[str, str]) -> RateLimitInfo:
    return RateLimitInfo(
        limit_requests=_as_int(_header(headers, "x-ratelimit-limit-requests")),
        remaining_requests=_as_int(_header(headers, "x-ratelimit-remaining-requests")),
        reset_requests=_header(headers, "x-ratelimit-reset-requests"),
        limit_tokens=_as_int(_header(headers, "x-ratelimit-limit-tokens")),
        remaining_tokens=_as_int(_header(headers, "x-ratelimit-remaining-tokens")),
        reset_tokens=_header(headers, "x-ratelimit-reset-tokens"),
        retry_after_seconds=_as_float(_header(headers, "retry-after")),
    )


def classify_429(
    *,
    headers: Mapping[str, str] | None = None,
    body_text: str = "",
) -> RateLimitMinuteError | RateLimitDayError:
    """Map a 429 into per-minute vs per-day app errors (DoD 3)."""
    info = parse_rate_limit_headers(headers or {})
    lowered = body_text.lower()
    details: dict[str, Any] = {
        "retry_after_seconds": info.retry_after_seconds,
        "reset_requests": info.reset_requests,
        "reset_tokens": info.reset_tokens,
        "remaining_requests": info.remaining_requests,
        "remaining_tokens": info.remaining_tokens,
    }

    # Prefer explicit body hints, then header exhaustion signals.
    if "per day" in lowered or "requests per day" in lowered or "rpd" in lowered:
        return RateLimitDayError(details=details)
    if "per minute" in lowered or "tokens per minute" in lowered or "tpm" in lowered:
        return RateLimitMinuteError(details=details)
    if info.exhausted_daily_requests and not info.exhausted_minute_tokens:
        return RateLimitDayError(details=details)
    if info.exhausted_minute_tokens:
        return RateLimitMinuteError(details=details)
    # Default: treat as short-window (retryable) minute limit.
    return RateLimitMinuteError(details=details)
