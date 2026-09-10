"""Full-Corpus Ingestion Pipeline & Completeness Validation Service for PolicyPilot.

Loads, cleans, chunks, tags, and accounts for every document across the full corpus.
Provides mathematical completeness reconciliation to prove zero documents are silently dropped.
"""

from __future__ import annotations

import datetime
import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup
from pypdf import PdfReader

from src.services.chunking_service import ChunkingService
from src.services.cleaning_service import TextCleaningService

logger = logging.getLogger(__name__)


@dataclass
class DocumentRecord:
    """Represents the processing outcome and metrics of a single source document."""

    source: str
    relative_path: str
    doc_type: str
    size_bytes: int
    raw_chars: int = 0
    cleaned_chars: int = 0
    chunk_count: int = 0
    total_tokens: int = 0
    status: str = "PENDING"  # SUCCESS | FAILED
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    ingested_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ChunkRecord:
    """Represents a chunk extracted from a document with full metadata and boundaries."""

    text: str
    source: str
    chunk_index: int
    total_chunks: int
    token_count: int
    start_token: int
    end_token: int
    char_length: int
    word_count: int
    doc_type: str
    ingested_at: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.metadata:
            self.metadata = {
                "source": self.source,
                "chunk_index": self.chunk_index,
                "total_chunks": self.total_chunks,
                "token_count": self.token_count,
                "start_token": self.start_token,
                "end_token": self.end_token,
                "char_length": self.char_length,
                "word_count": self.word_count,
                "doc_type": self.doc_type,
                "ingested_at": self.ingested_at,
            }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "source": self.source,
            "chunk_index": self.chunk_index,
            "total_chunks": self.total_chunks,
            "token_count": self.token_count,
            "start_token": self.start_token,
            "end_token": self.end_token,
            "char_length": self.char_length,
            "word_count": self.word_count,
            "doc_type": self.doc_type,
            "ingested_at": self.ingested_at,
            "metadata": self.metadata,
        }


@dataclass
class CompletenessValidation:
    """Mathematical validation proving no document was silently dropped."""

    status: str  # PASSED | FAILED
    is_reconciled: bool
    total_source_documents: int
    successfully_ingested: int
    failed_documents: int
    total_accounted: int
    discrepancy: int
    validation_message: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class IngestionSummary:
    """Aggregated summary of the full-corpus ingestion run."""

    run_timestamp: str
    data_dir: str
    chunk_size: int
    chunk_overlap: int
    clean_applied: bool
    total_source_documents: int
    successfully_ingested_count: int
    failed_count: int
    total_chunks_created: int
    total_tokens: int
    total_characters: int
    completeness: CompletenessValidation
    documents: List[DocumentRecord] = field(default_factory=list)
    failures: List[Dict[str, Any]] = field(default_factory=list)
    all_chunks: List[ChunkRecord] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_timestamp": self.run_timestamp,
            "data_dir": self.data_dir,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "clean_applied": self.clean_applied,
            "total_source_documents": self.total_source_documents,
            "successfully_ingested_count": self.successfully_ingested_count,
            "failed_count": self.failed_count,
            "total_chunks_created": self.total_chunks_created,
            "total_tokens": self.total_tokens,
            "total_characters": self.total_characters,
            "completeness_validation": self.completeness.to_dict(),
            "documents": [d.to_dict() for d in self.documents],
            "failures": self.failures,
            "sample_chunks_preview_count": len(self.all_chunks),
        }


class IngestionPipeline:
    """End-to-end ingestion pipeline with full-corpus traversal, cleaning, chunking, tagging, and validation."""

    def __init__(
        self,
        cleaner: Optional[TextCleaningService] = None,
        chunker: Optional[ChunkingService] = None,
    ):
        self.cleaner = cleaner or TextCleaningService()
        self.chunker = chunker or ChunkingService()

    def discover_files(self, data_dir: str | Path) -> List[Path]:
        """Discover all candidate files in the corpus directory, ignoring hidden files and .gitkeep."""
        path_dir = Path(data_dir)
        if not path_dir.exists() or not path_dir.is_dir():
            logger.error("Corpus directory does not exist: %s", data_dir)
            return []

        files = []
        for p in sorted(path_dir.rglob("*")):
            if p.is_file() and not p.name.startswith(".") and p.name != ".gitkeep":
                files.append(p)
        return files

    def extract_text(self, file_path: Path) -> str:
        """Extract plain text from supported document formats (.pdf, .txt, .md, .html, .htm)."""
        suffix = file_path.suffix.lower()

        if suffix == ".pdf":
            reader = PdfReader(file_path)
            parts = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    parts.append(text)
            if not parts:
                raise ValueError("PDF contains no extractable text or is empty")
            return "\n".join(parts)

        elif suffix in (".txt", ".md"):
            return file_path.read_text(encoding="utf-8", errors="ignore")

        elif suffix in (".html", ".htm"):
            raw_html = file_path.read_text(encoding="utf-8", errors="ignore")
            soup = BeautifulSoup(raw_html, "html.parser")
            for element in soup(["script", "style"]):
                element.decompose()
            text = soup.get_text(" ")
            return text

        else:
            raise ValueError(f"Unsupported file format: '{suffix}'")

    def run_pipeline(
        self,
        data_dir: str | Path = "data",
        clean: bool = True,
        chunk_size: int = 400,
        chunk_overlap: int = 60,
    ) -> IngestionSummary:
        """Execute the full ingestion pipeline end-to-end over the whole corpus."""
        data_path = Path(data_dir)
        run_time = datetime.datetime.now(datetime.timezone.utc).isoformat()

        discovered_files = self.discover_files(data_path)
        total_discovered = len(discovered_files)

        documents: List[DocumentRecord] = []
        failures: List[Dict[str, Any]] = []
        all_chunks: List[ChunkRecord] = []

        total_tokens_all = 0
        total_chars_all = 0

        for file_path in discovered_files:
            source_name = file_path.name
            rel_path = str(file_path.relative_to(data_path.parent))
            doc_type = file_path.suffix.lower().lstrip(".") or "unknown"
            size_bytes = file_path.stat().st_size

            doc_rec = DocumentRecord(
                source=source_name,
                relative_path=rel_path,
                doc_type=doc_type,
                size_bytes=size_bytes,
                ingested_at=run_time,
            )

            try:
                # Stage 1 & 2: Load & Extract
                raw_text = self.extract_text(file_path)
                doc_rec.raw_chars = len(raw_text)

                # Stage 3: Clean & Normalize
                processed_text = raw_text
                if clean:
                    processed_text = self.cleaner.clean_text(raw_text)
                doc_rec.cleaned_chars = len(processed_text)

                # Stage 4: Token-Aware Chunking
                raw_chunks = self.chunker.chunk_text(
                    processed_text,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                )
                num_chunks = len(raw_chunks)
                doc_rec.chunk_count = num_chunks

                # Stage 5: Tag Chunks with Rich Metadata
                doc_tokens = 0
                for c in raw_chunks:
                    c_tokens = c["token_count"]
                    doc_tokens += c_tokens
                    c_text = c["text"]

                    chunk_rec = ChunkRecord(
                        text=c_text,
                        source=source_name,
                        chunk_index=c["index"],
                        total_chunks=num_chunks,
                        token_count=c_tokens,
                        start_token=c["start_token"],
                        end_token=c["end_token"],
                        char_length=len(c_text),
                        word_count=len(c_text.split()),
                        doc_type=doc_type,
                        ingested_at=run_time,
                    )
                    all_chunks.append(chunk_rec)

                doc_rec.total_tokens = doc_tokens
                doc_rec.status = "SUCCESS"
                total_tokens_all += doc_tokens
                total_chars_all += doc_rec.cleaned_chars
                documents.append(doc_rec)

            except Exception as exc:
                doc_rec.status = "FAILED"
                doc_rec.error_message = str(exc)
                doc_rec.error_type = exc.__class__.__name__
                documents.append(doc_rec)
                failures.append({
                    "source": source_name,
                    "relative_path": rel_path,
                    "doc_type": doc_type,
                    "size_bytes": size_bytes,
                    "error_type": exc.__class__.__name__,
                    "error_message": str(exc),
                })
                logger.warning("Document ingestion failed for '%s': %s", source_name, exc)

        # Stage 6: Mathematical Completeness Validation
        success_count = sum(1 for d in documents if d.status == "SUCCESS")
        failure_count = len(failures)
        accounted_total = success_count + failure_count
        discrepancy = total_discovered - accounted_total
        is_reconciled = (discrepancy == 0) and (total_discovered == len(documents))

        validation_status = "PASSED" if is_reconciled else "FAILED"
        if is_reconciled:
            val_msg = (
                f"Completeness Verified: Total discovered ({total_discovered}) matches "
                f"ingested ({success_count}) + failed ({failure_count}). Zero documents silently dropped."
            )
        else:
            val_msg = (
                f"Completeness Audit FAILED: Discovered {total_discovered} documents, "
                f"but accounted for {accounted_total} (Discrepancy: {discrepancy})."
            )

        completeness = CompletenessValidation(
            status=validation_status,
            is_reconciled=is_reconciled,
            total_source_documents=total_discovered,
            successfully_ingested=success_count,
            failed_documents=failure_count,
            total_accounted=accounted_total,
            discrepancy=discrepancy,
            validation_message=val_msg,
        )

        return IngestionSummary(
            run_timestamp=run_time,
            data_dir=str(data_dir),
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            clean_applied=clean,
            total_source_documents=total_discovered,
            successfully_ingested_count=success_count,
            failed_count=failure_count,
            total_chunks_created=len(all_chunks),
            total_tokens=total_tokens_all,
            total_characters=total_chars_all,
            completeness=completeness,
            documents=documents,
            failures=failures,
            all_chunks=all_chunks,
        )

    def generate_markdown_summary(self, summary: IngestionSummary) -> str:
        """Generate a clean, professional Markdown summary of the ingestion run."""
        lines = [
            "# PolicyPilot Corpus Ingestion Summary & Completeness Audit",
            "",
            f"- **Run Timestamp (UTC):** `{summary.run_timestamp}`",
            f"- **Corpus Source Directory:** `{summary.data_dir}`",
            f"- **Chunk Configuration:** Target Size = `{summary.chunk_size}` tokens | Overlap = `{summary.chunk_overlap}` tokens",
            f"- **Text Normalization:** `{'Enabled (NFKC, line-wraps, whitespace, boilerplate removal)' if summary.clean_applied else 'Disabled'}`",
            "",
            "## 1. Executive Ingestion Matrix",
            "",
            "| Metric | Count / Value | Status |",
            "| :--- | :---: | :---: |",
            f"| **Total Source Documents Discovered** | **{summary.total_source_documents}** | `Audited` |",
            f"| **Successfully Ingested Documents** | **{summary.successfully_ingested_count}** | `Ready` |",
            f"| **Failed / Skipped Documents** | **{summary.failed_count}** | `Isolated` |",
            f"| **Total Chunks Created** | **{summary.total_chunks_created}** | `Indexed` |",
            f"| **Total Ingested Tokens** | **{summary.total_tokens:,}** | `Counted` |",
            f"| **Total Ingested Characters** | **{summary.total_characters:,}** | `Processed` |",
            f"| **Completeness Validation Check** | **{summary.completeness.status}** | `{'PASS' if summary.completeness.is_reconciled else 'FAIL'}` |",
            "",
            "## 2. Completeness Validation Audit",
            "",
            f"> **Reconciliation Equation:**",
            f"> $$\\text{{Total Discovered ({summary.total_source_documents})}} = \\text{{Ingested ({summary.successfully_ingested_count})}} + \\text{{Failures ({summary.failed_count})}}$$",
            "",
            f"- **Validation Status:** `{summary.completeness.status}`",
            f"- **Reconciled:** `{summary.completeness.is_reconciled}`",
            f"- **Discrepancy:** `{summary.completeness.discrepancy}` documents",
            f"- **Audit Proof:** {summary.completeness.validation_message}",
            "",
            "## 3. Per-Document Ingestion Breakdown",
            "",
            "| Source Document | Format | Size (Bytes) | Raw Chars | Clean Chars | Chunks | Tokens | Status |",
            "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
        ]

        for d in summary.documents:
            status_badge = "OK" if d.status == "SUCCESS" else "FAILED"
            lines.append(
                f"| `{d.source}` | `{d.doc_type}` | {d.size_bytes:,} | {d.raw_chars:,} | {d.cleaned_chars:,} | {d.chunk_count} | {d.total_tokens:,} | `{status_badge}` |"
            )

        lines.extend([
            "",
            "## 4. Isolated Failures & Skipped Files",
            "",
        ])

        if summary.failures:
            lines.extend([
                "The following files failed parsing during intake and were safely isolated without interrupting the pipeline:",
                "",
                "| Source Document | Format | Size | Exception Type | Failure Reason |",
                "| :--- | :---: | :---: | :--- | :--- |",
            ])
            for f in summary.failures:
                lines.append(
                    f"| `{f['source']}` | `{f['doc_type']}` | {f['size_bytes']} B | `{f['error_type']}` | `{f['error_message']}` |"
                )
        else:
            lines.append("No document ingestion failures recorded.")

        lines.append("")
        return "\n".join(lines)

    def generate_sample_chunks_markdown(
        self,
        summary: IngestionSummary,
        samples_per_doc: int = 2,
    ) -> str:
        """Generate a detailed Markdown inspection artifact of sample chunks across all documents."""
        lines = [
            "# PolicyPilot Ingested Chunks & Metadata Inspection",
            "",
            "This report provides sample chunk inspections across every successfully ingested document in the full corpus. "
            "Inspect cleaned text quality, chunk boundary preservation, source identifiers, token counts, and complete metadata dictionaries.",
            "",
            f"- **Ingestion Run UTC:** `{summary.run_timestamp}`",
            f"- **Total Successfully Ingested Documents:** {summary.successfully_ingested_count}",
            f"- **Total Chunks Produced:** {summary.total_chunks_created}",
            "",
            "---",
            "",
        ]

        # Group chunks by source document
        chunks_by_source: Dict[str, List[ChunkRecord]] = {}
        for c in summary.all_chunks:
            chunks_by_source.setdefault(c.source, []).append(c)

        for source, doc_chunks in chunks_by_source.items():
            doc_rec = next((d for d in summary.documents if d.source == source), None)
            doc_type = doc_rec.doc_type if doc_rec else "unknown"

            lines.extend([
                f"## Document: `{source}` ({doc_type.upper()})",
                f"- **Total Chunks in Document:** {len(doc_chunks)}",
                f"- **Displaying First {min(samples_per_doc, len(doc_chunks))} Sample Chunk(s):**",
                "",
            ])

            for chunk in doc_chunks[:samples_per_doc]:
                lines.extend([
                    f"### Chunk Index `{chunk.chunk_index}` of `{chunk.total_chunks}`",
                    f"- **Source Identifier:** `{chunk.source}`",
                    f"- **Token Count:** `{chunk.token_count}` tokens (Range: `[{chunk.start_token} : {chunk.end_token}]`)",
                    f"- **Character Length:** `{chunk.char_length}` chars | **Word Count:** `{chunk.word_count}` words",
                    f"- **Document Format:** `{chunk.doc_type}`",
                    f"- **Ingested Timestamp:** `{chunk.ingested_at}`",
                    "",
                    "#### Chunk Text Content:",
                    "```text",
                    chunk.text,
                    "```",
                    "",
                    "#### Chunk Metadata Tag Dictionary:",
                    "```json",
                    json.dumps(chunk.metadata, indent=2),
                    "```",
                    "",
                    "---",
                    "",
                ])

        return "\n".join(lines)
