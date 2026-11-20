"""Safe local ``.env`` upsert helpers for beginner BYOK (never log secret values).

Writing ``GROQ_API_KEY`` to a project ``.env`` is an **intentional** product
choice so first-run users get the same file they would hand-edit. The key is
never logged; optional OS keyring remains available for vault-style storage.
``data/`` and export/backup paths must never receive this secret.
"""

from __future__ import annotations

import os
import re
import stat
from pathlib import Path

_ENV_LINE_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=")


def default_env_path() -> Path:
    """Project ``.env`` (cwd) or ``PERSONA_BOT_ENV_FILE`` override for tests."""
    override = os.environ.get("PERSONA_BOT_ENV_FILE", "").strip()
    if override:
        return Path(override)
    return Path(".env")


def _restrict_env_file_permissions(path: Path) -> None:
    """Best-effort owner-only mode (``0o600``). No-op when the OS rejects chmod."""
    try:
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        # Windows / restricted FS — file still written; caller must not log secrets.
        return


def _write_local_env_bytes(path: Path, payload: bytes) -> None:
    """Persist local ``.env`` bytes with restrictive perms when supported.

    This is the single clear-text sink for beginner BYOK ``.env`` upserts.
    Equivalent to a hand-edited ``.env``; never commit the file; never log
    ``payload``. CodeQL: intentional local secret file, not remote exfil.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    # Owner read/write only on create (Unix). Windows may ignore mode bits.
    fd = os.open(path, flags, 0o600)
    try:
        # Local BYOK .env for beginners (same as manual edit). Never log.
        os.write(fd, payload)  # codeql[py/clear-text-storage-sensitive-data]  # nosec
    finally:
        os.close(fd)
    _restrict_env_file_permissions(path)


def _format_env_assignment(name: str, value: str) -> str:
    """Build one ``KEY=value`` line; does not log ``value``."""
    raw_value = value.strip()
    # Quote when value has spaces or special shell-ish chars.
    if raw_value and re.search(r'[\s#"\'\\]', raw_value):
        escaped = raw_value.replace("\\", "\\\\").replace('"', '\\"')
        return f'{name}="{escaped}"\n'
    return f"{name}={raw_value}\n"


def upsert_env_var(env_path: Path, key: str, value: str) -> Path:
    """Insert or replace ``KEY=value`` in an ``.env`` file.

    - Creates the file (and parents) when missing.
    - Preserves unrelated lines and comments.
    - Restricts file mode to owner read/write when the OS allows.
    - Does **not** log ``value``.
    """
    name = key.strip()
    if not name or not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", name):
        raise ValueError(f"invalid env key: {key!r}")
    line = _format_env_assignment(name, value)
    path = Path(env_path)

    if not path.is_file():
        _write_local_env_bytes(path, line.encode("utf-8"))
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
    # Rewrite whole file through the documented local-secret sink (never log).
    _write_local_env_bytes(path, "".join(out).encode("utf-8"))
    return path


def upsert_groq_api_key(api_key: str, *, env_path: Path | None = None) -> Path:
    """Persist ``GROQ_API_KEY`` into local ``.env`` for beginner BYOK.

    Session state still owns the live key for the current run. Optional OS
    keyring remains available via ``keyring_store``. Never log ``api_key``.

    Note: Copilot Autofix suggested refusing clear-text writes; we keep the
    intentional local ``.env`` upsert (product plan) with owner-only mode and
    CodeQL alert suppression on the documented sink instead.
    """
    key = api_key.strip()
    if not key:
        raise ValueError("empty API key")
    return upsert_env_var(env_path or default_env_path(), "GROQ_API_KEY", key)
