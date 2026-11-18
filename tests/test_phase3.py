"""Phase 3 distribution helpers — no Groq / no ONNX downloads."""

from __future__ import annotations

from pathlib import Path

import pytest
from app import cli
from app.config import Settings
from app.healthcheck import run_health_check
from app.keyring_store import SERVICE_NAME, USERNAME
from app.versioning import (
    DATA_SCHEMA_VERSION,
    ensure_data_version,
    get_app_version,
    read_version_file,
)


def test_project_root_finds_main() -> None:
    root = cli.project_root()
    assert (root / "app" / "main.py").exists()
    assert (root / "pyproject.toml").exists()


def test_version_migration(tmp_path: Path) -> None:
    info = ensure_data_version(tmp_path)
    assert info.data_schema == DATA_SCHEMA_VERSION
    assert info.app_version == get_app_version()
    again = read_version_file(tmp_path)
    assert again is not None
    assert again.data_schema == DATA_SCHEMA_VERSION


def test_health_check_reports_missing_key(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env.example").write_text("x", encoding="utf-8")
    settings = Settings(
        GROQ_MODEL_PRIMARY="model-a",
        GROQ_MODEL_FALLBACK="model-b",
        GROQ_API_KEY="",
        DATA_DIR=str(tmp_path / "data"),
    )
    report = run_health_check(settings, api_key="", project_root=tmp_path)
    assert report.models_configured is True
    assert report.api_key_present is False
    assert report.data_dir_writable is True
    assert "api_key_missing" in report.notes


def test_keyring_roundtrip(monkeypatch: pytest.MonkeyPatch) -> None:
    store: dict[tuple[str, str], str] = {}

    class FakeKeyring:
        def set_password(self, service: str, username: str, password: str) -> None:
            store[(service, username)] = password

        def get_password(self, service: str, username: str) -> str | None:
            return store.get((service, username))

        def delete_password(self, service: str, username: str) -> None:
            store.pop((service, username), None)

    import keyring

    monkeypatch.setattr(keyring, "set_password", FakeKeyring().set_password)
    monkeypatch.setattr(keyring, "get_password", FakeKeyring().get_password)
    monkeypatch.setattr(keyring, "delete_password", FakeKeyring().delete_password)

    from app import keyring_store

    keyring_store.save_api_key("gsk_test_key_value")
    assert keyring_store.load_api_key() == "gsk_test_key_value"
    keyring_store.delete_api_key()
    assert keyring_store.load_api_key() == ""
    assert SERVICE_NAME and USERNAME


def test_start_scripts_exist() -> None:
    root = Path(__file__).resolve().parents[1]
    assert (root / "start.bat").exists()
    assert (root / "start.sh").exists()
    assert (root / "start.command").exists()
    assert (root / "Dockerfile").exists()
    assert (root / "docker-compose.yml").exists()
