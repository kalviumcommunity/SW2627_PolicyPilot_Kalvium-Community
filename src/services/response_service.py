"""Language-model response generation and hallucination guardrail services for PolicyPilot.

Provides pre-generation retrieval quality verification, safe refusal handling
when context is weak or missing, and grounded answer generation with source citations.
"""

import os
import re
import logging
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from openai import OpenAI

from src.services.retrieval_service import RetrievalService
from src.services.prompt_service import build_augmented_prompt

load_dotenv()
logger = logging.getLogger(__name__)

DEFAULT_MIN_TOP_SCORE = 0.40
DEFAULT_MIN_SUPPORTING_CHUNKS = 1
SAFE_REFUSAL_MESSAGE = "I don't have enough reliable context to answer that."


def retrieval_is_strong(
    chunks: List[Dict[str, Any]],
    min_top_score: float = DEFAULT_MIN_TOP_SCORE,
    min_supporting_chunks: int = DEFAULT_MIN_SUPPORTING_CHUNKS,
) -> bool:
    """Check if retrieved chunks satisfy minimum similarity score and count thresholds.

    Args:
        chunks: List of retrieved chunk dictionaries with 'score' key.
        min_top_score: Minimum similarity score threshold (default 0.40).
        min_supporting_chunks: Minimum number of chunks that must exceed the threshold.

    Returns:
        bool: True if retrieval is sufficiently strong, False otherwise.
    """
    if not chunks:
        return False

    strong_chunks = [chunk for chunk in chunks if chunk.get("score", 0.0) >= min_top_score]
    return len(strong_chunks) >= min_supporting_chunks


class ResponseService:
    """Service to evaluate retrieval guardrails and generate grounded responses."""

    def __init__(
        self,
        retrieval_service: Optional[RetrievalService] = None,
        client: Optional[OpenAI] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        min_top_score: float = DEFAULT_MIN_TOP_SCORE,
        min_supporting_chunks: int = DEFAULT_MIN_SUPPORTING_CHUNKS,
    ):
        """Initialize ResponseService with retrieval and language model clients.

        Args:
            retrieval_service: RetrievalService instance.
            client: Optional OpenAI client instance.
            base_url: Optional API base URL.
            api_key: Optional API key.
            model: Chat model name.
            min_top_score: Default minimum similarity threshold for guardrails.
            min_supporting_chunks: Default minimum supporting chunks count.
        """
        self.retrieval_service = retrieval_service or RetrievalService()
        self.base_url = base_url if base_url is not None else (os.getenv("API_BASE_URL") or os.getenv("OPENAI_BASE_URL"))
        self.api_key = api_key if api_key is not None else (os.getenv("API_KEY") or os.getenv("OPENAI_API_KEY"))
        self.model = model or os.getenv("CHAT_MODEL", "qwen/qwen3.6-27b")
        self.min_top_score = min_top_score
        self.min_supporting_chunks = min_supporting_chunks
        self._client = client

    def get_client(self) -> Optional[OpenAI]:
        """Get or initialize OpenAI chat client."""
        if self._client is None and bool(self.api_key):
            client_kwargs: Dict[str, Any] = {"api_key": self.api_key}
            if self.base_url:
                client_kwargs["base_url"] = self.base_url
            try:
                self._client = OpenAI(**client_kwargs)
            except Exception as e:
                logger.warning("Could not initialize OpenAI client: %s", e)
        return self._client

    def generate(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        max_tokens: int = 1024,
    ) -> str:
        """Generate a grounded response using retrieved chunks.

        Uses OpenAI chat completion API if configured; falls back to an extracted
        deterministic summary in offline/test environments.
        """
        if not chunks:
            return SAFE_REFUSAL_MESSAGE

        prompt_data = build_augmented_prompt(question=query, retrieved_chunks=chunks)
        client = self.get_client()

        if client and bool(self.api_key):
            try:
                response = client.chat.completions.create(
                    model=self.model,
                    messages=prompt_data["messages"],
                    temperature=0.0,
                    max_tokens=max_tokens,
                )
                raw_answer = response.choices[0].message.content.strip()
                # Clean thinking tags if present
                clean_answer = raw_answer
                if "<think>" in raw_answer:
                    if "</think>" in raw_answer:
                        clean_answer = raw_answer.split("</think>", 1)[1].strip()
                    else:
                        clean_answer = re.sub(r"<think>.*?(?=\n\n[A-Z]|\n\nBased|\n\nTo|\n\nEmployees|$)", "", raw_answer, flags=re.DOTALL).strip()
                
                # Strip residual markers if needed
                clean_answer = clean_answer.replace("<think>", "").replace("</think>", "").strip()
                if clean_answer and len(clean_answer) > 10 and not clean_answer.lower().startswith("here's a thinking"):
                    return clean_answer
            except Exception as e:
                logger.warning("LLM generation API call failed (%s), using deterministic synthesis", e)

        # Deterministic grounded fallback synthesis for tests and offline usage
        if not chunks:
            return SAFE_REFUSAL_MESSAGE

        citations = []
        snippets = []
        for idx, c in enumerate(chunks, start=1):
            src = c.get("metadata", {}).get("source", "source")
            text = c.get("text", "").strip()
            # Extract first sentence or key clause
            first_sentence = re.split(r"(?<=[.!?])\s+", text)[0]
            snippets.append(f"{first_sentence} [{idx}]")
            citations.append(f"[{idx}] {src}")

        combined_answer = " ".join(snippets[:2])
        return combined_answer

    def guarded_answer(
        self,
        question: str,
        k: int = 4,
        min_top_score: Optional[float] = None,
        min_supporting_chunks: Optional[int] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
        collection_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Evaluate retrieval strength and return either a safe refusal or a grounded answer.

        Guardrail workflow:
        1. Retrieve candidate chunks from vector database.
        2. Evaluate retrieval strength against similarity score and count thresholds.
        3. If weak/empty: Halt generation and return status='refused_weak_context'.
        4. If strong: Generate answer from context and return status='answered'.

        Args:
            question: The user query string.
            k: Number of candidate chunks to retrieve.
            min_top_score: Minimum similarity threshold (overrides service default).
            min_supporting_chunks: Minimum chunk count (overrides service default).
            metadata_filter: Optional metadata filter dict for retrieval.
            collection_name: Optional target collection name.

        Returns:
            Dictionary containing:
                - answer: The answer text or safe refusal message.
                - sources: List of source metadata dictionaries used in the answer.
                - status: 'answered' or 'refused_weak_context'.
                - top_score: Highest similarity score among retrieved chunks.
                - supporting_chunks_count: Number of chunks above threshold.
                - total_retrieved: Total chunks fetched in stage 1.
                - question: Original user query.
        """
        threshold = min_top_score if min_top_score is not None else self.min_top_score
        min_count = min_supporting_chunks if min_supporting_chunks is not None else self.min_supporting_chunks

        # Stage 1: Retrieval
        chunks = self.retrieval_service.retrieve(
            query=question,
            k=k,
            metadata_filter=metadata_filter,
            collection_name=collection_name,
        )

        top_score = max([c.get("score", 0.0) for c in chunks], default=0.0)
        strong_chunks = [c for c in chunks if c.get("score", 0.0) >= threshold]

        # Stage 2: Guardrail Evaluation
        if not retrieval_is_strong(chunks, min_top_score=threshold, min_supporting_chunks=min_count):
            return {
                "answer": SAFE_REFUSAL_MESSAGE,
                "sources": [],
                "status": "refused_weak_context",
                "top_score": round(top_score, 4),
                "supporting_chunks_count": len(strong_chunks),
                "total_retrieved": len(chunks),
                "question": question,
            }

        # Stage 3: Grounded Answer Generation
        answer_text = self.generate(query=question, chunks=strong_chunks)

        return {
            "answer": answer_text,
            "sources": [c.get("metadata", {}) for c in strong_chunks],
            "status": "answered",
            "top_score": round(top_score, 4),
            "supporting_chunks_count": len(strong_chunks),
            "total_retrieved": len(chunks),
            "question": question,
        }