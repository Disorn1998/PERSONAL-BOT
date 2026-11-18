"""Thai UI strings (Phase 0 starter keys).

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
        "error.not_found_strict": "ไม่พบข้อมูลที่เกี่ยวข้องในคลังความรู้",
        "status.ready": "พร้อมใช้งาน",
        "status.thinking": "กำลังคิด…",
        "label.sources": "แหล่งข้อมูล",
        "label.tokens": "โทเคน",
        "label.model": "โมเดล",
    }
}
