"""In-app persona create/edit, duplicate, and knowledge upload."""

from __future__ import annotations

from pathlib import Path

import pytest
from persona_bot.config import Settings
from persona_bot.persona import PersonaConfig, load_persona_yaml
from persona_bot.persona_editor import (
    KnowledgeTooLargeError,
    PersonaEditorError,
    add_knowledge_bytes,
    add_knowledge_paste,
    assert_knowledge_within_limit,
    create_user_persona,
    duplicate_persona_to_user,
    index_status_key,
    save_user_persona,
)

ROOT = Path(__file__).resolve().parents[1]


def _settings(tmp_path: Path) -> Settings:
    return Settings(
        DATA_DIR=tmp_path / "data",
        PERSONAS_DIR=tmp_path / "data" / "personas",
        EXAMPLES_DIR=ROOT / "personas" / "examples",
        MAX_KNOWLEDGE_MB=1,
        GROQ_API_KEY="",
        GROQ_MODEL_PRIMARY="openai/gpt-oss-120b",
        GROQ_MODEL_FALLBACK="openai/gpt-oss-20b",
    )


def test_create_and_save_user_persona(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    pack = create_user_persona(
        personas_dir=settings.personas_dir,
        persona_id="my-bot",
        name="บอทของฉัน",
        system_prompt="คุณเป็นผู้ช่วยทดสอบ",
        description="ทดสอบ",
        config=PersonaConfig(answer_mode="strict", temperature=0.1, top_k=3),
    )
    assert pack.id == "my-bot"
    yaml_path = settings.personas_dir / "my-bot" / "persona.yaml"
    assert yaml_path.exists()
    assert (settings.personas_dir / "my-bot" / "knowledge").is_dir()

    pack.config.temperature = 0.5
    pack.name = "บอทแก้แล้ว"
    saved = save_user_persona(personas_dir=settings.personas_dir, pack=pack)
    assert saved.name == "บอทแก้แล้ว"
    assert load_persona_yaml(yaml_path).config.temperature == 0.5


def test_duplicate_example_to_user_pack(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    pack = duplicate_persona_to_user(settings=settings, source_id="study-buddy")
    assert pack.id == "study-buddy-copy"
    assert (settings.personas_dir / "study-buddy-copy" / "persona.yaml").exists()
    knowledge = settings.personas_dir / "study-buddy-copy" / "knowledge"
    assert any(knowledge.rglob("*.md")) or any(knowledge.rglob("*.txt"))

    again = duplicate_persona_to_user(settings=settings, source_id="study-buddy")
    assert again.id == "study-buddy-copy-2"


def test_knowledge_upload_paste_and_limits(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    create_user_persona(
        personas_dir=settings.personas_dir,
        persona_id="know-bot",
        name="Know",
        system_prompt="hi",
    )
    dest = add_knowledge_paste(
        settings=settings,
        persona_id="know-bot",
        text="# สวัสดี\nความรู้ทดสอบ",
        filename="note.md",
    )
    assert dest.name == "note.md"
    assert dest.read_text(encoding="utf-8").startswith("# สวัสดี")

    dest2 = add_knowledge_bytes(
        settings=settings,
        persona_id="know-bot",
        filename="extra.txt",
        data=b"more knowledge",
    )
    assert dest2.exists()
    listed = load_persona_yaml(settings.personas_dir / "know-bot" / "persona.yaml")
    assert any(name.endswith("note.md") for name in listed.knowledge_files)
    assert any(name.endswith("extra.txt") for name in listed.knowledge_files)

    with pytest.raises(PersonaEditorError):
        add_knowledge_bytes(
            settings=settings,
            persona_id="know-bot",
            filename="bad.exe",
            data=b"nope",
        )

    # Path components are stripped to basename (safe); weird names still rejected.
    escaped = add_knowledge_bytes(
        settings=settings,
        persona_id="know-bot",
        filename="../escape.md",
        data=b"safe basename",
    )
    assert escaped.name == "escape.md"
    assert escaped.parent == settings.personas_dir / "know-bot" / "knowledge"

    with pytest.raises(PersonaEditorError):
        add_knowledge_bytes(
            settings=settings,
            persona_id="know-bot",
            filename="weird*.md",
            data=b"x",
        )

    with pytest.raises(KnowledgeTooLargeError):
        add_knowledge_bytes(
            settings=settings,
            persona_id="know-bot",
            filename="huge.txt",
            data=b"x" * (2 * 1024 * 1024),  # over MAX_KNOWLEDGE_MB=1
        )

    # Existing on-disk knowledge over the limit is rejected before rebuild/ingest.
    fat = settings.personas_dir / "know-bot" / "knowledge" / "fat.bin"
    fat.write_bytes(b"y" * (2 * 1024 * 1024))
    with pytest.raises(KnowledgeTooLargeError):
        assert_knowledge_within_limit(
            settings.personas_dir / "know-bot" / "knowledge",
            max_knowledge_mb=1,
        )


def test_example_knowledge_upload_blocked(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    with pytest.raises(PersonaEditorError):
        add_knowledge_paste(
            settings=settings,
            persona_id="study-buddy",
            text="should fail",
        )


def test_index_status_keys() -> None:
    assert index_status_key(needs_rebuild=False, file_count=0) == "status.knowledge_empty"
    assert index_status_key(needs_rebuild=True, file_count=2) == "status.knowledge_needs_rebuild"
    assert index_status_key(needs_rebuild=False, file_count=2) == "status.knowledge_ready"


def test_create_rejects_bad_id(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    with pytest.raises(PersonaEditorError):
        create_user_persona(
            personas_dir=settings.personas_dir,
            persona_id="Bad ID!",
            name="x",
            system_prompt="y",
        )
