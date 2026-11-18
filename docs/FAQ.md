# FAQ — persona-bot

## ต้องจ่ายอะไรไหม / Is it free?

ใช่สำหรับการรันแอป — คุณใช้ **Groq BYOK** (คีย์ของคุณ) และ embeddings โลนเครื่อง  
Yes for running the app: Groq BYOK + local embeddings. No paid SaaS in the stack.

## คีย์ API เก็บที่ไหน / Where is my API key stored?

ค่าเริ่มต้นอยู่ใน session เท่านั้น ไม่เขียนลง `data/`  
Optional: OS keyring เมื่อตั้ง `PERSONA_BOT_REMEMBER_KEY=1` (นอก `data/`, ไม่รวมใน export/backup)

## ทำไมโหมด strict ตอบว่าไม่พบข้อมูล

`answer_mode: strict` จะ **ไม่เรียก LLM** ถ้าไม่มีชิ้นความรู้ผ่าน `min_score` — ประหยัดโควตา

## CI เรียก Groq จริงไหม

ไม่ — unit tests ใช้ mock + `FakeEmbedder`  
Canary รายสัปดาห์เรียกแค่ `GET /models` (ไม่เรียก `chat/completions`)

## เปลี่ยนโมเดลอย่างไร

แก้ใน `.env` เท่านั้น (`GROQ_MODEL_PRIMARY` / `FALLBACK`) — ห้าม hardcode ในโค้ด  
ตรวจ deprecations: https://console.groq.com/docs/deprecations

## Eval thresholds (DoD 7)

ตัวเลขใน `tests/eval/baseline.json` ยัง **provisional** (0.70 / 0.80) จนกว่าเจ้าของจะ lock

## Coverage floors

ข้อเสนอ ~60% overall / ~80% core — **ยังไม่ lock** ใน CI (`fail_under=0`)
