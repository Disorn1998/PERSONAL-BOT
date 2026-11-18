# FAQ — persona-bot

## ต้องจ่ายอะไรไหม / Is it free?

ใช่สำหรับการรันแอป — คุณใช้ **Groq BYOK** (คีย์ของคุณ) และ embeddings โลนเครื่อง  
Yes for running the app: Groq BYOK + local embeddings. No paid SaaS in the stack.

## คีย์ API เก็บที่ไหน / Where is my API key stored?

ค่าเริ่มต้นอยู่ใน session เท่านั้น ไม่เขียนลง `data/`  
Optional: OS keyring เมื่อตั้ง `PERSONA_BOT_REMEMBER_KEY=1` (นอก `data/`, ไม่รวมใน export/backup)

## ทำไมโหมด strict ตอบว่าไม่พบข้อมูล

`answer_mode: strict` จะ **ไม่เรียก LLM** ถ้าไม่มีชิ้นความรู้ผ่าน `min_score` — ประหยัดโควตา

## เพิ่ม PDF / ความรู้ของฉันอย่างไร / How do I add my own PDFs?

1. ถ้าเป็นเพอร์โซนาตัวอย่าง กด **ทำสำเนา** ก่อน (ตัวอย่างแก้ไม่ได้)  
2. เปิด「คลังความรู้」→ อัปโหลด `.txt` `.md` `.pdf` `.docx` หรือวางข้อความ  
3. กด **สร้างดัชนีใหม่** จนสถานะเป็น **พร้อมแล้ว**  
ข้อมูลอยู่ใต้ `data/personas/<id>/knowledge/` บนเครื่องคุณเท่านั้น

## CI เรียก Groq จริงไหม

ไม่ — unit tests ใช้ mock + `FakeEmbedder`  
Canary รายสัปดาห์เรียกแค่ `GET /models` (ไม่เรียก `chat/completions`)

## เปลี่ยนโมเดลอย่างไร

แก้ใน `.env` เท่านั้น (`GROQ_MODEL_PRIMARY` / `FALLBACK`) — ห้าม hardcode ในโค้ด  
ตรวจ deprecations: https://console.groq.com/docs/deprecations

## Eval thresholds (DoD 7)

**LOCKED** (2026-11-18): hit@top_k ≥ **0.70**; strict OOS / not-found ≥ **0.80**  
(`tests/eval/baseline.json` → `provisional: false`)

## Coverage floors

**LOCKED** (2026-11-18): overall ≥ **60%** hard-fail in CI (`--cov-fail-under=60`).  
Core ≥ **80%** is a documented target until split core coverage exists.
