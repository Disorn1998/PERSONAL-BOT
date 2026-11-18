"""Persona loading helpers."""

from __future__ import annotations

from app.services import load_available_personas


def test_loads_examples_with_study_buddy_first() -> None:
    packs = load_available_personas()
    ids = [p.id for p in packs]
    assert "study-buddy" in ids
    assert ids[0] == "study-buddy"
    assert "tech-explainer" in ids
