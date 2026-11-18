# ASSUMPTIONS — persona-bot Phase 0

Assumptions made when the owner has not answered yet, plus §3 / pre-flight
verification results. Update when the owner replies or when APIs change.

## Package / Python

| Item | Assumption / result | Status |
|---|---|---|
| Importable package name | Spec tree uses `app/` for Phase 0; ask owner whether to rename to `persona_bot` (F1) | **Ask owner** |
| `requires-python` | Kept `>=3.11,<3.14` | Verified enough for Phase 0 (see below) |
| Python 3.13 + chromadb / fastembed+onnxruntime / pythainlp | PyPI / upstream metadata declare 3.13 support for current releases; install verification recorded in Phase 0 report | Partially verified on host Python (see installed versions) |

## §3 Fast-changing external info

| Topic | Result | Verified? |
|---|---|---|
| Groq model deprecations | Fetched https://console.groq.com/docs/deprecations (HTTP 200) on 18 Nov 2026. Confirmed shutdowns: `llama-3.1-8b-instant` & `llama-3.3-70b-versatile` (16 Aug 2026); `qwen/qwen3-32b` & `meta-llama/llama-4-scout-17b-16e-instruct` (17 Jul 2026). Recommended replacements include `openai/gpt-oss-120b` / `openai/gpt-oss-20b` (and newer Qwen IDs). Also noted later 2026 deprecations (`groq/compound*`, `qwen/qwen3.6-27b`). | **Verified** (docs page) |
| `GET /v1/models` | Called without a key → HTTP **401** `invalid_api_key`. Endpoint reachable; live model list **not** retrieved (no key by design). | **Unverified** (auth required) |
| Never call `chat/completions` | Honoured in Phase 0 | N/A |
| Streaming usage location | OpenAI-compatible streaming: set `stream=True` and `stream_options={"include_usage": true}`; usage appears on the **final chunk** (`chunk.usage`), with empty `choices`. | **Verified** (OpenAI docs; Groq OpenAI-compat assumed) |
| `x-ratelimit-*` headers | Groq docs: `x-ratelimit-limit/remaining/reset-requests` map to **RPD**; `…-tokens` map to **TPM**; `retry-after` on 429 only. Access via openai SDK `with_raw_response` / response headers (not on parsed completion alone). | **Verified** (Groq rate-limits docs) |
| Chroma collection names | 3–512 chars (docs) / some code paths still cite 3–63; start/end alphanumeric; dots/dashes/underscores allowed; no `..`; not an IPv4. Prefer lowercase slug from persona id. | **Verified** (docs); re-check against installed chromadb at first RAG use |
| Embedding max input lengths | `TextEmbedding.list_supported_models()` works (41 models on fastembed 0.9.1). Examples: `BAAI/bge-small-en-v1.5` → 512 tok; `sentence-transformers/all-MiniLM-L6-v2` → 256; `paraphrase-multilingual-MiniLM-L12-v2` → **128**; `intfloat/multilingual-e5-large` → 512 (+ E5 prefixes). Measure Thai `chunk_chars=900` vs tokens before locking lite defaults (F5). | **Verified** API; **TODO(verify)** Thai char→token ratio |
| E5 prefixes | Still document `passage: ` / `query: ` when an E5 model is selected | Assumed (spec §3) |
| Free-tier quotas | Never hardcode in README; link official Groq pages only | Honoured |
| Streamlit version / features | Installed **streamlit 1.67.0**. Theme keys used: `primaryColor`, backgrounds, `textColor`, `font`, `gatherUsageStats=false`. Custom fontFaces / static serving deferred until fonts land. `st.write_stream` / Stop-button behaviour still **TODO(verify)** in Phase 1 prototype (F9/F22). | Version verified; UI APIs deferred |

## UX tokens (§17.2)

Phase 0 tokens in `app/ui/tokens.py` + `.streamlit/config.toml` use a light teal
primary (`#0F766E`) on cool off-white. The store copy of the master prompt
abbreviates full §17.2 tables — **if the owner’s Complete English Edition differs,
tokens must be updated to match** before UI phases. F23 contrast automated test
remains authoritative later.

## Coverage

Proposed floors (not locked): **overall ≈ 60%**, **core ≈ 80%**. Ask owner before
enabling `fail_under` in CI.

## Test / tooling extras

| Item | Assumption |
|---|---|
| Type checker | **mypy** (not pyright) wired non-strict for Phase 0 |
| PDF fixtures for tests | Prefer stdlib where possible; announce any PDF generator dependency before adding (F7) |
| OS CI matrix | Phase 0 stub = Ubuntu × Python 3.11/3.12/3.13 only |

## Missing source sections (F1)

Original **§16.8** and **§18.9** are still missing; Appendix A / provisional §18.9
remain lowest priority until the owner supplies the originals.
