"""Thai UI strings (Phase 1a expands error/hint keys).

Add more keys as UI parts land; never put Thai copy in product logic modules.
"""

from __future__ import annotations

from typing import Final

STRINGS: Final[dict[str, dict[str, str]]] = {
    "th": {
        "app.title": "persona-bot",
        "app.tagline": "แชตบอทส่วนตัวที่ตั้งบทบาท ความรู้ และค่าปรับแต่งได้",
        "app.welcome": "ยินดีต้อนรับ — ใส่คีย์ Groq ของคุณเพื่อเริ่มใช้งาน",
        "action.new_chat": "แชตใหม่",
        "action.clear_chat": "ล้างแชต",
        "action.stop": "หยุด",
        "action.send": "ส่ง",
        "error.generic": "เกิดข้อผิดพลาด กรุณาลองใหม่",
        "error.no_api_key": "ยังไม่มี API key — ใส่คีย์ Groq ในช่องตั้งค่า",
        "error.missing_model_config": "ยังไม่ได้ตั้งค่าโมเดลในไฟล์ .env",
        "error.not_found_strict": "ไม่พบข้อมูลที่เกี่ยวข้องในคลังความรู้",
        "error.rate_limit_minute": "โควตาต่อนาทีเต็มแล้ว — รอสักครู่แล้วลองใหม่",
        "error.rate_limit_day": "โควตารายวันเต็มแล้ว — ลองใหม่พรุ่งนี้อีกครั้ง",
        "error.llm_transport": "เชื่อมต่อบริการโมเดลไม่สำเร็จ",
        "error.llm_response": "โมเดลตอบกลับผิดพลาด",
        "error.persona_load": "โหลด Persona Pack ไม่สำเร็จ",
        "error.hint.retry": "ลองใหม่อีกครั้ง หรือตรวจการตั้งค่า",
        "error.hint.add_api_key": "วางคีย์จาก console.groq.com ในช่อง API key",
        "error.hint.set_models": "ตั้ง GROQ_MODEL_PRIMARY (และ FALLBACK) ใน .env",
        "error.hint.wait_retry": "รอตาม retry-after แล้วส่งข้อความอีกครั้ง",
        "error.hint.wait_day": "ลดการใช้งานหรือรอจนโควตารายวันรีเซ็ต",
        "error.hint.check_network": "ตรวจอินเทอร์เน็ตและ GROQ_BASE_URL",
        "error.hint.fix_persona": "ตรวจ persona.yaml ให้ครบและเป็น UTF-8",
        "error.hint.add_knowledge": "เพิ่มไฟล์ความรู้ใน Persona Pack หรือเปลี่ยนโหมดคำตอบ",
        "status.ready": "พร้อมใช้งาน",
        "status.thinking": "กำลังคิด…",
        "label.sources": "แหล่งข้อมูล",
        "label.tokens": "โทเคน",
        "label.model": "โมเดล",
    }
}
