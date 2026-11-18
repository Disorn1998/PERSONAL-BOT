# DECISIONS — persona-bot

Proposals and provisional decisions. Items marked **ASK** need owner confirmation
before locking. Format: date · status · decision.

## Phase 2 (2026-11-18)

### RAG stack — **DONE**

- Loaders (txt/md/pdf/docx), chunker, FakeEmbedder/FastEmbedder, Chroma store
- `index_fingerprint` + atomic collection rebuild + JSON manifest under `data/index/`
- Retrieval query = previous user + latest; `min_score` filter; strict short-circuit (no LLM)
- Sources expander + citation validation; knowledge health + search lab + prompt inspector
- Example knowledge for study-buddy + tech-explainer

### PDF generation dep — **NOT ADDED**

- No reportlab/fpdf; tests use a minimal hand-written PDF + Thai markdown fixtures (F7).

## Phase 1b (2026-11-18)

### Chat UX shell — **DONE**

- Welcome card when no API key (F15); advanced key controls in sidebar.
- New chat vs clear chat (F16); threads in sqlite `data/chat.sqlite3`.
- Thai error cards via `strings.py` only; CSS bubbles/theme in `app/ui/theme.py`.
- Partial assistant text persisted during stream (F9).
- Usage in `data/usage.json`; model badge + token chips under replies.
- study-buddy default; knowledge/RAG deferred to Phase 2.

### Privacy notice (F19) — **DECISION**

- First-run ack button; persist `data/privacy_ack`.

## Phase 1a (2026-11-18)

### F10 — Phase 1 split — **ASSUMED**

- Proceed with **1a / 1b**. This PR = **1a only** (config, errors, security,
  logging_setup, ratelimit, llm+StreamResult mocks, persona schema, prompt).
- **1b** (Streamlit shell, chat loop, Stop/partial, usage tracker, budget) waits
  for owner 「ไปต่อ」.

### Package name (F1) — **ASSUMED keep `app`**

- Still **ASK** whether to rename to `persona_bot` later.

### Coverage — **ASK (not locked)**

- Proposal remains overall **~60%** / core **~80%**.
- CI `fail_under` stays `0`.

### §17.2 palette — **DECISION (Phase 1a)**

- Migrate from Phase 0 teal → warm cream `#F4F1EA` + primary `#6A5ACD`.

### F2 — Retry layering — **DECISION**

- OpenAI/Groq client `max_retries=0` (`app.llm.SDK_MAX_RETRIES`).
- App owns minute-limit/transport fallback to secondary model; day-limit does not fallback.

### F8 — Model names — **DECISION**

- No silent Python model-id fallbacks; empty `GROQ_MODEL_PRIMARY` → `MissingModelConfigError`.

### Answer modes — **ASSUMED**

- `strict` | `balanced` | `open` with fixed rules blocks in `app/prompt.py`.

### §16.8 / §18.9 — **ASSUMED provisional**

- Keep Appendix A / provisional §18.9 until owner supplies originals.

## Earlier Phase 0 proposals (still active)

### F15 — Key-entry placement — **PROPOSAL** (Phase 1b UI)

- Welcome card when no API key; advanced options after.

### F16 — New chat vs clear chat — **PROPOSAL**

- New thread vs clear current thread; distinct Thai strings already present.

### F17 — SVG avatars — **PROPOSAL**

- SVG repo-only for examples; user packs raster/emoji.

### F18 — Persona form fields — **PROPOSAL**

- Extra §16 fields in advanced editor section (1b+).

### F19 — Privacy notice flag — **PROPOSAL**

- Persist under `data/`.

### F20 — Relevance thresholds — **PROPOSAL**

- Live in embedding preset table + persona overrides.

### F21 — Microcopy — **PROPOSAL**

- Expanded error/hint keys in `app/ui/strings.py` (Phase 1a).

### F22 — Streamlit constraints — **PROPOSAL / VERIFY**

- Streamlit shell deferred to **1b**; pin to installed 1.67.x behaviour.

### F12 — DAILY_TOKEN_LIMIT — **DECISION**

- Display-only; documented in `.env.example`.

### Type checker — **DECISION**

- **mypy** (not pyright); strict core later.

## Open owner questions

1. Lock coverage floors? (proposal 60% / 80%)
2. Rename package `app` → `persona_bot`? (currently keeping `app`)
3. Supply original **§16.8** and **§18.9**
4. Confirm answer_mode triad (`strict`/`balanced`/`open`) vs Complete Edition wording
5. After 1a merge: 「ไปต่อ」 for Phase **1b**
