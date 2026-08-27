"""Knowledge-base retrieval services with semantic relevance checking for PolicyPilot."""

import math
import re
from collections import Counter
from typing import Dict, List, Any, Optional, Tuple

from src.services.document_service import DocumentService

DEFAULT_RELEVANCE_THRESHOLD = 0.25

STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "if", "because", "as", "what", "which",
    "who", "whom", "this", "that", "these", "those", "am", "is", "are", "was",
    "were", "be", "been", "being", "have", "has", "had", "having", "do", "does",
    "did", "doing", "can", "could", "should", "would", "may", "might", "must",
    "shall", "will", "our", "my", "your", "for", "to", "in", "on", "of", "at",
    "by", "with", "from", "up", "about", "into", "over", "after", "is", "it"
}


def tokenize(text: str) -> List[str]:
    """Extract clean lowercase words excluding common stopwords."""
    words = re.findall(r"\b[a-z0-9]+\b", text.lower())
    return [w for w in words if w not in STOPWORDS and len(w) > 1]


class RetrievalService:
    """Find relevant policy documents for a user question using TF-IDF cosine similarity."""

    def __init__(self, data_dir: Optional[str] = None):
        self.doc_service = DocumentService(data_dir=data_dir)
        self.chunks: List[Dict[str, Any]] = []
        self.idf: Dict[str, float] = {}
        self.index_documents()

    def index_documents(self) -> None:
        """Load and index all document chunks into memory."""
        docs = self.doc_service.load_documents()
        self.chunks = self.doc_service.chunk_documents(docs)

        if not self.chunks:
            return

        total_docs = len(self.chunks)
        df: Counter = Counter()

        for chunk in self.chunks:
            tokens = set(tokenize(chunk["content"]))
            for token in tokens:
                df[token] += 1

        self.idf = {
            token: math.log((total_docs + 1) / (count + 1)) + 1.0
            for token, count in df.items()
        }

    def _tfidf_vector(self, tokens: List[str]) -> Dict[str, float]:
        tf = Counter(tokens)
        length = len(tokens) or 1
        return {
            token: (count / length) * self.idf.get(token, 1.0)
            for token, count in tf.items()
        }

    def _cosine_similarity(self, vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
        intersection = set(vec1.keys()) & set(vec2.keys())
        dot_product = sum(vec1[w] * vec2[w] for w in intersection)

        norm1 = math.sqrt(sum(v ** 2 for v in vec1.values()))
        norm2 = math.sqrt(sum(v ** 2 for v in vec2.values()))

        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot_product / (norm1 * norm2)

    def search(
        self,
        query: str,
        top_k: int = 3,
        threshold: float = DEFAULT_RELEVANCE_THRESHOLD
    ) -> Dict[str, Any]:
        """Search policy knowledge base and compute relevance score.

        Args:
            query: User's question.
            top_k: Max number of top chunks to return.
            threshold: Minimum relevance score required to consider context sufficient.

        Returns:
            Dict containing query, relevant_chunks, max_score, and is_sufficient flag.
        """
        query_tokens = tokenize(query)
        if not query_tokens or not self.chunks:
            return {
                "query": query,
                "relevant_chunks": [],
                "max_score": 0.0,
                "is_sufficient": False,
            }

        query_vec = self._tfidf_vector(query_tokens)
        scored_chunks: List[Tuple[float, Dict[str, Any]]] = []

        for chunk in self.chunks:
            chunk_tokens = tokenize(chunk["content"])
            chunk_vec = self._tfidf_vector(chunk_tokens)
            score = self._cosine_similarity(query_vec, chunk_vec)

            # Boost score if key query nouns/numbers match directly
            overlap_ratio = len(set(query_tokens) & set(chunk_tokens)) / len(set(query_tokens))
            combined_score = (score * 0.6) + (overlap_ratio * 0.4)

            scored_chunks.append((combined_score, chunk))

        # Sort by score descending
        scored_chunks.sort(key=lambda x: x[0], reverse=True)

        relevant_chunks = []
        max_score = scored_chunks[0][0] if scored_chunks else 0.0

        for score, chunk in scored_chunks[:top_k]:
            if score >= threshold:
                relevant_chunks.append({
                    "chunk_id": chunk["chunk_id"],
                    "source": chunk["source"],
                    "content": chunk["content"],
                    "score": round(score, 4),
                })

        is_sufficient = (max_score >= threshold) and (len(relevant_chunks) > 0)

        return {
            "query": query,
            "relevant_chunks": relevant_chunks,
            "max_score": round(max_score, 4),
            "threshold_used": threshold,
            "is_sufficient": is_sufficient,
        }