"""Persona loading helpers."""

from __future__ import annotations

from pathlib import Path

from persona_bot.config import Settings
from persona_bot.services import (
    chat_db_path,
    is_user_persona,
    load_available_personas,
    persona_dir_for,
    usage_path,
)


def test_loads_examples_with_study_buddy_first() -> None:
    packs = load_available_personas()
    ids = [p.id for p in packs]
    assert "study-buddy" in ids
    assert ids[0] == "study-buddy"
    assert "tech-explainer" in ids
    assert "thai-tax-advisor" in ids
    assert "company-faq-bot" in ids
    assert "meeting-notes" in ids
    assert "pdf-handbook-demo" in ids
    assert "en-study-coach" in ids
    assert len(ids) == len(set(ids))


def test_persona_dir_user_vs_example_and_paths(tmp_path: Path) -> None:
    examples = Path("personas/examples").resolve()
    personas = tmp_path / "personas"
    data = tmp_path / "data"
    user_pack = personas / "study-buddy"
    user_pack.mkdir(parents=True)
    (user_pack / "persona.yaml").write_text(
        (examples / "study-buddy" / "persona.yaml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    settings = Settings(
        EXAMPLES_DIR=str(examples),
        PERSONAS_DIR=str(personas),
        DATA_DIR=str(data),
    )
    assert is_user_persona("study-buddy", settings) is True
    assert is_user_persona("no-such-pack", settings) is False
    assert persona_dir_for("study-buddy", settings) == user_pack
    assert persona_dir_for("tech-explainer", settings) == examples / "tech-explainer"
    assert persona_dir_for("missing-id", settings) is None
    assert chat_db_path(settings) == data / "chat.sqlite3"
    assert usage_path(settings) == data / "usage.json"

    packs = load_available_personas(settings)
    # User pack loads in addition to examples (same id may appear twice if both exist).
    assert any(p.id == "study-buddy" for p in packs)
