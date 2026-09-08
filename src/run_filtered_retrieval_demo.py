"""Command-Line Demo Runner for PolicyPilot Filtered & Hybrid Retrieval.

Demonstrates:
1. Metadata filtering restricting vector search to corpus subsets (doc_type, source).
2. Side-by-side comparison of unfiltered vs. filtered retrieval for identical queries.
3. Hybrid search combining dense vector similarity with keyword match scoring.
4. Precision improvement demonstration (eliminating cross-document noise).
5. Output reports generated in outputs/filtered_retrieval_results.json and outputs/filtered_retrieval_demo_report.md.
"""

import json
import logging
import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.services.retrieval_service import RetrievalService

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

OUTPUTS_DIR = PROJECT_ROOT / "outputs"
OUTPUTS_DIR.mkdir(exist_ok=True)

RESULTS_JSON = OUTPUTS_DIR / "filtered_retrieval_results.json"
REPORT_MD = OUTPUTS_DIR / "filtered_retrieval_demo_report.md"


def run_demo():
    print("=" * 80)
    print("      PolicyPilot Metadata Filtered & Hybrid Retrieval Demonstration")
    print("=" * 80)

    retrieval_service = RetrievalService()

    # Query scenarios
    query_1 = "What is the maximum reimbursement amount for home internet allowance?"
    filter_1 = {"doc_type": "html"} # Restricts to stipend_faq.html

    query_2 = "What are the rules and deadlines for travel expense reimbursement?"
    filter_2 = {"source": "sample_policy.pdf"}

    query_3 = "How many hours per day and week are standard work hours?"
    keywords_3 = ["standard", "hours", "8", "40", "overtime"]

    print(f"\n[Task 1 & 2] Comparing Unfiltered vs Filtered Search (Query: \"{query_1}\")...")
    print(f"  Metadata Filter: {filter_1}")
    comp_1 = retrieval_service.compare_filtered_vs_unfiltered(query_1, metadata_filter=filter_1, top_k=3)

    print(f"\n  --- Unfiltered Search Results (Precision: {comp_1['unfiltered_precision_percent']}%) ---")
    for r in comp_1["unfiltered_results"]:
        snippet = r['content'][:90].replace('\n', ' ').strip()
        print(f"    [Rank #{r['rank']}] Score: {r['score']:.4f} | Source: {r['source']} ({r['metadata'].get('doc_type')}) | Content: \"{snippet}...\"")

    print(f"\n  --- Filtered Search Results (Precision: {comp_1['filtered_precision_percent']}%) ---")
    for r in comp_1["filtered_results"]:
        snippet = r['content'][:90].replace('\n', ' ').strip()
        print(f"    [Rank #{r['rank']}] Score: {r['score']:.4f} | Source: {r['source']} ({r['metadata'].get('doc_type')}) | Content: \"{snippet}...\"")

    print(f"\n[Task 3] Executing Hybrid Search (Vector + Lexical Keyword Matching)...")
    print(f"  Query: \"{query_3}\"")
    print(f"  Keywords to Boost: {keywords_3}")
    hybrid_results = retrieval_service.search_hybrid(
        query=query_3,
        alpha=0.6,
        keywords=keywords_3,
        top_k=3,
    )

    for r in hybrid_results:
        print(f"    [Rank #{r['rank']}] Hybrid Score: {r['score']:.4f} (Vector: {r['vector_score']:.4f}, Keyword: {r['keyword_score']:.4f}) | Source: {r['source']}")

    print(f"\n[Task 4] Demonstrating Improved Precision (Eliminating Cross-Document Noise)...")
    comp_2 = retrieval_service.compare_filtered_vs_unfiltered(query_2, metadata_filter=filter_2, top_k=3)
    print(f"  Query: \"{query_2}\"")
    print(f"  Filter: {filter_2}")
    print(f"  Unfiltered Target Match Ratio: {comp_2['unfiltered_target_matches']} ({comp_2['unfiltered_precision_percent']}%)")
    print(f"  Filtered Target Match Ratio:   {comp_2['filtered_target_matches']} ({comp_2['filtered_precision_percent']}%)")

    # Task 5: Save structured JSON and Markdown outputs
    payload = {
        "scenario_1_filtered_vs_unfiltered": comp_1,
        "scenario_2_precision_demonstration": comp_2,
        "scenario_3_hybrid_search": {
            "query": query_3,
            "keywords": keywords_3,
            "alpha": 0.6,
            "top_k_results": hybrid_results,
        },
    }

    with open(RESULTS_JSON, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    # Generate Markdown Report
    md_lines = [
        "# PolicyPilot Filtered & Hybrid Retrieval Demonstration Report\n",
        "- **Purpose:** Demonstrate metadata pre-filtering, hybrid (vector + keyword) retrieval, and precision enhancement over baseline top-k search.",
        "- **Corpus Scope:** `remote_policy.txt`, `stipend_faq.html`, `work_hours.md`, `sample_policy.pdf`.\n",
        "## 1. Task 1 & 2: Metadata Filtered vs. Unfiltered Search Comparison\n",
        f"### Query: *\"{query_1}\"*",
        f"- **Metadata Filter Applied:** `{json.dumps(filter_1)}`",
        f"- **Unfiltered Precision:** `{comp_1['unfiltered_precision_percent']}%` ({comp_1['unfiltered_target_matches']} target chunks)",
        f"- **Filtered Precision:** `{comp_1['filtered_precision_percent']}%` ({comp_1['filtered_target_matches']} target chunks)\n",
        "#### Unfiltered Top-K Vector Search Results:",
        "| Rank | Score | Source Document | Format | Content Snippet |",
        "| :---: | :---: | :--- | :---: | :--- |",
    ]

    for r in comp_1["unfiltered_results"]:
        snippet = r['content'][:80].replace('\n', ' ').strip() + "..."
        md_lines.append(
            f"| #{r['rank']} | `{r['score']:.4f}` | `{r['source']}` | `{r['metadata'].get('doc_type')}` | *\"{snippet}\"* |"
        )

    md_lines.extend([
        "\n#### Metadata Filtered Top-K Search Results:",
        "| Rank | Score | Source Document | Format | Content Snippet |",
        "| :---: | :---: | :--- | :---: | :--- |",
    ])

    for r in comp_1["filtered_results"]:
        snippet = r['content'][:80].replace('\n', ' ').strip() + "..."
        md_lines.append(
            f"| #{r['rank']} | `{r['score']:.4f}` | `{r['source']}` | `{r['metadata'].get('doc_type')}` | *\"{snippet}\"* |"
        )

    md_lines.extend([
        "\n## 2. Task 3: Hybrid Search (Vector Similarity + Lexical Keyword Matching)\n",
        f"### Query: *\"{query_3}\"*",
        f"- **Algorithm:** Hybrid Score $= 0.6 \\times \\text{{Vector Cosine Sim}} + 0.4 \\times \\text{{Keyword Match Score}}$",
        f"- **Target Boost Keywords:** `{keywords_3}`\n",
        "| Rank | Hybrid Score | Vector Score | Keyword Score | Source Document | Snippet |",
        "| :---: | :---: | :---: | :---: | :--- | :--- |",
    ])

    for r in hybrid_results:
        snippet = r['content'][:70].replace('\n', ' ').strip() + "..."
        md_lines.append(
            f"| #{r['rank']} | `{r['score']:.4f}` | `{r['vector_score']:.4f}` | `{r['keyword_score']:.4f}` | `{r['source']}` | *\"{snippet}\"* |"
        )

    md_lines.extend([
        "\n## 3. Task 4: Precision Improvement Demonstration\n",
        f"### Query: *\"{query_2}\"*",
        f"- **Applied Filter:** `{json.dumps(filter_2)}`",
        f"- **Baseline Unfiltered Precision:** `{comp_2['unfiltered_precision_percent']}%` — Top-k vector search retrieves unrelated chunks from `work_hours.md` and `stipend_faq.html` due to generic word overlap ('reimbursement', 'guidelines').",
        f"- **Filtered Search Precision:** `{comp_2['filtered_precision_percent']}%` — Eliminates cross-document noise, ensuring 100% of retrieved chunks belong strictly to `sample_policy.pdf`.\n",
        "## 4. Technical Guide for Video Walkthrough Script\n",
        "### Q1: Why does metadata filtering improve retrieval precision?",
        "- Metadata filtering pre-screens candidate vector chunks before distance/similarity calculations.",
        "- By scoping retrieval to specific document types, sources, categories, or date ranges, it guarantees zero irrelevant chunks from outside the target domain enter the top-k context window.",
        "",
        "### Q2: Difference between Vector Search and Keyword Search?",
        "- **Vector Search:** Maps text to high-dimensional embeddings to capture semantic intent and synonyms (e.g. 'work from home' matches 'remote work'), but can suffer from soft semantic hallucination or keyword dilution.",
        "- **Keyword Search:** Looks for exact string tokens, policy numbers, or IDs (e.g. '$75', 'Form 1040'), guaranteeing literal term matching but failing when word phrasing differs.",
        "",
        "### Q3: When is Hybrid Search better than pure vector search?",
        "- Hybrid search is superior whenever queries contain specific numeric limits (`$75`), exact policy names (`PolicyPilot`), product codes, or domain jargon alongside natural language questions.",
        "",
        "### Q4: Follow-up — What filter would our RAG problem statement need?",
        "- For PolicyPilot, filtering by `department` (HR vs. Travel vs. Finance), `user_role` (Employee vs. Manager), and `document_status` (Active vs. Archived) ensures staff receive only currently applicable, role-authorized policies.",
        "",
    ])

    with open(REPORT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    print("\n" + "=" * 80)
    print("             FILTERED RETRIEVAL ARTIFACTS SAVED SUCCESSFULLY")
    print("=" * 80)
    print(f"  [1] JSON Filtered Results:   {RESULTS_JSON}")
    print(f"  [2] Markdown Filter Report: {REPORT_MD}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    run_demo()
