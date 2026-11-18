# Phase 0 report — persona-bot

Date: 2026-11-18  
Branch: `cursor/phase0-scaffold-c230`  
Repo: https://github.com/Disorn1998/PERSONAL-BOT

## 1. Files created/changed

- `LICENSE` (MIT)
- `pyproject.toml` + `uv.lock` (installable via uv; entry point `persona-bot`)
- `.gitignore`, `.env.example`, `.pre-commit-config.yaml`
- `.github/workflows/ci.yml` (minimal matrix: Ubuntu × 3.11/3.12/3.13)
- `.streamlit/config.toml`
- `persona_bot/__init__.py`, `persona_bot/cli.py` (empty skeleton), `app/i18n.py`
- `persona_bot/ui/__init__.py`, `persona_bot/ui/tokens.py`, `persona_bot/ui/strings.py`
- `app/rag/__init__.py`, `persona_bot/static/fonts/.gitkeep`
- `personas/examples/.gitkeep`, `assets/.gitkeep`, `scripts/.gitkeep`
- `tests/test_smoke.py`
- `docs/ASSUMPTIONS.md`, `docs/DECISIONS.md`, `docs/phase0-report.md`
- `README.md` (Thai + English summary placeholder)
- `THIRD_PARTY_NOTICES.md` (fonts deferred stub)

## 2. Run/test commands

```bash
uv sync --extra dev
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest
uv run persona-bot   # no-op skeleton, exit 0
```

## 3. ruff / pytest results

| Check | Result |
|---|---|
| `ruff check .` | ✅ pass |
| `ruff format --check .` | ✅ pass |
| `mypy` (non-strict scaffold) | ✅ Success: no issues found in 7 source files |
| `pytest` | ✅ 3 passed (`tests/test_smoke.py`) |
| `persona-bot` CLI | ✅ exit 0 (empty skeleton) |

## 4. Pass criteria

| Criterion | Status |
|---|---|
| MIT LICENSE | ✅ |
| Installable pyproject + uv; `requires-python = '>=3.11,<3.14'` | ✅ |
| Entry point `persona-bot` empty skeleton | ✅ |
| Folder skeleton per §6 (Phase 0 subset) | ✅ |
| `.gitignore` covers `.env`, `data/`, caches | ✅ |
| `.env.example` with GROQ_* + §16/Appendix A vars | ✅ |
| ruff + pre-commit + mypy wired | ✅ (chose **mypy**) |
| CI matrix stub 3.11/3.12/3.13 | ✅ (Ubuntu only for Phase 0) |
| UX/UI Phase 0: config.toml, tokens, strings, i18n | ✅ |
| README Thai + EN summary; no fake Groq quota numbers | ✅ |
| THIRD_PARTY_NOTICES stub | ✅ |
| ASSUMPTIONS + DECISIONS started | ✅ |
| DoD items advanced | none yet (DoD maps to later phases) |
| Phase 1+ product logic | ❌ intentionally not started |

## 5. Unsure / TODO(verify)

- Full live `GET /models` catalogue (needs owner key; endpoint reachable → 401 without key).
- Thai `chunk_chars=900` vs embedding token limits for chosen lite model (F5).
- Streamlit Stop / partial-stream behaviour on 1.67 (F9) — Phase 1 prototype.
- Exact §17.2 palette from Complete English Edition if it differs from Phase 0 teal tokens.
- Original **§16.8** / **§18.9** still missing (Appendix A / provisional §18.9).
- Chroma name max length: public docs say 3–512; some code paths historically 3–63 — re-check against chromadb 1.5.9 when implementing RAG.

## 6. Next phase proposal

**Recommend splitting Phase 1 into 1a / 1b (F10) — ask owner.**

### Phase 1a (foundation)

- `config` / Settings (pydantic-settings); model IDs from env only (F8)
- `llm` client skeleton + `StreamResult`; `max_retries=0` (F2); mocks only
- `ratelimit`, `errors`, `security`, `logging_setup`
- `chat_store` skeleton (sqlite)
- Streamlit shell: welcome card / key entry (F15), sidebar shell, Thai error cards
- Example persona **YAML metadata** for 3 examples; study-buddy selectable without knowledge yet (F4)

### Phase 1b (chat loop)

- `prompt` + `budget.fit_prompt`
- Streaming chat UI + Stop/partial save (F9)
- UsageTracker + model badge / token counter (no real Groq in CI)
- Wire rate-limit header parsing into StreamResult
- Privacy notice first-run flag (F19)

If the owner prefers a single Phase 1, merge 1a+1b but expect a large PR.

---

## F1–F23 decisions / questions

| # | Handling in Phase 0 |
|---|---|
| F1 | **ASK:** package `persona_bot` vs `persona_bot`; original §16.8 / §18.9 still missing |
| F2 | **PROPOSAL** in DECISIONS: SDK `max_retries=0` |
| F3 | Document later as Known limitation (calm UX) — Phase 1 |
| F4 | Phase 1: YAML for 3 examples; study-buddy for chat; knowledge Phase 2 |
| F5 | Recorded embedding input limits; Thai measure **TODO(verify)** |
| F6 | `@pytest.mark.slow` reserved; calibration later |
| F7 | Prefer stdlib; announce PDF gen before adding |
| F8 | **PROPOSAL:** no silent Python model fallback |
| F9 | Prototype in Phase 1b |
| F10 | **ASK:** approve 1a/1b split? |
| F11 | Keep `<3.14`; 3.13 deps declare support; CI includes 3.13 |
| F12 | Display-only `DAILY_TOKEN_LIMIT` in `.env.example` |
| F13 | Deprecations page re-verified 18 Nov 2026 (see §3 below) |
| F14 | Fake-server fidelity later |
| F15–F22 | Proposals recorded in `docs/DECISIONS.md` |
| F23 | Info; automated contrast test later — Phase 0 tokens provisional vs full §17.2 |

## §3 verified vs unverified

| Item | Status |
|---|---|
| Groq deprecations page | **Verified** (HTTP 200) |
| `GET /models` body | **Unverified** (401 without key; never asked for key) |
| Streaming usage (`stream_options.include_usage` final chunk) | **Verified** via OpenAI-compat docs |
| `x-ratelimit-*` semantics (RPD vs TPM) | **Verified** via Groq rate-limits docs |
| Chroma collection-name rules | **Verified** via docs |
| `TextEmbedding.list_supported_models()` | **Verified** after install |
| Embedding max input lengths | **Verified** from model metadata; Thai ratio TODO |
| Python 3.13 support (metadata) | **Verified** upstream; CI will exercise |
| No `chat/completions` called | **Honoured** |

## Installed versions (host: Python 3.12.3)

| Package | Version |
|---|---|
| Python | 3.12.3 (CI also 3.11 / 3.13) |
| streamlit | 1.67.0 |
| chromadb | 1.5.9 |
| fastembed | 0.9.1 |
| onnxruntime | 1.32.0 |
| pythainlp | 5.4.0 |
| openai | 3.54.0 |
| ruff | 0.17.5 |
| mypy | 2.4.1 |
| pytest | 9.2.0 |

## Coverage proposal (**ask before lock**)

- Overall **≈ 60%**
- Core modules **≈ 80%**
- `fail_under` remains `0` until owner locks

## Questions for the owner

1. Lock coverage floors (60% / 80%)?
2. Approve Phase **1a / 1b** split (F10)?
3. Keep import package name **`app`** or rename to **`persona_bot`** (F1)?
4. Please supply original **§16.8** and **§18.9** (replace provisional Appendix A / §18.9).
5. Confirm Phase 0 **§17.2** colour tokens or provide the authoritative palette table.

**STOP.** Awaiting owner **"ไปต่อ"** / continue before Phase 1.
