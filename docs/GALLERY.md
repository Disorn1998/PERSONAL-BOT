# Gallery — example Persona Packs

Bundled under `personas/examples/` (read-only in Docker image).

| Id | Name | Answer mode | Knowledge |
|---|---|---|---|
| `study-buddy` | เพื่อนติว | balanced | photosynthesis + study tips |
| `tech-explainer` | อธิบายเทค | **strict** | HTTP basics + RAG overview |
| `writing-coach` | โค้ชเขียน | open | (none — style helper) |
| `thai-tax-advisor` | ที่ปรึกษาภาษีตัวอย่าง | **strict** | fictional VAT + PIT overview + disclaimer (`min_score` placeholder) |
| `company-faq-bot` | FAQ บริษัทโนวาสมาร์ท | **strict** | fictional company overview / leave / IT |
| `meeting-notes` | จดบันทึกประชุม | balanced | fictional demo meeting + note template |
| `pdf-handbook-demo` | PDF Handbook Demo | **strict** | fictional Cedarvale Maker Space PDFs + disclaimer |
| `en-study-coach` | EN Study Coach | balanced | EN spaced-repetition + exam-week plan (md) |
| `personal-notes` | โน้ตส่วนตัว | **strict** | guided personal-notes template + fictional sample notes |

All example packs include `icon`, `greeting`, `starter_questions`, and `metadata`.
Tax/FAQ/handbook knowledge is **self-written fictional demo content** — not legal or safety advice.
`pdf-handbook-demo` ships tiny self-authored PDFs so clones can verify PDF ingest + citations.
`en-study-coach` is English-first for international onboarding (complements TH `study-buddy`).
`personal-notes` teaches the everyday loop: duplicate → paste your notes → Ready → chat
(works with knowledge-only mode when there is no Groq key/quota).

## Share your pack

1. Sidebar → **Data & backup** → **Download persona (zip)** (single-click)
2. Import on another machine (preview first; duplicate id → reject/rename/overwrite + confirm)
3. Never put API keys inside a pack zip

## Screenshots

UI reference captures (honest layout mockups matching current Streamlit shell + Thai copy;
not marketing composites). Open them from [`assets/`](../assets/).

| Screen | File | What to look for |
|---|---|---|
| Welcome / first run | [`assets/welcome.png`](../assets/welcome.png) | Brand title, onboarding steps, API key + remember status |
| Persona picker | [`assets/persona-picker.png`](../assets/persona-picker.png) | Sidebar persona select + description caption |
| Knowledge panel | [`assets/knowledge.png`](../assets/knowledge.png) | Index status, used/limit MB, upload/paste, rebuild |
| Sources expander | [`assets/sources.png`](../assets/sources.png) | Chat reply with sources list |
| Error card (429) | [`assets/error-card.png`](../assets/error-card.png) | Rate-limit title + retry-after / reset hint |

Also linked from the [README](../README.md) screenshots section.
