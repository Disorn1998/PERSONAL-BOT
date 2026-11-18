"""Backup / restore / wipe tests."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pytest
from app.backup import BackupError, create_backup, delete_all_data, restore_backup
from app.versioning import ensure_data_version, read_version_file


def test_backup_restore_roundtrip(tmp_path: Path) -> None:
    data = tmp_path / "data"
    ensure_data_version(data)
    (data / "usage.json").write_text('{"total_tokens": 3}', encoding="utf-8")
    personas = data / "personas" / "x"
    personas.mkdir(parents=True)
    (personas / "persona.yaml").write_text(
        "id: demo-x\nname: X\nsystem_prompt: hi\nconfig: {}\n",
        encoding="utf-8",
    )
    payload, summary = create_backup(data)
    assert summary.member_count >= 2

    other = tmp_path / "restored"
    other.mkdir()
    (other / "junk.txt").write_text("gone", encoding="utf-8")
    restore_backup(payload, data_dir=other)
    assert (other / "usage.json").read_text(encoding="utf-8") == '{"total_tokens": 3}'
    assert not (other / "junk.txt").exists()
    assert read_version_file(other) is not None


def test_backup_rejects_env(tmp_path: Path) -> None:
    data = tmp_path / "data"
    data.mkdir()
    (data / ".env").write_text("GROQ_API_KEY=gsk_secret", encoding="utf-8")
    (data / "usage.json").write_text("{}", encoding="utf-8")
    payload, _ = create_backup(data)
    # .env must not be inside the archive
    with zipfile.ZipFile(io.BytesIO(payload)) as zf:
        names = zf.namelist()
    assert ".env" not in names
    assert all(".env" not in n for n in names)


def test_delete_all_data_keeps_version(tmp_path: Path) -> None:
    data = tmp_path / "data"
    ensure_data_version(data)
    (data / "chat.sqlite3").write_bytes(b"sqlite")
    (data / "personas" / "a").mkdir(parents=True)
    delete_all_data(data, keep_version=True)
    assert not (data / "chat.sqlite3").exists()
    assert not (data / "personas").exists()
    assert (data / "version.json").exists()


def test_restore_rejects_traversal(tmp_path: Path) -> None:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("../outside.txt", "nope")
    with pytest.raises(BackupError):
        restore_backup(buf.getvalue(), data_dir=tmp_path / "data")
