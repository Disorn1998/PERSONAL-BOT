"""Safe Persona Pack zip import/export (zip-bomb / symlink / whitelist)."""

from __future__ import annotations

import io
import re
import shutil
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, BinaryIO, Literal

from persona_bot.errors import AppError, PersonaLoadError
from persona_bot.persona import PersonaPack, load_persona_yaml, save_persona_yaml
from persona_bot.security import assert_no_secret_in_mapping

ConflictPolicy = Literal["reject", "rename", "overwrite"]

# Whitelist — root + knowledge + optional avatar only.
_PERSONA_YAML = "persona.yaml"
_KNOWLEDGE_PREFIX = "knowledge/"
_ALLOWED_KNOWLEDGE_SUFFIX = (".txt", ".md", ".pdf", ".docx")
_ALLOWED_AVATAR_SUFFIX = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg")
_AVATAR_NAMES = tuple(f"avatar{ext}" for ext in _ALLOWED_AVATAR_SUFFIX)

# Zip-bomb / size guards (bytes / counts).
DEFAULT_MAX_UNCOMPRESSED_BYTES = 80 * 1024 * 1024
DEFAULT_MAX_MEMBER_BYTES = 40 * 1024 * 1024
DEFAULT_MAX_MEMBERS = 200
DEFAULT_MAX_COMPRESSION_RATIO = 100.0

_ID_SAFE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


class PersonaPackIoError(AppError):
    code = "error.persona_pack_io"
    string_key = "error.persona_pack_io"
    hint_key = "error.hint.persona_pack_io"


@dataclass(slots=True)
class PackMemberPreview:
    name: str
    size: int
    kind: str


@dataclass(slots=True)
class PackPreview:
    """Safe preview of a zip before import (no extraction to disk)."""

    persona_id: str
    persona_name: str
    description: str
    members: list[PackMemberPreview] = field(default_factory=list)
    knowledge_files: list[str] = field(default_factory=list)
    duplicate_of: str | None = None
    warnings: list[str] = field(default_factory=list)
    total_uncompressed: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "persona_id": self.persona_id,
            "persona_name": self.persona_name,
            "description": self.description,
            "members": [{"name": m.name, "size": m.size, "kind": m.kind} for m in self.members],
            "knowledge_files": list(self.knowledge_files),
            "duplicate_of": self.duplicate_of,
            "warnings": list(self.warnings),
            "total_uncompressed": self.total_uncompressed,
        }


def _normalize_member_name(name: str) -> str:
    # Zip entries may use backslashes on Windows-created archives.
    cleaned = name.replace("\\", "/").lstrip("/")
    if cleaned.startswith("./"):
        cleaned = cleaned[2:]
    return cleaned


def _is_symlink_info(info: zipfile.ZipInfo) -> bool:
    # Unix symlink: upper 4 bits of external_attr create mode == 0o120000
    return (info.external_attr >> 16) & 0o170000 == 0o120000


def _classify_member(name: str) -> str | None:
    if name == _PERSONA_YAML:
        return "persona"
    if name in _AVATAR_NAMES:
        return "avatar"
    if name.startswith(_KNOWLEDGE_PREFIX) and not name.endswith("/"):
        rel = name[len(_KNOWLEDGE_PREFIX) :]
        if not rel or ".." in rel.split("/"):
            return None
        lower = rel.lower()
        if any(lower.endswith(suf) for suf in _ALLOWED_KNOWLEDGE_SUFFIX):
            return "knowledge"
    return None


def _validate_zip_members(
    zf: zipfile.ZipFile,
    *,
    max_uncompressed_bytes: int,
    max_member_bytes: int,
    max_members: int,
    max_compression_ratio: float,
) -> tuple[list[zipfile.ZipInfo], list[str], int]:
    infos = [i for i in zf.infolist() if not i.is_dir()]
    if len(infos) > max_members:
        raise PersonaPackIoError(
            "too many zip members",
            details={"count": len(infos), "max": max_members},
        )

    allowed: list[zipfile.ZipInfo] = []
    warnings: list[str] = []
    total = 0
    seen_names: set[str] = set()

    for info in infos:
        name = _normalize_member_name(info.filename)
        if not name or name.endswith("/"):
            continue
        if name != info.filename.replace("\\", "/").lstrip("/"):
            # Keep using normalized name going forward.
            pass
        if ".." in Path(name).parts or name.startswith("/") or ":" in name.split("/")[0]:
            raise PersonaPackIoError(
                "path traversal rejected",
                details={"member": info.filename},
            )
        if _is_symlink_info(info):
            raise PersonaPackIoError(
                "symlink members are not allowed",
                details={"member": info.filename},
            )
        kind = _classify_member(name)
        if kind is None:
            raise PersonaPackIoError(
                "member not on whitelist",
                details={"member": name},
            )
        if name in seen_names:
            raise PersonaPackIoError(
                "duplicate member name",
                details={"member": name},
            )
        seen_names.add(name)
        size = int(info.file_size)
        if size < 0 or size > max_member_bytes:
            raise PersonaPackIoError(
                "member too large",
                details={"member": name, "size": size},
            )
        compressed = max(1, int(info.compress_size) or 1)
        ratio = float(size) / float(compressed)
        if size > 1024 and ratio > max_compression_ratio:
            raise PersonaPackIoError(
                "suspicious compression ratio",
                details={"member": name, "ratio": ratio},
            )
        total += size
        if total > max_uncompressed_bytes:
            raise PersonaPackIoError(
                "uncompressed size exceeds limit",
                details={"total": total, "max": max_uncompressed_bytes},
            )
        # Store normalized filename on a shallow copy via filename rewrite for extract.
        info.filename = name
        allowed.append(info)

    if _PERSONA_YAML not in seen_names:
        raise PersonaPackIoError("persona.yaml missing from zip")

    return allowed, warnings, total


def preview_persona_zip(
    source: Path | BinaryIO | bytes,
    *,
    personas_dir: Path,
    max_uncompressed_bytes: int = DEFAULT_MAX_UNCOMPRESSED_BYTES,
    max_member_bytes: int = DEFAULT_MAX_MEMBER_BYTES,
    max_members: int = DEFAULT_MAX_MEMBERS,
    max_compression_ratio: float = DEFAULT_MAX_COMPRESSION_RATIO,
) -> PackPreview:
    """Inspect a zip in memory and return a preview (no disk write)."""
    raw = _read_zip_bytes(source)
    with zipfile.ZipFile(io.BytesIO(raw), mode="r") as zf:
        members, warnings, total = _validate_zip_members(
            zf,
            max_uncompressed_bytes=max_uncompressed_bytes,
            max_member_bytes=max_member_bytes,
            max_members=max_members,
            max_compression_ratio=max_compression_ratio,
        )
        yaml_bytes = zf.read(_PERSONA_YAML)
        try:
            text = yaml_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise PersonaPackIoError("persona.yaml must be UTF-8") from exc
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as td:
            path = Path(td) / _PERSONA_YAML
            path.write_text(text, encoding="utf-8")
            pack = load_persona_yaml(path)

        previews: list[PackMemberPreview] = []
        knowledge: list[str] = []
        for info in members:
            kind = _classify_member(info.filename) or "other"
            previews.append(
                PackMemberPreview(name=info.filename, size=int(info.file_size), kind=kind)
            )
            if kind == "knowledge":
                knowledge.append(info.filename[len(_KNOWLEDGE_PREFIX) :])

        duplicate = None
        if (personas_dir / pack.id / _PERSONA_YAML).exists():
            duplicate = pack.id
            warnings.append(f"duplicate id: {pack.id}")

        return PackPreview(
            persona_id=pack.id,
            persona_name=pack.name,
            description=pack.description,
            members=previews,
            knowledge_files=knowledge,
            duplicate_of=duplicate,
            warnings=warnings,
            total_uncompressed=total,
        )


def export_persona_zip(
    persona_dir: Path,
    *,
    dest: Path | None = None,
    api_key: str = "",
) -> bytes:
    """Zip a persona directory (whitelist only). Returns zip bytes; optionally writes ``dest``."""
    yaml_path = persona_dir / _PERSONA_YAML
    if not yaml_path.exists():
        raise PersonaPackIoError("persona.yaml not found", details={"dir": str(persona_dir)})
    pack = load_persona_yaml(yaml_path)
    forbidden = [api_key] if api_key else []
    assert_no_secret_in_mapping(pack.model_dump(mode="python"), forbidden=forbidden)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(yaml_path, arcname=_PERSONA_YAML)
        knowledge = persona_dir / "knowledge"
        if knowledge.is_dir():
            for path in sorted(knowledge.rglob("*")):
                if not path.is_file():
                    continue
                if path.is_symlink():
                    raise PersonaPackIoError(
                        "refusing to export symlink",
                        details={"path": str(path)},
                    )
                rel = path.relative_to(persona_dir).as_posix()
                if _classify_member(rel) != "knowledge":
                    continue
                zf.write(path, arcname=rel)
        for avatar_name in _AVATAR_NAMES:
            avatar = persona_dir / avatar_name
            if avatar.is_file() and not avatar.is_symlink():
                zf.write(avatar, arcname=avatar_name)

    data = buf.getvalue()
    if dest is not None:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
    return data


def import_persona_zip(
    source: Path | BinaryIO | bytes,
    *,
    personas_dir: Path,
    conflict: ConflictPolicy = "reject",
    max_uncompressed_bytes: int = DEFAULT_MAX_UNCOMPRESSED_BYTES,
    max_member_bytes: int = DEFAULT_MAX_MEMBER_BYTES,
    max_members: int = DEFAULT_MAX_MEMBERS,
    max_compression_ratio: float = DEFAULT_MAX_COMPRESSION_RATIO,
) -> PersonaPack:
    """Validate, preview-equivalent checks, then extract into ``personas_dir/<id>/``."""
    preview = preview_persona_zip(
        source,
        personas_dir=personas_dir,
        max_uncompressed_bytes=max_uncompressed_bytes,
        max_member_bytes=max_member_bytes,
        max_members=max_members,
        max_compression_ratio=max_compression_ratio,
    )
    target_id = preview.persona_id
    if preview.duplicate_of:
        if conflict == "reject":
            raise PersonaPackIoError(
                "duplicate persona id",
                details={"id": target_id},
            )
        if conflict == "rename":
            target_id = _allocate_unique_id(personas_dir, preview.persona_id)
        # overwrite: reuse target_id

    raw = _read_zip_bytes(source)
    personas_dir.mkdir(parents=True, exist_ok=True)
    target_dir = personas_dir / target_id
    staging = personas_dir / f".import-staging-{target_id}"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True, exist_ok=True)

    try:
        with zipfile.ZipFile(io.BytesIO(raw), mode="r") as zf:
            members, _, _ = _validate_zip_members(
                zf,
                max_uncompressed_bytes=max_uncompressed_bytes,
                max_member_bytes=max_member_bytes,
                max_members=max_members,
                max_compression_ratio=max_compression_ratio,
            )
            for info in members:
                name = _normalize_member_name(info.filename)
                out_path = staging / name
                out_path.parent.mkdir(parents=True, exist_ok=True)
                # Never follow links; write bytes directly.
                data = zf.read(info)
                if len(data) != int(info.file_size):
                    # Some zip tools lie; still bound by max_member already checked.
                    pass
                out_path.write_bytes(data)
                if out_path.is_symlink():
                    raise PersonaPackIoError("symlink created during extract")

        pack = load_persona_yaml(staging / _PERSONA_YAML)
        if target_id != pack.id:
            pack = pack.model_copy(update={"id": target_id})
            save_persona_yaml(pack, staging / _PERSONA_YAML)

        if target_dir.exists() and conflict == "overwrite":
            shutil.rmtree(target_dir)
        elif target_dir.exists():
            raise PersonaPackIoError(
                "target directory exists",
                details={"id": target_id},
            )
        staging.rename(target_dir)
        return load_persona_yaml(target_dir / _PERSONA_YAML)
    except (PersonaLoadError, PersonaPackIoError):
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)
        raise
    except Exception as exc:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)
        raise PersonaPackIoError(str(exc), details={"id": target_id}) from exc


def delete_user_persona(*, personas_dir: Path, persona_id: str) -> None:
    """Delete a user persona pack directory (never touches examples/)."""
    if not _ID_SAFE.match(persona_id):
        raise PersonaPackIoError("invalid persona id", details={"id": persona_id})
    target = personas_dir / persona_id
    if not target.exists():
        raise PersonaPackIoError("persona not found", details={"id": persona_id})
    if target.is_symlink():
        raise PersonaPackIoError("refusing to delete symlink persona dir")
    shutil.rmtree(target)


def _allocate_unique_id(personas_dir: Path, base: str) -> str:
    candidate = f"{base}-import"
    n = 2
    while (personas_dir / candidate / _PERSONA_YAML).exists():
        candidate = f"{base}-import-{n}"
        n += 1
        if n > 1000:
            raise PersonaPackIoError("could not allocate unique persona id")
    return candidate


def _read_zip_bytes(source: Path | BinaryIO | bytes) -> bytes:
    if isinstance(source, bytes):
        return source
    if isinstance(source, Path):
        return source.read_bytes()
    data = source.read()
    if isinstance(data, bytes):
        return data
    raise PersonaPackIoError("zip source must be bytes")
