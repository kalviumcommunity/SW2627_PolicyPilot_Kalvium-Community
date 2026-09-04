"""Metadata Filtering & Hybrid Search service for PolicyPilot."""

import re
from typing import List, Dict, Any, Optional
from src.services.embedding_service import EmbeddingService
from src.services.similarity_service import SimilarityService


class MetadataSearchService:
    """Service to handle metadata filtering and hybrid vector-keyword retrieval."""

    def __init__(
        self,
        embedding_service: Optional[EmbeddingService] = None,
        similarity_service: Optional[SimilarityService] = None,
    ):
        self.embedding_service = embedding_service or EmbeddingService()
        self.similarity_service = similarity_service or SimilarityService(
            embedding_service=self.embedding_service
        )

    def filter_chunks(
        self,
        chunks: List[Dict[str, Any]],
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Filter candidate chunks based on metadata criteria.

        Args:
            chunks: List of chunk dictionaries.
            metadata_filter: Dict specifying key-value filter conditions (e.g. {"section": "Account access"}).
                             If None or empty, returns all input chunks.

        Returns:
            Filtered list of chunk dictionaries preserving all original metadata.
        """
        if not chunks or not metadata_filter:
            return list(chunks)

        filtered = []
        for chunk in chunks:
            match = True
            for key, expected_val in metadata_filter.items():
                # Check top-level chunk dict first, then nested 'metadata' dict if present
                actual_val = chunk.get(key)
                if actual_val is None and "metadata" in chunk and isinstance(chunk["metadata"], dict):
                    actual_val = chunk["metadata"].get(key)

                if actual_val is None:
                    match = False
                    break

                # Support flexible case-insensitive matching for string values
                if isinstance(expected_val, str) and isinstance(actual_val, str):
                    if expected_val.strip().lower() != actual_val.strip().lower():
                        match = False
                        break
                elif actual_val != expected_val:
                    match = False
                    break

            if match:
                filtered.append(chunk)

        return filtered

    def calculate_keyword_score(self, query: str, text: str) -> float:
        """Calculate a normalized keyword match score (0.0 to 1.0) based on term frequency and phrase match.

        Args:
            query: Query string.
            text: Text content of the chunk.

        Returns:
            Float keyword score between 0.0 and 1.0 rounded to 6 decimal places.
        """
        if not query or not text:
            return 0.0

        text_lower = text.lower()
        query_words = re.findall(r"\b\w+\b", query.lower())

        stop_words = {
            "what", "is", "our", "the", "a", "an", "can", "i", "for", "to",
            "are", "under", "with", "in", "of", "and", "on", "it", "do",
            "does", "should", "how", "where", "when", "why", "which"
        }
        keywords = [w for w in query_words if w not in stop_words]
        if not keywords:
            keywords = query_words

        if not keywords:
            return 0.0

        # Term coverage ratio
        unique_keywords = list(set(keywords))
        matched = sum(1 for kw in unique_keywords if kw in text_lower)
        coverage_ratio = matched / len(unique_keywords)

        # Exact phrase bonus if query keywords appear in order
        clean_query = " ".join(keywords)
        phrase_bonus = 0.2 if clean_query in text_lower else 0.0

        score = min(1.0, coverage_ratio + phrase_bonus)
        return round(float(score), 6)

    def search(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        metadata_filter: Optional[Dict[str, Any]] = None,
        top_k: Optional[int] = None,
        enable_hybrid: bool = False,
        vector_weight: float = 0.8,
        keyword_weight: float = 0.2,
    ) -> List[Dict[str, Any]]:
        """Search and rank chunks using metadata filtering, vector similarity, and optional hybrid scoring.

        Args:
            query: User query string.
            chunks: List of candidate chunk dictionaries.
            metadata_filter: Optional dict of key-value filters.
            top_k: Optional limit on the number of returned chunks.
            enable_hybrid: Whether to enable hybrid vector + keyword search.
            vector_weight: Weight for vector similarity in hybrid score (default 0.8).
            keyword_weight: Weight for keyword score in hybrid score (default 0.2).

        Returns:
            List of ranked chunk dictionaries sorted by similarity_score or hybrid_score descending.
        """
        if not query or not chunks:
            return []

        # 1. Filter candidate chunks by metadata
        candidates = self.filter_chunks(chunks, metadata_filter)
        if not candidates:
            return []

        # 2. Compute vector similarity scores via SimilarityService
        query_embedding = self.embedding_service.generate_embedding(query)
        ranked_chunks = self.similarity_service.rank_chunks(query_embedding, candidates)

        results = []
        for chunk in ranked_chunks:
            item = dict(chunk)
            sim_score = item.get("similarity_score", 0.0)

            if enable_hybrid:
                content_text = item.get("content") or item.get("text", "")
                kw_score = self.calculate_keyword_score(query, content_text)
                hyb_score = (vector_weight * sim_score) + (keyword_weight * kw_score)

                item["keyword_score"] = round(float(kw_score), 6)
                item["hybrid_score"] = round(float(hyb_score), 6)

            results.append(item)

        # 3. Sort results: by hybrid_score if hybrid enabled, else by similarity_score
        if enable_hybrid:
            results.sort(key=lambda x: x["hybrid_score"], reverse=True)
        else:
            results.sort(key=lambda x: x.get("similarity_score", 0.0), reverse=True)

        if top_k is not None:
            return results[:top_k]
        return results
