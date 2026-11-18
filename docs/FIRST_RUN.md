# First run / ออฟไลน์แคช

## เป้าหมาย DoD 1

ดับเบิลคลิก `start.bat` (Windows) หรือรัน `./start.sh` แล้วเริ่มแชตได้ในประมาณ 5 นาที  
**ไม่นับเวลาดาวน์โหลดโมเดล embedding ครั้งแรก**

## ขั้นตอนเร็ว

1. ติดตั้ง [uv](https://docs.astral.sh/uv/) (สคริปต์ `start.*` ช่วยติดตั้งให้ถ้ายังไม่มี)
2. คัดลอก `.env.example` → `.env` แล้วใส่ `GROQ_API_KEY`, `GROQ_MODEL_PRIMARY`, `GROQ_MODEL_FALLBACK`
3. รัน `start.bat` / `start.sh` / `docker compose up --build`
4. เปิด UI ที่ **http://127.0.0.1:8501** เท่านั้น (โลคอล)

## Localhost bind (non-Docker)

`persona-bot` / `uv run persona-bot` บังคับ `--server.address=127.0.0.1`  
และ `.streamlit/config.toml` ตั้ง `server.address = "127.0.0.1"`  
Docker Compose ผูกพอร์ต `127.0.0.1:8501:8501` เช่นกัน — ไม่เปิดออกเน็ตภายนอกโดยค่าเริ่มต้น

## Streamlit email / onboarding banner

ครั้งแรก Streamlit อาจถามอีเมล (“Welcome to Streamlit!”)  
`persona-bot` CLI จะสร้าง `~/.streamlit/credentials.toml` ด้วย `email = ""` ถ้ายังไม่มี
เพื่อข้าม prompt นี้

ข้ามเองด้วยมือ:

```bash
mkdir -p ~/.streamlit
printf '%s\n' '[general]' 'email = ""' > ~/.streamlit/credentials.toml
```

Windows (PowerShell):

```powershell
New-Item -ItemType Directory -Force -Path "$HOME\.streamlit" | Out-Null
Set-Content -Path "$HOME\.streamlit\credentials.toml" -Value "[general]`nemail = `"`""
```

`STREAMLIT_BROWSER_GATHER_USAGE_STATS=false` / `gatherUsageStats = false` ปิด telemetry
แต่ **ไม่** แทนที่ credentials ด้านบน

## Embedding cache (โลคอล)

fastembed / Hugging Face จะดาวน์โหลดไฟล์โมเดลครั้งแรก

| สภาพแวดล้อม | ตำแหน่งแคช |
|---|---|
| โลคอล (ค่าเริ่มต้น) | แคชของผู้ใช้ (`HF_HOME` / แคช fastembed ตามไลบรารี) |
| Docker Compose | volume `persona-bot-cache` → `/cache` (`HF_HOME`, `FASTEMBED_CACHE_PATH`) |

ตั้ง `HF_HOME` / `FASTEMBED_CACHE_PATH` เองได้ถ้าต้องการย้ายแคชไปดิสก์อื่น

## ไม่เรียก Groq ใน CI

เทสต์ใช้ mock LLM + `FakeEmbedder` เท่านั้น — `scripts/smoke_test.py` เป็นของเจ้าของโปรเจกต์เท่านั้น

## Multi-arch Docker

อิมเมจฐาน `python:3.11.11-slim-bookworm` รองรับ amd64/arm64 ผ่าน Docker Hub  
สร้างบนเครื่องอื่น:

```bash
docker buildx build --platform linux/amd64,linux/arm64 -t persona-bot:local .
```
