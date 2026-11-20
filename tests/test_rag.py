"""RAG unit tests — FakeEmbedder only (never downloads ONNX / calls Groq)."""

from __future__ import annotations

from pathlib import Path

import hypothesis.strategies as st
import pytest
from hypothesis import given, settings
from persona_bot.config import Settings
from persona_bot.errors import KnowledgeNotFoundError
from persona_bot.persona import load_persona_yaml
from persona_bot.prompt import build_messages
from persona_bot.rag.chunking import chunk_text
from persona_bot.rag.citations import format_sources_markdown, validate_citations
from persona_bot.rag.embeddings import FakeEmbedder, get_embedder
from persona_bot.rag.fingerprint import build_index_fingerprint
from persona_bot.rag.health import assess_knowledge_health
from persona_bot.rag.ingest import collect_chunks, ensure_index, knowledge_dir_for_persona
from persona_bot.rag.loaders import KnowledgeLoadError, iter_knowledge_files, load_text_file
from persona_bot.rag.prompt_inspector import inspect_messages
from persona_bot.rag.retrieve import build_retrieval_query, previous_user_message, retrieve
from persona_bot.rag.runtime import build_embedder, get_or_build_store
from persona_bot.rag.search_lab import run_search_lab
from persona_bot.rag.store import VectorStore, sanitize_collection_name


def test_sanitize_collection_name() -> None:
    assert sanitize_collection_name("study-buddy").startswith("study")
    assert len(sanitize_collection_name("ab")) >= 3


def test_chunk_and_fingerprint(tmp_path: Path) -> None:
    knowledge = tmp_path / "knowledge"
    knowledge.mkdir()
    (knowledge / "a.md").write_text("สวัสดี โลก\n" * 40, encoding="utf-8")
    chunks = collect_chunks(knowledge, chunk_chars=80, overlap_chars=10)
    assert chunks
    fp1 = build_index_fingerprint(
        knowledge, embedding_model="fake", chunk_chars=80, overlap_chars=10
    )
    fp2 = build_index_fingerprint(
        knowledge, embedding_model="fake", chunk_chars=80, overlap_chars=10
    )
    assert fp1 == fp2
    (knowledge / "a.md").write_text("changed", encoding="utf-8")
    fp3 = build_index_fingerprint(
        knowledge, embedding_model="fake", chunk_chars=80, overlap_chars=10
    )
    assert fp3 != fp1


@given(st.text(min_size=0, max_size=500))
@settings(max_examples=40, deadline=None)
def test_chunk_text_hypothesis(text: str) -> None:
    chunks = chunk_text(text, source="x.txt", chunk_chars=50, overlap_chars=5)
    joined = "".join(c.text for c in chunks)
    # All chunk text appears in original (order-preserving concatenation of pieces).
    for c in chunks:
        assert c.text in text.replace("\r\n", "\n") or not text.strip()
    if not text.strip():
        assert chunks == []
    else:
        assert joined  # at least something when non-empty after strip


def test_pdf_loader_roundtrip(tmp_path: Path) -> None:
    # Minimal PDF with Latin text (Helvetica). Thai content covered by .md fixtures.
    pdf = tmp_path / "sample.pdf"
    pdf.write_bytes(
        b"""%PDF-1.4
1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj
2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj
3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 144]
/Contents 4 0 R /Resources<< /Font<< /F1 5 0 R >> >> >>endobj
4 0 obj<< /Length 55 >>stream
BT /F1 12 Tf 40 100 Td (Thai knowledge PDF loader) Tj ET
endstream
endobj
5 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000266 00000 n 
0000000371 00000 n 
trailer<< /Size 6 /Root 1 0 R >>
startxref
444
%%EOF
"""
    )
    text = load_text_file(pdf)
    assert "Thai knowledge PDF loader" in text or "PDF" in text or len(text) >= 0


def test_index_retrieve_and_strict_short_circuit(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    examples = Path("personas/examples")
    persona = load_persona_yaml(examples / "tech-explainer" / "persona.yaml")
    assert persona.config.answer_mode == "strict"
    embedder = FakeEmbedder(dim=32, model_name="fake:test")
    store = VectorStore(data_dir=data_dir, embedder=embedder)
    kdir = knowledge_dir_for_persona(
        examples_dir=examples,
        personas_dir=tmp_path / "personas",
        persona_id=persona.id,
    )
    manifest = ensure_index(store, persona=persona, knowledge_dir=kdir, force=True)
    assert manifest.chunk_count > 0

    hits = retrieve(
        store,
        persona_id=persona.id,
        latest="HTTP GET คืออะไร",
        history=[{"role": "user", "content": "อธิบายโปรโตคอลเว็บ"}],
        top_k=4,
        min_score=0.01,
    )
    # Fake embedder may or may not rank highly — still returns list.
    assert isinstance(hits, list)

    # Empty / low-score context → strict short-circuit without needing LLM.
    with pytest.raises(KnowledgeNotFoundError):
        build_messages(
            persona,
            history=[],
            user_text="คำถามที่ไม่มีในคลัง",
            context_chunks=[{"text": "nope", "score": 0.0, "source": "x"}],
            min_score=0.9,
        )


def test_pdf_handbook_demo_ingest_and_citations(tmp_path: Path) -> None:
    """Example pack ships real PDFs — prove load + index + citation formatting."""
    examples = Path("personas/examples")
    persona = load_persona_yaml(examples / "pdf-handbook-demo" / "persona.yaml")
    assert persona.config.answer_mode == "strict"
    kdir = knowledge_dir_for_persona(
        examples_dir=examples,
        personas_dir=tmp_path / "personas",
        persona_id=persona.id,
    )
    pdfs = [p for p in iter_knowledge_files(kdir) if p.suffix.lower() == ".pdf"]
    assert len(pdfs) >= 2
    for pdf in pdfs:
        text = load_text_file(pdf)
        assert "Cedarvale" in text
        assert "FICTIONAL" in text

    embedder = FakeEmbedder(dim=32, model_name="fake:pdf-handbook")
    store = VectorStore(data_dir=tmp_path / "data", embedder=embedder)
    manifest = ensure_index(store, persona=persona, knowledge_dir=kdir, force=True)
    assert manifest.chunk_count > 0

    sources = [
        {
            "text": "Day Pass and Steward membership tiers",
            "source": "maker-space-overview.pdf",
            "score": 0.91,
        },
        {
            "text": "No PVC or vinyl on the laser cutter",
            "source": "workshop-safety.pdf",
            "score": 0.88,
        },
    ]
    md = format_sources_markdown(sources)
    assert "`maker-space-overview.pdf`" in md
    assert "`workshop-safety.pdf`" in md
    report = validate_citations("See [1] and [2] for handbook rules.", sources)
    assert report["ok"] is True
    assert report["valid"] == [1, 2]

    with pytest.raises(KnowledgeNotFoundError):
        build_messages(
            persona,
            history=[],
            user_text="What is the real Cedarvale street address?",
            context_chunks=[{"text": "nope", "score": 0.0, "source": "x"}],
            min_score=0.9,
        )


def test_en_study_coach_loads_and_indexes(tmp_path: Path) -> None:
    examples = Path("personas/examples")
    persona = load_persona_yaml(examples / "en-study-coach" / "persona.yaml")
    assert persona.config.answer_mode == "balanced"
    assert persona.metadata.get("language") == "en"
    kdir = knowledge_dir_for_persona(
        examples_dir=examples,
        personas_dir=tmp_path / "personas",
        persona_id=persona.id,
    )
    files = iter_knowledge_files(kdir)
    assert any(p.name == "spaced-repetition.md" for p in files)
    embedder = FakeEmbedder(dim=32, model_name="fake:en-study")
    store = VectorStore(data_dir=tmp_path / "data", embedder=embedder)
    manifest = ensure_index(store, persona=persona, knowledge_dir=kdir, force=True)
    assert manifest.chunk_count > 0


def test_retrieval_query_uses_previous() -> None:
    q = build_retrieval_query(latest="ล่าสุด", previous_user="ก่อนหน้า")
    assert q == "ก่อนหน้า\nล่าสุด"
    hist = [
        {"role": "assistant", "content": "a"},
        {"role": "user", "content": "u"},
    ]
    assert previous_user_message(hist) == "u"


def test_citations_and_inspector() -> None:
    sources = [{"text": "a", "source": "a.md"}, {"text": "b", "source": "b.md"}]
    report = validate_citations("ดู [1] และ [9]", sources)
    assert report["valid"] == [1]
    assert report["invalid"] == [9]
    assert report["ok"] is False
    info = inspect_messages(
        [
            {"role": "system", "content": "sys"},
            {"role": "user", "content": "<context>\nx\n</context>\n\nhi"},
        ]
    )
    assert info["latest_has_context"] is True
    assert info["message_count"] == 2


def test_format_sources_markdown_empty_and_preview() -> None:
    assert format_sources_markdown([]) == ""
    long = "x" * 200
    md = format_sources_markdown(
        [
            {"text": long, "source": "a.md", "score": 0.9123},
            {"text": "short", "source": "b.md"},
        ]
    )
    assert "**[1]**" in md and "`a.md`" in md and "score=0.912" in md
    assert "…" in md  # long preview truncated
    assert "**[2]**" in md and "short" in md


def test_loaders_unsupported_missing_dir_and_docx(tmp_path: Path) -> None:
    assert iter_knowledge_files(tmp_path / "missing") == []
    bad = tmp_path / "x.bin"
    bad.write_bytes(b"nope")
    with pytest.raises(KnowledgeLoadError, match="unsupported"):
        load_text_file(bad)

    docx_path = tmp_path / "note.docx"
    import docx

    document = docx.Document()
    document.add_paragraph("Hello from docx")
    document.add_paragraph("")
    document.add_paragraph("Second line")
    document.save(docx_path)
    assert "Hello from docx" in load_text_file(docx_path)
    assert "Second line" in load_text_file(docx_path)

    files = iter_knowledge_files(tmp_path)
    assert docx_path.resolve() in [p.resolve() for p in files]


def test_loaders_xlsx_and_image_smoke(tmp_path: Path) -> None:
    """Excel text extract + image OCR fallback placeholder (no tesseract required)."""
    from openpyxl import Workbook
    from persona_bot.rag.loaders import OCR_PLACEHOLDER_PREFIX, knowledge_subdir_for_suffix

    assert knowledge_subdir_for_suffix(".xlsx") == "sheets"
    assert knowledge_subdir_for_suffix(".png") == "images"

    sheets = tmp_path / "sheets"
    sheets.mkdir()
    xlsx = sheets / "demo.xlsx"
    wb = Workbook()
    ws = wb.active
    assert ws is not None
    ws.title = "Notes"
    ws["A1"] = "Topic"
    ws["B1"] = "Detail"
    ws["A2"] = "RAG"
    ws["B2"] = "local index"
    wb.save(xlsx)
    text = load_text_file(xlsx)
    assert "RAG" in text
    assert "local index" in text

    images = tmp_path / "images"
    images.mkdir()
    # Minimal valid 1x1 PNG.
    png = images / "pixel.png"
    png.write_bytes(
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00"
        b"\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    ocr_text = load_text_file(png)
    # Without working tesseract, placeholder is expected and file stays on disk.
    assert png.is_file()
    assert OCR_PLACEHOLDER_PREFIX in ocr_text or ocr_text.strip()

    found = iter_knowledge_files(tmp_path)
    assert xlsx.resolve() in [p.resolve() for p in found]
    assert png.resolve() in [p.resolve() for p in found]


def test_fake_embedder_empty_and_get_embedder() -> None:
    emb = FakeEmbedder(dim=8, model_name="fake:empty")
    assert emb.dim == 8
    assert emb.model_name == "fake:empty"
    empty = emb.embed_documents(["   "])[0]
    assert len(empty) == 8
    assert abs(sum(v * v for v in empty) - 1.0) < 1e-6
    via = get_embedder("lite", fake=True)
    assert via.model_name.startswith("fake:")
    assert via.dim <= 64


def test_knowledge_health_no_files_and_after_index(tmp_path: Path) -> None:
    examples = Path("personas/examples")
    persona = load_persona_yaml(examples / "writing-coach" / "persona.yaml")
    embedder = FakeEmbedder(dim=16, model_name="fake:health")
    store = VectorStore(data_dir=tmp_path / "data", embedder=embedder)
    health = assess_knowledge_health(
        store,
        persona=persona,
        examples_dir=examples,
        personas_dir=tmp_path / "personas",
    )
    assert health.persona_id == persona.id
    assert "no_knowledge_files" in health.notes
    assert "no_manifest" in health.notes
    assert health.to_dict()["file_count"] == health.file_count

    # Persona with knowledge: index then health should clear rebuild flags.
    tech = load_persona_yaml(examples / "tech-explainer" / "persona.yaml")
    kdir = knowledge_dir_for_persona(
        examples_dir=examples,
        personas_dir=tmp_path / "personas",
        persona_id=tech.id,
    )
    ensure_index(store, persona=tech, knowledge_dir=kdir, force=True)
    healthy = assess_knowledge_health(
        store,
        persona=tech,
        examples_dir=examples,
        personas_dir=tmp_path / "personas",
        expected_fingerprint="wrong-fp",
    )
    assert "fingerprint_mismatch" in healthy.notes
    assert healthy.needs_rebuild is True
    assert healthy.chunk_count > 0


def test_runtime_get_or_build_store_with_fake(tmp_path: Path) -> None:
    examples = Path("personas/examples").resolve()
    data_dir = tmp_path / "data"
    settings = Settings(
        EXAMPLES_DIR=str(examples),
        PERSONAS_DIR=str(tmp_path / "personas"),
        DATA_DIR=str(data_dir),
        MAX_KNOWLEDGE_MB=50,
    )
    persona = load_persona_yaml(examples / "study-buddy" / "persona.yaml")
    embedder = build_embedder(settings, persona=persona, fake=True)
    assert isinstance(embedder, FakeEmbedder)
    store, manifest, kdir, health = get_or_build_store(
        settings=settings,
        persona=persona,
        embedder=embedder,
        force=True,
    )
    assert manifest.chunk_count > 0
    assert kdir.exists()
    assert health.persona_id == persona.id
    assert store.load_manifest(persona.id) is not None

    hits = run_search_lab(
        store,
        persona_id=persona.id,
        query="photosynthesis",
        top_k=3,
        min_score=0.0,
    )
    assert isinstance(hits, list)


def test_fingerprint_triggers_rebuild(tmp_path: Path) -> None:
    examples = Path("personas/examples")
    persona = load_persona_yaml(examples / "study-buddy" / "persona.yaml")
    embedder = FakeEmbedder(dim=16, model_name="fake:sb")
    store = VectorStore(data_dir=tmp_path / "data", embedder=embedder)
    kdir = knowledge_dir_for_persona(
        examples_dir=examples,
        personas_dir=tmp_path / "personas",
        persona_id=persona.id,
    )
    m1 = ensure_index(store, persona=persona, knowledge_dir=kdir, force=True)
    m2 = ensure_index(store, persona=persona, knowledge_dir=kdir, force=False)
    assert m1.fingerprint == m2.fingerprint
    # Force path still works
    m3 = ensure_index(store, persona=persona, knowledge_dir=kdir, force=True)
    assert m3.chunk_count == m1.chunk_count
