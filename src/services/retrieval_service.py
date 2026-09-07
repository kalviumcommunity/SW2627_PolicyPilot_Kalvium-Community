"""Knowledge-base retrieval services for PolicyPilot RAG Assistant.

Provides query embedding using the corpus embedding model, top-k similarity search
against vector database chunks, rich metadata retention, and multi-k demonstration.
"""

json_ok = True
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.services.embedding_service import EmbeddingService
from src.services.document_service import DocumentService

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CACHE_FILE = PROJECT_ROOT / "outputs" / "embedded_chunks.json"


class RetrievalService:
    """Find relevant document chunks in vector store for user questions."""

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

                store[c_id] = {
                    "chunk_id": c_id,
                    "source": source,
                    "content": content,
                    "embedding": vec,
                    "vector_dim": len(vec),
                    "chunk_index": c_index,
                    "token_count": chunk.get("token_count", 0),
                    "start_token": chunk.get("start_token", 0),
                    "end_token": chunk.get("end_token", 0),
                    "metadata": {
                        "source": source,
                        "chunk_index": c_index,
                        "token_count": chunk.get("token_count", 0),
                        "start_token": chunk.get("start_token", 0),
                        "end_token": chunk.get("end_token", 0),
                        "doc_type": Path(source).suffix.lstrip("."),
                    },
                }

        self._vector_store_cache = store
        return store

    def search(
        self,
        query: str,
        top_k: int = 3,
        vector_store: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Run top-k similarity search against vector store for a user query.

        Args:
            query: User search query or question.
            top_k: Number of most similar chunks to return (default: 3). Must be > 0.
            vector_store: Optional pre-loaded dict of chunks. If None, uses cached store.

        Returns:
            List of top-k retrieved chunk dictionaries sorted descending by similarity score,
            including similarity scores, source text, source document, chunk index, and metadata.
        """
        if top_k <= 0:
            raise ValueError(f"top_k must be positive, got {top_k}")

        if not query or not query.strip():
            logger.warning("Empty query passed to search.")
            return []

        # 1. Task 1: Embed query using identical model
        query_vec = self.embed_query(query)

        # 2. Get vector store chunks
        store = vector_store if vector_store is not None else self.load_vector_store()

        if not store:
            logger.warning("Vector store is empty! No chunks available for search.")
            return []

        # 3. Task 2 & Task 3: Calculate cosine similarity and collect scores + metadata
        candidates: List[Dict[str, Any]] = []

        for item_id, item in store.items():
            chunk_vec = item.get("embedding")
            if not chunk_vec:
                continue

            sim_score = self.embedding_service.cosine_similarity(query_vec, chunk_vec)
            rounded_score = round(float(sim_score), 4)

            source = item.get("source", "unknown")
            content = item.get("content") or item.get("text", "")
            chunk_idx = item.get("chunk_index", 0)

            # Extract or build rich metadata
            item_metadata = item.get("metadata", {}).copy() if isinstance(item.get("metadata"), dict) else {}
            item_metadata.setdefault("source", source)
            item_metadata.setdefault("chunk_index", chunk_idx)
            item_metadata.setdefault("token_count", item.get("token_count", 0))
            item_metadata.setdefault("doc_type", Path(source).suffix.lstrip("."))

            candidates.append({
                "chunk_id": item_id,
                "score": rounded_score,
                "source": source,
                "chunk_index": chunk_idx,
                "content": content,
                "metadata": item_metadata,
            })

        # Sort descending by score
        candidates.sort(key=lambda x: x["score"], reverse=True)

        # Truncate to top_k and add rank field
        top_results = candidates[:top_k]
        for rank_idx, res in enumerate(top_results, start=1):
            res["rank"] = rank_idx

        return top_results

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