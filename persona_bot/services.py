"""Small orchestration helpers shared by the Streamlit shell."""

from __future__ import annotations

from pathlib import Path

from persona_bot.config import Settings, get_settings
from persona_bot.persona import PersonaPack, list_example_persona_dirs, load_persona_yaml


def load_available_personas(settings: Settings | None = None) -> list[PersonaPack]:
    cfg = settings or get_settings()
    packs: list[PersonaPack] = []
    for directory in list_example_persona_dirs(cfg.examples_dir):
        packs.append(load_persona_yaml(directory / "persona.yaml"))
    # User personas (runtime)
    if cfg.personas_dir.exists():
        for path in sorted(cfg.personas_dir.glob("*/persona.yaml")):
            packs.append(load_persona_yaml(path))
    # Prefer study-buddy first for onboarding.
    packs.sort(key=lambda p: (0 if p.id == "study-buddy" else 1, p.name))
    return packs


def is_user_persona(persona_id: str, settings: Settings | None = None) -> bool:
    cfg = settings or get_settings()
    return (cfg.personas_dir / persona_id / "persona.yaml").exists()


def persona_dir_for(persona_id: str, settings: Settings | None = None) -> Path | None:
    """Return the on-disk pack directory (user pack preferred over example)."""
    cfg = settings or get_settings()
    user = cfg.personas_dir / persona_id
    if (user / "persona.yaml").exists():
        return user
    example = cfg.examples_dir / persona_id
    if (example / "persona.yaml").exists():
        return example
    return None


def chat_db_path(settings: Settings | None = None) -> Path:
    cfg = settings or get_settings()
    return cfg.data_dir / "chat.sqlite3"


def usage_path(settings: Settings | None = None) -> Path:
    cfg = settings or get_settings()
    return cfg.data_dir / "usage.json"
