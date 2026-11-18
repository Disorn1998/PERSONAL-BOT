# DECISIONS — persona-bot

Proposals and provisional decisions. Items marked **ASK** need owner confirmation
before locking. Format: date · status · decision.

## Phase 0 proposals

### F2 — Retry layering (SDK vs app) — **PROPOSAL**

- Set OpenAI/Groq client `max_retries=0` so the app owns retry / fallback / rate-limit
  behaviour (no double-retry with SDK backoff).
- App-level retries only under the strict conditions in §7.3 / §16.1.

### F8 — Model names vs Settings defaults — **PROPOSAL**

- Never hardcode model IDs in Python modules.
- Defaults live only in `.env.example` / settings load from env.
- If primary/fallback unset at runtime → clear Thai setup message; **no silent
  Python fallback string**.

### Package name (F1) — **ASK**

- Phase 0 keeps import path `app` as in the §6 tree.
- Question: rename installable/importable package to `persona_bot` (or keep `app`)?

### Type checker — **DECISION (Phase 0)**

- Use **mypy** (not pyright). Strict mode only for core modules in later phases.

### Coverage threshold — **ASK before lock**

- Proposal: overall **~60%**, core **~80%**.
- `fail_under` stays `0` until the owner locks numbers.

### F10 — Phase 1 split — **ASK**

- Proposal: split Phase 1 into **1a** (config/settings, llm+StreamResult mocks,
  ratelimit/errors/security/logging, chat_store skeleton, Streamlit shell + key UX)
  and **1b** (prompt/budget, full chat loop, Stop/partial save, usage tracker,
  example persona YAML wiring for study-buddy).
- Owner may keep a single Phase 1 instead.

### F15 — Key-entry placement — **PROPOSAL**

- Show a welcome card when no API key is present; advanced key options after
  first successful entry / in settings.

### F16 — New chat vs clear chat — **PROPOSAL**

- **New chat** = start a new thread (preserve old threads in store).
- **Clear chat** = wipe messages of the current thread only.
- Record distinct Thai strings (`action.new_chat` / `action.clear_chat`).

### F17 — SVG avatars — **PROPOSAL**

- SVG avatars allowed in the repo for example personas only.
- User-created / imported packs use raster images or emoji (no arbitrary SVG
  execution path).

### F18 — Persona form fields from §16 — **PROPOSAL**

- Place extra §16 persona fields in the advanced section of the persona editor
  (§18.6 note); keep the primary form short.

### F19 — Privacy notice first-time flag — **PROPOSAL**

- Persist acknowledgement under `data/` (not in Persona Pack export).

### F20 — Relevance word thresholds — **PROPOSAL**

- Single config table (with embedding presets) + calibration notes; no scattered
  magic numbers.

### F21 — Missing microcopy — **PROPOSAL**

- Starter Thai keys live in `app/ui/strings.py`; expand from §18.7 when UI parts land.

### F22 — Streamlit constraints — **PROPOSAL / VERIFY**

- Pin behaviour to the installed Streamlit major/minor recorded in ASSUMPTIONS /
  Phase 0 report; avoid APIs newer than that version without bumping the pin.

### F12 — DAILY_TOKEN_LIMIT — **DECISION**

- Display-only hint; documented in `.env.example`. Does not enforce Groq quota.

## Open owner questions (summary)

1. Supply original **§16.8** and **§18.9** (replace provisional Appendix A / §18.9).
2. Keep package import name **`app`** or rename to **`persona_bot`**?
3. Lock coverage floors? (proposal 60% / 80%)
4. Approve Phase **1a/1b** split?
5. Confirm or correct Phase 0 **§17.2** token colours if the Complete Edition differs.
