"""Command-Line Demo Runner for PolicyPilot Vector Retrieval Pipeline.

Embeds sample user queries, executes top-k similarity search against indexed vector store,
includes similarity scores and metadata, demonstrates changing k values (k=2 vs k=5),
and exports sample query results to outputs/retrieval_results.json and outputs/retrieval_demo_report.md.
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

RESULTS_JSON = OUTPUTS_DIR / "retrieval_results.json"
REPORT_MD = OUTPUTS_DIR / "retrieval_demo_report.md"


def run_demo():
    print("=" * 80)
    print("         PolicyPilot Vector Database Top-K Retrieval Demonstration")
    print("=" * 80)

    retrieval_service = RetrievalService()

    # Sample user query for demonstration
    sample_query = "How many days per week can eligible employees work remotely?"
    k_values = [2, 5]

    print(f"\n[Task 1] Embedding User Query using identical EmbeddingModel...")
    print(f"  Query: \"{sample_query}\"")
    query_vector = retrieval_service.embed_query(sample_query)
    print(f"  Generated Vector Dimensions: {len(query_vector)} floats")
    print(f"  Vector Preview (first 5 components): {query_vector[:5]}")

    print(f"\n[Task 2 & 3] Running Top-K Similarity Search (Scores & Metadata)...")
    top_3_results = retrieval_service.search(sample_query, top_k=3)

    for res in top_3_results:
        print(f"\n  Rank #{res['rank']} | Score: {res['score']:.4f} | Source: {res['source']}")
        print(f"  Chunk Index: {res['chunk_index']} | Tokens: {res['metadata'].get('token_count', 'N/A')}")
        snippet = res['content'][:120].replace("\n", " ").strip()
        print(f"  Content Snippet: \"{snippet}...\"")

    print(f"\n[Task 4] Demonstrating Changing K Values ({k_values})...")
    multi_k_comparison = retrieval_service.compare_k(sample_query, k_values=k_values)

    for k_key, comp in multi_k_comparison["comparisons"].items():
        k_val = comp["k"]
        print(f"\n  --- Results for k={k_val} (Retrieved: {comp['retrieved_count']} chunks) ---")
        print(f"  Score Range: Max={comp['max_score']:.4f}, Min={comp['min_score']:.4f}")
        for r in comp["results"]:
            print(f"    [Rank #{r['rank']}] Score: {r['score']:.4f} | Source: {r['source']} (Index #{r['chunk_index']})")

    # Task 5: Commit sample query results to JSON and Markdown report
    results_payload = {
        "sample_query": sample_query,
        "query_embedding_dimension": len(query_vector),
        "query_embedding_sample": query_vector[:10],
        "k_values_evaluated": k_values,
        "results_by_k": multi_k_comparison["comparisons"],
        "top_k_retrieved_chunks": top_3_results,
    }

    with open(RESULTS_JSON, "w", encoding="utf-8") as f:
        json.dump(results_payload, f, indent=2)

    # Generate Markdown Report
    md_lines = [
        "# PolicyPilot Vector Retrieval Demonstration Report\n",
        f"- **Sample User Query:** *\"{sample_query}\"*",
        f"- **Query Embedding Dimension:** `{len(query_vector)}`",
        f"- **Embedding Model:** Same model as document chunks (`EmbeddingService` / `text-embedding-ada-002` deterministic vectorizer)",
        f"- **Evaluated K Values:** `{k_values}`\n",
        "## 1. Top-K Similarity Search Results (k=3)\n",
        "| Rank | Cosine Score | Source Document | Chunk Index | Token Count | Content Snippet |",
        "| :---: | :---: | :--- | :---: | :---: | :--- |",
    ]

    for r in top_3_results:
        snippet = r['content'][:80].replace('\n', ' ').strip() + "..."
        t_count = r['metadata'].get('token_count', 'N/A')
        md_lines.append(
            f"| #{r['rank']} | `{r['score']:.4f}` | `{r['source']}` | #{r['chunk_index']} | {t_count} | *\"{snippet}\"* |"
        )

    md_lines.extend([
        "\n## 2. Multi-K Demonstration & Comparison\n",
        "Running the exact same query across different values of $k$ illustrates how retrieval scope expands:\n",
    ])

    for k_key, comp in multi_k_comparison["comparisons"].items():
        k_val = comp["k"]
        md_lines.extend([
            f"### Demonstration for $k={k_val}$",
            f"- **Chunks Retrieved:** `{comp['retrieved_count']}`",
            f"- **Highest Similarity Score:** `{comp['max_score']:.4f}`",
            f"- **Lowest Similarity Score in Top-{k_val}:** `{comp['min_score']:.4f}`\n",
            "| Rank | Score | Source Document | Chunk Index | Snippet |",
            "| :---: | :---: | :--- | :---: | :--- |",
        ])
        for r in comp["results"]:
            snippet = r['content'][:60].replace('\n', ' ').strip() + "..."
            md_lines.append(
                f"| #{r['rank']} | `{r['score']:.4f}` | `{r['source']}` | #{r['chunk_index']} | *\"{snippet}\"* |"
            )
        md_lines.append("")

    md_lines.extend([
        "## 3. Technical Answers for Video Walkthrough\n",
        "### Q1: What does top-$k$ mean and how is $k$ chosen?",
        "- **Definition:** Top-$k$ similarity search retrieves the $k$ document chunks from the vector database that have the highest cosine similarity scores relative to the embedded user query vector.",
        "- **How $k$ is Chosen:** $k$ is selected based on context window budget, corpus density, and question complexity. Smaller $k$ (e.g. 2-3) minimizes LLM prompt tokens and prevents irrelevant distraction, while larger $k$ (e.g. 5-10) improves recall for multi-document synthesis.",
        "",
        "### Q2: Why must the user query use the exact same embedding model as documents?",
        "- Vector embeddings represent text as points in a high-dimensional mathematical vector space.",
        "- Different embedding models map semantic concepts to completely different vector spaces with different coordinate axes and dimensions.",
        "- Comparing a query vector from Model A against chunk vectors from Model B produces meaningless dot products and invalid cosine similarity scores.",
        "",
        "### Q3: What is the trade-off of using a larger $k$?",
        "- **Pros:** Higher recall — reduces risk of omitting crucial background information or supporting policy clauses.",
        "- **Cons:** Increased prompt length, higher API latency, higher token cost, and risk of introducing noisy/irrelevant context that dilutes model focus ('lost in the middle' phenomenon).",
        "",
    ])

    with open(REPORT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    print("\n" + "=" * 80)
    print("                 RETRIEVAL ARTIFACTS SAVED SUCCESSFULLY")
    print("=" * 80)
    print(f"  [1] JSON Query Results:     {RESULTS_JSON}")
    print(f"  [2] Markdown Demo Report:   {REPORT_MD}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    run_demo()
