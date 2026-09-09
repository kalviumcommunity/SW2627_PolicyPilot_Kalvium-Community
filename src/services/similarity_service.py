"""Vector similarity calculation and chunk ranking service for PolicyPilot."""

import math
from typing import Any, Dict, List, Optional
from src.services.embedding_service import EmbeddingService


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Compute cosine similarity score between two float vectors.

    Score range: -1.0 to 1.0 (returns 0.0 for zero vectors or dimension mismatch).
    """
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0

    dot_product = sum(a * b for a, b in zip(v1, v2))
    norm_v1 = math.sqrt(sum(a * a for a in v1))
    norm_v2 = math.sqrt(sum(b * b for b in v2))

    if norm_v1 == 0.0 or norm_v2 == 0.0:
        return 0.0

    return dot_product / (norm_v1 * norm_v2)


class SimilarityService:
    """Service to rank candidate chunks by similarity to a query embedding."""

    def __init__(self, embedding_service: Optional[EmbeddingService] = None):
        """Initialize SimilarityService with an optional EmbeddingService instance."""
        self.embedding_service = embedding_service or EmbeddingService()

    def rank_chunks(
        self,
        query_vector: List[float],
        candidate_chunks: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Rank candidate chunk dictionaries by cosine similarity to a query vector.

        Args:
            query_vector: Embedding vector of the query.
            candidate_chunks: List of chunk dictionaries containing text or pre-generated embedding.

        Returns:
            List of chunk dictionaries sorted by 'score' descending.
        """
        if not query_vector or not candidate_chunks:
            return []

        scored_chunks = []
        for chunk in candidate_chunks:
            chunk_copy = dict(chunk)
            chunk_embedding = chunk.get("embedding")
            if not chunk_embedding:
                text = chunk.get("text") or chunk.get("content") or ""
                chunk_embedding = self.embedding_service.generate_embedding(text)

            score = cosine_similarity(query_vector, chunk_embedding)
            chunk_copy["score"] = round(score, 4)
            scored_chunks.append(chunk_copy)

        scored_chunks.sort(key=lambda x: x["score"], reverse=True)
        return scored_chunks
