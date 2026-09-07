"""Chunk Re-Ranking service for PolicyPilot RAG Assistant.

Provides two-stage retrieval and re-ranking pipeline: retrieves an expanded candidate
set from vector storage, scores query-chunk relevance with cross-scoring / LLM evaluation,
and surfaces the most precise chunks to the top of the context window.
"""

import os
import re
import math
import time
import logging
from typing import List, Dict, Any, Optional, Callable
from dotenv import load_dotenv
from openai import OpenAI

from src.services.retrieval_service import RetrievalService

load_dotenv()
logger = logging.getLogger(__name__)


def compute_cross_relevance_score(query: str, chunk_text: str) -> float:
    """Compute deterministic cross-attention relevance score between query and chunk (0.0 to 10.0).

    Used for fast local scoring, test environments, and fallback when LLM API is unreachable.
    Evaluates exact keyword matches, phrase alignment, term density, and intent coverage.
    """
    if not query or not chunk_text:
        return 0.0

    query_clean = re.findall(r"\b\w+\b", query.lower())
    chunk_clean = re.findall(r"\b\w+\b", chunk_text.lower())

    if not query_clean or not chunk_clean:
        return 0.0

    # Stopwords to deprioritize generic grammatical tokens
    stopwords = {
        "what", "is", "are", "the", "for", "and", "or", "to", "in", "of", "a", "an",
        "how", "can", "do", "does", "their", "when", "where", "which", "on", "at", "by"
    }

    content_query_terms = [w for w in query_clean if w not in stopwords] or query_clean
    chunk_set = set(chunk_clean)

    # 1. Term Coverage (Ratio of unique content query terms present in chunk)
    matched_terms = [w for w in content_query_terms if w in chunk_set]
    coverage_ratio = len(matched_terms) / len(content_query_terms)

    # 2. Term Frequency & Density in Chunk
    term_counts = sum(chunk_clean.count(w) for w in content_query_terms)
    density_score = min(term_counts / (len(chunk_clean) + 5) * 10.0, 3.0)

    # 3. Exact Multi-Word Phrase Matching
    query_str_clean = " ".join(content_query_terms)
    chunk_str_clean = " ".join(chunk_clean)
    phrase_bonus = 0.0

    # Check for 2-term and 3-term phrase co-occurrence
    for i in range(len(content_query_terms) - 1):
        bigram = f"{content_query_terms[i]} {content_query_terms[i+1]}"
        if bigram in chunk_str_clean:
            phrase_bonus += 1.5

    # Check if full query content phrase is directly contained
    if query_str_clean in chunk_str_clean:
        phrase_bonus += 2.5

    # Base score: coverage accounts for up to 5.0 points
    base_score = coverage_ratio * 5.0
    total_score = base_score + density_score + phrase_bonus

    # Normalize and clamp to 0.0 - 10.0
    clamped_score = max(0.0, min(10.0, total_score))
    return round(clamped_score, 2)


class RerankingService:
    """Service to re-rank retrieved candidates for high-precision RAG context selection."""

    def __init__(
        self,
        retrieval_service: Optional[RetrievalService] = None,
        client: Optional[OpenAI] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        method: str = "cross_attention",
        scoring_fn: Optional[Callable[[str, Dict[str, Any]], float]] = None,
    ):
        """Initialize RerankingService with retrieval provider and scoring configuration.

        Args:
            retrieval_service: RetrievalService instance for initial stage candidate retrieval.
            client: Optional OpenAI client instance.
            base_url: Optional API base URL (falls back to API_BASE_URL or OPENAI_BASE_URL).
            api_key: Optional API key (falls back to API_KEY or OPENAI_API_KEY).
            model: Model name for LLM scoring (falls back to CHAT_MODEL).
            method: Re-ranking method ('cross_attention' or 'llm'). Default is 'cross_attention'.
            scoring_fn: Optional custom scoring function (query, chunk) -> float.
        """
        self.retrieval_service = retrieval_service or RetrievalService()
        self.base_url = base_url or os.getenv("API_BASE_URL") or os.getenv("OPENAI_BASE_URL")
        self.api_key = api_key or os.getenv("API_KEY") or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("CHAT_MODEL", "qwen/qwen3.6-27b")
        self.method = method
        self.custom_scoring_fn = scoring_fn
        self._client = client

    def get_client(self) -> Optional[OpenAI]:
        """Get or initialize the OpenAI-compatible chat client."""
        if self._client is None and self.api_key:
            client_kwargs: Dict[str, Any] = {"api_key": self.api_key}
            if self.base_url:
                client_kwargs["base_url"] = self.base_url
            try:
                self._client = OpenAI(**client_kwargs)
            except Exception as e:
                logger.warning("Could not initialize OpenAI client for re-ranking: %s", e)
        return self._client

    def rerank_score_llm(self, query: str, chunk: Dict[str, Any]) -> float:
        """Score how relevant a chunk is to the query (0 to 10) using an LLM chat completion."""
        chunk_text = chunk.get("text", "")
        prompt = (
            f"Score how relevant this chunk is to the query from 0 to 10.\n"
            f"Query: {query}\n"
            f"Chunk: {chunk_text}\n"
            f"Return only the number."
        )

        client = self.get_client()
        if not client:
            raise RuntimeError("LLM client not configured for scoring.")

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a strict relevance evaluation grader for search retrieval. "
                    "Rate how directly and accurately the text answers the user query on a scale from 0 to 10. "
                    "Output ONLY the numeric score (e.g. 8.5 or 3)."
                ),
            },
            {"role": "user", "content": prompt},
        ]

        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.0,
            max_tokens=10,
        )

        raw_output = response.choices[0].message.content.strip()

        # Extract numeric value using regex
        match = re.search(r"(\d+(?:\.\d+)?)", raw_output)
        if match:
            score = float(match.group(1))
            return max(0.0, min(10.0, score))

        raise ValueError(f"Could not parse numeric score from LLM response: {raw_output}")

    def rerank_score(
        self,
        query: str,
        chunk: Dict[str, Any],
        method: Optional[str] = None,
    ) -> float:
        """Score candidate chunk relevance against query on 0-10 scale.

        Args:
            query: The search query string.
            chunk: Chunk dictionary containing 'text' and 'metadata'.
            method: Optional scoring method override ('cross_attention' or 'llm').
        """
        if self.custom_scoring_fn is not None:
            return self.custom_scoring_fn(query, chunk)

        active_method = method or self.method

        if active_method == "llm" and self.api_key:
            try:
                return self.rerank_score_llm(query, chunk)
            except Exception as e:
                logger.warning("LLM scoring failed (%s), falling back to cross-attention scorer", e)

        return compute_cross_relevance_score(query, chunk.get("text", ""))

    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_n: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Re-rank a list of candidate chunks by computed relevance score.

        Args:
            query: The user search query string.
            candidates: List of candidate chunk dictionaries from initial retrieval.
            top_n: Number of top re-ranked chunks to return. If None, returns all.

        Returns:
            List of re-ranked candidate chunk dictionaries with attached 'rerank_score' and 'rerank_rank'.
        """
        if not candidates:
            return []

        reranked: List[Dict[str, Any]] = []

        for chunk in candidates:
            score = self.rerank_score(query, chunk)
            reranked.append({
                **chunk,
                "rerank_score": round(score, 2),
            })

        # Sort by rerank_score descending; use initial vector score as secondary tie-breaker
        reranked.sort(
            key=lambda item: (item.get("rerank_score", 0.0), item.get("score", 0.0)),
            reverse=True,
        )

        for rank_idx, item in enumerate(reranked, start=1):
            item["rerank_rank"] = rank_idx

        if top_n is not None and top_n > 0:
            return reranked[:top_n]
        return reranked

    def retrieve_and_rerank(
        self,
        query: str,
        candidate_k: int = 10,
        final_k: int = 3,
        metadata_filter: Optional[Dict[str, Any]] = None,
        collection_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute complete two-stage Retrieval + Re-Ranking pipeline.

        1. Stage 1: Vector similarity retrieval of candidate_k items.
        2. Stage 2: Cross-scoring and re-ordering of candidates to select final_k context chunks.

        Args:
            query: The user search query.
            candidate_k: Number of candidate chunks to fetch in initial retrieval (e.g. 10).
            final_k: Number of high-precision chunks to select after re-ranking (e.g. 3).
            metadata_filter: Optional metadata filter for initial retrieval.
            collection_name: Optional ChromaDB collection name.

        Returns:
            Dictionary containing:
                - query: Search query text.
                - candidate_k: Number of initial candidates requested.
                - final_k: Final top-k context size.
                - candidates: Initial candidate chunks with vector scores.
                - initial_top_k: Top final_k chunks before re-ranking.
                - reranked_all: All candidate chunks sorted by rerank_score.
                - final_context: Final top final_k chunks after re-ranking.
                - ordering_changed: Whether re-ranking altered the top-k chunk IDs or order.
                - latency_retrieval_ms: Duration of vector retrieval stage in ms.
                - latency_rerank_ms: Duration of re-ranking stage in ms.
                - total_latency_ms: Total pipeline duration in ms.
        """
        if candidate_k < final_k:
            raise ValueError(
                f"candidate_k ({candidate_k}) must be greater than or equal to final_k ({final_k})"
            )

        # Stage 1: Initial Vector Retrieval
        t0 = time.perf_counter()
        candidates = self.retrieval_service.retrieve(
            query=query,
            k=candidate_k,
            metadata_filter=metadata_filter,
            collection_name=collection_name,
        )
        t1 = time.perf_counter()

        # Stage 2: Re-Ranking
        reranked_all = self.rerank(query=query, candidates=candidates, top_n=None)
        t2 = time.perf_counter()

        initial_top_k = candidates[:final_k]
        final_context = reranked_all[:final_k]

        initial_ids = [c["id"] for c in initial_top_k]
        final_ids = [c["id"] for c in final_context]
        ordering_changed = (initial_ids != final_ids)

        retrieval_ms = round((t1 - t0) * 1000, 2)
        rerank_ms = round((t2 - t1) * 1000, 2)
        total_ms = round((t2 - t0) * 1000, 2)

        return {
            "query": query,
            "candidate_k": candidate_k,
            "final_k": final_k,
            "candidates_count": len(candidates),
            "candidates": candidates,
            "initial_top_k": initial_top_k,
            "reranked_all": reranked_all,
            "final_context": final_context,
            "ordering_changed": ordering_changed,
            "latency_retrieval_ms": retrieval_ms,
            "latency_rerank_ms": rerank_ms,
            "total_latency_ms": total_ms,
        }


def show(label: str, rows: List[Dict[str, Any]]) -> None:
    """Print formatted before-and-after comparison table for retrieved chunks."""
    print(label)
    for rank, item in enumerate(rows, start=1):
        print("rank:", rank)
        print("vector_score:", round(item.get("score", 0.0), 4))
        print("rerank_score:", item.get("rerank_score"))
        print("source:", item.get("metadata", {}).get("source", "unknown"))
        print("text:", item.get("text", "")[:120].replace("\n", " "))
        print("-" * 40)
