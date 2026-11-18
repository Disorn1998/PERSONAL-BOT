#!/usr/bin/env python3
"""Owner-only Thai quality smoke test against real Groq.

Never run in CI. Requires GROQ_API_KEY + models in the environment / .env.
Usage (from repo root):

    uv run python scripts/smoke_test.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    from app.config import get_settings
    from app.llm import LlmClient, StreamResult
    from app.persona import load_persona_yaml

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
