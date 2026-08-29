"""Demonstration script for Sprint 2 Concept 11 Text Cleaning Pipeline.

Loads the raw and cleaned documents, shows a comparison of before/after stats,
and outputs a markdown report to outputs/cleaning_before_after_report.md.
"""

import os
import sys
from pathlib import Path

# Ensure src/ is in python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.document_service import DocumentService


def generate_report():
    print("=" * 60)
    print("PolicyPilot Document Processing - Text Cleaning Pipeline Demo")
    print("=" * 60)
    print("Loading documents and running comparisons...")
    print()

    service = DocumentService()
    
    # Load raw documents
    print("[1/2] Loading raw documents (clean=False)...")
    raw_docs = service.load_documents(data_dir="data", clean=False)
    
    # Load cleaned documents
    print("[2/2] Loading cleaned documents (clean=True)...")
    cleaned_docs = service.load_documents(data_dir="data", clean=True)

    # Align by source file name
    raw_map = {doc["source"]: doc["text"] for doc in raw_docs}
    cleaned_map = {doc["source"]: doc["text"] for doc in cleaned_docs}

    report_lines = [
        "# Text Cleaning Pipeline Before/After Report",
        "",
        "This report demonstrates the effect of the Text Extraction & Cleaning Pipeline on the documents in our corpus.",
        "",
        "## Summary Statistics",
        "",
        "| Document Source | Raw Chars | Cleaned Chars | Change (Chars) | Reduction (%) |",
        "| --- | --- | --- | --- | --- |",
    ]

    print("\n" + "=" * 60)
    print(f"{'Source File':<25} | {'Raw Chars':<10} | {'Cleaned Chars':<13} | {'Reduction %':<12}")
    print("-" * 60)

    for source in sorted(raw_map.keys()):
        raw_text = raw_map[source]
        cleaned_text = cleaned_map.get(source, "")
        
        raw_len = len(raw_text)
        clean_len = len(cleaned_text)
        diff = raw_len - clean_len
        pct = (diff / raw_len * 100) if raw_len > 0 else 0
        
        print(f"{source:<25} | {raw_len:<10} | {clean_len:<13} | {pct:.1f}%")
        report_lines.append(f"| {source} | {raw_len} | {clean_len} | -{diff} | {pct:.1f}% |")

    report_lines.extend([
        "",
        "## Detailed Before / After Comparisons",
        "",
    ])

    for source in sorted(raw_map.keys()):
        raw_text = raw_map[source]
        cleaned_text = cleaned_map.get(source, "")

        # Find first 400 characters for visual comparison
        raw_preview = raw_text[:400].replace("\r", "")
        cleaned_preview = cleaned_text[:400]

        report_lines.extend([
            f"### Document: `{source}`",
            "",
            "#### BEFORE (Raw Extracted Text Preview):",
            "```text",
            raw_preview + ("..." if len(raw_text) > 400 else ""),
            "```",
            "",
            "#### AFTER (Cleaned & Normalised Text Preview):",
            "```text",
            cleaned_preview + ("..." if len(cleaned_text) > 400 else ""),
            "```",
            "",
            "---",
            ""
        ])

    # Ensure output directory exists
    outputs_dir = Path("outputs")
    outputs_dir.mkdir(exist_ok=True)
    
    report_path = outputs_dir / "cleaning_before_after_report.md"
    report_path.write_text("\n".join(report_lines), encoding="utf-8")
    
    print()
    print("=" * 60)
    print(f"Report successfully saved to: {report_path}")
    print("=" * 60)


if __name__ == "__main__":
    generate_report()
