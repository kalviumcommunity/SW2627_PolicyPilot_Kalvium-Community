"""Unit and integration tests for Full-Corpus Ingestion Pipeline & Completeness Validation."""

import json
from pathlib import Path
import pytest

from src.services.ingestion_service import (
    IngestionPipeline,
    IngestionSummary,
    DocumentRecord,
    ChunkRecord,
    CompletenessValidation,
)


@pytest.fixture
def pipeline():
    return IngestionPipeline()


def test_discover_files_excludes_gitkeep_and_hidden(pipeline, tmp_path):
    """Verify that file discovery finds valid documents and ignores .gitkeep and hidden files."""
    # Create sample files
    (tmp_path / "doc1.txt").write_text("Hello world", encoding="utf-8")
    (tmp_path / "doc2.md").write_text("# Heading", encoding="utf-8")
    (tmp_path / ".gitkeep").write_text("", encoding="utf-8")
    (tmp_path / ".hidden_file.txt").write_text("Hidden", encoding="utf-8")

    discovered = pipeline.discover_files(tmp_path)
    discovered_names = [p.name for p in discovered]

    assert "doc1.txt" in discovered_names
    assert "doc2.md" in discovered_names
    assert ".gitkeep" not in discovered_names
    assert ".hidden_file.txt" not in discovered_names
    assert len(discovered) == 2


def test_full_corpus_ingestion_run(pipeline):
    """Verify that running the pipeline on the actual data/ corpus produces an IngestionSummary."""
    data_dir = Path(__file__).resolve().parents[1] / "data"
    summary = pipeline.run_pipeline(data_dir=data_dir, clean=True, chunk_size=400, chunk_overlap=60)

    assert isinstance(summary, IngestionSummary)
    assert summary.total_source_documents > 0
    assert summary.successfully_ingested_count > 0
    assert summary.total_chunks_created > 0
    assert summary.total_tokens > 0
    assert summary.total_characters > 0


def test_completeness_validation_reconciliation(pipeline):
    """Verify mathematical completeness check: total_discovered == ingested + failed."""
    data_dir = Path(__file__).resolve().parents[1] / "data"
    summary = pipeline.run_pipeline(data_dir=data_dir)

    comp = summary.completeness
    assert comp.is_reconciled is True
    assert comp.status == "PASSED"
    assert comp.discrepancy == 0
    assert comp.total_source_documents == comp.successfully_ingested + comp.failed_documents
    assert comp.total_accounted == comp.total_source_documents


def test_corrupt_file_isolated_not_dropped(pipeline):
    """Verify that corrupt_file.pdf is recorded as a failure and accounted for in the audit."""
    data_dir = Path(__file__).resolve().parents[1] / "data"
    summary = pipeline.run_pipeline(data_dir=data_dir)

    # Check that corrupt_file.pdf is in failures
    corrupt_failures = [f for f in summary.failures if f["source"] == "corrupt_file.pdf"]
    assert len(corrupt_failures) == 1
    assert corrupt_failures[0]["doc_type"] == "pdf"
    assert corrupt_failures[0]["error_type"] in (
        "PdfStreamError",
        "PdfReadError",
        "PyPdfError",
        "EmptyFileError",
        "ValueError",
        "Exception",
    )

    # Check that corrupt_file.pdf is also in documents list with FAILED status
    corrupt_docs = [d for d in summary.documents if d.source == "corrupt_file.pdf"]
    assert len(corrupt_docs) == 1
    assert corrupt_docs[0].status == "FAILED"


def test_chunk_metadata_completeness(pipeline):
    """Verify that all generated chunks have complete and accurate metadata tags."""
    data_dir = Path(__file__).resolve().parents[1] / "data"
    summary = pipeline.run_pipeline(data_dir=data_dir)

    for chunk in summary.all_chunks:
        assert isinstance(chunk, ChunkRecord)
        assert chunk.source != ""
        assert chunk.chunk_index >= 0
        assert chunk.total_chunks >= 1
        assert chunk.token_count > 0
        assert chunk.start_token >= 0
        assert chunk.end_token > chunk.start_token
        assert chunk.char_length == len(chunk.text)
        assert chunk.word_count == len(chunk.text.split())
        assert chunk.doc_type in ("pdf", "txt", "md", "html", "htm")
        assert chunk.ingested_at is not None

        # Verify metadata dictionary contains all keys
        m = chunk.metadata
        for req_key in [
            "source",
            "chunk_index",
            "total_chunks",
            "token_count",
            "start_token",
            "end_token",
            "char_length",
            "word_count",
            "doc_type",
            "ingested_at",
        ]:
            assert req_key in m


def test_summary_markdown_and_json_generation(pipeline):
    """Verify that Markdown and JSON summaries are properly constructed."""
    data_dir = Path(__file__).resolve().parents[1] / "data"
    summary = pipeline.run_pipeline(data_dir=data_dir)

    # Markdown Summary
    md = pipeline.generate_markdown_summary(summary)
    assert "# PolicyPilot Corpus Ingestion Summary & Completeness Audit" in md
    assert "Executive Ingestion Matrix" in md
    assert "Completeness Validation Audit" in md
    assert "Per-Document Ingestion Breakdown" in md
    assert "corrupt_file.pdf" in md

    # JSON Summary
    summary_dict = summary.to_dict()
    assert summary_dict["completeness_validation"]["status"] == "PASSED"
    assert summary_dict["total_source_documents"] == summary.total_source_documents


def test_sample_chunks_markdown_generation(pipeline):
    """Verify that sample chunks markdown is created with chunk text and metadata dicts."""
    data_dir = Path(__file__).resolve().parents[1] / "data"
    summary = pipeline.run_pipeline(data_dir=data_dir)

    sample_md = pipeline.generate_sample_chunks_markdown(summary, samples_per_doc=2)
    assert "# PolicyPilot Ingested Chunks & Metadata Inspection" in sample_md
    assert "Chunk Metadata Tag Dictionary:" in sample_md
    assert "Token Count:" in sample_md


def test_synthetic_unsupported_file_isolation(pipeline, tmp_path):
    """Verify that an unsupported file format (e.g. .xyz) is trapped as an isolated failure."""
    (tmp_path / "valid.txt").write_text("Valid text content.", encoding="utf-8")
    (tmp_path / "invalid.xyz").write_text("Unknown binary data", encoding="utf-8")

    summary = pipeline.run_pipeline(data_dir=tmp_path)
    assert summary.total_source_documents == 2
    assert summary.successfully_ingested_count == 1
    assert summary.failed_count == 1
    assert summary.completeness.is_reconciled is True
    assert summary.completeness.status == "PASSED"
    assert summary.failures[0]["source"] == "invalid.xyz"
    assert "Unsupported file format" in summary.failures[0]["error_message"]
