"""Safe ``.env`` upsert helpers (never log secret values)."""

from __future__ import annotations

import os
import re
from pathlib import Path

_ENV_LINE_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=")


def default_env_path() -> Path:
    """Project ``.env`` (cwd) or ``PERSONA_BOT_ENV_FILE`` override for tests."""
    override = os.environ.get("PERSONA_BOT_ENV_FILE", "").strip()
    if override:
        return Path(override)
    return Path(".env")


def upsert_env_var(env_path: Path, key: str, value: str) -> Path:
    """Insert or replace ``KEY=value`` in an ``.env`` file.

    - Creates the file (and parents) when missing.
    - Preserves unrelated lines and comments.
    - Does **not** log ``value``.
    """
    name = key.strip()
    if not name or not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", name):
        raise ValueError(f"invalid env key: {key!r}")
    raw_value = value.strip()
    # Quote when value has spaces or special shell-ish chars.
    if raw_value and re.search(r'[\s#"\'\\]', raw_value):
        escaped = raw_value.replace("\\", "\\\\").replace('"', '\\"')
        line = f'{name}="{escaped}"\n'
    else:
        line = f"{name}={raw_value}\n"

    path = Path(env_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.is_file():
        path.write_text(line, encoding="utf-8")
        return path

    existing = path.read_text(encoding="utf-8")
    lines = existing.splitlines(keepends=True)
    replaced = False
    out: list[str] = []
    for current in lines:
        match = _ENV_LINE_RE.match(current)
        if match and match.group(1) == name:
            out.append(line)
            replaced = True
        else:
            out.append(current if current.endswith("\n") else f"{current}\n")
    if not replaced:
        if out and not out[-1].endswith("\n"):
            out[-1] = f"{out[-1]}\n"
        out.append(line)
    path.write_text("".join(out), encoding="utf-8")
    return path


def upsert_groq_api_key(api_key: str, *, env_path: Path | None = None) -> Path:
    """Persist ``GROQ_API_KEY`` into ``.env`` (session still owns the live key)."""
    key = api_key.strip()
    if not key:
        raise ValueError("empty API key")
    return upsert_env_var(env_path or default_env_path(), "GROQ_API_KEY", key)
