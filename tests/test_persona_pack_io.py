"""Safe persona zip import/export tests."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pytest
from app.persona import PersonaConfig, PersonaPack, save_persona_yaml
from app.persona_pack_io import (
    PersonaPackIoError,
    delete_user_persona,
    export_persona_zip,
    import_persona_zip,
    preview_persona_zip,
)


def _write_pack(root: Path, *, pid: str = "demo-pack") -> Path:
    pack_dir = root / pid
    (pack_dir / "knowledge").mkdir(parents=True)
    pack = PersonaPack(
        id=pid,
        name="Demo",
        description="demo pack",
        system_prompt="You are a demo.",
        config=PersonaConfig(answer_mode="balanced"),
        knowledge_files=["knowledge/note.txt"],
    )
    save_persona_yaml(pack, pack_dir / "persona.yaml")
    (pack_dir / "knowledge" / "note.txt").write_text("hello knowledge", encoding="utf-8")
    return pack_dir


def test_export_import_roundtrip(tmp_path: Path) -> None:
    src = _write_pack(tmp_path / "src")
    data = export_persona_zip(src)
    dest_root = tmp_path / "personas"
    preview = preview_persona_zip(data, personas_dir=dest_root)
    assert preview.persona_id == "demo-pack"
    assert "note.txt" in preview.knowledge_files
    imported = import_persona_zip(data, personas_dir=dest_root, conflict="reject")
    assert imported.id == "demo-pack"
    assert (dest_root / "demo-pack" / "knowledge" / "note.txt").read_text(
        encoding="utf-8"
    ) == "hello knowledge"


def test_reject_path_traversal(tmp_path: Path) -> None:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("persona.yaml", "id: x\nname: x\nsystem_prompt: hi\n")
        zf.writestr("../evil.txt", "nope")
    with pytest.raises(PersonaPackIoError):
        preview_persona_zip(buf.getvalue(), personas_dir=tmp_path)


def test_reject_non_whitelist(tmp_path: Path) -> None:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr(
            "persona.yaml",
            "id: badpack\nname: Bad\nsystem_prompt: hi\nconfig: {}\n",
        )
        zf.writestr("malware.exe", b"MZ")
    with pytest.raises(PersonaPackIoError):
        preview_persona_zip(buf.getvalue(), personas_dir=tmp_path)


def test_reject_symlink_member(tmp_path: Path) -> None:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr(
            "persona.yaml",
            "id: linky\nname: L\nsystem_prompt: hi\nconfig: {}\n",
        )
        info = zipfile.ZipInfo("knowledge/note.txt")
        info.create_system = 3
        info.external_attr = 0o120777 << 16
        zf.writestr(info, b"target")
    with pytest.raises(PersonaPackIoError):
        preview_persona_zip(buf.getvalue(), personas_dir=tmp_path)


def test_duplicate_id_reject_and_rename(tmp_path: Path) -> None:
    src = _write_pack(tmp_path / "src", pid="dup-id")
    data = export_persona_zip(src)
    personas = tmp_path / "personas"
    import_persona_zip(data, personas_dir=personas, conflict="reject")
    preview = preview_persona_zip(data, personas_dir=personas)
    assert preview.duplicate_of == "dup-id"
    with pytest.raises(PersonaPackIoError):
        import_persona_zip(data, personas_dir=personas, conflict="reject")
    renamed = import_persona_zip(data, personas_dir=personas, conflict="rename")
    assert renamed.id == "dup-id-import"
    assert (personas / "dup-id-import" / "persona.yaml").exists()


def test_zip_bomb_ratio(tmp_path: Path) -> None:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "persona.yaml",
            "id: bomb\nname: B\nsystem_prompt: hi\nconfig: {}\n",
        )
        # Highly compressible payload
        zf.writestr("knowledge/big.txt", ("A" * 200_000).encode("utf-8"))
    with pytest.raises(PersonaPackIoError):
        preview_persona_zip(
            buf.getvalue(),
            personas_dir=tmp_path,
            max_compression_ratio=5.0,
        )


def test_delete_user_persona(tmp_path: Path) -> None:
    src = _write_pack(tmp_path / "personas", pid="todelete")
    delete_user_persona(personas_dir=tmp_path / "personas", persona_id="todelete")
    assert not src.exists()
