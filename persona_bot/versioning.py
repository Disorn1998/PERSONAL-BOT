"""App version + data/version.json migration helpers."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

# Bump when on-disk data layout changes (chat schema, manifests, …).
DATA_SCHEMA_VERSION = 1


@dataclass(slots=True)
class VersionInfo:
    app_version: str
    data_schema: int
    migrated_from: int | None
    updated_at: float

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


def get_app_version() -> str:
    try:
        return version("persona-bot")
    except PackageNotFoundError:
        return "0.1.0"


def version_path(data_dir: Path) -> Path:
    return Path(data_dir) / "version.json"


def read_version_file(data_dir: Path) -> VersionInfo | None:
    path = version_path(data_dir)
    if not path.exists():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return VersionInfo(
            app_version=str(raw.get("app_version", "")),
            data_schema=int(raw.get("data_schema", 0)),
            migrated_from=raw.get("migrated_from"),
            updated_at=float(raw.get("updated_at", 0.0)),
        )
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return None


def write_version_file(data_dir: Path, info: VersionInfo) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    path = version_path(data_dir)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(
        json.dumps(info.to_json(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    tmp.replace(path)


def ensure_data_version(data_dir: Path) -> VersionInfo:
    """Create or migrate ``data/version.json``; currently a no-op schema bump."""
    current = read_version_file(data_dir)
    app_ver = get_app_version()
    if current is None:
        info = VersionInfo(
            app_version=app_ver,
            data_schema=DATA_SCHEMA_VERSION,
            migrated_from=None,
            updated_at=time.time(),
        )
        write_version_file(data_dir, info)
        return info
    if current.data_schema < DATA_SCHEMA_VERSION:
        # Placeholder for future migrations (chat/index layout).
        info = VersionInfo(
            app_version=app_ver,
            data_schema=DATA_SCHEMA_VERSION,
            migrated_from=current.data_schema,
            updated_at=time.time(),
        )
        write_version_file(data_dir, info)
        return info
    if current.app_version != app_ver:
        info = VersionInfo(
            app_version=app_ver,
            data_schema=current.data_schema,
            migrated_from=current.migrated_from,
            updated_at=time.time(),
        )
        write_version_file(data_dir, info)
        return info
    return current
