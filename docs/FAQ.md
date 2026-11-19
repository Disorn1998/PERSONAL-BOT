# FAQ — persona-bot

## สำหรับคนทั่วไป / For everyone

### ต้องเป็นโปรแกรมเมอร์ไหม / Do I need to be a developer?

ไม่จำเป็น — ดู [FIRST_RUN.md](FIRST_RUN.md) ส่วน「สำหรับคนทั่วไป」: Docker หรือ `start.bat` → วางคีย์ (หรือข้าม) → เลือก「โน้ตส่วนตัว」→ วางความรู้ → ถาม

### นี่คืออะไร / ไม่ใช่อะไร

**คือ:** บอทส่วนตัวบนเครื่องคุณ · เบราว์เซอร์บนคอม · คีย์ Groq ของคุณเมื่อต้องการ AI · ความรู้ใน `data/`  
**ไม่ใช่:** แอปมือถือ / Line · ซิงค์ข้ามเครื่องอัตโนมัติ · แชตคลาวด์สาธารณะ

### ใช้หลายเครื่องอย่างไร / Multi-device

ไม่มีซิงค์คลาวด์ — ใช้ **ส่งออก zip** บนเครื่อง A แล้ว **นำเข้า** บนเครื่อง B (แถบข้าง → ข้อมูลและการสำรอง)  
อย่าใส่คีย์ใน zip

### ไม่มีคีย์ / โควตาหมด / ออฟไลน์ แล้วยังคุยได้ไหม?

ได้แบบจำกัด: แอปค้นหาโน้ตโลคอลแล้วตอบ「ตอบจากคลังความรู้ (ไม่ใช้ AI ออนไลน์)」เมื่อมีผลลัพธ์  
ถ้าไม่เจอโน้ต จะแสดงสถานะว่างอย่างใจเย็น — **ไม่ใช่** LLM โลคอลคุณภาพ ChatGPT

### มือถือเปิด `127.0.0.1` ได้ไหม?

ได้เฉพาะเบราว์เซอร์บน**เครื่องเดียวกับที่รันแอป** — อย่าเปิดพอร์ตออก LAN เพื่อมือถือเครื่องอื่น (ความเป็นส่วนตัว)

## ต้องจ่ายอะไรไหม / Is it free?

ใช่สำหรับการรันแอป — คุณใช้ **Groq BYOK** (คีย์ของคุณ) และ embeddings โลนเครื่อง  
Yes for running the app: Groq BYOK + local embeddings. No paid SaaS in the stack.  
โหมดคลังความรู้ alone ไม่เรียก Groq

## คีย์ API เก็บที่ไหน / Where is my API key stored?

ค่าเริ่มต้นอยู่ใน session เท่านั้น ไม่เขียนลง `data/`  
Optional remember: ติ๊ก「จำคีย์ในระบบ」**หรือ**ตั้ง `PERSONA_BOT_REMEMBER_KEY=1` — ทั้งสองแบบ
**บันทึกและโหลด** จาก OS keyring (นอก `data/`, ไม่รวมใน export/backup)  
ติ๊กครั้งหนึ่ง → พรุ่งนี้เปิด `start.bat` แล้วคุยต่อได้

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

## ทำไมโหมด「ตอบเฉพาะความรู้」ตอบว่าไม่พบ / Why does strict say ไม่พบ?

`answer_mode: strict` (UI: **ตอบเฉพาะความรู้**) จะ **ไม่เรียก LLM** ถ้าไม่มีชิ้นความรู้ผ่าน `min_score`  
ข้อความว่างอย่างใจเย็นเป็นพฤติกรรมที่ตั้งใจ — ประหยัดโควตาและไม่เดา

ถ้าต้องการคำตอบยืดหยุ่นกว่านี้: เปลี่ยนเป็น **ยืดหยุ่น** / **สไตล์อิสระ** ในตัวแก้ไขเพอร์โซนา  
หรือเพิ่มไฟล์ความรู้แล้วรอสถานะ **พร้อมแล้ว** (อัปโหลด/วางจะสร้างดัชนีให้อัตโนมัติ)

## เพิ่ม PDF / ความรู้ของฉันอย่างไร / How do I add my own PDFs?

1. ถ้าเป็นเพอร์โซนาตัวอย่าง กด **ทำสำเนา** ก่อน (ตัวอย่างแก้ไม่ได้)  
2. เปิด「คลังความรู้」→ อัปโหลด `.txt` `.md` `.pdf` `.docx` หรือวางข้อความ  
3. กด **บันทึกความรู้ให้พร้อมใช้** จนสถานะเป็น **พร้อมแล้ว** (สร้างดัชนีอัตโนมัติ)  
4. แผงความรู้แสดงขนาดใช้ไป / ขีดจำกัด `MAX_KNOWLEDGE_MB` — อัปโหลดเกินลิมิตจะถูกปฏิเสธ  

ข้อมูลอยู่ใต้ `data/personas/<id>/knowledge/` บนเครื่องคุณเท่านั้น  
ทาง zip สำรอง: ส่งออก → ใส่ไฟล์ใน `knowledge/` → นำเข้า (เปลี่ยนชื่อถ้า id ซ้ำ)

**เทมเพลตโน้ตส่วนตัว:** เลือก `personal-notes` /「โน้ตส่วนตัว」→ ทำสำเนา → วางโน้ตของคุณ  
ตัวอย่าง PDF ในแกลเลอรี: `pdf-handbook-demo` (strict) — ดู [GALLERY.md](GALLERY.md)

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
คนทั่วไป**ไม่จำเป็นต้องแตะ** — ค่าแนะนำอยู่ใน `.env.example`  
ตรวจ deprecations: https://console.groq.com/docs/deprecations

## Eval thresholds (DoD 7)

**LOCKED** (2026-11-18): hit@top_k ≥ **0.70**; strict OOS / not-found ≥ **0.80**  
(`tests/eval/baseline.json` → `provisional: false`)

## Coverage floors

**LOCKED** (2026-11-18 / core split 2026-11-19): overall ≥ **60%** hard-fail in CI
(`--cov-fail-under=60`). Core ≥ **80%** hard-fail via
`coverage report --rcfile=coverage.core.toml` (omits Streamlit shell / UI /
helpers — see `docs/DECISIONS.md`).
