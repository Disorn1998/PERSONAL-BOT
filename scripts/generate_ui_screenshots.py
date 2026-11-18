#!/usr/bin/env python3
"""Generate honest UI-reference PNGs for README/GALLERY.

Renders simplified Streamlit-shell layouts with the real design tokens and Thai UI
strings from ``persona_bot.ui``. These are labeled layout references (not live
AppTest captures) and intentionally avoid inventing alternate product chrome.
"""

from __future__ import annotations

from pathlib import Path

from persona_bot.ui import tokens
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets"
W, H = 960, 540
SIDE_W = 280


def _load(path: str, size: int) -> ImageFont.ImageFont | None:
    p = Path(path)
    if not p.exists():
        return None
    try:
        return ImageFont.truetype(str(p), size=size)
    except OSError:
        return None


def _fonts(size: int) -> tuple[ImageFont.ImageFont, ImageFont.ImageFont]:
    latin = (
        _load("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
        or _load("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", size)
        or ImageFont.load_default()
    )
    thai = (
        _load("/usr/share/fonts/truetype/noto/NotoSansThai-Regular.ttf", size)
        or _load("/usr/share/fonts/truetype/noto/NotoLoopedThai-Regular.ttf", size)
        or latin
    )
    return latin, thai


def _is_thai(ch: str) -> bool:
    return "\u0e00" <= ch <= "\u0e7f"


def _draw_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    *,
    size: int,
    fill: tuple[int, int, int],
) -> None:
    """Draw mixed Thai/Latin using the appropriate face per run of characters."""
    latin, thai = _fonts(size)
    x, y = xy
    buf = ""
    mode_thai: bool | None = None

    def flush() -> None:
        nonlocal x, buf, mode_thai
        if not buf:
            return
        font = thai if mode_thai else latin
        draw.text((x, y), buf, fill=fill, font=font)
        box = draw.textbbox((x, y), buf, font=font)
        x = box[2]
        buf = ""

    for ch in text:
        want_thai = _is_thai(ch)
        if mode_thai is None:
            mode_thai = want_thai
        elif want_thai != mode_thai and ch not in " \t":
            flush()
            mode_thai = want_thai
        buf += ch
    flush()


def _rgb(hex_color: str) -> tuple[int, int, int]:
    value = hex_color.lstrip("#")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


BG = _rgb(tokens.COLOR_BACKGROUND)
SIDE = _rgb(tokens.COLOR_SECONDARY_BACKGROUND)
PRIMARY = _rgb(tokens.COLOR_PRIMARY)
TEXT = _rgb(tokens.COLOR_TEXT)
MUTED = _rgb(tokens.COLOR_MUTED_TEXT)
BORDER = _rgb(tokens.COLOR_BORDER)
ERROR = _rgb(tokens.COLOR_ERROR)
WHITE = (255, 255, 255)


def _base(*, sidebar: bool = True) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    if sidebar:
        draw.rectangle([0, 0, SIDE_W, H], fill=SIDE)
        draw.line([(SIDE_W, 0), (SIDE_W, H)], fill=BORDER, width=1)
    _draw_text(
        draw,
        (12, H - 22),
        "persona-bot UI reference (layout + current copy)",
        size=11,
        fill=MUTED,
    )
    return img, draw


def _save(img: Image.Image, name: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    img.save(path, format="PNG")
    print("wrote", path.relative_to(ROOT))


def welcome() -> None:
    img, draw = _base(sidebar=False)
    draw.rounded_rectangle([48, 40, 912, 460], radius=8, fill=SIDE, outline=BORDER)
    _draw_text(draw, (72, 64), "persona-bot", size=28, fill=PRIMARY)
    _draw_text(draw, (72, 110), "เริ่มต้นครั้งแรก", size=16, fill=TEXT)
    _draw_text(
        draw,
        (72, 140),
        "ทำสามขั้นตอนนี้แล้วเริ่มแชตได้: คัดลอก .env.example เป็น .env",
        size=13,
        fill=MUTED,
    )
    _draw_text(draw, (72, 190), "1) วาง Groq API key", size=16, fill=TEXT)
    _draw_text(draw, (72, 220), "2) เลือกเพอร์โซนาด้านซ้าย", size=16, fill=TEXT)
    _draw_text(draw, (72, 250), "3) พิมพ์ข้อความด้านล่าง", size=16, fill=TEXT)
    draw.rounded_rectangle([72, 300, 520, 340], radius=6, fill=WHITE, outline=BORDER)
    _draw_text(draw, (84, 312), "Groq API key", size=13, fill=MUTED)
    draw.rectangle([72, 360, 92, 380], outline=PRIMARY, width=2)
    _draw_text(draw, (104, 360), "จำคีย์ในระบบ (keyring)", size=13, fill=TEXT)
    _draw_text(
        draw,
        (72, 396),
        "คีย์อยู่ในเซสชันนี้เท่านั้น — ไม่โหลดอัตโนมัติหลังรีสตาร์ท",
        size=12,
        fill=MUTED,
    )
    draw.rounded_rectangle([72, 430, 220, 468], radius=6, fill=PRIMARY)
    _draw_text(draw, (96, 440), "ใช้คีย์นี้", size=16, fill=WHITE)
    _save(img, "welcome.png")


def persona_picker() -> None:
    img, draw = _base()
    _draw_text(draw, (24, 24), "เพอร์โซนา", size=12, fill=MUTED)
    draw.rounded_rectangle([24, 48, 256, 96], radius=6, fill=WHITE, outline=PRIMARY)
    _draw_text(draw, (36, 64), "เพื่อนติว", size=15, fill=TEXT)
    _draw_text(draw, (24, 112), "เพื่อนช่วยทบทวนบทเรียน อธิบายทีละขั้น", size=12, fill=MUTED)
    draw.rounded_rectangle([24, 160, 140, 196], radius=6, fill=PRIMARY)
    _draw_text(draw, (44, 170), "แชตใหม่", size=12, fill=WHITE)
    draw.rounded_rectangle([152, 160, 256, 196], radius=6, fill=WHITE, outline=BORDER)
    _draw_text(draw, (168, 170), "ล้างแชต", size=12, fill=TEXT)
    _draw_text(draw, (320, 40), "persona-bot", size=22, fill=PRIMARY)
    _draw_text(
        draw,
        (320, 90),
        "ยินดีต้อนรับ — ใส่คีย์ Groq ของคุณเพื่อเริ่มใช้งาน",
        size=15,
        fill=MUTED,
    )
    draw.rounded_rectangle([320, 140, 900, 260], radius=8, fill=WHITE, outline=BORDER)
    _draw_text(draw, (340, 170), "ยังไม่มีข้อความ — เริ่มคุยกับเพอร์โซนาได้เลย", size=15, fill=TEXT)
    _draw_text(draw, (340, 210), "คำถามเริ่มต้น", size=12, fill=MUTED)
    _save(img, "persona-picker.png")


def knowledge() -> None:
    img, draw = _base()
    _draw_text(draw, (24, 24), "คลังความรู้", size=12, fill=MUTED)
    draw.rounded_rectangle([24, 48, 256, 360], radius=8, fill=WHITE, outline=BORDER)
    _draw_text(draw, (36, 64), "สถานะดัชนีความรู้: พร้อมแล้ว", size=14, fill=PRIMARY)
    _draw_text(draw, (36, 96), "2 files · 12 chunks", size=12, fill=MUTED)
    _draw_text(draw, (36, 118), "ขนาดคลังความรู้: 0.15 / 50 MB", size=12, fill=MUTED)
    draw.rounded_rectangle([36, 160, 244, 196], radius=6, fill=PRIMARY)
    _draw_text(draw, (56, 170), "อัปโหลดไฟล์ความรู้", size=12, fill=WHITE)
    draw.rounded_rectangle([36, 212, 244, 280], radius=6, fill=SIDE, outline=BORDER)
    _draw_text(draw, (48, 236), "วางข้อความความรู้", size=12, fill=MUTED)
    draw.rounded_rectangle([36, 300, 244, 336], radius=6, fill=PRIMARY)
    _draw_text(draw, (64, 310), "สร้างดัชนีใหม่", size=12, fill=WHITE)
    _draw_text(draw, (320, 40), "persona-bot", size=22, fill=PRIMARY)
    _draw_text(
        draw,
        (320, 100),
        "แผงความรู้แสดงขนาดใช้ไป / ขีดจำกัด MAX_KNOWLEDGE_MB",
        size=14,
        fill=MUTED,
    )
    _save(img, "knowledge.png")


def sources() -> None:
    img, draw = _base(sidebar=False)
    _draw_text(draw, (40, 28), "persona-bot", size=22, fill=PRIMARY)
    draw.rounded_rectangle([40, 80, 920, 200], radius=8, fill=WHITE, outline=BORDER)
    _draw_text(draw, (60, 110), "HTTP คือโปรโตคอลสำหรับรับส่งข้อมูลบนเว็บ", size=15, fill=TEXT)
    _draw_text(draw, (60, 145), "อ้างอิงจากคลังความรู้ของเพอร์โซนา", size=12, fill=MUTED)
    draw.rounded_rectangle([40, 220, 920, 380], radius=8, fill=SIDE, outline=BORDER)
    _draw_text(draw, (60, 240), "แหล่งข้อมูล", size=15, fill=MUTED)
    _draw_text(draw, (60, 280), "1. knowledge/http-basics.md  (score 0.82)", size=12, fill=TEXT)
    _draw_text(draw, (60, 310), "2. knowledge/rag-overview.md  (score 0.71)", size=12, fill=TEXT)
    _save(img, "sources.png")


def error_card() -> None:
    img, draw = _base(sidebar=False)
    _draw_text(draw, (40, 28), "persona-bot", size=22, fill=PRIMARY)
    draw.rounded_rectangle([40, 100, 920, 280], radius=8, fill=SIDE, outline=BORDER)
    draw.rectangle([40, 100, 48, 280], fill=ERROR)
    _draw_text(
        draw,
        (70, 130),
        "โควตาต่อนาทีเต็มแล้ว — รอสักครู่แล้วลองใหม่",
        size=15,
        fill=TEXT,
    )
    _draw_text(draw, (70, 175), "รอตาม retry-after แล้วส่งข้อความอีกครั้ง", size=12, fill=MUTED)
    _draw_text(draw, (70, 205), "ลองใหม่ได้ในประมาณ 12 วินาที", size=12, fill=MUTED)
    _draw_text(draw, (70, 235), "รีเซ็ตโทเคน: 7.66s (~7.66s)", size=12, fill=MUTED)
    _save(img, "error-card.png")


def main() -> None:
    welcome()
    persona_picker()
    knowledge()
    sources()
    error_card()


if __name__ == "__main__":
    main()
