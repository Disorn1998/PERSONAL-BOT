"""Optional OS keyring storage for the Groq API key (never under data/)."""

from __future__ import annotations

import os
from typing import Final

SERVICE_NAME: Final[str] = "persona-bot"
USERNAME: Final[str] = "groq_api_key"


def remember_enabled() -> bool:
    raw = os.environ.get("PERSONA_BOT_REMEMBER_KEY", "").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def save_api_key(api_key: str) -> None:
    if not api_key.strip():
        return
    import keyring

    keyring.set_password(SERVICE_NAME, USERNAME, api_key.strip())


def load_api_key() -> str:
    try:
        import keyring

        value = keyring.get_password(SERVICE_NAME, USERNAME)
        return value or ""
    except Exception:  # noqa: BLE001 — keyring backends vary by OS
        return ""


def delete_api_key() -> None:
    try:
        import keyring

        keyring.delete_password(SERVICE_NAME, USERNAME)
    except Exception:  # noqa: BLE001
        return
