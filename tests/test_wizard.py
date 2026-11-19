"""First-run wizard + overwrite-import helpers."""

from __future__ import annotations

from pathlib import Path

from persona_bot.i18n import set_locale
from persona_bot.ui.wizard import (
    load_entry_path,
    overwrite_confirm_required,
    progress_markup,
    save_entry_path,
    wizard_step,
)


def test_wizard_step_order() -> None:
    assert wizard_step(has_key=False, privacy_ack=False) == 1
    assert wizard_step(has_key=True, privacy_ack=False) == 2
    assert wizard_step(has_key=True, privacy_ack=True) == 3


def test_overwrite_confirm_required() -> None:
    assert not overwrite_confirm_required("reject", {"duplicate_of": "x"})
    assert not overwrite_confirm_required("overwrite", None)
    assert not overwrite_confirm_required("overwrite", {"duplicate_of": None})
    assert overwrite_confirm_required("overwrite", {"duplicate_of": "demo"})


def test_progress_markup_marks_active_step() -> None:
    set_locale("en")
    html = progress_markup(2)
    assert "pb-wizard-step active" in html
    assert "pb-wizard-step done" in html
    assert "Privacy" in html


def test_entry_path_persist_roundtrip(tmp_path: Path) -> None:
    assert load_entry_path(tmp_path) is None
    save_entry_path(tmp_path, "api")
    assert load_entry_path(tmp_path) == "api"
    save_entry_path(tmp_path, "knowledge")
    assert load_entry_path(tmp_path) == "knowledge"
