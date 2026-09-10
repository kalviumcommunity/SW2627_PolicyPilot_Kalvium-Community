"""Batch Embedding Pipeline Runner for PolicyPilot.

Embeds chunks in configurable batches, handles transient errors via backoff retries,
skips already-embedded chunks on re-runs, tracks token cost, and outputs run summary reports.
"""

import argparse
import hashlib
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.services.document_service import DocumentService
from src.services.embedding_service import EmbeddingService

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

OUTPUTS_DIR = PROJECT_ROOT / "outputs"
OUTPUTS_DIR.mkdir(exist_ok=True)

CACHE_FILE = OUTPUTS_DIR / "embedded_chunks.json"
SUMMARY_MD = OUTPUTS_DIR / "batch_embedding_summary.md"
SUMMARY_JSON = OUTPUTS_DIR / "batch_embedding_summary.json"


def compute_chunk_hash(text: str) -> str:
    """Compute MD5 hash of chunk text for duplicate detection."""
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def load_embedding_cache() -> Dict[str, Dict[str, Any]]:
    """Load existing embedded chunks cache if present."""
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except Exception as err:
            logging.warning("Could not read embedding cache file (%s). Starting fresh.", err)
    return {}


def save_embedding_cache(cache: Dict[str, Dict[str, Any]]) -> None:
    """Save embedded chunks cache to JSON store."""
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)
    logging.info("Saved %d embedded chunks to %s", len(cache), CACHE_FILE)


def run_pipeline(
    batch_size: int = 10,
    max_retries: int = 3,
    force_reembed: bool = False,
) -> Dict[str, Any]:
    """Execute batch embedding pipeline with caching, retries, and cost tracking."""
    logging.info("Starting Batch Embedding Pipeline (batch_size=%d, max_retries=%d)...", batch_size, max_retries)

    # 1. Load document chunks
    doc_service = DocumentService()
    data_path = PROJECT_ROOT / "data"
    chunks = doc_service.load_and_chunk_documents(data_dir=str(data_path))

    if not chunks:
        logging.warning("No document chunks found in data directory!")
        return {"error": "No chunks found"}

    total_chunks = len(chunks)

    # 2. Load existing cache
    cache = {} if force_reembed else load_embedding_cache()

    to_embed_chunks = []
    skipped_chunks_count = 0

    for chunk in chunks:
        content_text = chunk.get("text") or chunk.get("content", "")
        c_hash = compute_chunk_hash(content_text)
        chunk_id = chunk.get("chunk_id", c_hash)

        if not force_reembed and (chunk_id in cache or c_hash in cache):
            skipped_chunks_count += 1
        else:
            to_embed_chunks.append({
                "chunk_id": chunk_id,
                "content_hash": c_hash,
                "source": chunk.get("source", "unknown"),
                "content": content_text,
                "token_count": chunk.get("token_count", 0),
            })

    logging.info(
        "Total Chunks: %d | Already Embedded (Skipped): %d | Chunks to Embed: %d",
        total_chunks, skipped_chunks_count, len(to_embed_chunks)
    )

    embed_service = EmbeddingService()
    newly_embedded_count = 0
    total_tokens = 0
    failed_batches: List[int] = []

    # 3. Process un-embedded chunks in batches
    if to_embed_chunks:
        texts_to_embed = [item["content"] for item in to_embed_chunks]
        embeddings, total_tokens, failed_batches = embed_service.generate_batch_embeddings(
            texts=texts_to_embed,
            batch_size=batch_size,
            max_retries=max_retries,
        )

        for item, vec in zip(to_embed_chunks, embeddings):
            cache[item["chunk_id"]] = {
                "chunk_id": item["chunk_id"],
                "content_hash": item["content_hash"],
                "source": item["source"],
                "content": item["content"],
                "embedding": vec,
                "vector_dim": len(vec),
            }
            newly_embedded_count += 1

        save_embedding_cache(cache)

    # 4. Compute metrics and estimated cost
    cost_usd = embed_service.estimate_cost(total_tokens)

    run_summary = {
        "total_chunks": total_chunks,
        "already_embedded_skipped": skipped_chunks_count,
        "newly_embedded": newly_embedded_count,
        "failed_batches_count": len(failed_batches),
        "failed_batch_indices": failed_batches,
        "batch_size": batch_size,
        "total_tokens_processed": total_tokens,
        "estimated_cost_usd": cost_usd,
        "cost_rate": "$0.00002 per 1,000 tokens",
        "cache_store_path": str(CACHE_FILE),
    }

    # 5. Save summary output files
    with open(SUMMARY_JSON, "w", encoding="utf-8") as f:
        json.dump(run_summary, f, indent=2)

    md_content = [
        "# PolicyPilot Batch Embedding Run Summary\n",
        f"- **Total Chunks in Corpus:** `{total_chunks}`",
        f"- **Skipped Chunks (Already Embedded):** `{skipped_chunks_count}`",
        f"- **Newly Embedded Chunks:** `{newly_embedded_count}`",
        f"- **Configured Batch Size:** `{batch_size}`",
        f"- **Failed Batches:** `{len(failed_batches)}`" + (f" (Indices: {failed_batches})" if failed_batches else " (None)"),
        f"- **Total Tokens Processed:** `{total_tokens:,}`",
        f"- **Estimated Run Cost:** `${cost_usd:.6f} USD`",
        f"- **Cache Store:** `{CACHE_FILE.name}`\n",
        "## Pipeline Performance Highlights",
        "1. **Batching:** Processed inputs in chunks of " + str(batch_size) + " to optimize API throughput.",
        "2. **Resilience:** Handled transient failures with exponential backoff retries.",
        "3. **Duplicate Prevention:** Detected existing content hashes and skipped duplicate API calls.",
    ]

    with open(SUMMARY_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(md_content))

    logging.info("Run summary saved to %s and %s", SUMMARY_MD, SUMMARY_JSON)
    return run_summary


def main():
    parser = argparse.ArgumentParser(description="PolicyPilot Batch Embedding Pipeline")
    parser.add_argument("--batch-size", type=int, default=10, help="Number of chunks per API batch")
    parser.add_argument("--max-retries", type=int, default=3, help="Max retry attempts per failed batch")
    parser.add_argument("--force-reembed", action="store_true", help="Force re-embedding all chunks ignoring cache")
    args = parser.parse_args()

    summary = run_pipeline(
        batch_size=args.batch_size,
        max_retries=args.max_retries,
        force_reembed=args.force_reembed,
    )

    print("\n========================================")
    print("      Batch Embedding Run Summary")
    print("========================================")
    print(f"Total Chunks:           {summary['total_chunks']}")
    print(f"Skipped (Already Done): {summary['already_embedded_skipped']}")
    print(f"Newly Embedded:         {summary['newly_embedded']}")
    print(f"Failed Batches:         {summary['failed_batches_count']}")
    print(f"Total Tokens:           {summary['total_tokens_processed']:,}")
    print(f"Estimated Cost:         ${summary['estimated_cost_usd']:.6f} USD")
    print("========================================\n")


if __name__ == "__main__":
    main()
