"""Similarity & Distance Metrics service for PolicyPilot."""

import numpy as np
from typing import Any, Dict, List, Optional
from src.services.embedding_service import EmbeddingService


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Calculate the cosine similarity between two vector lists."""
    vec1 = np.array(v1)
    vec2 = np.array(v2)

    dot_product = np.dot(vec1, vec2)
    norm_v1 = np.linalg.norm(vec1)
    norm_v2 = np.linalg.norm(vec2)

    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0

    return float(dot_product / (norm_v1 * norm_v2))


def rank_chunks(
    query_embedding: List[float],
    chunks: List[Dict[str, Any]],
    embedding_service: Optional[EmbeddingService] = None,
) -> List[Dict[str, Any]]:
    """Rank candidate chunks by cosine similarity to a query embedding.

    Args:
        query_embedding: 1536-dimensional vector representing the search query.
        chunks: List of chunk dictionaries containing text/content and metadata
                (e.g., 'source', 'chunk_index', 'content').
        embedding_service: Optional EmbeddingService instance for on-the-fly chunk embedding.

    Returns:
        A new list of chunk dictionaries sorted in descending order of 'similarity_score',
        preserving all existing chunk metadata.
    """
    if not chunks or not query_embedding:
        return []

    service = embedding_service or EmbeddingService()
    ranked_results = []

    for chunk in chunks:
        # Use precomputed embedding if available, otherwise generate embedding from content
        chunk_embedding = chunk.get("embedding")
        if chunk_embedding is None:
            text_content = chunk.get("content") or chunk.get("text", "")
            chunk_embedding = service.generate_embedding(text_content)

        score = cosine_similarity(query_embedding, chunk_embedding)

        # Preserve all original chunk metadata and append similarity_score
        ranked_chunk = dict(chunk)
        ranked_chunk["similarity_score"] = round(float(score), 6)
        ranked_results.append(ranked_chunk)

    # Sort descending by similarity_score
    ranked_results.sort(key=lambda item: item["similarity_score"], reverse=True)
    return ranked_results


class SimilarityService:
    """Service to handle vector similarity calculations and chunk ranking."""

    def __init__(self, embedding_service: Optional[EmbeddingService] = None):
        self.embedding_service = embedding_service or EmbeddingService()

    def cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        return cosine_similarity(v1, v2)

    def rank_chunks(
        self,
        query_embedding: List[float],
        chunks: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Rank candidate chunks by cosine similarity in descending order."""
        return rank_chunks(
            query_embedding, chunks, embedding_service=self.embedding_service
        )
