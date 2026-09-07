"""Knowledge-base retrieval and evaluation services for PolicyPilot RAG Assistant.

Manages query vector generation, nearest-neighbor retrieval from vector storage,
metadata filtering, similarity score thresholding, and relevance evaluation against
ground-truth query-source pairs.
"""

import os
import math
import hashlib
import logging
from typing import List, Dict, Any, Optional, Callable
from dotenv import load_dotenv

from src.services.vector_store_service import VectorStoreService
from src.services.embedding_service import EmbeddingService

load_dotenv()
logger = logging.getLogger(__name__)


import re


def generate_deterministic_vector(text: str, dim: int = 1536) -> List[float]:
    """Generate normalized semantic projection vector of specified dimension."""
    if not text or not text.strip():
        return [0.0] * dim

    words = re.findall(r"\b\w+\b", text.lower())
    if not words:
        return [0.0] * dim

    vec = [0.0] * dim
    for word in words:
        h = int(hashlib.sha256(word.encode("utf-8")).hexdigest(), 16)
        # Distribute word features across multiple vector dimensions
        for i in range(6):
            idx = (h + i * 37) % dim
            sign = 1.0 if ((h >> (i * 4)) & 1) == 0 else -1.0
            weight = 1.0 + (min(len(word), 10) * 0.1)
            vec[idx] += sign * weight

    # Add character n-grams (3-grams) for subword and morphological matching
    clean_text = "".join(ch for ch in text.lower() if ch.isalnum() or ch.isspace())
    for j in range(len(clean_text) - 2):
        trigram = clean_text[j : j + 3]
        h_tri = int(hashlib.md5(trigram.encode("utf-8")).hexdigest(), 16)
        idx_tri = h_tri % dim
        sign_tri = 1.0 if (h_tri & 1) == 0 else -1.0
        vec[idx_tri] += sign_tri * 0.35

    magnitude = math.sqrt(sum(v * v for v in vec))
    if magnitude == 0.0:
        return [0.0] * dim
    return [round(v / magnitude, 6) for v in vec]


class RetrievalService:
    """Find and evaluate relevant document chunks for user queries."""

    def __init__(
        self,
        vector_service: Optional[VectorStoreService] = None,
        embedding_service: Optional[EmbeddingService] = None,
        default_collection: str = "rag_chunks",
        dimension: int = 1536,
        embedding_fn: Optional[Callable[[str], List[float]]] = None,
    ):
        """Initialize RetrievalService with vector store and embedding providers.

        Args:
            vector_service: VectorStoreService instance for vector database access.
            embedding_service: EmbeddingService instance for dense vector generation.
            default_collection: Default ChromaDB collection name.
            dimension: Vector dimension expected by the collection (default 1536).
            embedding_fn: Optional custom embedding function callable.
        """
        self.vector_service = vector_service or VectorStoreService(
            default_collection=default_collection,
            dimension=dimension,
        )
        self.embedding_service = embedding_service or EmbeddingService()
        self.default_collection = default_collection
        self.dimension = dimension
        self.embedding_fn = embedding_fn

    def embed_query(self, query: str) -> List[float]:
        """Generate an embedding vector for a query string.

        Tries live API embedding first; falls back to deterministic vector if
        API credentials are unavailable or non-OpenAI endpoints are used.
        """
        if not query or not query.strip():
            raise ValueError("Query string cannot be empty or whitespace only.")

        if self.embedding_fn is not None:
            vec = self.embedding_fn(query)
            if len(vec) != self.dimension:
                raise ValueError(
                    f"Custom embedding_fn returned dimension {len(vec)}, expected {self.dimension}"
                )
            return vec

        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL", "")

        # Try live OpenAI embedding if API key is present and not a third-party non-embedding endpoint
        if api_key and "groq.com" not in base_url:
            try:
                return self.embedding_service.embed_query(query)
            except Exception as e:
                logger.warning("Live query embedding failed (%s), using deterministic vector.", e)

        return generate_deterministic_vector(query, dim=self.dimension)

    def retrieve(
        self,
        query: str,
        k: int = 3,
        metadata_filter: Optional[Dict[str, Any]] = None,
        min_score: Optional[float] = None,
        collection_name: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve the top-k most relevant document chunks for a query.

        Applies nearest-neighbor vector search, optional metadata filtering,
        and minimum similarity score thresholding.

        Args:
            query: The user search query string.
            k: Number of nearest chunks to retrieve. Must be >= 1.
            metadata_filter: Optional ChromaDB metadata filter dictionary (e.g. {"doc_type": "guide"}).
            min_score: Optional minimum cosine similarity score threshold (e.g. 0.30).
            collection_name: Collection to search. Defaults to self.default_collection.

        Returns:
            List of matching chunk dictionaries containing id, score, text, metadata, and rank.
        """
        if k <= 0:
            raise ValueError(f"k must be a positive integer, got {k}")

        if not query or not query.strip():
            return []

        col_name = collection_name or self.default_collection
        query_vector = self.embed_query(query)

        raw_hits = self.vector_service.query_similar(
            query_vector=query_vector,
            top_k=k,
            filter_metadata=metadata_filter,
            collection_name=col_name,
        )

        results: List[Dict[str, Any]] = []
        rank = 1

        for hit in raw_hits:
            score = hit.get("similarity", 0.0)
            if min_score is not None and score < min_score:
                continue

            results.append({
                "id": hit["id"],
                "score": score,
                "distance": hit.get("distance", 0.0),
                "text": hit.get("text", ""),
                "metadata": hit.get("metadata", {}),
                "rank": rank,
            })
            rank += 1

        return results

    def evaluate_setting(
        self,
        setting: Dict[str, Any],
        test_queries: List[Dict[str, Any]],
        collection_name: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Evaluate a single retrieval setting against a set of ground-truth test queries.

        Args:
            setting: Configuration dictionary with keys:
                - name: Setting identifier (e.g., 'baseline_k3')
                - k: Number of chunks to retrieve
                - filter / metadata_filter: Optional metadata filter dict
                - min_score: Minimum similarity threshold float
            test_queries: List of dicts with 'query' and 'expected_source'.
            collection_name: Optional target collection name.

        Returns:
            List of evaluated query row dictionaries detailing hits, ranks, returned sources,
            and retrieved chunks.
        """
        k = setting.get("k", 3)
        metadata_filter = setting.get("filter") if "filter" in setting else setting.get("metadata_filter")
        min_score = setting.get("min_score")

        rows: List[Dict[str, Any]] = []

        for item in test_queries:
            query_text = item["query"]
            expected = item["expected_source"]

            results = self.retrieve(
                query=query_text,
                k=k,
                metadata_filter=metadata_filter,
                min_score=min_score,
                collection_name=collection_name,
            )

            sources = [r["metadata"].get("source", "") for r in results]
            hit = expected in sources
            top_1_hit = (len(sources) > 0 and sources[0] == expected)

            rank = None
            reciprocal_rank = 0.0
            if hit:
                rank = sources.index(expected) + 1
                reciprocal_rank = 1.0 / rank

            rows.append({
                "query": query_text,
                "expected_source": expected,
                "returned_sources": sources,
                "returned_count": len(results),
                "hit": hit,
                "top_1_hit": top_1_hit,
                "rank": rank,
                "reciprocal_rank": reciprocal_rank,
                "results": results,
            })

        return rows

    @staticmethod
    def compute_metrics(evaluation_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compute key Information Retrieval (IR) and RAG relevance metrics from evaluation rows.

        Metrics computed:
            - total_queries: Number of evaluated queries.
            - hits: Number of queries where expected source was retrieved.
            - hit_rate: Proportion of queries with at least one hit (Recall@k).
            - top_1_hits: Number of queries where expected source was ranked #1.
            - top_1_hit_rate: Proportion of queries where expected source was top hit (Accuracy@1).
            - mrr: Mean Reciprocal Rank (evaluates ranking position quality).
            - avg_returned_chunks: Average count of returned chunks per query.
        """
        if not evaluation_rows:
            return {
                "total_queries": 0,
                "hits": 0,
                "hit_rate": 0.0,
                "top_1_hits": 0,
                "top_1_hit_rate": 0.0,
                "mrr": 0.0,
                "avg_returned_chunks": 0.0,
            }

        total = len(evaluation_rows)
        hits = sum(1 for row in evaluation_rows if row["hit"])
        top_1_hits = sum(1 for row in evaluation_rows if row.get("top_1_hit", False))
        mrr_sum = sum(row.get("reciprocal_rank", 0.0) for row in evaluation_rows)
        total_chunks = sum(row.get("returned_count", 0) for row in evaluation_rows)

        return {
            "total_queries": total,
            "hits": hits,
            "hit_rate": round(hits / total, 4),
            "top_1_hits": top_1_hits,
            "top_1_hit_rate": round(top_1_hits / total, 4),
            "mrr": round(mrr_sum / total, 4),
            "avg_returned_chunks": round(total_chunks / total, 2),
        }

    def evaluate_all_settings(
        self,
        settings: List[Dict[str, Any]],
        test_queries: List[Dict[str, Any]],
        collection_name: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Run evaluation across multiple retrieval settings and generate comparative summary.

        Args:
            settings: List of setting dictionaries.
            test_queries: Ground-truth query-source pairs.
            collection_name: Optional target collection name.

        Returns:
            List of summary dictionaries containing setting configurations, metrics, and row details.
        """
        summary: List[Dict[str, Any]] = []

        for setting in settings:
            rows = self.evaluate_setting(
                setting=setting,
                test_queries=test_queries,
                collection_name=collection_name,
            )
            metrics = self.compute_metrics(rows)

            summary.append({
                "setting": setting.get("name", "unnamed"),
                "config": {
                    "k": setting.get("k", 3),
                    "filter": setting.get("filter") or setting.get("metadata_filter"),
                    "min_score": setting.get("min_score", 0.0),
                },
                "hit_rate": metrics["hit_rate"],
                "top_1_hit_rate": metrics["top_1_hit_rate"],
                "mrr": metrics["mrr"],
                "avg_returned_chunks": metrics["avg_returned_chunks"],
                "metrics": metrics,
                "details": rows,
            })

        return summary