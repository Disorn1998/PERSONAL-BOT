"""Backup / restore / wipe helpers for ``data/`` (never includes API keys)."""

from __future__ import annotations

import io
import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

from app.errors import AppError
from app.persona_pack_io import (
    DEFAULT_MAX_COMPRESSION_RATIO,
    DEFAULT_MAX_MEMBER_BYTES,
    DEFAULT_MAX_MEMBERS,
    DEFAULT_MAX_UNCOMPRESSED_BYTES,
)
from app.security import redact_secrets
from app.versioning import ensure_data_version

# Paths under data/ that must never appear in a backup archive.
_FORBIDDEN_NAME_PARTS = (".env", "api_key", "groq_api_key")


class BackupError(AppError):
    code = "error.backup"
    string_key = "error.backup"
    hint_key = "error.hint.backup"


@dataclass(slots=True)
class BackupSummary:
    member_count: int
    total_bytes: int
    path: str | None = None


def _is_forbidden(rel: str) -> bool:
    lower = rel.lower().replace("\\", "/")
    name = Path(lower).name
    if name.startswith(".env"):
        return True
    return any(part in lower for part in _FORBIDDEN_NAME_PARTS)


def create_backup(
    data_dir: Path,
    *,
    dest: Path | None = None,
    api_key: str = "",
) -> tuple[bytes, BackupSummary]:
    """Zip the contents of ``data_dir`` excluding secret-looking files."""
    if not data_dir.exists():
        data_dir.mkdir(parents=True, exist_ok=True)
    ensure_data_version(data_dir)

    buf = io.BytesIO()
    count = 0
    total = 0
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(data_dir.rglob("*")):
            if not path.is_file():
                continue
            if path.is_symlink():
                continue
            rel = path.relative_to(data_dir).as_posix()
            if _is_forbidden(rel):
                continue
            # Skip staging leftovers
            if rel.startswith(".import-staging-"):
                continue
            data = path.read_bytes()
            if api_key and api_key.encode("utf-8") in data:
                raise BackupError(
                    "refusing to backup file containing API key",
                    details={"path": rel},
                )
            zf.writestr(rel, data)
            count += 1
            total += len(data)

    payload = buf.getvalue()
    summary = BackupSummary(member_count=count, total_bytes=total, path=str(dest) if dest else None)
    if dest is not None:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(payload)
        summary.path = str(dest)
    return payload, summary


def restore_backup(
    source: Path | BinaryIO | bytes,
    *,
    data_dir: Path,
    max_uncompressed_bytes: int = DEFAULT_MAX_UNCOMPRESSED_BYTES,
    max_member_bytes: int = DEFAULT_MAX_MEMBER_BYTES,
    max_members: int = DEFAULT_MAX_MEMBERS,
    max_compression_ratio: float = DEFAULT_MAX_COMPRESSION_RATIO,
) -> BackupSummary:
    """Replace ``data_dir`` contents with a previously created backup zip."""
    raw = (
        source
        if isinstance(source, bytes)
        else (source.read_bytes() if isinstance(source, Path) else source.read())
    )
    if not isinstance(raw, bytes):
        raise BackupError("backup source must be bytes")

    staging = data_dir.parent / f".restore-staging-{data_dir.name}"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True, exist_ok=True)

    try:
        with zipfile.ZipFile(io.BytesIO(raw), mode="r") as zf:
            infos = [i for i in zf.infolist() if not i.is_dir()]
            if len(infos) > max_members:
                raise BackupError("too many backup members", details={"count": len(infos)})
            total = 0
            for info in infos:
                name = info.filename.replace("\\", "/").lstrip("/")
                if not name or ".." in Path(name).parts or name.startswith("/"):
                    raise BackupError("path traversal in backup", details={"member": info.filename})
                if (info.external_attr >> 16) & 0o170000 == 0o120000:
                    raise BackupError("symlink in backup rejected", details={"member": name})
                if _is_forbidden(name):
                    raise BackupError("forbidden file in backup", details={"member": name})
                size = int(info.file_size)
                if size > max_member_bytes:
                    raise BackupError("backup member too large", details={"member": name})
                compressed = max(1, int(info.compress_size) or 1)
                if size > 1024 and (size / compressed) > max_compression_ratio:
                    raise BackupError("suspicious compression ratio", details={"member": name})
                total += size
                if total > max_uncompressed_bytes:
                    raise BackupError("backup uncompressed size exceeds limit")
                out = staging / name
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_bytes(zf.read(info))
                if out.is_symlink():
                    raise BackupError("symlink created during restore")

        # Swap into place: wipe existing files under data_dir then move staging in.
        if data_dir.exists():
            for child in data_dir.iterdir():
                if child.is_dir() and not child.is_symlink():
                    shutil.rmtree(child)
                elif child.is_file() or child.is_symlink():
                    child.unlink()
        else:
            data_dir.mkdir(parents=True, exist_ok=True)
        for child in staging.iterdir():
            dest = data_dir / child.name
            shutil.move(str(child), str(dest))
        ensure_data_version(data_dir)
        return BackupSummary(member_count=len(infos), total_bytes=total, path=str(data_dir))
    except BackupError:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)
        raise
    except Exception as exc:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)
        raise BackupError(redact_secrets(str(exc))) from exc
    finally:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)


def delete_all_data(data_dir: Path, *, keep_version: bool = True) -> None:
    """Wipe runtime data under ``data_dir`` (chat, chroma, personas, usage)."""
    if not data_dir.exists():
        data_dir.mkdir(parents=True, exist_ok=True)
        if keep_version:
            ensure_data_version(data_dir)
        return
    for child in list(data_dir.iterdir()):
        if keep_version and child.name == "version.json":
            continue
        if child.is_symlink():
            child.unlink(missing_ok=True)
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink(missing_ok=True)
    if keep_version:
        ensure_data_version(data_dir)
