"""Rate-limit header parsing and 429 classification."""

from __future__ import annotations

import pytest
from persona_bot.errors import RateLimitDayError, RateLimitMinuteError
from persona_bot.i18n import set_locale
from persona_bot.ratelimit import classify_429, parse_rate_limit_headers, parse_reset_to_seconds
from persona_bot.ui.errors import format_error_card, format_retry_after_line


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


def test_error_card_surfaces_retry_after() -> None:
    set_locale("en")
    try:
        err = classify_429(
            headers={
                "retry-after": "12",
                "x-ratelimit-reset-tokens": "7.66s",
                "x-ratelimit-remaining-tokens": "0",
            },
            body_text="tokens per minute",
        )
        assert isinstance(err, RateLimitMinuteError)
        line = format_retry_after_line(err.details)
        assert line is not None
        assert "12" in line
        title, hint = format_error_card(err.to_info())
        assert "quota" in title.lower() or "minute" in title.lower()
        assert hint is not None
        assert "12" in hint
        assert "7.66s" in hint
    finally:
        set_locale("th")
