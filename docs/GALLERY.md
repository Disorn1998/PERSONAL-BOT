# Gallery — example Persona Packs

Bundled under `personas/examples/` (read-only in Docker image).

| Id | Name (TH) | Answer mode | Knowledge |
|---|---|---|---|
| `study-buddy` | เพื่อนติว | balanced | photosynthesis + study tips |
| `tech-explainer` | อธิบายเทค | **strict** | HTTP basics + RAG overview |
| `writing-coach` | โค้ชเขียน | open | (none — style helper) |
| `thai-tax-advisor` | ที่ปรึกษาภาษีตัวอย่าง | **strict** | fictional VAT + PIT overview + disclaimer (`min_score` placeholder) |
| `company-faq-bot` | FAQ บริษัทโนวาสมาร์ท | **strict** | fictional company overview / leave / IT |

All example packs include `icon`, `greeting`, `starter_questions`, and `metadata`.
Tax/FAQ knowledge is **self-written fictional demo content** — not legal advice.

## Share your pack

1. Sidebar → **Data & backup** → Export persona (zip)
2. Import on another machine (preview first; duplicate id → reject/rename/overwrite)
3. Never put API keys inside a pack zip

## Screenshots

Owner eye-check: attach UI screenshots to releases / README when available.
Streamlit cloud-agent environments may omit visual captures — describe layout in phase reports instead.
