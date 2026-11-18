# ASSUMPTIONS — persona-bot

Assumptions made when the owner has not answered yet, plus verification notes.
Update when the owner replies or when APIs change.

## Phase 1b notes (2026-11-18)

| Item | Assumption |
|---|---|
| Token budget | Heuristic `chars/3` in `app/budget.py` — **TODO(verify)** vs Groq tokenizer |
| Stop button | Streamlit rerun interrupts stream; partials flushed to sqlite each chunk (F9) |
| RAG context | Empty in 1b; strict personas short-circuit to not-found without LLM |
| Privacy ack | Flag file `data/privacy_ack` (F19) |
| No external fonts/scripts | Theme CSS uses system/sans-serif from Streamlit config only |

## Phase 1a defaults (owner unanswered; 2026-11-18)

| Item | Assumption | Status |
|---|---|---|
| Coverage floors | Propose overall **~60%** / core **~80%**; **do not lock** in CI (`fail_under=0`) | Open ask |
| Phase split (F10) | **1a / 1b** — this work is **1a only** | Assumed |
| Package name (F1) | Keep importable package **`app`** for now | Open ask |
| §16.8 / §18.9 | Keep provisional Appendix A / §18.9 | Open ask |
| §17.2 palette | Warm cream `#F4F1EA` + primary `#6A5ACD` (migrated from Phase 0 teal) | Assumed per coordinator |

## Package / Python

| Item | Assumption / result | Status |
|---|---|---|
| Importable package name | Keep `app/` (F1 still open for rename to `persona_bot`) | **Ask owner** |
| `requires-python` | `>=3.11,<3.14` | Kept |
| Python 3.13 deps | chromadb / fastembed+onnxruntime / pythainlp declare 3.13 support | Phase 0 verified metadata |

## Module API notes (full §7 text abbreviated in store copy)

Phase 1a APIs follow §0.2 lifecycle + §16 names (`StreamResult`, ratelimit split,
persona fields, security P0). Where the Complete English Edition tables differ,
prefer the owner message and adjust — mark `# TODO(verify)` at call sites.

| Topic | Assumption |
|---|---|
| `answer_mode` | Enum: `strict` \| `balanced` \| `open` |
| Fallback rules | Minute 429 / transport → try fallback model; **day** 429 → no fallback |
| Embedding presets | Single table in `app/config.py`: `lite`, `multilingual`, `quality` |
| Prompt cache prefix | `system_prompt + fixed rules` byte-stable per persona/mode |

## §3 Fast-changing external info

| Topic | Result | Verified? |
|---|---|---|
| Groq deprecations | Page checked Phase 0 (18 Nov 2026) | **Verified** (docs) |
| `GET /v1/models` | 401 without key | **Unverified** (auth) |
| Streaming usage | Final chunk via `stream_options.include_usage` | **Verified** (docs) |
| `x-ratelimit-*` | requests=RPD, tokens=TPM | **Verified** (docs) |
| Chroma collection names | Docs rules recorded in Phase 0 | **Verified** (docs) |
| Embedding max lengths | Via `TextEmbedding.list_supported_models()` | **Verified**; Thai ratio **TODO(verify)** |
| Groq rate-limit headers on **streaming** create | Assumed present on `with_raw_response` | **TODO(verify)** |
| Never call real `chat/completions` in tests/CI | Honoured (mocks only) | Honoured |

## UX tokens (§17.2)

Migrated in Phase 1a: primary `#6A5ACD`, background `#F4F1EA`, secondary `#EBE6DC`.
F23 contrast automated test remains later.

## Coverage

Proposed floors (not locked): **overall ≈ 60%**, **core ≈ 80%**.

## Missing source sections (F1)

Original **§16.8** and **§18.9** still missing; provisional Appendix A / §18.9 remain.
