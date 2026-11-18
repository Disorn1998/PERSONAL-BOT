"""Knowledge file loaders — txt/md/pdf/docx (UTF-8)."""

from __future__ import annotations

from pathlib import Path

from persona_bot.errors import AppError


class KnowledgeLoadError(AppError):
    code = "error.knowledge_load"
    string_key = "error.knowledge_load"
    hint_key = "error.hint.knowledge_file"


SUPPORTED_SUFFIXES = {".txt", ".md", ".markdown", ".pdf", ".docx"}


def load_text_file(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md", ".markdown"}:
        return path.read_text(encoding="utf-8")
    if suffix == ".pdf":
        return _load_pdf(path)
    if suffix == ".docx":
        return _load_docx(path)
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


def iter_knowledge_files(directory: Path) -> list[Path]:
    if not directory.exists():
        return []
    files = [
        p
        for p in sorted(directory.rglob("*"))
        if p.is_file() and p.suffix.lower() in SUPPORTED_SUFFIXES
    ]
    return files
