"""Knowledge-base retrieval services for PolicyPilot RAG Assistant.

Provides query embedding using the corpus embedding model, top-k similarity search
against vector database chunks, metadata filtering, hybrid search (vector + keyword),
rich metadata retention, and multi-k & filtered comparison demonstrations.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set

from src.services.embedding_service import EmbeddingService
from src.services.document_service import DocumentService

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CACHE_FILE = PROJECT_ROOT / "outputs" / "embedded_chunks.json"


class RetrievalService:
    """Find relevant document chunks in vector store for user questions with filtering and hybrid search support."""

    def __init__(
        self,
        embedding_service: Optional[EmbeddingService] = None,
        cache_file: Optional[Path | str] = None,
    ):
        """Initialize RetrievalService with embedding service and vector store cache path."""
        self.embedding_service = embedding_service or EmbeddingService()
        self.cache_file = Path(cache_file) if cache_file else DEFAULT_CACHE_FILE
        self._vector_store_cache: Optional[Dict[str, Any]] = None

    def embed_query(self, query: str) -> List[float]:
        """Embed a user query using the exact same embedding model as document chunks.

        Args:
            query: The user prompt or question string.

        Returns:
            1536-dimensional vector embedding of the query.
        """
        if not query or not query.strip():
            logger.warning("Empty query provided for embedding.")
            return [0.0] * 1536

        return self.embedding_service.generate_embedding(query)

    def load_vector_store(self, force_reload: bool = False) -> Dict[str, Any]:
        """Load indexed document chunks and vector embeddings from store.

        If cache file does not exist, dynamically generates embeddings for corpus documents.
        """
        if self._vector_store_cache is not None and not force_reload:
            return self._vector_store_cache

        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    store = json.load(f)
                    if isinstance(store, dict) and store:
                        logger.info("Loaded %d embedded chunks from %s", len(store), self.cache_file)
                        self._vector_store_cache = store
                        return store
            except Exception as err:
                logger.warning("Failed to load vector store cache (%s). Re-indexing...", err)

        # Fallback: Load documents dynamically and embed them
        logger.info("Indexing corpus documents dynamically for vector store...")
        doc_service = DocumentService()
        data_dir = PROJECT_ROOT / "data"
        chunks = doc_service.load_and_chunk_documents(data_dir=str(data_dir))

        store: Dict[str, Any] = {}
        if chunks:
            texts = [c.get("text") or c.get("content", "") for c in chunks]
            embeddings, _, _ = self.embedding_service.generate_batch_embeddings(texts)

            for idx, (chunk, vec) in enumerate(zip(chunks, embeddings)):
                c_id = chunk.get("chunk_id", f"chunk_{idx}")
                source = chunk.get("source", "unknown")
                content = chunk.get("text") or chunk.get("content", "")
                c_index = chunk.get("index", idx)
                doc_type = Path(source).suffix.lstrip(".")

                store[c_id] = {
                    "chunk_id": c_id,
                    "source": source,
                    "content": content,
                    "embedding": vec,
                    "vector_dim": len(vec),
                    "chunk_index": c_index,
                    "doc_type": doc_type,
                    "token_count": chunk.get("token_count", 0),
                    "start_token": chunk.get("start_token", 0),
                    "end_token": chunk.get("end_token", 0),
                    "metadata": {
                        "source": source,
                        "chunk_index": c_index,
                        "token_count": chunk.get("token_count", 0),
                        "start_token": chunk.get("start_token", 0),
                        "end_token": chunk.get("end_token", 0),
                        "doc_type": doc_type,
                    },
                }

        self._vector_store_cache = store
        return store

    @staticmethod
    def _matches_metadata_filter(item: Dict[str, Any], metadata_filter: Dict[str, Any]) -> bool:
        """Check if candidate item satisfies all key-value constraints in metadata_filter.

        Args:
            item: Candidate chunk dictionary containing top-level properties and 'metadata' dict.
            metadata_filter: Dict specifying required key-value metadata criteria.

        Returns:
            True if candidate matches all specified filter attributes; False otherwise.
        """
        if not metadata_filter:
            return True

        item_meta = item.get("metadata", {}) if isinstance(item.get("metadata"), dict) else {}

        for filter_key, expected_val in metadata_filter.items():
            # Check item top-level property first, then metadata dictionary
            actual_val = item.get(filter_key)
            if actual_val is None:
                actual_val = item_meta.get(filter_key)
            if actual_val is None and filter_key == "doc_type" and item.get("source"):
                actual_val = Path(item["source"]).suffix.lstrip(".")

            if actual_val is None:
                return False

            if isinstance(expected_val, (list, tuple, set)):
                expected_set = {str(v).lower() for v in expected_val}
                if str(actual_val).lower() not in expected_set:
                    return False
            else:
                if str(actual_val).lower() != str(expected_val).lower():
                    return False

        return True

    @staticmethod
    def _calculate_keyword_score(
        query: str,
        content: str,
        keywords: Optional[List[str]] = None,
    ) -> float:
        """Calculate a lexical keyword matching score (0.0 to 1.0) based on term overlap and exact keyword hits.

        Args:
            query: User search query string.
            content: Candidate chunk text content.
            keywords: Optional list of specific terms, numbers, or IDs to boost.

        Returns:
            Normalized float score representing keyword match strength.
        """
        if not content or not content.strip():
            return 0.0

        content_lower = content.lower()
        query_words = set(re.findall(r"\b\w+\b", query.lower()))
        content_words = set(re.findall(r"\b\w+\b", content_lower))

        if not query_words:
            return 0.0

        # Base term overlap Jaccard-style recall score
        overlap_count = len(query_words & content_words)
        overlap_score = overlap_count / max(1, len(query_words))

        # Check for specific target keywords or numbers (e.g., "$75", "75", exact terms)
        keyword_boost = 0.0
        target_terms = list(keywords) if keywords else [w for w in query_words if len(w) > 2]

        for term in target_terms:
            clean_term = term.lower().strip()
            if clean_term and clean_term in content_lower:
                keyword_boost += 0.25

        total_score = min(1.0, overlap_score + keyword_boost)
        return float(total_score)

    def search(
        self,
        query: str,
        top_k: int = 3,
        metadata_filter: Optional[Dict[str, Any]] = None,
        hybrid: bool = False,
        alpha: float = 0.7,
        keywords: Optional[List[str]] = None,
        vector_store: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Run similarity search (pure vector or filtered/hybrid) against vector store for a user query.

        Args:
            query: User search query or question.
            top_k: Number of most relevant chunks to return (default: 3). Must be > 0.
            metadata_filter: Optional dict of metadata key-value criteria to restrict search pool.
            hybrid: If True, combines vector cosine similarity with keyword matching.
            alpha: Weight assigned to vector similarity score in hybrid search (0.0 to 1.0).
            keywords: Optional explicit list of target keywords to boost in hybrid mode.
            vector_store: Optional pre-loaded dict of chunks. If None, uses cached store.

        Returns:
            List of top-k retrieved chunk dictionaries sorted descending by final score.
        """
        if top_k <= 0:
            raise ValueError(f"top_k must be positive, got {top_k}")

        if not query or not query.strip():
            logger.warning("Empty query passed to search.")
            return []

        # 1. Embed query using identical model
        query_vec = self.embed_query(query)

        # 2. Get vector store chunks
        store = vector_store if vector_store is not None else self.load_vector_store()

        if not store:
            logger.warning("Vector store is empty! No chunks available for search.")
            return []

        candidates: List[Dict[str, Any]] = []

        # 3. Traversal, metadata pre-filtering, and similarity scoring
        for item_id, item in store.items():
            # Apply metadata filter constraint (Pre-filtering)
            if metadata_filter and not self._matches_metadata_filter(item, metadata_filter):
                continue

            chunk_vec = item.get("embedding")
            if not chunk_vec:
                continue

            vector_score = float(self.embedding_service.cosine_similarity(query_vec, chunk_vec))
            content = item.get("content") or item.get("text", "")
            source = item.get("source", "unknown")
            chunk_idx = item.get("chunk_index", 0)

            if hybrid:
                kw_score = self._calculate_keyword_score(query, content, keywords=keywords)
                # Combined weighted score
                final_score = round(alpha * max(0.0, vector_score) + (1.0 - alpha) * kw_score, 4)
            else:
                kw_score = 0.0
                final_score = round(vector_score, 4)

            # Build rich metadata
            item_metadata = item.get("metadata", {}).copy() if isinstance(item.get("metadata"), dict) else {}
            item_metadata.setdefault("source", source)
            item_metadata.setdefault("chunk_index", chunk_idx)
            item_metadata.setdefault("token_count", item.get("token_count", 0))
            item_metadata.setdefault("doc_type", Path(source).suffix.lstrip("."))

            candidates.append({
                "chunk_id": item_id,
                "score": final_score,
                "vector_score": round(vector_score, 4),
                "keyword_score": round(kw_score, 4),
                "source": source,
                "chunk_index": chunk_idx,
                "content": content,
                "metadata": item_metadata,
            })

        # Sort descending by score
        candidates.sort(key=lambda x: x["score"], reverse=True)

        # Truncate to top_k and assign rank
        top_results = candidates[:top_k]
        for rank_idx, res in enumerate(top_results, start=1):
            res["rank"] = rank_idx

        return top_results

    def search_filtered(
        self,
        query: str,
        metadata_filter: Dict[str, Any],
        top_k: int = 3,
        vector_store: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Run top-k similarity search restricted to chunks matching metadata_filter."""
        return self.search(
            query=query,
            top_k=top_k,
            metadata_filter=metadata_filter,
            vector_store=vector_store,
        )

    def search_hybrid(
        self,
        query: str,
        metadata_filter: Optional[Dict[str, Any]] = None,
        alpha: float = 0.7,
        keywords: Optional[List[str]] = None,
        top_k: int = 3,
        vector_store: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Run top-k hybrid search combining vector similarity and keyword match scoring."""
        return self.search(
            query=query,
            top_k=top_k,
            metadata_filter=metadata_filter,
            hybrid=True,
            alpha=alpha,
            keywords=keywords,
            vector_store=vector_store,
        )

    def compare_filtered_vs_unfiltered(
        self,
        query: str,
        metadata_filter: Dict[str, Any],
        top_k: int = 3,
        vector_store: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Compare retrieval outcomes for the same query with and without metadata filtering.

        Args:
            query: Test user search query.
            metadata_filter: Metadata filter criteria dictionary.
            top_k: Number of top chunks to retrieve per search.
            vector_store: Optional pre-loaded vector store.

        Returns:
            Dictionary containing query, filter, unfiltered results, filtered results,
            and comparative precision metrics.
        """
        store = vector_store if vector_store is not None else self.load_vector_store()

        unfiltered_results = self.search(query=query, top_k=top_k, vector_store=store)
        filtered_results = self.search_filtered(query=query, metadata_filter=metadata_filter, top_k=top_k, vector_store=store)

        # Calculate target precision (fraction of retrieved chunks matching the filter criteria)
        unfiltered_target_count = sum(
            1 for r in unfiltered_results if self._matches_metadata_filter(r, metadata_filter)
        )
        filtered_target_count = sum(
            1 for r in filtered_results if self._matches_metadata_filter(r, metadata_filter)
        )

        unfiltered_precision = round((unfiltered_target_count / max(1, len(unfiltered_results))) * 100.0, 2) if unfiltered_results else 0.0
        filtered_precision = round((filtered_target_count / max(1, len(filtered_results))) * 100.0, 2) if filtered_results else 0.0

        return {
            "query": query,
            "metadata_filter": metadata_filter,
            "top_k": top_k,
            "unfiltered_precision_percent": unfiltered_precision,
            "filtered_precision_percent": filtered_precision,
            "unfiltered_target_matches": f"{unfiltered_target_count}/{len(unfiltered_results)}",
            "filtered_target_matches": f"{filtered_target_count}/{len(filtered_results)}",
            "unfiltered_results": unfiltered_results,
            "filtered_results": filtered_results,
        }

    def compare_k(
        self,
        query: str,
        k_values: List[int] = [2, 5],
        vector_store: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Demonstrate changing k by running the same query across multiple k values.

        Args:
            query: Sample user query string.
            k_values: List of k values to compare (e.g. [2, 5]).
            vector_store: Optional vector store dict.

        Returns:
            Dictionary mapping each k value to its retrieved top-k results, score range,
            and comparative summary.
        """
        comparisons: Dict[str, Any] = {}
        store = vector_store if vector_store is not None else self.load_vector_store()

        for k in k_values:
            results = self.search(query, top_k=k, vector_store=store)
            scores = [r["score"] for r in results]

            comparisons[f"k_{k}"] = {
                "k": k,
                "retrieved_count": len(results),
                "max_score": max(scores) if scores else 0.0,
                "min_score": min(scores) if scores else 0.0,
                "results": results,
            }

        return {
            "query": query,
            "k_values_evaluated": k_values,
            "comparisons": comparisons,
        }
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

    def retrieve_ranked_chunks(
        self,
        query: str,
        candidate_chunks: List[Dict[str, Any]],
        top_k: int = 4,
    ) -> List[Dict[str, Any]]:
        """Rank and return top_k candidate chunks by similarity to query embedding."""
        if not query or not query.strip() or not candidate_chunks:
            return []

        query_vec = self.embed_query(query)
        scored = []
        for c in candidate_chunks:
            chunk_copy = dict(c)
            chunk_vec = c.get("embedding")
            if not chunk_vec:
                text = c.get("text") or c.get("content") or ""
                try:
                    chunk_vec = self.embedding_service.embed_query(text)
                except Exception:
                    chunk_vec = generate_deterministic_vector(text, dim=self.dimension)
            
            # Compute cosine similarity
            if query_vec and chunk_vec and len(query_vec) == len(chunk_vec):
                dot = sum(a * b for a, b in zip(query_vec, chunk_vec))
                norm_q = math.sqrt(sum(a * a for a in query_vec))
                norm_c = math.sqrt(sum(b * b for b in chunk_vec))
                sim = dot / (norm_q * norm_c) if norm_q > 0 and norm_c > 0 else 0.0
            else:
                sim = 0.0
            chunk_copy["score"] = round(sim, 4)
            scored.append(chunk_copy)

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k] if top_k else scored


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
