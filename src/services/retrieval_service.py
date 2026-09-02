"""Knowledge-base retrieval services."""

from typing import Any, Dict, List, Optional
from src.services.embedding_service import EmbeddingService
from src.services.similarity_service import SimilarityService


class RetrievalService:
    """Find relevant documents for a user question."""

    def __init__(
        self,
        embedding_service: Optional[EmbeddingService] = None,
        similarity_service: Optional[SimilarityService] = None,
    ):
        self.embedding_service = embedding_service or EmbeddingService()
        self.similarity_service = similarity_service or SimilarityService(
            embedding_service=self.embedding_service
        )

    def search(self, query: str, context_documents: str) -> str:
        """Return sections of context_documents relevant to a query.

        Splits context_documents by section blocks and filters based on
        matching keywords from the query.
        """
        if not context_documents or not query:
            return ""

        # Normalize query and extract keywords
        query_words = set(query.lower().replace("?", "").replace(".", "").split())
        stop_words = {
            "what",
            "is",
            "our",
            "the",
            "a",
            "an",
            "can",
            "i",
            "for",
            "to",
            "are",
            "under",
            "with",
            "in",
            "of",
            "and",
            "on",
            "it",
            "do",
            "does",
            "should",
        }
        keywords = query_words - stop_words

        # Split into distinct policy blocks
        sections = [
            sec.strip() for sec in context_documents.split("\n\n") if sec.strip()
        ]
        relevant_sections = []

        for section in sections:
            section_lower = section.lower()
            matches = sum(1 for kw in keywords if kw in section_lower)
            if matches > 0:
                relevant_sections.append((section, matches))

        if relevant_sections:
            # Sort sections by keyword match density descending
            relevant_sections.sort(key=lambda x: x[1], reverse=True)
            return "\n\n".join([sec[0] for sec in relevant_sections])

        # If no specific matches, return empty so grounding failure is triggered correctly
        return ""

    def retrieve_ranked_chunks(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        top_k: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve and rank chunks against a query using semantic similarity.

        Args:
            query: The user query string.
            chunks: List of chunk dictionaries with metadata (e.g. source, chunk_index).
            top_k: Optional maximum number of top results to return.

        Returns:
            List of ranked chunk dictionaries in descending order of similarity score.
        """
        if not query or not chunks:
            return []

        query_embedding = self.embedding_service.generate_embedding(query)
        ranked = self.similarity_service.rank_chunks(query_embedding, chunks)

        if top_k is not None:
            return ranked[:top_k]
        return ranked
