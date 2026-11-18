"""Secret redaction and logging filter."""

from __future__ import annotations

import logging

import pytest
from persona_bot.logging_setup import setup_logging
from persona_bot.security import (
    hostname_equals,
    hostname_in_allowlist,
    password_ok,
    redact_secrets,
    safe_exception_message,
    url_hostname,
)


def test_redact_gsk_and_bearer() -> None:
    text = "Authorization: Bearer gsk_abcdefghijklmnop and key=sk-1234567890abcd"
    out = redact_secrets(text)
    assert "gsk_abcdefghijklmnop" not in out
    assert "sk-1234567890abcd" not in out


def test_safe_exception_message_strips_explicit_key() -> None:
    key = "super-secret-key-value"
    msg = safe_exception_message(RuntimeError(f"failed with {key}"), api_key=key)
    assert key not in msg
    assert "***REDACTED***" in msg


def test_password_gate() -> None:
    assert password_ok("", "anything")
    assert password_ok("secret", "secret")
    assert not password_ok("secret", "nope")


def test_logging_filter_redacts(caplog: pytest.LogCaptureFixture) -> None:
    setup_logging("INFO", api_key="gsk_TESTKEY12345678")
    logger = logging.getLogger("test.security")
    with caplog.at_level(logging.INFO):
        logger.info("using gsk_TESTKEY12345678 now")
    assert "gsk_TESTKEY12345678" not in caplog.text


def test_url_hostname_equality_not_substring() -> None:
    assert url_hostname("https://api.groq.com/openai/v1") == "api.groq.com"
    assert hostname_equals("https://api.groq.com/openai/v1", "api.groq.com")
    assert hostname_equals("https://API.Groq.Com/openai/v1", "api.groq.com")
    # Substring decoys must not pass — the CodeQL class of bug.
    assert not hostname_equals("https://evil.example/?q=api.groq.com", "api.groq.com")
    assert not hostname_equals("https://api.groq.com.evil.example/v1", "api.groq.com")
    assert not hostname_equals("https://notgroq.com/api.groq.com", "api.groq.com")
    assert hostname_in_allowlist(
        "http://fake-groq:8080/v1",
        ("api.groq.com", "fake-groq", "127.0.0.1"),
    )
    assert not hostname_in_allowlist("https://attacker.test/v1", ("api.groq.com",))
