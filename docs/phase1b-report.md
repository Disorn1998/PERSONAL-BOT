# Phase 1b report — persona-bot

Date: 2026-11-18 (Asia/Bangkok)  
Branch: `cursor/phase1b-chat-shell-c230`  
Repo: https://github.com/Disorn1998/PERSONAL-BOT

## 1. Files created/changed

### Core
- `persona_bot/budget.py` — `fit_prompt` token budget trim
- `app/chat_store.py` — sqlite threads/messages + partial updates
- `app/usage.py` — `UsageTracker` → `data/usage.json`
- `app/services.py` — persona discovery helpers
- `persona_bot/main.py` — Streamlit shell + chat loop
- `persona_bot/cli.py` — launches Streamlit via `persona-bot`

### UI
- `persona_bot/ui/theme.py` — CSS (bubbles/welcome/error/badge; no external fonts/scripts)
- `persona_bot/ui/errors.py` — error card formatter
- `persona_bot/ui/strings.py` — onboarding + chat copy expanded
- `.streamlit/config.toml` — unchanged §17.2 tokens from 1a

### Tests / docs
- `tests/test_{budget,chat_store,usage,services,smoke}.py` (+ updates)
- `docs/ASSUMPTIONS.md`, `docs/DECISIONS.md`, `docs/phase1b-report.md`
- `README.md` — quick start

**Not in 1b / deferred:** RAG/knowledge (Phase 2), OCR, multi-user, §19 extras.

## 2. Run/test commands

```bash
uv sync --extra dev
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest
uv run persona-bot   # launches Streamlit UI
```

## 3. ruff / pytest results

| Check | Result |
|---|---|
| ruff | ✅ |
| mypy | ✅ |
| pytest | ✅ **31 passed** |

## 4. Pass criteria

| Criterion | Status |
|---|---|
| Streamlit welcome / key entry (F15) | ✅ |
| Sidebar persona + new/clear chat (F16) | ✅ |
| Thai error cards from `strings.py` | ✅ |
| Theme/bubbles/onboarding CSS; no external fonts/scripts | ✅ |
| ~360px usable (responsive padding / max-width) | ✅ (CSS; owner eye-check) |
| No hardcoded Thai in `main`/ui chrome except `strings.py` | ✅ (`prompt.py` keeps exact not-found phrase for LLM rules) |
| chat_store + partial save during stream (F9) | ✅ |
| budget.fit_prompt wired before LLM | ✅ |
| UsageTracker + model badge / token chips | ✅ |
| study-buddy default selectable | ✅ |
| ~2 min to first message | ✅ path: key → persona → chat (owner eye-check) |
| Phase 2 RAG not started | ✅ |
| DoD 3/4 continued | ✅ rate-limit errors + key redaction still in place |

## 5. Unsure / TODO(verify)

- Token heuristic vs real Groq tokenizer (`budget.py`).
- Stop UX: Streamlit interrupt relies on per-chunk sqlite flush (no native mid-stream Stop widget that aborts without rerun).
- Layout at exactly 360px — owner visual check (§14.8).
- Full §18 part tables still abbreviated in store master prompt.

## 6. Next phase proposal — **Phase 2**

- Local embeddings (fastembed) + Chroma index per persona
- Ingest knowledge files; retrieval query = latest + previous user msg
- Strict short-circuit with real scores; sources expander + citation validation
- Example persona knowledge for study-buddy / tech-explainer
- Rebuild on `chunk_chars` change; refresh keeps history (DoD 2/5)

**STOP.** Await owner 「ไปต่อ」 before Phase 2.
