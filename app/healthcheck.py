"""System health checks for first-run wizard / sidebar (no Groq chat calls)."""

from __future__ import annotations

import shutil
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from app.config import Settings
from app.versioning import ensure_data_version, get_app_version


@dataclass(slots=True)
class HealthReport:
    ok: bool
    app_version: str
    python_ok: bool
    data_dir_writable: bool
    env_file_present: bool
    models_configured: bool
    api_key_present: bool
    disk_free_mb: float | None
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def run_health_check(
    settings: Settings,
    *,
    api_key: str = "",
    project_root: Path | None = None,
) -> HealthReport:
    root = project_root or Path.cwd()
    notes: list[str] = []
    data_dir = settings.data_dir
    if not data_dir.is_absolute():
        data_dir = (root / data_dir).resolve()
    data_dir.mkdir(parents=True, exist_ok=True)
    ensure_data_version(data_dir)

    writable = False
    try:
        probe = data_dir / ".write_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        writable = True
    except OSError:
        notes.append("data_dir_not_writable")

    env_present = (root / ".env").exists()
    if not env_present:
        notes.append("env_missing")

    try:
        primary, _fallback = settings.require_models()
        models_ok = bool(primary)
    except ValueError:
        models_ok = False
        notes.append("models_unset")

    key_ok = bool(api_key.strip() or settings.groq_api_key.strip())
    if not key_ok:
        notes.append("api_key_missing")

    disk_free: float | None
    try:
        disk_free = shutil.disk_usage(data_dir).free / (1024 * 1024)
    except OSError:
        disk_free = None

    ok = writable and models_ok and key_ok
    return HealthReport(
        ok=ok,
        app_version=get_app_version(),
        python_ok=True,
        data_dir_writable=writable,
        env_file_present=env_present,
        models_configured=models_ok,
        api_key_present=key_ok,
        disk_free_mb=disk_free,
        notes=notes,
    )
