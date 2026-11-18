# First run / ออฟไลน์แคช

## เป้าหมาย DoD 1

ดับเบิลคลิก `start.bat` (Windows) หรือรัน `./start.sh` แล้วเริ่มแชตได้ในประมาณ 5 นาที  
**ไม่นับเวลาดาวน์โหลดโมเดล embedding ครั้งแรก**

## ขั้นตอนเร็ว

1. ติดตั้ง [uv](https://docs.astral.sh/uv/) (สคริปต์ `start.*` ช่วยติดตั้งให้ถ้ายังไม่มี)
2. คัดลอก `.env.example` → `.env` แล้วใส่ `GROQ_API_KEY`, `GROQ_MODEL_PRIMARY`, `GROQ_MODEL_FALLBACK`
3. รัน `start.bat` / `start.sh` / `docker compose up --build`

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
