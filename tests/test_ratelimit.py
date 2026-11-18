"""Rate-limit header parsing and 429 classification."""

from __future__ import annotations

import pytest
from app.errors import RateLimitDayError, RateLimitMinuteError
from app.ratelimit import classify_429, parse_rate_limit_headers, parse_reset_to_seconds


def test_parse_headers() -> None:
    info = parse_rate_limit_headers(
        {
            "x-ratelimit-limit-requests": "1000",
            "x-ratelimit-remaining-requests": "12",
            "x-ratelimit-reset-requests": "6h12m3.5s",
            "x-ratelimit-limit-tokens": "8000",
            "x-ratelimit-remaining-tokens": "0",
            "x-ratelimit-reset-tokens": "7.66s",
            "retry-after": "2",
        }
    )
    assert info.limit_requests == 1000
    assert info.remaining_tokens == 0
    assert info.exhausted_minute_tokens
    assert info.retry_after_seconds == 2.0


def test_parse_reset_strings() -> None:
    assert parse_reset_to_seconds("7.66s") == pytest.approx(7.66)
    assert parse_reset_to_seconds("2m59.56s") == pytest.approx(179.56)
    assert parse_reset_to_seconds("1h") == pytest.approx(3600)


def test_classify_429_day_vs_minute() -> None:
    day = classify_429(body_text="Rate limit reached: requests per day (RPD)")
    assert isinstance(day, RateLimitDayError)
    minute = classify_429(
        headers={"x-ratelimit-remaining-tokens": "0", "x-ratelimit-remaining-requests": "50"}
    )
    assert isinstance(minute, RateLimitMinuteError)
