"""Optional OS keyring storage for the Groq API key (never under data/)."""

from __future__ import annotations

import os
from typing import Final

SERVICE_NAME: Final[str] = "persona-bot"
USERNAME: Final[str] = "groq_api_key"
# Separate keyring entry so UI checkbox opt-in survives restarts without env.
_OPT_IN_USERNAME: Final[str] = "remember_key_opt_in"


def env_remember_enabled() -> bool:
    raw = os.environ.get("PERSONA_BOT_REMEMBER_KEY", "").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def ui_remember_preference() -> bool:
    """True when the user previously opted in via the UI checkbox."""
    try:
        import keyring

        return (keyring.get_password(SERVICE_NAME, _OPT_IN_USERNAME) or "") == "1"
    except Exception:  # noqa: BLE001 — keyring backends vary by OS
        return False


def set_ui_remember_preference(enabled: bool) -> None:
    """Persist checkbox opt-in outside ``data/`` (keyring), so load works next run."""
    try:
        import keyring

        if enabled:
            keyring.set_password(SERVICE_NAME, _OPT_IN_USERNAME, "1")
        else:
            try:
                keyring.delete_password(SERVICE_NAME, _OPT_IN_USERNAME)
            except Exception:  # noqa: BLE001
                return
    except Exception:  # noqa: BLE001
        return


def remember_enabled() -> bool:
    """Env ``PERSONA_BOT_REMEMBER_KEY`` **or** prior UI checkbox opt-in."""
    return env_remember_enabled() or ui_remember_preference()


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
    set_ui_remember_preference(False)


def remember_status_key(*, loaded_from_keyring: bool = False) -> str:
    """Return a ``strings.py`` status key describing remember-key state."""
    if loaded_from_keyring:
        return "status.remember_loaded"
    if env_remember_enabled():
        return "status.remember_env"
    if ui_remember_preference():
        return "status.remember_ui"
    return "status.remember_session_only"
