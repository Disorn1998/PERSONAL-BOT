# persona-bot

แชตบอท AI ส่วนตัวที่รันฟรีบนเครื่องคุณ (BYOK ผ่าน Groq + embeddings แบบโลคอล)

Personal AI chatbot you can clone and run for free. Bring your own Groq API key;
embeddings run locally. Configure a **Persona Pack** (role + knowledge + tuning)
and chat in Thai UI.

## สถานะโปรเจกต์ / Status

**Phase 0** — repository scaffold only (no chat UI / RAG / LLM wiring yet).

## ความต้องการ / Requirements

- Python **3.11–3.13** (`requires-python = '>=3.11,<3.14'`)
- [uv](https://docs.astral.sh/uv/)
- Groq API key (owner-provided; never commit)

## ติดตั้งแบบย่อ / Quick start

```bash
uv sync --extra dev
cp .env.example .env
# put GROQ_API_KEY + GROQ_MODEL_* in .env locally — never paste keys into chat
uv run persona-bot
# or: uv run streamlit run app/main.py
```

โควตา/ลิมิตของ Groq ดูจากเอกสารทางการเท่านั้น — ห้ามใส่ตัวเลขโควตาตายตัวใน README  
See official Groq docs for free-tier limits (never hardcode quota numbers here):
https://console.groq.com/docs/rate-limits

## โครงสร้างหลัก / Layout

- `app/` — application package (Phase 0: CLI skeleton + UI tokens/i18n)
- `personas/examples/` — read-only example persona packs (later)
- `data/` — runtime only (gitignored)
- `docs/` — ASSUMPTIONS, DECISIONS, phase reports

## พัฒนา / Development

```bash
uv sync --extra dev
uv run ruff check .
uv run ruff format .
uv run mypy
uv run pytest
```

## ใบอนุญาต / License

MIT — see `LICENSE`.
