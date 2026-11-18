"""Phase 0 smoke tests — package import and entry skeleton."""

from __future__ import annotations

from app import cli, i18n
from app.ui import strings, tokens


def test_import_package() -> None:
    assert cli.main is not None
    assert i18n.DEFAULT_LOCALE == "th"
    assert "th" in strings.STRINGS
    assert tokens.COLOR_PRIMARY.startswith("#")


def test_cli_main_is_noop() -> None:
    assert cli.main() is None


def test_i18n_resolves_thai_key() -> None:
    assert i18n.t("app.title") == "persona-bot"
    assert i18n.t("missing.key") == "missing.key"
