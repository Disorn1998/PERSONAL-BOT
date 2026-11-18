#!/usr/bin/env python3
"""Owner-only live smoke checklist against real Groq (+ optional embedder).

Never run in CI. Requires GROQ_API_KEY + models in the environment / .env.

Usage (from repo root)::

    uv run python scripts/smoke_test.py
    PERSONA_BOT_EVAL_LIVE=1 uv run pytest -m slow tests/eval/test_eval_slow.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CHECKLIST = """
Owner smoke checklist (Phase 4)
-------------------------------
[ ] Fresh start.bat / start.sh reaches UI (~5 min excluding first model download)
[ ] Welcome card → save Groq key → study-buddy chat streams Thai reply
[ ] tech-explainer strict: in-file HTTP question cites sources; OOS question → not-found (no LLM)
[ ] Language toggle TH/EN updates sidebar + errors without restart
[ ] Export persona zip → preview import → import (reject duplicate, then rename)
[ ] Backup data/ → restore into a temp copy; delete-all keeps version.json
[ ] Optional: PERSONA_BOT_EVAL_LIVE=1 pytest -m slow (DoD 7 real embedder)
[ ] No API key appears in logs, backup zip, or export zip
"""


def main() -> int:
    print(CHECKLIST)
    from persona_bot.config import get_settings
    from persona_bot.llm import LlmClient, StreamResult
    from persona_bot.persona import load_persona_yaml

    settings = get_settings()
    if not settings.groq_api_key.strip():
        print("GROQ_API_KEY missing — aborting (owner-run only).", file=sys.stderr)
        return 2
    try:
        settings.require_models()
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    persona = load_persona_yaml(ROOT / "personas/examples/study-buddy/persona.yaml")
    client = LlmClient(settings=settings, api_key=settings.groq_api_key)
    messages = [
        {"role": "system", "content": persona.system_prompt},
        {
            "role": "user",
            "content": "อธิบายการสังเคราะห์ด้วยแสงสั้น ๆ เป็นภาษาไทย 3 ประโยค",
        },
    ]
    result = StreamResult()
    text = "".join(
        client.stream_chat(
            messages,
            temperature=0.2,
            max_tokens=256,
            result=result,
        )
    )
    print("--- smoke output ---")
    print(text)
    print("--- meta ---")
    print(
        f"model={result.model} fallback={result.used_fallback} tokens={result.usage.total_tokens}"
    )
    return 0 if text.strip() else 1


if __name__ == "__main__":
    raise SystemExit(main())
