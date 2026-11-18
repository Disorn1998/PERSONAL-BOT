"""Small orchestration helpers shared by the Streamlit shell."""

from __future__ import annotations

from pathlib import Path

from app.config import Settings, get_settings
from app.persona import PersonaPack, list_example_persona_dirs, load_persona_yaml


def load_available_personas(settings: Settings | None = None) -> list[PersonaPack]:
    cfg = settings or get_settings()
    packs: list[PersonaPack] = []
    for directory in list_example_persona_dirs(cfg.examples_dir):
        packs.append(load_persona_yaml(directory / "persona.yaml"))
    # User personas (runtime) — optional in Phase 1b
    if cfg.personas_dir.exists():
        for path in sorted(cfg.personas_dir.glob("*/persona.yaml")):
            packs.append(load_persona_yaml(path))
    # Prefer study-buddy first for onboarding.
    packs.sort(key=lambda p: (0 if p.id == "study-buddy" else 1, p.name))
    return packs


def chat_db_path(settings: Settings | None = None) -> Path:
    cfg = settings or get_settings()
    return cfg.data_dir / "chat.sqlite3"


def usage_path(settings: Settings | None = None) -> Path:
    cfg = settings or get_settings()
    return cfg.data_dir / "usage.json"
