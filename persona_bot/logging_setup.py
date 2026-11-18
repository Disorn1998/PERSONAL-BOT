"""Logging configuration with secret redaction."""

from __future__ import annotations

import logging
import sys
from typing import Any

from app.security import redact_secrets


class RedactingFilter(logging.Filter):
    """Scrub API-key-like material from log records."""

    def __init__(self, *, extra_secrets: list[str] | None = None) -> None:
        super().__init__()
        self._extra = list(extra_secrets or [])

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = redact_secrets(str(record.msg), extra_secrets=self._extra)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {
                    k: redact_secrets(str(v), extra_secrets=self._extra)
                    if isinstance(v, str)
                    else v
                    for k, v in record.args.items()
                }
            elif isinstance(record.args, tuple):
                scrubbed: list[Any] = []
                for arg in record.args:
                    if isinstance(arg, str):
                        scrubbed.append(redact_secrets(arg, extra_secrets=self._extra))
                    else:
                        scrubbed.append(arg)
                record.args = tuple(scrubbed)
        return True


def setup_logging(level: str = "INFO", *, api_key: str = "") -> None:
    """Configure root logger once for the process."""
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level.upper())

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s"))
    extras = [api_key] if api_key else []
    handler.addFilter(RedactingFilter(extra_secrets=extras))
    root.addHandler(handler)

    # Keep noisy third-party loggers quieter by default.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
