"""End-to-End Full-Corpus Ingestion & Completeness Validation Runner for PolicyPilot.

Runs the complete ingestion pipeline over all documents in the corpus, proves zero
documents were silently dropped via mathematical reconciliation, displays sample chunks,
and generates structured JSON & Markdown audit reports.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.services.ingestion_service import IngestionPipeline


def run_full_ingestion_demonstration():
    print("=" * 80)
    print("      PolicyPilot End-to-End Full-Corpus Ingestion & Completeness Audit")
    print("=" * 80)

    data_dir = PROJECT_ROOT / "data"
    outputs_dir = PROJECT_ROOT / "outputs"
    outputs_dir.mkdir(exist_ok=True)

    print(f"\n[1] Initializing IngestionPipeline...")
    print(f"    - Target Corpus Directory: {data_dir}")
    print(f"    - Target Production Chunker: 400 max tokens, 60 overlap tokens (15%)")
    print(f"    - Text Cleaning Normalization: NFKC, Line-wraps, Whitespace, Boilerplate")

    pipeline = IngestionPipeline()

    # Step 1: Run full pipeline
    print(f"\n[2] Executing Full Ingestion Pipeline across the entire corpus...")
    summary = pipeline.run_pipeline(
        data_dir=data_dir,
        clean=True,
        chunk_size=400,
        chunk_overlap=60,
    )

    # Step 2: Print Ingestion Summary Table
    print("\n" + "=" * 80)
    print("                       CORPUS INGESTION SUMMARY")
    print("=" * 80)
    print(f"{'Source Document':<24} | {'Type':<6} | {'Raw Chars':<10} | {'Clean Chars':<11} | {'Chunks':<6} | {'Tokens':<8} | {'Status'}")
    print("-" * 80)

    for doc in summary.documents:
        status_str = "[OK] SUCCESS" if doc.status == "SUCCESS" else "[!] FAILED"
        print(
            f"{doc.source:<24} | {doc.doc_type:<6} | {doc.raw_chars:<10,d} | {doc.cleaned_chars:<11,d} | {doc.chunk_count:<6d} | {doc.total_tokens:<8,d} | {status_str}"
        )
    print("-" * 80)

    # Step 3: Print Failure Isolation Details if any
    if summary.failures:
        print("\n" + "-" * 80)
        print("  ISOLATED INGESTION FAILURES (Safely trapped without silent drop):")
        print("-" * 80)
        for f in summary.failures:
            print(f"  * File: {f['source']} ({f['doc_type']}) - Size: {f['size_bytes']} bytes")
            print(f"    Error: [{f['error_type']}] {f['error_message']}")
        print("-" * 80)

    # Step 4: Completeness Validation Audit
    comp = summary.completeness
    print("\n" + "=" * 80)
    print("                  COMPLETENESS VALIDATION AUDIT")
    print("=" * 80)
    print(f"  Reconciliation Formula: Total Discovered = Successfully Ingested + Recorded Failures")
    print(f"  Formula Evaluation:     {comp.total_source_documents} = {comp.successfully_ingested} + {comp.failed_documents}")
    print(f"  Reconciliation Match:   {comp.is_reconciled} (Discrepancy: {comp.discrepancy})")
    print(f"  Audit Status:           [{comp.status}]")
    print(f"  Proof:                  {comp.validation_message}")
    print("=" * 80)

    # Step 5: Display Sample Chunks with Rich Metadata
    print("\n" + "=" * 80)
    print("             SAMPLE INGESTED CHUNKS WITH METADATA INSPECTION")
    print("=" * 80)

    samples_shown = 0
    for chunk in summary.all_chunks:
        if samples_shown >= 3:
            break
        samples_shown += 1
        print(f"\n--- Sample Chunk #{samples_shown} (Doc: '{chunk.source}', Index: {chunk.chunk_index}/{chunk.total_chunks}) ---")
        print(f"  Tokens: {chunk.token_count} (Span: [{chunk.start_token}:{chunk.end_token}]) | Length: {chunk.char_length} chars | Words: {chunk.word_count}")
        print(f"  Metadata: {json.dumps(chunk.metadata)}")
        print(f"  Text Preview:\n  \"{chunk.text[:180].replace(chr(10), ' ')}...\"")

    # Step 6: Export Reports
    summary_json_path = outputs_dir / "ingestion_summary.json"
    summary_md_path = outputs_dir / "ingestion_summary.md"
    sample_chunks_md_path = outputs_dir / "sample_ingested_chunks.md"

    # Write JSON
    with open(summary_json_path, "w", encoding="utf-8") as f:
        json.dump(summary.to_dict(), f, indent=2)

    # Write Markdown Summary
    md_summary = pipeline.generate_markdown_summary(summary)
    with open(summary_md_path, "w", encoding="utf-8") as f:
        f.write(md_summary)

    # Write Sample Chunks Markdown
    md_samples = pipeline.generate_sample_chunks_markdown(summary, samples_per_doc=2)
    with open(sample_chunks_md_path, "w", encoding="utf-8") as f:
        f.write(md_samples)

    print("\n" + "=" * 80)
    print("                 OUTPUT ARTIFACTS SUCCESSFULLY SAVED")
    print("=" * 80)
    print(f"  [1] JSON Summary:         {summary_json_path}")
    print(f"  [2] Markdown Audit:       {summary_md_path}")
    print(f"  [3] Sample Chunks Report: {sample_chunks_md_path}")
    print("=" * 80)


if __name__ == "__main__":
    run_full_ingestion_demonstration()
