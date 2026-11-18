# DESIGN — persona-bot

Design tokens live in `app/ui/tokens.py` and `.streamlit/config.toml` (§17.2).
Product copy lives in `app/ui/strings.py` (Thai primary, English secondary).

## Accessibility checklist (Phase 4)

Owner eye-check after UI changes. Streamlit limits some semantics; prefer native widgets.

| # | Check | Status / notes |
|---|---|---|
| A1 | Text/background contrast — primary `#6A5ACD` on cream `#F4F1EA`, body `#1A1D21` | Automated token test remains authoritative (F23); spot-check in light UI |
| A2 | Do not rely on color alone for errors — error cards include text + hint | Implemented via `strings.py` + `format_error_card` |
| A3 | Hit targets — sidebar actions use Streamlit buttons (full-width where paired) | Export/import/backup use standard widgets |
| A4 | Language toggle reachable in sidebar (`label.language`) without burying under Advanced | Phase 4 |
| A5 | Form labels — every input uses `t(...)` label keys (no unlabeled password/key fields) | Keep when adding widgets |
| A6 | Focus order — primary chat input remains page-bottom; destructive actions behind confirm | Delete persona / delete all require confirm click |
| A7 | Motion — no essential information only in animation; Streamlit defaults only | No custom flashing |
| A8 | Attachments — zip import shows preview JSON before confirm (filename + sizes) | Safe pack I/O |
| A9 | Non-text — example avatars may be emoji/raster; SVG examples stay repo-only (F17) | Still proposal for custom packs |
| A10 | Keyboard — Streamlit chat input + tab through sidebar controls | Owner eye-check on Windows/macOS |
| A11 | Locale fallback — missing EN key falls back to TH then raw key | `app/i18n.py` |
| A12 | No regenerate control in v1 (§19 deferred) | Explicitly out of Phase 4 |

## Visual principles (short)

- Warm cream surface + single primary accent; avoid purple-glow / dark-mode drift beyond tokens.
- One job per sidebar expander (knowledge, data tools, health, advanced).
- Thai-first UI; English is a complete secondary table, not a partial overlay.
