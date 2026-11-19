# DECISIONS — persona-bot

Proposals and provisional decisions. Items marked **ASK** need owner confirmation
before locking. Format: date · status · decision.

## First-run guided tour (2026-11-19) — **DECISION**

- Interactive 6-step coach overlay (welcome paths → path cue → persona →
  knowledge ready → chat input → done). CSS spotlight + coach card only — no
  real 3D / WebGL / `.glb`. Mascot from existing illustrations (`chat.svg` /
  welcome hero). Persist completion in `data/tour_done`; Skip or Start using
  marks done; replay via「เปิดทัวร์อีกครั้ง」under More settings. Strings TH/EN.

## Welcome hero motion (2026-11-19) — **DECISION**

- Soft **2D CSS-only** float (~5s) + subtle tilt/parallax (`translate` +
  `rotate`) + shadow pulse on `.pb-welcome-hero` / img. No WebGL / Three.js /
  `.glb`. Hero inlined as JPEG data URI so the class wraps the image under
  Streamlit. `prefers-reduced-motion: reduce` disables animation.

## Chat interior polish (2026-11-19) — **DECISION**

- Chat column matches welcome electric-blue soft-3D: user/assistant bubbles,
  citation chips, short model/token badges, chat-input focus, light `pb-fade`.
- Reliable role markers (`.pb-role-user` / `.pb-role-assistant`) wrap messages so
  bubble CSS works when Streamlit `:has(avatar)` is flaky (e.g. Windows).
- Hide 1–2–3 wizard strip once `entry_path` is set; knowledge-only replies show
  the knowledge badge only (no token chrome).

## Simple beginner sidebar (2026-11-19) — **DECISION**

- Default sidebar = language, persona, chat thread / new+clear, simple Knowledge,
  one「ตั้งค่า」(API key). No tagline / usage / version / health dump at top level.
- Usage, version, persona editor, backup, health, Advanced labs live under
  collapsed「ตั้งค่าเพิ่มเติม」. Power features kept, not deleted.
- Short plain TH/EN labels; no `DAILY_TOKEN_LIMIT` / long help walls in the
  default chrome. Version UI prefers checkout `APP_VERSION` over stale metadata.

## Everyday beginner UX + knowledge-only fallback (2026-11-19) — **DECISION**

- **Audience docs:** README / FIRST_RUN / FAQ lead with「สำหรับคนทั่วไป」; pin what
  this is/isn’t; multi-device = zip only; honest offline/token limits (no fake
  local ChatGPT claim).
- **Editor UX:** default fields = name + system prompt + plain answer-mode labels
  (ตอบเฉพาะความรู้ / ยืดหยุ่น / สไตล์อิสระ) + knowledge; temperature / top_k /
  min_score / chunk / embedding under「ขั้นสูง」. Search lab + prompt inspector
  live under Advanced only.
- **Knowledge ready:** upload/paste primary action auto-rebuilds index
  (「บันทึกความรู้ให้พร้อมใช้」); manual rebuild remains secondary; banner when
  `needs_rebuild`.
- **Calm OOS:** strict not-found is an info empty state — no error card / model
  token chrome when no LLM call.
- **Knowledge-only mode:** `persona_bot/knowledge_answer.py` formats extractive
  citations when key missing, 429 (minute/day), transport error, or user chose
  continue-without-key. BYOK + Groq remains primary when key+quota available.
- **Template:** example pack `personal-notes` (strict, fictional sample notes).

## P0 in-app persona / knowledge editor (2026-11-18)

### F18 — Persona form + knowledge upload — **DECISION**

- User packs under `data/personas/<id>/`: create + edit name, system prompt,
  `answer_mode`, temperature, max_tokens, embedding preset, top_k, min_score,
  chunk_chars; save `persona.yaml`.
- Knowledge: upload `.txt/.md/.pdf/.docx` or paste → `knowledge/`; enforce
  extension whitelist + `MAX_KNOWLEDGE_MB`; one-click rebuild with plain Thai
  status (`พร้อมแล้ว` / `ต้องสร้างดัชนีใหม่`).
- Examples remain read-only for edit/delete; **ทำสำเนา** copies to a user pack
  (`<id>-copy`).
- Logic in `persona_bot/persona_editor.py`; UI sidebar expanders; README
  “Customize knowledge” bridge kept for zip path.

## Finish v1 gaps (2026-11-18) — owner authorized

### Package name (F1) — **DECISION**

- Renamed importable package **`app` → `persona_bot`**.
- Package root lives at `persona_bot/` (same layout as former `app/`).
- Console script entry: `persona-bot = "persona_bot.cli:main"`.
- Docker image `WORKDIR` remains `/app` (container path, not the Python package).
- i18n string keys such as `app.title` are unchanged (UI keys, not imports).

### Example personas (§9) — **DECISION**

- Restored `thai-tax-advisor` + `company-faq-bot` alongside study-buddy / tech-explainer / writing-coach.
- Schema fields: `icon`, `greeting`, `starter_questions`, `metadata` (optional).
- Knowledge is self-written fictional demo content only; tax pack carries disclaimer + `min_score` placeholder note.

### CI hardening — **DECISION**

- `.gitattributes`: `* text=auto eol=lf` (Windows ruff format / CRLF).
- `.gitleaks.toml`: allowlist test fixture secret shapes (history + current).
- `pip-audit`: `--ignore-vuln` for chromadb PYSEC IDs with empty Fix Versions until upstream patches; recorded in ASSUMPTIONS.

## Locks (2026-11-18) — owner authorized

### Eval thresholds (DoD 7) — **LOCKED**

- In-scope hit@top_k **≥ 0.70**; strict out-of-scope / not-found **≥ 0.80**.
- `tests/eval/baseline.json` sets `provisional: false`.
- No longer provisional; treat DoD 7 numerics as final until a future owner revision.

### Coverage CI gates — **LOCKED** (overall + core split)

- Overall **≥ 60%**: hard fail via `pyproject.toml` `fail_under = 60` and CI
  `--cov-fail-under=60` (not soft).
- Core **≥ 80%**: hard fail via `coverage report --rcfile=coverage.core.toml`
  (omit Streamlit shell / UI chrome / non-core helpers). See omitlist below.
  Do **not** raise overall `fail_under` above 60 until `main.py` is thinned or
  has meaningful AppTest coverage.

### Core coverage omitlist — **DECISION** (2026-11-19)

Modules **omitted** from the core ≥80% gate (still counted toward overall ≥60%):

| Path | Why omitted |
|---|---|
| `persona_bot/main.py` | Streamlit UI shell monolith |
| `persona_bot/ui/*` | UI chrome (theme/strings/wizard) |
| `persona_bot/eval_harness.py` | Offline/live eval harness |
| `persona_bot/backup.py` | Ops helper |
| `persona_bot/cli.py` | Packaging / entrypoint helper |
| `persona_bot/versioning.py` | Version display helper |

Config file: `coverage.core.toml`. CI step runs after the overall cov job.

### Release tag — **AUTHORIZED**

- Cut annotated tag `v0.1.0` on the merge commit of this lock PR to trigger GHCR.

## Phase 5 (2026-11-18) — final phase wrap-up

### CI / DoD 6 — **DECISION**

- Matrix: Ubuntu × {3.11,3.12,3.13} + Windows/macOS × {3.12}
- Jobs: ruff, format, mypy, pytest `-m "not slow"` + hard coverage (≥60%), Docker e2e (fake Groq)
- Security workflow: gitleaks (docker), pip-audit (`uvx`), CodeQL (public)
- Canary workflow: weekly `GET /models` vs `.env.example`; never `chat/completions`
- Release workflow: tag `v*` → GHCR

### Coverage — **LOCKED** (2026-11-18; core split 2026-11-19)

- Overall ≥60% hard-fail; core ≥80% hard-fail via `coverage.core.toml` omitlist.

### Eval thresholds — **LOCKED** (2026-11-18)

- 0.70 hit@top_k / 0.80 OOS not-found (DoD 7 final until revised).

### Docs/legal — **DECISION**

- CODE_OF_CONDUCT, CODEOWNERS, FAQ, GALLERY, issue/PR templates, SemVer CHANGELOG,
  expanded THIRD_PARTY_NOTICES model licence table (TODO(verify) on HF cards)

## Phase 4 (2026-11-18)

### Eval thresholds (DoD 7) — **LOCKED** (superseded provisional; 2026-11-18)

- Baseline in `tests/eval/baseline.json` with `provisional: false`.
- Numbers: in-scope hit@top_k **0.70**; out-of-scope not-found **0.80**.

### Persona zip I/O — **DECISION**

- Safe import: reject path traversal, symlinks, non-whitelist members, zip bombs.
- Duplicate id policies: reject (default) / rename / overwrite; UI always previews first.
- Export never includes secrets (`assert_no_secret_in_mapping` when api_key known).

### Data tools — **DECISION**

- Sidebar: export/import, delete user persona, backup/restore, delete-all (with confirm).
- Backup skips `.env` / api_key-looking paths; restore uses same zip guards.

### Bilingual UI — **DECISION**

- `strings.py` has complete `th` + `en`; `i18n.set_locale` + sidebar language select.
- Missing EN key falls back to TH then the raw key.

### F20 relevance thresholds — **DECISION**

- Remain in embedding preset table + persona overrides; calibrated via eval baseline.

## Phase 3 (2026-11-18)

### Distribution — **DONE**

- `start.bat` / `start.command` / `start.sh`; CLI chdirs to project root; telemetry off
- Dockerfile non-root + healthcheck; compose localhost + `./data` + cache volume
- `data/version.json` schema v1 + UI version caption; system health + first-run wizard
- Optional keyring remember-key; APP_PASSWORD gate retained

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
- Thai error cards via `strings.py` only; CSS bubbles/theme in `persona_bot/ui/theme.py`.
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

### Package name (F1) — **SUPERSEDED**

- Originally kept `app`; owner later authorized rename → see **Finish v1 gaps**.

### Coverage — **LOCKED** (2026-11-18; see Locks section)

- Overall **≥ 60%** hard-fail; core **≥ 80%** target when split feasible.

### §17.2 palette — **DECISION (Phase 1a)**

- Migrate from Phase 0 teal → warm cream `#F4F1EA` + primary `#6A5ACD`.

### F2 — Retry layering — **DECISION**

- OpenAI/Groq client `max_retries=0` (`persona_bot.llm.SDK_MAX_RETRIES`).
- App owns minute-limit/transport fallback to secondary model; day-limit does not fallback.

### F8 — Model names — **DECISION**

- No silent Python model-id fallbacks; empty `GROQ_MODEL_PRIMARY` → `MissingModelConfigError`.

### Answer modes — **ASSUMED**

- `strict` | `balanced` | `open` with fixed rules blocks in `persona_bot/prompt.py`.

### §16.8 / §18.9 — **ASSUMED provisional**

- Keep Appendix A / provisional §18.9 until owner supplies originals.

## Earlier Phase 0 proposals (still active)

### F15 — Key-entry placement — **PROPOSAL** (Phase 1b UI)

- Welcome card when no API key; advanced options after.

### F16 — New chat vs clear chat — **PROPOSAL**

- New thread vs clear current thread; distinct Thai strings already present.

### F17 — SVG avatars — **PROPOSAL**

- SVG repo-only for examples; user packs raster/emoji.

### F18 — Persona form fields — **SUPERSEDED**

- Implemented as P0 in-app editor (see top section).

### F19 — Privacy notice flag — **PROPOSAL**

- Persist under `data/`.

### F20 — Relevance thresholds — **PROPOSAL**

- Live in embedding preset table + persona overrides.

### F21 — Microcopy — **PROPOSAL**

- Expanded error/hint keys in `persona_bot/ui/strings.py` (Phase 1a).

### F22 — Streamlit constraints — **PROPOSAL / VERIFY**

- Streamlit shell deferred to **1b**; pin to installed 1.67.x behaviour.

### F12 — DAILY_TOKEN_LIMIT — **DECISION**

- Display-only; documented in `.env.example`; shown in usage sidebar as `tokens / limit`.

### Type checker — **DECISION**

- **mypy** (not pyright); strict core later.

## Open owner questions

1. ~~Lock coverage floors?~~ → **LOCKED** 2026-11-18 (overall 60%; core 80% target)
2. ~~Rename package `app` → `persona_bot`?~~ → **DONE** 2026-11-18
3. Supply original **§16.8** and **§18.9**
4. Confirm answer_mode triad (`strict`/`balanced`/`open`) vs Complete Edition wording
5. ~~Lock or revise Phase 4 eval numbers?~~ → **LOCKED** 2026-11-18 (0.70 / 0.80)
6. Add maintainer secret `GROQ_API_KEY` for weekly canary (optional but recommended)
7. Verify embedding model licences on Hugging Face cards (clear TODO(verify) in THIRD_PARTY_NOTICES)
8. ~~When to add split core-coverage CI gate (≥80%)?~~ → **DONE** 2026-11-19 (`coverage.core.toml`)
