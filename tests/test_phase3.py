"""Phase 3 distribution helpers — no Groq / no ONNX downloads."""

from __future__ import annotations

from pathlib import Path

import pytest
from persona_bot import cli
from persona_bot.config import Settings
from persona_bot.healthcheck import run_health_check
from persona_bot.keyring_store import SERVICE_NAME, USERNAME
from persona_bot.versioning import (
    DATA_SCHEMA_VERSION,
    ensure_data_version,
    get_app_version,
    read_version_file,
)


def test_project_root_finds_main() -> None:
    root = cli.project_root()
    assert (root / "persona_bot" / "main.py").exists()
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

    from persona_bot import keyring_store

    keyring_store.save_api_key("gsk_test_key_value")
    assert keyring_store.load_api_key() == "gsk_test_key_value"
    keyring_store.delete_api_key()
    assert keyring_store.load_api_key() == ""
    assert SERVICE_NAME and USERNAME


def test_remember_key_env_or_ui_preference(monkeypatch: pytest.MonkeyPatch) -> None:
    store: dict[tuple[str, str], str] = {}

    class FakeKeyring:
        def set_password(self, service: str, username: str, password: str) -> None:
            store[(service, username)] = password

        def get_password(self, service: str, username: str) -> str | None:
            return store.get((service, username))

        def delete_password(self, service: str, username: str) -> None:
            if (service, username) not in store:
                raise keyring.errors.PasswordDeleteError("missing")
            store.pop((service, username), None)

    import keyring

    monkeypatch.setattr(keyring, "set_password", FakeKeyring().set_password)
    monkeypatch.setattr(keyring, "get_password", FakeKeyring().get_password)
    monkeypatch.setattr(keyring, "delete_password", FakeKeyring().delete_password)

    from persona_bot import keyring_store

    monkeypatch.delenv("PERSONA_BOT_REMEMBER_KEY", raising=False)
    assert keyring_store.remember_enabled() is False
    keyring_store.set_ui_remember_preference(True)
    assert keyring_store.remember_enabled() is True
    assert keyring_store.remember_status_key() == "status.remember_ui"

    monkeypatch.setenv("PERSONA_BOT_REMEMBER_KEY", "1")
    assert keyring_store.env_remember_enabled() is True
    assert keyring_store.remember_status_key() == "status.remember_env"

    keyring_store.set_ui_remember_preference(False)
    monkeypatch.delenv("PERSONA_BOT_REMEMBER_KEY", raising=False)
    assert keyring_store.remember_enabled() is False
    assert keyring_store.remember_status_key() == "status.remember_session_only"
    assert keyring_store.remember_status_key(loaded_from_keyring=True) == "status.remember_loaded"


def test_cli_binds_localhost_and_skips_email(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Pass home explicitly — Windows Path.home() ignores HOME and uses USERPROFILE.
    cred = tmp_path / ".streamlit" / "credentials.toml"
    path = cli.ensure_streamlit_credentials(home=tmp_path)
    assert path == cred
    text = cred.read_text(encoding="utf-8")
    assert 'email = ""' in text
    # Idempotent — does not overwrite an existing file.
    cred.write_text('[general]\nemail = "keep@example.com"\n', encoding="utf-8")
    cli.ensure_streamlit_credentials(home=tmp_path)
    assert "keep@example.com" in cred.read_text(encoding="utf-8")

    # CLI argv contract (without launching Streamlit).
    monkeypatch.setattr(cli, "project_root", lambda: Path(__file__).resolve().parents[1])
    monkeypatch.setattr(cli, "ensure_streamlit_credentials", lambda: cred)
    captured: dict[str, list[str]] = {}

    class FakeStcli:
        @staticmethod
        def main() -> int:
            import sys

            captured["argv"] = list(sys.argv)
            return 0

    import streamlit.web.cli as stcli

    monkeypatch.setattr(stcli, "main", FakeStcli.main)
    with pytest.raises(SystemExit) as exited:
        cli.main()
    assert exited.value.code == 0
    assert "--server.address=127.0.0.1" in captured["argv"]
    assert "--browser.gatherUsageStats=false" in captured["argv"]


def test_start_scripts_exist() -> None:
    root = Path(__file__).resolve().parents[1]
    assert (root / "start.bat").exists()
    assert (root / "start.sh").exists()
    assert (root / "start.command").exists()
    assert (root / "Dockerfile").exists()
    assert (root / "docker-compose.yml").exists()
    config = (root / ".streamlit" / "config.toml").read_text(encoding="utf-8")
    assert 'address = "127.0.0.1"' in config
