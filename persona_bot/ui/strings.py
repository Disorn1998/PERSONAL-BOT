"""UI strings — Thai primary, English secondary (Phase 4 bilingual)."""

from __future__ import annotations

from typing import Final

_TH: dict[str, str] = {
    "app.title": "persona-bot",
    "app.tagline": "แชตบอทส่วนตัวที่ตั้งบทบาท ความรู้ และค่าปรับแต่งได้",
    "app.welcome": "ยินดีต้อนรับ — ใส่คีย์ Groq หรือเริ่มแบบคลังความรู้เท่านั้น",
    "app.welcome.body": (
        "คีย์เก็บในเซสชันนี้เป็นค่าเริ่มต้น ไม่ถูกบันทึกลง data/ "
        "ถ้ายังไม่มีคีย์ ก็วางโน้ตแล้วถาม-ตอบจากคลังได้ (ไม่ใช้ AI ออนไลน์)"
    ),
    "app.onboarding.step1": "1) (แนะนำ) วาง Groq API key — หรือข้ามไปใช้คลังความรู้",
    "app.onboarding.step2": "2) เลือกเพอร์โซนา เช่น「โน้ตส่วนตัว」หรือ「เพื่อนติว」",
    "app.onboarding.step3": "3) วางความรู้แล้วถาม — หรือพิมพ์ข้อความด้านล่าง",
    "app.what_this_is": (
        "นี่คืออะไร: บอทส่วนตัวบนเครื่องคุณ · เปิดในเบราว์เซอร์บนคอม · "
        "ใช้คีย์ Groq ของคุณเมื่อต้องการ AI · ไม่ซิงค์ข้ามเครื่องอัตโนมัติ · "
        "ไม่ใช่แอปมือถือ/Line — ย้ายเครื่องด้วย zip ส่งออก/นำเข้า"
    ),
    "wizard.step1": "API key",
    "wizard.step2": "ความเป็นส่วนตัว",
    "wizard.step3": "เริ่มแชต",
    "wizard.locked_tools": ("สำรอง/นำเข้าอยู่ใน「ตั้งค่าเพิ่มเติม」หลังมีคีย์ — ความรู้และแชตจากโน้ตใช้ได้แม้ยังไม่มีคีย์"),
    "wizard.knowledge_only_hint": (
        "ตอบจากโน้ตบนเครื่อง (ไม่ใช้ AI ออนไลน์) เมื่อไม่มีคีย์ / โควตาหมด / ออฟไลน์"
    ),
    "action.new_chat": "แชตใหม่",
    "action.clear_chat": "ล้างแชต",
    "action.confirm_clear_chat": "ยืนยันล้างแชต",
    "action.stop": "หยุด",
    "action.send": "ส่ง",
    "action.save_key": "ใช้คีย์นี้",
    "action.forget_key": "ลืมคีย์ในเซสชัน",
    "action.got_it": "เข้าใจแล้ว",
    "action.export_persona": "ดาวน์โหลดเพอร์โซนา (zip)",
    "action.import_persona": "นำเข้าเพอร์โซนา (zip)",
    "action.preview_import": "ดูตัวอย่างก่อนนำเข้า",
    "action.confirm_import": "ยืนยันนำเข้า",
    "action.confirm_overwrite": "ยืนยันเขียนทับแพ็กที่มีอยู่",
    "action.delete_persona": "ลบเพอร์โซนาผู้ใช้",
    "action.backup": "สำรอง data/",
    "action.restore": "คืนค่าจากสำรอง",
    "action.delete_all_data": "ลบข้อมูลทั้งหมด",
    "action.confirm_delete": "ยืนยันการลบ",
    "action.create_persona": "สร้างเพอร์โซนา",
    "action.save_persona": "บันทึกเพอร์โซนา",
    "action.duplicate_persona": "ทำสำเนา",
    "action.upload_knowledge": "อัปโหลดไฟล์",
    "action.paste_knowledge": "บันทึกข้อความที่วาง",
    "action.make_knowledge_ready": "บันทึกให้พร้อมใช้",
    "action.continue_knowledge_only": "ใช้แบบความรู้เท่านั้น (ไม่ใส่คีย์)",
    "action.use_knowledge_only": "ตอบจากความรู้แทน",
    "label.api_key": "คีย์ Groq",
    "label.persona": "เพอร์โซนา",
    "label.thread": "แชต",
    "label.sources": "แหล่งข้อมูล",
    "label.tokens": "โทเคน",
    "label.daily_token_limit": "ลิมิตต่อวัน (ดูอย่างเดียว)",
    "label.model": "โมเดล",
    "label.fallback": "โมเดลสำรอง",
    "label.usage_today": "ใช้ไปวันนี้",
    "label.settings": "ตั้งค่า",
    "label.more_settings": "ตั้งค่าเพิ่มเติม",
    "label.advanced": "ขั้นสูง",
    "label.password": "รหัสแอป (ถ้ามี)",
    "label.knowledge": "ความรู้",
    "label.knowledge_health": "สถานะ",
    "label.knowledge_files": "{n} ไฟล์",
    "label.knowledge_size": "ขนาด",
    "label.knowledge_paste": "วางข้อความ",
    "label.knowledge_paste_name": "ชื่อไฟล์",
    "label.search_lab": "ทดลองค้นหา",
    "label.prompt_inspector": "ดูพรอมต์",
    "label.rebuild_index": "สร้างดัชนีใหม่",
    "label.search_query": "คำค้น",
    "label.version": "เวอร์ชัน",
    "label.health": "ตรวจระบบ",
    "label.first_run": "เริ่มต้นครั้งแรก",
    "label.remember_key": "จำคีย์ไว้ในเครื่อง",
    "label.remember_key_help": ("ติ๊กครั้งหนึ่งแล้วเปิดแอปวันพรุ่งนี้ได้ต่อ — หรือตั้ง PERSONA_BOT_REMEMBER_KEY=1"),
    "label.language": "ภาษา",
    "label.data_tools": "สำรองข้อมูล",
    "label.import_preview": "ตัวอย่างนำเข้า",
    "label.conflict_policy": "เมื่อรหัสซ้ำ",
    "label.conflict.reject": "ปฏิเสธ",
    "label.conflict.rename": "เปลี่ยนชื่อ",
    "label.conflict.overwrite": "เขียนทับ",
    "label.persona_editor": "แก้เพอร์โซนา",
    "label.persona_create": "สร้างเพอร์โซนาใหม่",
    "label.persona_id": "รหัส (a-z, 0-9, -, _)",
    "label.persona_name": "ชื่อ",
    "label.persona_description": "คำอธิบายสั้น ๆ",
    "label.system_prompt": "บทบาท / คำสั่ง",
    "label.answer_mode": "โหมดคำตอบ",
    "label.answer_mode.strict": "ตอบเฉพาะความรู้",
    "label.answer_mode.balanced": "ยืดหยุ่น",
    "label.answer_mode.open": "สไตล์อิสระ",
    "label.temperature": "อุณหภูมิ",
    "label.max_tokens": "โทเคนสูงสุด",
    "label.embedding_preset": "ชุดฝังตัว",
    "label.top_k": "จำนวนผลค้นหา",
    "label.min_score": "คะแนนขั้นต่ำ",
    "label.chunk_chars": "ขนาดชิ้นข้อความ",
    "label.optional_override": "ว่าง = ใช้ค่าเริ่มต้น",
    "label.lab_tuning": "ค่าแล็บ",
    "label.knowledge_only_badge": "ตอบจากความรู้ (ไม่ใช้ AI ออนไลน์)",
    "label.needs_rebuild_banner": ("ความรู้ยังไม่พร้อม — กดบันทึกให้พร้อมใช้ หรือสร้างดัชนีใหม่ก่อนถาม"),
    "action.run_search": "ค้นหา",
    "action.run_health": "ตรวจสุขภาพ",
    "first_run.body": (
        "สำหรับคนทั่วไป: ติดตั้ง Docker Desktop หรือดับเบิลคลิก start.bat → "
        "วางคีย์ Groq ฟรีในช่องด้านล่าง (โมเดลตั้งให้แล้วใน .env) → เริ่มแชต "
        "หรือกด「ใช้แบบคลังความรู้เท่านั้น」ถ้ายังไม่มีคีย์"
    ),
    "status.health_ok": "ระบบพร้อม",
    "status.health_issues": "ยังไม่ครบเงื่อนไขการเริ่มใช้งาน",
    "status.import_ok": "นำเข้าเพอร์โซนาสำเร็จ",
    "status.export_ok": "ส่งออกเพอร์โซนาสำเร็จ",
    "status.backup_ok": "สร้างไฟล์สำรองสำเร็จ",
    "status.restore_ok": "คืนค่าข้อมูลสำเร็จ",
    "status.delete_persona_ok": "ลบเพอร์โซนาแล้ว",
    "status.delete_all_ok": "ลบข้อมูลภายใต้ data/ แล้ว",
    "status.example_persona_readonly": "เพอร์โซนาตัวอย่างลบไม่ได้ — ใช้แพ็กผู้ใช้เท่านั้น",
    "status.example_edit_readonly": ("เพอร์โซนาตัวอย่างแก้ไขไม่ได้ — กด「ทำสำเนา」เพื่อสร้างแพ็กผู้ใช้แล้วค่อยแก้"),
    "status.persona_saved": "บันทึกเพอร์โซนาแล้ว",
    "status.persona_created": "สร้างเพอร์โซนาแล้ว",
    "status.persona_duplicated": "ทำสำเนาเป็นแพ็กผู้ใช้แล้ว — แก้ไขและอัปโหลดความรู้ได้",
    "status.knowledge_uploaded": "อัปโหลดไฟล์ความรู้แล้ว — กำลังทำให้พร้อมใช้",
    "status.knowledge_pasted": "บันทึกข้อความความรู้แล้ว — กำลังทำให้พร้อมใช้",
    "status.knowledge_ready_after_save": "บันทึกความรู้และสร้างดัชนีแล้ว — พร้อมใช้",
    "status.knowledge_ready": "พร้อมแล้ว",
    "status.knowledge_needs_rebuild": "ต้องสร้างดัชนีใหม่",
    "status.knowledge_empty": "ยังไม่มีไฟล์ความรู้",
    "status.knowledge_only_empty": (
        "ไม่พบข้อความที่เกี่ยวข้องในคลังความรู้ของคุณ — เพิ่มโน้ตแล้วรอสถานะพร้อมแล้ว หรือใส่คีย์ Groq เพื่อคุยแบบ AI"
    ),
    "status.knowledge_only_fallback": (
        "ใช้คำตอบจากคลังความรู้แทน (ไม่ใช้ AI ออนไลน์) เพราะคีย์/โควตา/เครือข่ายไม่พร้อม"
    ),
    "status.oos_calm": "ไม่พบข้อมูลที่เกี่ยวข้องในคลังความรู้",
    "status.remember_loaded": "โหลดคีย์จาก OS keyring แล้ว — จะใช้ได้หลังรีสตาร์ท",
    "status.remember_env": "จำคีย์เปิดผ่าน PERSONA_BOT_REMEMBER_KEY — บันทึกและโหลดจาก keyring",
    "status.remember_ui": "จำคีย์เปิดจากช่องนี้ — บันทึกและโหลดจาก keyring หลังรีสตาร์ท",
    "status.remember_session_only": "คีย์อยู่ในเซสชันนี้เท่านั้น — ไม่โหลดอัตโนมัติหลังรีสตาร์ท",
    "status.daily_limit_unset": "ยังไม่ตั้งลิมิตต่อวัน",
    "chat.placeholder": "พิมพ์ข้อความ…",
    "chat.empty": "ยังไม่มีข้อความ — เริ่มคุยกับเพอร์โซนาได้เลย",
    "label.starter_questions": "คำถามเริ่มต้น",
    "status.ready": "พร้อมใช้งาน",
    "status.thinking": "กำลังคิด…",
    "status.partial_saved": "บันทึกข้อความบางส่วนแล้ว",
    "status.no_key": "รอ API key",
    "status.index_ready": "ดัชนีพร้อม",
    "status.index_rebuilt": "สร้างดัชนีใหม่แล้ว",
    "status.citations_invalid": "พบการอ้างอิงที่ไม่ตรงกับแหล่งข้อมูล",
    "error.generic": "เกิดข้อผิดพลาด กรุณาลองใหม่",
    "error.persona_editor": "สร้าง/แก้ไขเพอร์โซนาหรืออัปโหลดความรู้ไม่สำเร็จ",
    "error.no_api_key": "ยังไม่มี API key — ใส่คีย์ Groq ในช่องตั้งค่า",
    "error.missing_model_config": "ยังไม่ได้ตั้งค่าโมเดลในไฟล์ .env",
    "error.not_found_strict": "ไม่พบข้อมูลที่เกี่ยวข้องในคลังความรู้",
    "error.rate_limit_minute": "โควตาต่อนาทีเต็มแล้ว — รอสักครู่แล้วลองใหม่",
    "error.rate_limit_day": "โควตารายวันเต็มแล้ว — ลองใหม่พรุ่งนี้อีกครั้ง",
    "error.llm_transport": "เชื่อมต่อบริการโมเดลไม่สำเร็จ",
    "error.llm_response": "โมเดลตอบกลับผิดพลาด",
    "error.persona_load": "โหลด Persona Pack ไม่สำเร็จ",
    "error.persona_pack_io": "นำเข้า/ส่งออก Persona Pack ไม่สำเร็จ",
    "error.backup": "สำรองหรือคืนค่าข้อมูลไม่สำเร็จ",
    "error.app_password": "รหัสแอปไม่ถูกต้อง",
    "error.knowledge_load": "อ่านไฟล์ความรู้ไม่สำเร็จ",
    "error.knowledge_too_large": "ขนาดคลังความรู้เกินขีดจำกัด MAX_KNOWLEDGE_MB",
    "error.hint.retry": "ลองใหม่อีกครั้ง หรือตรวจการตั้งค่า",
    "error.hint.add_api_key": (
        "วางคีย์จาก console.groq.com ในช่อง API key — หรือใช้โหมดคลังความรู้ถ้ามีโน้ตพร้อมแล้ว"
    ),
    "error.hint.set_models": (
        "ตั้ง GROQ_MODEL_PRIMARY (และ FALLBACK) ใน .env — ค่าแนะนำมีใน .env.example แล้ว"
    ),
    "error.hint.wait_retry": ("รอตาม retry-after แล้วส่งอีกครั้ง — หรือใช้คำตอบจากคลังความรู้ถ้ามีผลค้นหา"),
    "error.hint.wait_day": ("โควตารายวันเต็ม — รอรีเซ็ต หรือให้แอปตอบจากคลังความรู้ถ้ามีโน้ตตรงคำถาม"),
    "error.hint.retry_after": "ลองใหม่ได้ในประมาณ {seconds} วินาที",
    "error.hint.reset_tokens": "รีเซ็ตโทเคน: {reset} (~{seconds}s)",
    "error.hint.reset_requests": "รีเซ็ตคำขอ: {reset} (~{seconds}s)",
    "error.hint.check_network": "ตรวจอินเทอร์เน็ตและ GROQ_BASE_URL",
    "error.hint.fix_persona": "ตรวจ persona.yaml ให้ครบและเป็น UTF-8",
    "error.hint.persona_pack_io": (
        "ใช้ zip ที่ได้จากส่งออกเท่านั้น — ไม่รับ symlink / path traversal / ไฟล์นอก whitelist"
    ),
    "error.hint.backup": "ใช้ไฟล์สำรองจากแอปนี้ และอย่าใส่ .env หรือคีย์ลงใน zip",
    "error.hint.add_knowledge": "เพิ่มไฟล์ความรู้ใน Persona Pack หรือเปลี่ยนโหมดคำตอบ",
    "error.hint.password": "ใส่รหัสที่ตั้งไว้ใน APP_PASSWORD",
    "error.hint.knowledge_file": "รองรับ .txt .md .pdf .docx — ตรวจรหัสอักขระ UTF-8",
    "error.hint.knowledge_size": (
        "ลดขนาดไฟล์หรือลบความรู้เก่า — ดูขนาดใช้ไป/ขีดจำกัดในแผงคลังความรู้ หรือปรับ MAX_KNOWLEDGE_MB ใน .env"
    ),
    "error.hint.persona_editor": (
        "ใช้รหัสเพอร์โซนา a-z0-9-_ เท่านั้น · ความรู้รองรับ .txt/.md/.pdf/.docx · "
        "ตัวอย่างอ่านอย่างเดียว — กดทำสำเนาก่อน"
    ),
    "privacy.notice": ("ข้อความแชตถูกเก็บในเครื่องคุณ (data/) — ไม่ส่งไปที่อื่นนอกจาก Groq เมื่อมีการเรียกโมเดล"),
    "warn.delete_all": "จะลบแชต ดัชนี และเพอร์โซนาผู้ใช้ภายใต้ data/ — ย้อนกลับไม่ได้",
    "warn.delete_persona": "ลบแพ็กผู้ใช้นี้และดัชนีที่เกี่ยวข้อง",
    "warn.clear_chat": "ลบข้อความในเธรดนี้ทั้งหมด — ย้อนกลับไม่ได้",
    "warn.overwrite_import": ("นโยบายเขียนทับจะแทนที่แพ็กผู้ใช้ที่มีรหัสเดียวกัน — ยืนยันด้านล่างก่อนนำเข้า"),
}

_EN: dict[str, str] = {
    "app.title": "persona-bot",
    "app.tagline": "A personal chatbot with role, knowledge, and tuning knobs",
    "app.welcome": "Welcome — add a Groq key or start knowledge-only",
    "app.welcome.body": (
        "The key stays in this session by default and is not written under data/. "
        "Without a key you can still paste notes and Q&A from your knowledge (no online AI)."
    ),
    "app.onboarding.step1": "1) (Recommended) Paste a Groq API key — or skip for knowledge-only",
    "app.onboarding.step2": "2) Pick a persona such as Personal notes or Study buddy",
    "app.onboarding.step3": "3) Add knowledge, then ask — or type a message below",
    "app.what_this_is": (
        "What this is: a personal bot on your machine · desktop browser · "
        "your Groq key when you want AI · no automatic multi-device sync · "
        "not a phone/Line app — move machines via export/import zip"
    ),
    "wizard.step1": "API key",
    "wizard.step2": "Privacy",
    "wizard.step3": "Start chat",
    "wizard.locked_tools": (
        "Backup/import live under More settings after you add a key — "
        "Knowledge and note-based chat work even without a key"
    ),
    "wizard.knowledge_only_hint": (
        "Answers from local notes (no online AI) "
        "when there is no key / quota is exhausted / you are offline"
    ),
    "action.new_chat": "New chat",
    "action.clear_chat": "Clear chat",
    "action.confirm_clear_chat": "Confirm clear chat",
    "action.stop": "Stop",
    "action.send": "Send",
    "action.save_key": "Use this key",
    "action.forget_key": "Forget session key",
    "action.got_it": "Got it",
    "action.export_persona": "Download persona (zip)",
    "action.import_persona": "Import persona (zip)",
    "action.preview_import": "Preview import",
    "action.confirm_import": "Confirm import",
    "action.confirm_overwrite": "Confirm overwrite of the existing pack",
    "action.delete_persona": "Delete user persona",
    "action.backup": "Backup data/",
    "action.restore": "Restore from backup",
    "action.delete_all_data": "Delete all data",
    "action.confirm_delete": "Confirm delete",
    "action.create_persona": "Create persona",
    "action.save_persona": "Save persona",
    "action.duplicate_persona": "Duplicate",
    "action.upload_knowledge": "Upload file",
    "action.paste_knowledge": "Save pasted text",
    "action.make_knowledge_ready": "Save & make ready",
    "action.continue_knowledge_only": "Continue with knowledge only (no key)",
    "action.use_knowledge_only": "Answer from knowledge instead",
    "label.api_key": "Groq key",
    "label.persona": "Persona",
    "label.thread": "Chat",
    "label.sources": "Sources",
    "label.tokens": "Tokens",
    "label.daily_token_limit": "Daily limit (view only)",
    "label.model": "Model",
    "label.fallback": "Fallback model",
    "label.usage_today": "Used today",
    "label.settings": "Settings",
    "label.more_settings": "More settings",
    "label.advanced": "Advanced",
    "label.password": "App password (if set)",
    "label.knowledge": "Knowledge",
    "label.knowledge_health": "Status",
    "label.knowledge_files": "{n} files",
    "label.knowledge_size": "Size",
    "label.knowledge_paste": "Paste text",
    "label.knowledge_paste_name": "File name",
    "label.search_lab": "Search lab",
    "label.prompt_inspector": "Prompt inspector",
    "label.rebuild_index": "Rebuild index",
    "label.search_query": "Query",
    "label.version": "Version",
    "label.health": "System check",
    "label.first_run": "First run",
    "label.remember_key": "Remember key on this device",
    "label.remember_key_help": (
        "Tick once to keep chatting tomorrow — or set PERSONA_BOT_REMEMBER_KEY=1"
    ),
    "label.language": "Language",
    "label.data_tools": "Backup",
    "label.import_preview": "Import preview",
    "label.conflict_policy": "On duplicate id",
    "label.conflict.reject": "Reject",
    "label.conflict.rename": "Rename",
    "label.conflict.overwrite": "Overwrite",
    "label.persona_editor": "Edit persona",
    "label.persona_create": "Create new persona",
    "label.persona_id": "Id (a-z, 0-9, -, _)",
    "label.persona_name": "Name",
    "label.persona_description": "Short description",
    "label.system_prompt": "Role / instructions",
    "label.answer_mode": "Answer mode",
    "label.answer_mode.strict": "Knowledge only",
    "label.answer_mode.balanced": "Flexible",
    "label.answer_mode.open": "Free style",
    "label.temperature": "Temperature",
    "label.max_tokens": "Max tokens",
    "label.embedding_preset": "Embedding preset",
    "label.top_k": "Top-k results",
    "label.min_score": "Min score",
    "label.chunk_chars": "Chunk size",
    "label.optional_override": "Leave blank for defaults",
    "label.lab_tuning": "Lab tuning",
    "label.knowledge_only_badge": "Answer from knowledge (no online AI)",
    "label.needs_rebuild_banner": (
        "Knowledge not ready — save to make ready, or rebuild before asking"
    ),
    "action.run_search": "Search",
    "action.run_health": "Run health check",
    "first_run.body": (
        "For everyone: install Docker Desktop or double-click start.bat → "
        "paste a free Groq key below (models are prefilled in .env) → chat. "
        "Or click Continue with knowledge only if you have no key yet."
    ),
    "status.health_ok": "System ready",
    "status.health_issues": "Setup requirements are incomplete",
    "status.import_ok": "Persona imported",
    "status.export_ok": "Persona exported",
    "status.backup_ok": "Backup created",
    "status.restore_ok": "Data restored",
    "status.delete_persona_ok": "Persona deleted",
    "status.delete_all_ok": "Deleted data under data/",
    "status.example_persona_readonly": "Example personas cannot be deleted — user packs only",
    "status.example_edit_readonly": (
        "Example personas are read-only — click Duplicate to create an editable user pack"
    ),
    "status.persona_saved": "Persona saved",
    "status.persona_created": "Persona created",
    "status.persona_duplicated": "Duplicated as a user pack — you can edit and upload knowledge",
    "status.knowledge_uploaded": "Knowledge file uploaded — making it ready",
    "status.knowledge_pasted": "Pasted knowledge saved — making it ready",
    "status.knowledge_ready_after_save": "Knowledge saved and indexed — ready to use",
    "status.knowledge_ready": "Ready",
    "status.knowledge_needs_rebuild": "Rebuild the index",
    "status.knowledge_empty": "No knowledge files yet",
    "status.knowledge_only_empty": (
        "No matching notes in your knowledge — "
        "add notes and wait for Ready, or add a Groq key for AI chat"
    ),
    "status.knowledge_only_fallback": (
        "Using a knowledge-only answer (no online AI) because key/quota/network is unavailable"
    ),
    "status.oos_calm": "No relevant knowledge found in the pack",
    "status.remember_loaded": "Loaded key from OS keyring — available after restart",
    "status.remember_env": (
        "Remember enabled via PERSONA_BOT_REMEMBER_KEY — save and load from keyring"
    ),
    "status.remember_ui": (
        "Remember enabled via checkbox — save and load from keyring after restart"
    ),
    "status.remember_session_only": (
        "Key stays in this session only — not auto-loaded after restart"
    ),
    "status.daily_limit_unset": "No daily limit set",
    "chat.placeholder": "Type a message…",
    "chat.empty": "No messages yet — start chatting with the persona",
    "label.starter_questions": "Starter questions",
    "status.ready": "Ready",
    "status.thinking": "Thinking…",
    "status.partial_saved": "Partial message saved",
    "status.no_key": "Waiting for API key",
    "status.index_ready": "Index ready",
    "status.index_rebuilt": "Index rebuilt",
    "status.citations_invalid": "Found citations that do not match sources",
    "error.generic": "Something went wrong — please try again",
    "error.persona_editor": "Could not create/edit the persona or upload knowledge",
    "error.no_api_key": "No API key yet — add your Groq key in settings",
    "error.missing_model_config": "Models are not set in the .env file",
    "error.not_found_strict": "No relevant knowledge found in the pack",
    "error.rate_limit_minute": "Per-minute quota exhausted — wait and retry",
    "error.rate_limit_day": "Daily quota exhausted — try again tomorrow",
    "error.llm_transport": "Could not reach the model service",
    "error.llm_response": "The model returned an error",
    "error.persona_load": "Could not load Persona Pack",
    "error.persona_pack_io": "Persona Pack import/export failed",
    "error.backup": "Backup or restore failed",
    "error.app_password": "Incorrect app password",
    "error.knowledge_load": "Could not read a knowledge file",
    "error.knowledge_too_large": "Knowledge size exceeds the MAX_KNOWLEDGE_MB limit",
    "error.hint.retry": "Try again or check your settings",
    "error.hint.add_api_key": (
        "Paste a key from console.groq.com into the API key field — "
        "or use knowledge-only mode when notes are ready"
    ),
    "error.hint.set_models": (
        "Set GROQ_MODEL_PRIMARY (and FALLBACK) in .env — defaults are in .env.example"
    ),
    "error.hint.wait_retry": (
        "Wait for retry-after, then send again — or use a knowledge-only answer if hits exist"
    ),
    "error.hint.wait_day": (
        "Daily quota exhausted — wait for reset, or answer from knowledge when notes match"
    ),
    "error.hint.retry_after": "Retry in about {seconds} seconds",
    "error.hint.reset_tokens": "Token reset: {reset} (~{seconds}s)",
    "error.hint.reset_requests": "Request reset: {reset} (~{seconds}s)",
    "error.hint.check_network": "Check internet connectivity and GROQ_BASE_URL",
    "error.hint.fix_persona": "Ensure persona.yaml is complete and UTF-8",
    "error.hint.persona_pack_io": (
        "Use an export zip only — no symlinks, path traversal, or non-whitelist files"
    ),
    "error.hint.backup": "Use a backup from this app; never put .env or keys in the zip",
    "error.hint.add_knowledge": "Add knowledge files to the Persona Pack or change answer mode",
    "error.hint.password": "Enter the password configured in APP_PASSWORD",
    "error.hint.knowledge_file": "Supported: .txt .md .pdf .docx — use UTF-8 text",
    "error.hint.knowledge_size": (
        "Remove or shrink knowledge files — see used/limit in the Knowledge panel "
        "or raise MAX_KNOWLEDGE_MB in .env"
    ),
    "error.hint.persona_editor": (
        "Use persona ids a-z0-9-_ only · knowledge allows .txt/.md/.pdf/.docx · "
        "examples are read-only — duplicate first"
    ),
    "privacy.notice": (
        "Chat text stays on your machine (data/) — it is only sent to Groq when a model is called"
    ),
    "warn.delete_all": "This deletes chats, indexes, and user personas under data/ — irreversible",
    "warn.delete_persona": "Delete this user pack and its related index",
    "warn.clear_chat": "Delete all messages in this thread — irreversible",
    "warn.overwrite_import": (
        "Overwrite policy replaces the existing user pack with the same id — confirm below first"
    ),
}

STRINGS: Final[dict[str, dict[str, str]]] = {
    "th": _TH,
    "en": _EN,
}
