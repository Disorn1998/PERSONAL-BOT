# persona-bot

แชตบอท AI ส่วนตัวที่รันฟรีบนเครื่องคุณ (BYOK ผ่าน Groq + embeddings แบบโลคอล)

Personal AI chatbot you can clone and run for free. Bring your own Groq API key;
embeddings run locally. Configure a **Persona Pack** (role + knowledge + tuning)
and chat in Thai UI.

## Quick start — 3 วิธี / 3 ways

### 1) Windows (แนะนำสำหรับ DoD 1)

1. ติดตั้ง [Python 3.11+](https://www.python.org/downloads/) (ติ๊ก Add to PATH)
2. ดับเบิลคลิก `start.bat` (ติดตั้ง uv + sync + เปิด UI ให้)
3. คัดลอก `.env.example` → `.env` ใส่ `GROQ_API_KEY` และ `GROQ_MODEL_*` แล้วรีสตาร์ทถ้ายังไม่ได้ใส่

PowerShell (ทางเลือก):

```powershell
irm https://astral.sh/uv/install.ps1 | iex
Copy-Item .env.example .env
# edit .env — set GROQ_API_KEY + GROQ_MODEL_PRIMARY/FALLBACK
uv sync
uv run persona-bot
```

### 2) macOS / Linux (`uv`)

```bash
./start.sh
# or:
uv sync
cp -n .env.example .env
uv run persona-bot
```

### 3) Docker

```bash
cp -n .env.example .env   # set GROQ_* locally — never commit
docker compose up --build
# open http://127.0.0.1:8501
```

โควตา/ลิมิตของ Groq ดูจากเอกสารทางการเท่านั้น — ห้ามใส่ตัวเลขโควตาตายตัวใน README  
See official Groq docs for free-tier limits:
https://console.groq.com/docs/rate-limits

รายละเอียดแคชโมเดล / first-run: [docs/FIRST_RUN.md](docs/FIRST_RUN.md)

## ความต้องการ / Requirements

- Python **3.11–3.13** หรือ Docker
- [uv](https://docs.astral.sh/uv/)
- Groq API key (never commit)

## โครงสร้างหลัก / Layout

- `persona_bot/` — application (chat UI + RAG)
- `personas/examples/` — example persona packs
- `data/` — runtime only (gitignored)
- `start.bat` / `start.command` / `start.sh` — one-click launchers
- `Dockerfile` / `docker-compose.yml` — localhost-only packaging

## พัฒนา / Development

```bash
uv sync --extra dev
uv run ruff check .
uv run ruff format .
uv run mypy
uv run pytest -m "not slow" --cov=persona_bot --cov-fail-under=60
```

Owner-only live smoke (not CI): `uv run python scripts/smoke_test.py`  
Weekly canary (maintainer): `GET /models` only — see `.github/workflows/canary.yml`

Docs: [FAQ](docs/FAQ.md) · [Gallery](docs/GALLERY.md) · [First run](docs/FIRST_RUN.md) ·
[Design/a11y](docs/DESIGN.md) · [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md)

## ใบอนุญาต / License

MIT — see `LICENSE`. Third-party / model notices: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
