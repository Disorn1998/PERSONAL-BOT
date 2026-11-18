"""Smoke tests — package import, CLI launch wiring, §17.2 tokens."""

from __future__ import annotations

from pathlib import Path

import pytest
from app import cli, i18n
from app.ui import strings, tokens


def test_import_package() -> None:
    assert cli.main is not None
    assert i18n.DEFAULT_LOCALE == "th"
    assert "th" in strings.STRINGS
    assert tokens.COLOR_PRIMARY == "#6A5ACD"
    assert tokens.COLOR_BACKGROUND == "#F4F1EA"


def test_cli_launches_streamlit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("streamlit.web.cli.main", lambda: 0)
    with pytest.raises(SystemExit) as exited:
        cli.main()
    assert exited.value.code == 0
    assert (Path(__file__).resolve().parents[1] / "app" / "main.py").exists()


def test_i18n_resolves_thai_key() -> None:
    assert i18n.t("app.title") == "persona-bot"
    assert i18n.t("error.rate_limit_day").startswith("โควตา")
    assert i18n.t("action.got_it")
    assert i18n.t("missing.key") == "missing.key"


def test_i18n_english_table_complete_enough() -> None:
    th = strings.STRINGS["th"]
    en = strings.STRINGS["en"]
    missing = sorted(set(th) - set(en))
    assert missing == []
    i18n.set_locale("en")
    assert i18n.t("action.new_chat") == "New chat"
    assert i18n.t("error.not_found_strict").startswith("No relevant")
    i18n.set_locale("th")
    assert i18n.t("action.new_chat") == "แชตใหม่"


def test_main_module_imports() -> None:
    import app.main as main_mod

    assert callable(main_mod.run)
