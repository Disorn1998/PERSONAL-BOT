# ASSUMPTIONS — persona-bot

Assumptions made when the owner has not answered yet, plus verification notes.
Update when the owner replies or when APIs change.

## Locks (2026-11-18) — owner authorized

| Item | Locked value | Status |
|---|---|---|
| Eval DoD 7 in-scope hit@top_k | **≥ 0.70** | **LOCKED** |
| Eval DoD 7 strict OOS / not-found | **≥ 0.80** | **LOCKED** |
| Coverage CI overall | **≥ 60%** (`--cov-fail-under=60`, hard fail) | **LOCKED** |
| Coverage CI core | **≥ 80%** target — enforce when split core coverage is feasible | **TARGET** (not yet split in CI) |

## Phase 5 notes (2026-11-18)

| Item | Assumption | Status |
|---|---|---|
| OS matrix | Ubuntu 3.11/3.12/3.13 + Windows/macOS 3.12 (feasible subset) | Assumed |
| Coverage CI gate | Overall hard gate `--cov-fail-under=60`; core 80% target until split exists | **LOCKED** (2026-11-18) |
| Eval thresholds | DoD 7 locked: hit@top_k ≥ 0.70; strict OOS ≥ 0.80 | **LOCKED** (2026-11-18) |
| Canary | Weekly `GET /models` only; maintainer `GROQ_API_KEY`; skip forks; no duplicate issues | Assumed |
| CodeQL | Enabled when repo is public | Assumed |
| gitleaks | Docker image `zricethezav/gitleaks:v8.21.2` (no org licence required) | Assumed |
| GHCR image | `ghcr.io/<owner>/persona-bot` on tag `v*` | Assumed |
| Embedding model licences | Table in THIRD_PARTY_NOTICES with **TODO(verify)** on model cards | Assumed |
| Docker e2e | Fake Groq via `scripts/fake_groq_server.py` + `docker-compose.ci.yml` | Assumed |

## Phase 4 notes (2026-11-18)

| Item | Assumption | Status |
|---|---|---|
| Eval in-scope hit@top_k | **≥ 0.70** per example persona | **LOCKED** (2026-11-18) |
| Eval out-of-scope / not-found | **≥ 0.80** correctly below `min_score` for strict | **LOCKED** (2026-11-18) |
| Offline suite | FakeEmbedder + fixture expectations; controlled fixtures also use score_gate | Assumed |
| Live embedder eval | `@pytest.mark.slow` + `PERSONA_BOT_EVAL_LIVE=1` only; never CI | Assumed |
| Zip whitelist | `persona.yaml`, `knowledge/*.{txt,md,pdf,docx}`, `avatar.*` image/svg | Assumed |
| Zip bomb guards | 80 MiB uncompressed / 40 MiB member / 200 members / ratio ≤ 100 | Assumed |
| Bilingual UI | Thai default; English full table in `strings.py`; sidebar toggle | Assumed |
| Regenerate button | **Out of scope** (§19 deferred) | Assumed |
| Baseline path | `tests/eval/baseline.json` (`provisional: false`) | Assumed |

## Phase 3 notes (2026-11-18)

| Item | Assumption |
|---|---|
| Docker base | Pinned `python:3.11.11-slim-bookworm` (multi-arch notes in FIRST_RUN.md) |
| Compose bind | `127.0.0.1:8501` only |
| DoD 1 timing | ≈5 min excludes first embedding model download |
| Keyring | Opt-in via `PERSONA_BOT_REMEMBER_KEY`; stores outside `data/` |
| smoke_test.py | Owner-only; never CI |

## Phase 2 notes (2026-11-18)

| Item | Assumption |
|---|---|
| Branch base | Phase 2 rebased onto **main after PR #3 merge** (1b) |
| Embeddings in tests | **FakeEmbedder only** — CI never downloads ONNX |
| UI embedder | `FastEmbedder` (lite/multilingual/quality presets); first use may download model |
| Thai PDF | Loader supports PDF; fixture uses Helvetica Latin. Thai knowledge covered by `.md`/`.txt` |
| Search-lab / knowledge-health / prompt inspector | Included in Phase 2 sidebar / reply expanders (§16-style tooling) |
| score | `1 - cosine distance` with Chroma `hnsw:space=cosine` |

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
| Coverage floors | Overall **≥ 60%** locked in CI; core **≥ 80%** target when split feasible | **LOCKED** overall (2026-11-18) |
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

**LOCKED** (2026-11-18): overall **≥ 60%** hard-fail in CI (`fail_under=60` /
`--cov-fail-under=60`). Core **≥ 80%** remains a documented target until the
project adds a split core-coverage gate.

## Missing source sections (F1)

Original **§16.8** and **§18.9** still missing; provisional Appendix A / §18.9 remain.
