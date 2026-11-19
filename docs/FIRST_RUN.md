# First run / ออฟไลน์แคช

## สำหรับคนทั่วไป / For everyone

เป้าหมาย: เปิดแอปแล้วคุยได้โดยไม่ต้องเป็นวิศวกร

1. **ติดตั้ง Docker Desktop** (แนะนำถ้าไม่คุ้น Python) **หรือ** ดับเบิลคลิก `start.bat` / รัน `./start.sh`
2. สมัคร [Groq](https://console.groq.com/) ฟรี → คัดลอก API key  
   - วางในช่อง UI **หรือ** ใส่แค่ `GROQ_API_KEY` ใน `.env`  
   - **ไม่ต้องแก้** `GROQ_MODEL_*` — ค่าแนะนำมากับ `.env.example` แล้ว
3. เลือกเพอร์โซนา (เช่น「โน้ตส่วนตัว」) → ถามได้เลย  
   - ติ๊ก「จำคีย์」ครั้งหนึ่ง → พรุ่งนี้เปิด `start.bat` แล้วคุยต่อได้  
   - **ไม่มีคีย์?** กด「ใช้แบบคลังความรู้เท่านั้น」→ วางโน้ต → ถามจากคลัง

เปิด UI ที่ **http://127.0.0.1:8501** เท่านั้น (โลคอล)

### นี่คืออะไร / ไม่ใช่

- **คือ:** บอทส่วนตัวบนเครื่องคุณ · เบราว์เซอร์บนคอม · คีย์ Groq ของคุณ · ความรู้อยู่ใน `data/`
- **ไม่ใช่:** แอปมือถือ / Line · ซิงค์คลาวด์อัตโนมัติ · เปิดพอร์ตให้มือถือบน LAN (อย่าทำ — ความเป็นส่วนตัว)
- **หลายเครื่อง:** ส่งออกเพอร์โซนาเป็น zip → นำเข้าบนเครื่องอื่น (ดู FAQ)

### ออฟไลน์ / โควตาหมด (ข้อจำกัดที่ตรงไปตรงมา)

| สิ่งที่ทำได้โลคอล | สิ่งที่ต้องมีเน็ต + คีย์ + โควตา |
|---|---|
| ดึงความรู้ (Chroma + fastembed) | คำตอบแบบ AI จาก Groq |
| โหมด「ตอบจากคลังความรู้ (ไม่ใช้ AI ออนไลน์)」เมื่อมีผลค้นหา | คุณภาพระดับ ChatGPT / เขียนใหม่ยาว ๆ |

แอป**จะไม่**อ้างว่ามี LLM โลคอลเต็มรูปแบบ — เมื่อคีย์หาย / 429 / เน็ตล่ม จะตอบแบบอ้างข้อความจากโน้ตถ้ามี

**เวลา ~5 นาที (DoD 1):** นับจากหลังติดตั้ง Python/Docker แล้ว — **ไม่นับ** ดาวน์โหลดโมเดล embedding ครั้งแรก (อาจเห็นความคืบหน้าตอนสร้างดัชนีครั้งแรก)

## ขั้นตอนเร็ว (รายละเอียดเทคนิค)

1. ติดตั้ง [uv](https://docs.astral.sh/uv/) (สคริปต์ `start.*` ช่วยติดตั้งให้ถ้ายังไม่มี)
2. คัดลอก `.env.example` → `.env` แล้วใส่ `GROQ_API_KEY` (โมเดลมีค่าเริ่มต้นแล้ว)
3. รัน `start.bat` / `start.sh` / `docker compose up --build`
4. เปิด UI ที่ **http://127.0.0.1:8501** เท่านั้น (โลคอล)

## Localhost bind (non-Docker)

`persona-bot` / `uv run persona-bot` บังคับ `--server.address=127.0.0.1`  
และ `.streamlit/config.toml` ตั้ง `server.address = "127.0.0.1"`  
Docker Compose ผูกพอร์ต `127.0.0.1:8501:8501` เช่นกัน — ไม่เปิดออกเน็ตภายนอกโดยค่าเริ่มต้น

## Windows troubleshooting

### `uv` not on PATH

`start.bat` ติดตั้ง uv แล้วเติม `%USERPROFILE%\.local\bin` (และ `.cargo\bin`) ให้ **เฉพาะเซสชันนั้น**  
ถ้าเปิด PowerShell ใหม่แล้วขึ้น `uv: command not found`:

```powershell
$env:Path = "$env:USERPROFILE\.local\bin;$env:USERPROFILE\.cargo\bin;$env:Path"
# หรือเพิ่มโฟลเดอร์นี้ใน Settings → System → Environment Variables → Path
```

### SmartScreen

Windows อาจบล็อก `start.bat` ที่ดาวน์โหลดจาก GitHub — เลือก **More info → Run anyway**  
หรือข้ามไปใช้คำสั่ง PowerShell ใน README แทน

### Long paths

เส้นทางลึก / unzip ยาวเกินขีดจำกัดเก่าของ Windows อาจพังตอน `uv sync` หรือแตก zip  
เปิด **Win32 long paths** (Group Policy / registry) หรือคลอน repo ใกล้รากดิสก์ เช่น `C:\dev\PERSONAL-BOT`

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

fastembed / Hugging Face จะดาวน์โหลดไฟล์โมเดลครั้งแรก — อาจใช้เวลาและต้องการเน็ต**ครั้งแรกเท่านั้น**  
หลังแคชแล้ว การค้นหาความรู้ทำงานออฟไลน์ได้

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
