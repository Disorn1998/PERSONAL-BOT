# FAQ — persona-bot

## ต้องจ่ายอะไรไหม / Is it free?

ใช่สำหรับการรันแอป — คุณใช้ **Groq BYOK** (คีย์ของคุณ) และ embeddings โลนเครื่อง  
Yes for running the app: Groq BYOK + local embeddings. No paid SaaS in the stack.

## คีย์ API เก็บที่ไหน / Where is my API key stored?

ค่าเริ่มต้นอยู่ใน session เท่านั้น ไม่เขียนลง `data/`  
Optional remember: ติ๊ก「จำคีย์ในระบบ」**หรือ**ตั้ง `PERSONA_BOT_REMEMBER_KEY=1` — ทั้งสองแบบ
**บันทึกและโหลด** จาก OS keyring (นอก `data/`, ไม่รวมใน export/backup)

## ข้อมูลของฉันอยู่ที่ไหน / Where is my data?

ทั้งหมดอยู่บนเครื่องคุณภายใต้ `data/` (gitignored):

| Path | Contents |
|---|---|
| `data/chat.sqlite3` | Chat threads / messages |
| `data/personas/<id>/` | Your persona packs + `knowledge/` uploads |
| `data/chroma/` | Local vector index |
| `data/usage.json` | Local token counters |
| OS keyring | Optional remembered Groq key (not under `data/`) |

Embeddings cache อยู่ที่แคชของผู้ใช้ / Docker volume — ดู [FIRST_RUN.md](FIRST_RUN.md)  
Nothing is uploaded to a persona-bot server; only Groq receives chat prompts when you call the model.

## ทำไมโหมด strict ตอบว่า「ไม่พบ」/ Why does strict say ไม่พบ?

`answer_mode: strict` จะ **ไม่เรียก LLM** ถ้าไม่มีชิ้นความรู้ผ่าน `min_score`  
ข้อความ「ไม่พบข้อมูลที่เกี่ยวข้องในคลังความรู้」เป็นพฤติกรรมที่ตั้งใจ — ประหยัดโควตาและไม่เดา

ถ้าต้องการคำตอบยืดหยุ่นกว่านี้: เปลี่ยนเป็น `balanced` / `open` ในตัวแก้ไขเพอร์โซนา
หรือเพิ่มไฟล์ความรู้แล้วกด **สร้างดัชนีใหม่** และ/หรือลด `min_score`

## เพิ่ม PDF / ความรู้ของฉันอย่างไร / How do I add my own PDFs?

1. ถ้าเป็นเพอร์โซนาตัวอย่าง กด **ทำสำเนา** ก่อน (ตัวอย่างแก้ไม่ได้)  
2. เปิด「คลังความรู้」→ อัปโหลด `.txt` `.md` `.pdf` `.docx` หรือวางข้อความ  
3. กด **สร้างดัชนีใหม่** จนสถานะเป็น **พร้อมแล้ว**  
4. แผงความรู้แสดงขนาดใช้ไป / ขีดจำกัด `MAX_KNOWLEDGE_MB` — อัปโหลดเกินลิมิตจะถูกปฏิเสธ  

ข้อมูลอยู่ใต้ `data/personas/<id>/knowledge/` บนเครื่องคุณเท่านั้น  
ทาง zip สำรอง: ส่งออก → ใส่ไฟล์ใน `knowledge/` → นำเข้า (เปลี่ยนชื่อถ้า id ซ้ำ)

## Windows: `uv` / SmartScreen / long paths

- **`uv` not found:** `start.bat` เติม PATH ชั่วคราวเท่านั้น — เปิดเทอร์มินัลใหม่แล้วรัน  
  `$env:Path = "$env:USERPROFILE\.local\bin;$env:Path"` หรือเพิ่ม User PATH ถาวร  
- **SmartScreen:** More info → Run anyway สำหรับ `start.bat` หรือใช้ขั้นตอน PowerShell ใน README  
- **Path too long:** เปิด Win32 long paths หรือวางโปรเจกต์ใกล้ `C:\`  
ดู [FIRST_RUN.md](FIRST_RUN.md) ส่วน Windows troubleshooting

## `DAILY_TOKEN_LIMIT` คืออะไร

ค่าใน `.env` สำหรับ **แสดงในแถบใช้งาน** เท่านั้น (F12) — ไม่บังคับโควตา Groq  
ว่าง = แสดงจำนวนโทเคนสะสมโดยไม่มีตัวเศษ

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

**LOCKED** (2026-11-18 / core split 2026-11-19): overall ≥ **60%** hard-fail in CI
(`--cov-fail-under=60`). Core ≥ **80%** hard-fail via
`coverage report --rcfile=coverage.core.toml` (omits Streamlit shell / UI /
helpers — see `docs/DECISIONS.md`).
