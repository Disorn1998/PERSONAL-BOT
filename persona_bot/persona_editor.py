"""In-app Persona Pack create/edit, duplicate, and knowledge upload (P0)."""

from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import BinaryIO

from persona_bot.config import EmbeddingPresetId, Settings
from persona_bot.errors import AppError
from persona_bot.persona import (
    AnswerMode,
    PersonaConfig,
    PersonaPack,
    load_persona_yaml,
    save_persona_yaml,
)
from persona_bot.rag.loaders import SUPPORTED_SUFFIXES, iter_knowledge_files
from persona_bot.services import is_user_persona, persona_dir_for

_ID_SAFE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
_FILENAME_SAFE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._ -]*$")

# Keep in sync with zip import whitelist (persona_pack_io).
ALLOWED_KNOWLEDGE_SUFFIXES = {".txt", ".md", ".pdf", ".docx"}

# Single-file upload cap (bytes) — also bounded by MAX_KNOWLEDGE_MB total.
DEFAULT_MAX_UPLOAD_BYTES = 40 * 1024 * 1024


class PersonaEditorError(AppError):
    code = "error.persona_editor"
    string_key = "error.persona_editor"
    hint_key = "error.hint.persona_editor"


def _require_safe_id(persona_id: str) -> str:
    value = persona_id.strip().lower()
    if not _ID_SAFE.match(value):
        raise PersonaEditorError(
            "invalid persona id",
            details={"id": persona_id},
        )
    return value


def _knowledge_dir(pack_dir: Path) -> Path:
    path = pack_dir / "knowledge"
    path.mkdir(parents=True, exist_ok=True)
    return path


def knowledge_total_bytes(knowledge_dir: Path) -> int:
    if not knowledge_dir.exists():
        return 0
    total = 0
    for path in knowledge_dir.rglob("*"):
        if path.is_file() and not path.is_symlink():
            total += path.stat().st_size
    return total


def _assert_within_knowledge_budget(
    knowledge_dir: Path,
    *,
    incoming_bytes: int,
    max_knowledge_mb: int,
) -> None:
    limit = max(1, int(max_knowledge_mb)) * 1024 * 1024
    current = knowledge_total_bytes(knowledge_dir)
    if current + incoming_bytes > limit:
        raise PersonaEditorError(
            "knowledge size limit exceeded",
            details={
                "current_bytes": current,
                "incoming_bytes": incoming_bytes,
                "max_bytes": limit,
            },
        )


def _safe_knowledge_filename(filename: str) -> str:
    name = Path(filename).name.strip()
    if not name or name in {".", ".."} or "/" in name or "\\" in name:
        raise PersonaEditorError("invalid knowledge filename", details={"name": filename})
    if name.startswith(".") or ".." in name:
        raise PersonaEditorError("invalid knowledge filename", details={"name": filename})
    if not _FILENAME_SAFE.match(name):
        raise PersonaEditorError("invalid knowledge filename", details={"name": filename})
    suffix = Path(name).suffix.lower()
    if suffix not in ALLOWED_KNOWLEDGE_SUFFIXES:
        raise PersonaEditorError(
            "unsupported knowledge type",
            details={"name": name, "suffix": suffix},
        )
    return name


def _allocate_unique_id(personas_dir: Path, base: str) -> str:
    """Return ``base`` or ``base-2``… when the preferred id is taken."""
    base = _require_safe_id(base)
    if not (personas_dir / base / "persona.yaml").exists():
        return base
    n = 2
    while True:
        candidate = f"{base}-{n}"
        if not (personas_dir / candidate / "persona.yaml").exists():
            return candidate
        n += 1
        if n > 1000:
            raise PersonaEditorError("could not allocate unique persona id")


def _sync_knowledge_files(pack: PersonaPack, pack_dir: Path) -> PersonaPack:
    kdir = pack_dir / "knowledge"
    files = [
        f"knowledge/{p.relative_to(kdir).as_posix()}"
        for p in iter_knowledge_files(kdir)
        if p.suffix.lower() in SUPPORTED_SUFFIXES
    ]
    updated = pack.model_copy(update={"knowledge_files": files})
    save_persona_yaml(updated, pack_dir / "persona.yaml")
    return updated


def create_user_persona(
    *,
    personas_dir: Path,
    persona_id: str,
    name: str,
    system_prompt: str,
    description: str = "",
    config: PersonaConfig | None = None,
    icon: str | None = None,
    greeting: str | None = None,
    starter_questions: list[str] | None = None,
) -> PersonaPack:
    """Create a new user Persona Pack under ``personas_dir/<id>/``."""
    pid = _require_safe_id(persona_id)
    target = personas_dir / pid
    if (target / "persona.yaml").exists():
        raise PersonaEditorError("persona id already exists", details={"id": pid})
    pack = PersonaPack(
        id=pid,
        name=name.strip(),
        description=description.strip(),
        system_prompt=system_prompt.strip(),
        config=config or PersonaConfig(),
        knowledge_files=[],
        icon=icon,
        greeting=greeting,
        starter_questions=list(starter_questions or []),
    )
    personas_dir.mkdir(parents=True, exist_ok=True)
    _knowledge_dir(target)
    save_persona_yaml(pack, target / "persona.yaml")
    return load_persona_yaml(target / "persona.yaml")


def save_user_persona(
    *,
    personas_dir: Path,
    pack: PersonaPack,
) -> PersonaPack:
    """Overwrite ``persona.yaml`` for an existing user pack (never examples)."""
    pid = _require_safe_id(pack.id)
    target = personas_dir / pid
    if not (target / "persona.yaml").exists():
        raise PersonaEditorError("user persona not found", details={"id": pid})
    if pack.id != pid:
        raise PersonaEditorError("persona id mismatch", details={"id": pack.id})
    _knowledge_dir(target)
    save_persona_yaml(pack, target / "persona.yaml")
    return _sync_knowledge_files(load_persona_yaml(target / "persona.yaml"), target)


def duplicate_persona_to_user(
    *,
    settings: Settings,
    source_id: str,
    new_id: str | None = None,
) -> PersonaPack:
    """Copy an example (or user) pack into ``personas_dir`` as an editable user pack.

    Default id is ``<source>-copy`` (with numeric suffix if taken).
    """
    source_dir = persona_dir_for(source_id, settings)
    if source_dir is None:
        raise PersonaEditorError("source persona not found", details={"id": source_id})
    source = load_persona_yaml(source_dir / "persona.yaml")
    preferred = new_id.strip().lower() if new_id else f"{source.id}-copy"
    target_id = _allocate_unique_id(settings.personas_dir, preferred)
    target = settings.personas_dir / target_id
    if target.exists():
        raise PersonaEditorError("target already exists", details={"id": target_id})

    settings.personas_dir.mkdir(parents=True, exist_ok=True)

    # Copy tree but never follow symlinks into unexpected locations.
    def _ignore_symlinks(directory: str, names: list[str]) -> set[str]:
        ignored: set[str] = set()
        root = Path(directory)
        for name in names:
            if (root / name).is_symlink():
                ignored.add(name)
        return ignored

    shutil.copytree(source_dir, target, ignore=_ignore_symlinks, symlinks=False)
    pack = source.model_copy(
        update={
            "id": target_id,
            "name": f"{source.name} (สำเนา)" if "(สำเนา)" not in source.name else source.name,
        }
    )
    save_persona_yaml(pack, target / "persona.yaml")
    return _sync_knowledge_files(load_persona_yaml(target / "persona.yaml"), target)


def add_knowledge_bytes(
    *,
    settings: Settings,
    persona_id: str,
    filename: str,
    data: bytes,
    max_upload_bytes: int = DEFAULT_MAX_UPLOAD_BYTES,
) -> Path:
    """Write an uploaded knowledge file into a **user** pack ``knowledge/``."""
    if not is_user_persona(persona_id, settings):
        raise PersonaEditorError(
            "examples are read-only — duplicate first",
            details={"id": persona_id},
        )
    safe_name = _safe_knowledge_filename(filename)
    if len(data) <= 0:
        raise PersonaEditorError("empty upload", details={"name": safe_name})
    if len(data) > max_upload_bytes:
        raise PersonaEditorError(
            "upload too large",
            details={"size": len(data), "max": max_upload_bytes},
        )
    pack_dir = settings.personas_dir / persona_id
    kdir = _knowledge_dir(pack_dir)
    _assert_within_knowledge_budget(
        kdir,
        incoming_bytes=len(data),
        max_knowledge_mb=settings.max_knowledge_mb,
    )
    dest = kdir / safe_name
    if dest.exists():
        stem = dest.stem
        suffix = dest.suffix
        n = 2
        while True:
            candidate = kdir / f"{stem}-{n}{suffix}"
            if not candidate.exists():
                dest = candidate
                break
            n += 1
            if n > 1000:
                raise PersonaEditorError("could not allocate knowledge filename")
    dest.write_bytes(data)
    if dest.is_symlink():
        dest.unlink(missing_ok=True)
        raise PersonaEditorError("refusing symlink knowledge file")
    pack = load_persona_yaml(pack_dir / "persona.yaml")
    _sync_knowledge_files(pack, pack_dir)
    return dest


def add_knowledge_upload(
    *,
    settings: Settings,
    persona_id: str,
    filename: str,
    fileobj: BinaryIO,
    max_upload_bytes: int = DEFAULT_MAX_UPLOAD_BYTES,
) -> Path:
    data = fileobj.read()
    if not isinstance(data, (bytes, bytearray)):
        raise PersonaEditorError("upload must be bytes")
    return add_knowledge_bytes(
        settings=settings,
        persona_id=persona_id,
        filename=filename,
        data=bytes(data),
        max_upload_bytes=max_upload_bytes,
    )


def add_knowledge_paste(
    *,
    settings: Settings,
    persona_id: str,
    text: str,
    filename: str = "pasted.md",
) -> Path:
    """Save pasted text as a ``.md`` / ``.txt`` knowledge file in a user pack."""
    body = text.strip()
    if not body:
        raise PersonaEditorError("paste text is empty")
    name = Path(filename).name.strip() or "pasted.md"
    suffix = Path(name).suffix.lower()
    if suffix not in {".md", ".txt"}:
        name = f"{Path(name).stem or 'pasted'}.md"
    return add_knowledge_bytes(
        settings=settings,
        persona_id=persona_id,
        filename=name,
        data=body.encode("utf-8"),
    )


def build_persona_config(
    *,
    answer_mode: AnswerMode = "balanced",
    temperature: float = 0.2,
    max_tokens: int = 1024,
    embedding_preset: EmbeddingPresetId = "lite",
    top_k: int | None = None,
    min_score: float | None = None,
    chunk_chars: int | None = None,
) -> PersonaConfig:
    return PersonaConfig(
        answer_mode=answer_mode,
        temperature=temperature,
        max_tokens=max_tokens,
        embedding_preset=embedding_preset,
        top_k=top_k,
        min_score=min_score,
        chunk_chars=chunk_chars,
    )


def index_status_key(*, needs_rebuild: bool, file_count: int) -> str:
    """Return a ``strings.py`` key for plain-language index status."""
    if file_count <= 0:
        return "status.knowledge_empty"
    if needs_rebuild:
        return "status.knowledge_needs_rebuild"
    return "status.knowledge_ready"
