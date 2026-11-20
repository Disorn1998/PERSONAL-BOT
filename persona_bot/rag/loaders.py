"""Knowledge file loaders — txt/md/pdf/docx + Excel + images (OCR)."""

from __future__ import annotations

from pathlib import Path

from persona_bot.errors import AppError

# Typed subdirs under ``knowledge/`` (persona pack layout).
KNOWLEDGE_KIND_DIRS: dict[str, str] = {
    ".txt": "text",
    ".md": "text",
    ".markdown": "text",
    ".pdf": "pdf",
    ".docx": "docx",
    ".xlsx": "sheets",
    ".xls": "sheets",
    ".png": "images",
    ".jpg": "images",
    ".jpeg": "images",
    ".webp": "images",
}

SUPPORTED_SUFFIXES = set(KNOWLEDGE_KIND_DIRS)
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
SHEET_SUFFIXES = {".xlsx", ".xls"}
OCR_PLACEHOLDER_PREFIX = "[OCR unavailable:"


class KnowledgeLoadError(AppError):
    code = "error.knowledge_load"
    string_key = "error.knowledge_load"
    hint_key = "error.hint.knowledge_file"


def knowledge_subdir_for_suffix(suffix: str) -> str:
    """Return typed folder name under ``knowledge/`` for a file suffix."""
    kind = KNOWLEDGE_KIND_DIRS.get(suffix.lower())
    if kind is None:
        raise KnowledgeLoadError(f"unsupported file type: {suffix}")
    return kind


def ocr_placeholder(path: Path) -> str:
    """Clear placeholder when OCR fails — image file itself is kept on disk."""
    return f"{OCR_PLACEHOLDER_PREFIX} {path.name}]"


def load_text_file(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md", ".markdown"}:
        return path.read_text(encoding="utf-8")
    if suffix == ".pdf":
        return _load_pdf(path)
    if suffix == ".docx":
        return _load_docx(path)
    if suffix in SHEET_SUFFIXES:
        return _load_spreadsheet(path)
    if suffix in IMAGE_SUFFIXES:
        return _load_image_ocr(path)
    raise KnowledgeLoadError(
        f"unsupported file type: {suffix}",
        details={"path": str(path)},
    )


def _load_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover
        raise KnowledgeLoadError("pypdf missing", details={"path": str(path)}) from exc
    try:
        reader = PdfReader(str(path))
        parts: list[str] = []
        for page in reader.pages:
            text = page.extract_text() or ""
            if text.strip():
                parts.append(text)
        return "\n\n".join(parts)
    except Exception as exc:  # noqa: BLE001
        raise KnowledgeLoadError(str(exc), details={"path": str(path)}) from exc


def _load_docx(path: Path) -> str:
    try:
        import docx
    except ImportError as exc:  # pragma: no cover
        raise KnowledgeLoadError("python-docx missing", details={"path": str(path)}) from exc
    try:
        document = docx.Document(str(path))
        return "\n".join(p.text for p in document.paragraphs if p.text.strip())
    except Exception as exc:  # noqa: BLE001
        raise KnowledgeLoadError(str(exc), details={"path": str(path)}) from exc


def _load_spreadsheet(path: Path) -> str:
    """Extract cell text from ``.xlsx`` (and best-effort ``.xls``) via openpyxl."""
    try:
        from openpyxl import load_workbook
    except ImportError as exc:  # pragma: no cover
        raise KnowledgeLoadError("openpyxl missing", details={"path": str(path)}) from exc
    try:
        workbook = load_workbook(filename=str(path), read_only=True, data_only=True)
    except Exception as exc:  # noqa: BLE001 — .xls / corrupt → clear message
        raise KnowledgeLoadError(
            f"could not read spreadsheet: {exc}",
            details={"path": str(path)},
        ) from exc
    parts: list[str] = []
    try:
        for sheet in workbook.worksheets:
            rows: list[str] = []
            for row in sheet.iter_rows(values_only=True):
                cells = [
                    str(cell).strip() for cell in row if cell is not None and str(cell).strip()
                ]
                if cells:
                    rows.append("\t".join(cells))
            if rows:
                parts.append(f"# {sheet.title}\n" + "\n".join(rows))
    finally:
        workbook.close()
    return "\n\n".join(parts)


def _load_image_ocr(path: Path) -> str:
    """OCR image → text; on failure keep the image and return a clear placeholder."""
    try:
        from PIL import Image
    except ImportError:
        return ocr_placeholder(path)
    try:
        import pytesseract
    except ImportError:
        return ocr_placeholder(path)
    try:
        with Image.open(path) as img:
            text = pytesseract.image_to_string(img) or ""
        cleaned = text.strip()
        if not cleaned:
            return ocr_placeholder(path)
        return cleaned
    except Exception:  # noqa: BLE001 — tesseract missing / bad image
        return ocr_placeholder(path)


def iter_knowledge_files(directory: Path) -> list[Path]:
    if not directory.exists():
        return []
    files = [
        p
        for p in sorted(directory.rglob("*"))
        if p.is_file() and p.suffix.lower() in SUPPORTED_SUFFIXES
    ]
    return files
