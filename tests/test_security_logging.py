"""Secret redaction and logging filter."""

from __future__ import annotations

import logging

import pytest
from app.logging_setup import setup_logging
from app.security import password_ok, redact_secrets, safe_exception_message


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
