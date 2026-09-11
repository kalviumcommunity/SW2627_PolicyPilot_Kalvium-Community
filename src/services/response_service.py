"""
Response generation service for PolicyPilot RAG Assistant.

Handles:
- Retrieved-context formatting
- Retrieval quality checks
- Grounded LLM responses
- Safe fallback responses
- Source citation extraction
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

from src.services.prompt_service import (
    SYSTEM_PROMPT_CONSTRAINED,
    build_messages,
    build_augmented_prompt,
)
from src.services.retrieval_service import RetrievalService

load_dotenv()

logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# Constants
# ---------------------------------------------------------

SAFE_REFUSAL_MESSAGE = (
    "I don't have enough reliable context to answer that."
)

FALLBACK_REFUSAL_MESSAGE = (
    "I am unable to answer this question as it is not specified "
    "in the official policy guidelines."
)

DEFAULT_MIN_TOP_SCORE = 0.40
DEFAULT_MIN_SUPPORTING_CHUNKS = 1


# ---------------------------------------------------------
# Retrieval quality check
# ---------------------------------------------------------

def retrieval_is_strong(
    chunks: List[Dict[str, Any]],
    min_top_score: float = DEFAULT_MIN_TOP_SCORE,
    min_supporting_chunks: int = DEFAULT_MIN_SUPPORTING_CHUNKS,
) -> bool:
    """
    Check whether retrieved chunks are strong enough to answer safely.
    """

    if not chunks:
        return False

    strong_chunks = []

    for chunk in chunks:
        try:
            score = float(chunk.get("score", 0.0))
        except (TypeError, ValueError):
            score = 0.0

        if score >= min_top_score:
            strong_chunks.append(chunk)

    return len(strong_chunks) >= min_supporting_chunks


# ---------------------------------------------------------
# Response Service
# ---------------------------------------------------------

class ResponseService:
    """
    Generates grounded answers from retrieved policy context.
    """

    def __init__(
        self,
        retrieval_service: Optional[RetrievalService] = None,
        client: Optional[Any] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        min_top_score: float = DEFAULT_MIN_TOP_SCORE,
        min_supporting_chunks: int = DEFAULT_MIN_SUPPORTING_CHUNKS,
    ):

        self.retrieval_service = (
            retrieval_service
            if retrieval_service is not None
            else RetrievalService()
        )

        self.base_url = (
            base_url
            if base_url is not None
            else (
                os.getenv("API_BASE_URL")
                or os.getenv("OPENAI_BASE_URL")
            )
        )

        self.api_key = (
            api_key
            if api_key is not None
            else (
                os.getenv("API_KEY")
                or os.getenv("OPENAI_API_KEY")
            )
        )

        self.model = (
            model
            or os.getenv("CHAT_MODEL")
            or "gpt-3.5-turbo"
        )

        self.min_top_score = min_top_score
        self.min_supporting_chunks = min_supporting_chunks

        self._client = client
        self.use_remote = os.getenv("POLICYPILOT_ENABLE_REMOTE", "false").lower() in {"1", "true", "yes"}

    # -----------------------------------------------------
    # OpenAI-compatible client
    # -----------------------------------------------------

    def get_client(self) -> Optional[Any]:
        """
        Create the OpenAI-compatible client only when an API key exists.
        """

        if self._client is not None:
            return self._client

        if not self.api_key:
            logger.info("No API key configured. Using local fallback response generation.")
            return None
        if not self.use_remote:
            logger.info(
                "No API key configured. Using local fallback response generation."
            )
            return None

        try:
            from openai import OpenAI

            kwargs: Dict[str, Any] = {
                "api_key": self.api_key
            }

            if self.base_url:
                kwargs["base_url"] = self.base_url

            self._client = OpenAI(**kwargs)

        except Exception as exc:
            logger.warning(
                "Could not initialize OpenAI client: %s",
                exc,
            )
            self._client = None

        return self._client

    # -----------------------------------------------------
    # Context formatting
    # -----------------------------------------------------

    @staticmethod
    def format_context(
        context_chunks: List[Dict[str, Any]]
    ) -> str:
        """
        Convert retrieved chunks into a clean context block.

        Supports both:
            source/content/chunk_index

        and:
            metadata/source + text
        """

        if not context_chunks:
            return "No relevant policy context found."

        formatted_parts: List[str] = []

        for index, chunk in enumerate(
            context_chunks,
            start=1
        ):

            metadata = chunk.get("metadata") or {}

            source = (
                chunk.get("source")
                or metadata.get("source")
                or "unknown"
            )

            chunk_index = (
                chunk.get("chunk_index")
                if chunk.get("chunk_index") is not None
                else metadata.get("chunk_index", 0)
            )

            content = (
                chunk.get("content")
                or chunk.get("text")
                or ""
            )

            content = str(content).strip()

            if not content:
                continue

            formatted_parts.append(
                f"Context Chunk [{index}] "
                f"(Source: {source}, Chunk #{chunk_index}):\n"
                f"{content}"
            )

        if not formatted_parts:
            return "No relevant policy context found."

        return "\n\n".join(formatted_parts)

    # -----------------------------------------------------
    # Citation extraction
    # -----------------------------------------------------

    @staticmethod
    def extract_citations(text: str) -> List[str]:
        """
        Extract source filenames from generated text.
        """

        if not text:
            return []

        citations: List[str] = []
        seen = set()

        patterns = [
            r"\[Source:\s*([^\]]+)\]",
            r"\[source:\s*([^\]]+)\]",
        ]

        for pattern in patterns:

            matches = re.findall(
                pattern,
                text,
                flags=re.IGNORECASE,
            )

            for match in matches:

                source = match.strip()

                if source and source not in seen:
                    seen.add(source)
                    citations.append(source)

        # Fallback: detect filenames
        if not citations:

            matches = re.findall(
                r"\b[\w\- ]+\.(?:txt|pdf|html|md)\b",
                text,
                flags=re.IGNORECASE,
            )

            for match in matches:

                source = match.strip()

                if source and source not in seen:
                    seen.add(source)
                    citations.append(source)

        return citations

    # -----------------------------------------------------
    # Main grounded generation
    # -----------------------------------------------------

    def _generate_text(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        max_tokens: int = 1024,
    ) -> str:
        """
        Generate a grounded answer using only retrieved chunks.

        If an LLM is unavailable, use a safe deterministic fallback.
        """

        if not chunks:
            return SAFE_REFUSAL_MESSAGE

        prompt_data = build_augmented_prompt(
            question=query,
            retrieved_chunks=chunks,
        )

        client = self.get_client()

        # -------------------------------------------------
        # LLM generation
        # -------------------------------------------------

        if client is not None:

            try:

                response = client.chat.completions.create(
                    model=self.model,
                    messages=prompt_data["messages"],
                    temperature=0.0,
                    max_tokens=max_tokens,
                )

                raw_answer = (
                    response.choices[0]
                    .message.content
                    or ""
                ).strip()

                if raw_answer:

                    clean_answer = self._clean_answer(
                        raw_answer
                    )

                    if clean_answer:
                        return clean_answer

            except Exception as exc:

                logger.warning(
                    "LLM generation failed: %s. "
                    "Using deterministic fallback.",
                    exc,
                )

        # -------------------------------------------------
        # Local fallback
        # -------------------------------------------------

        return self._synthesize_grounded_answer(
            query=query,
            chunks=chunks,
        )

    def generate(
        self,
        query: str,
        chunks: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 1024,
        context_chunks: Optional[List[Dict[str, Any]]] = None,
    ) -> Any:
        """Generate text normally, or a structured result for evaluation callers."""
        structured = context_chunks is not None
        selected_chunks = context_chunks if structured else (chunks or [])
        answer = self._generate_text(query, selected_chunks, max_tokens=max_tokens)
        if not structured:
            return answer
        if not selected_chunks:
            answer = FALLBACK_REFUSAL_MESSAGE
        fallback = answer in {SAFE_REFUSAL_MESSAGE, FALLBACK_REFUSAL_MESSAGE}
        return {
            "generated_answer": answer,
            "context_chunks": selected_chunks,
            "is_fallback": fallback,
            "cited_sources": self.extract_citations(answer) if not fallback else [],
        }

    # -----------------------------------------------------
    # Clean LLM output
    # -----------------------------------------------------

    @staticmethod
    def _clean_answer(answer: str) -> str:
        """
        Remove model thinking markers if present.
        """

        if not answer:
            return ""

        answer = answer.strip()

        # Remove complete <think>...</think> block
        answer = re.sub(
            r"<think>.*?</think>",
            "",
            answer,
            flags=re.DOTALL | re.IGNORECASE,
        )

        # Remove unmatched markers
        answer = answer.replace(
            "<think>",
            "",
        )

        answer = answer.replace(
            "</think>",
            "",
        )

        return answer.strip()

    # -----------------------------------------------------
    # Deterministic fallback
    # -----------------------------------------------------

    def _synthesize_grounded_answer(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
    ) -> str:
        """
        Safe local fallback.

        This does NOT invent policy information.
        It only returns information directly present
        in retrieved chunks.
        """

        if not chunks:
            return SAFE_REFUSAL_MESSAGE

        query_lower = query.lower()

        # Explicitly reject clearly unrelated questions.
        out_of_scope_topics = {
            "pet",
            "pets",
            "dog",
            "dogs",
            "cat",
            "cats",
            "animal",
            "animals",
            "gym",
            "fitness",
            "workout",
        }

        query_words = set(
            re.findall(
                r"\b\w+\b",
                query_lower,
            )
        )

        if query_words.intersection(
            out_of_scope_topics
        ):
            return FALLBACK_REFUSAL_MESSAGE

        # Use the highest-scoring chunk.
        best_chunk = max(
            chunks,
            key=lambda c: self._get_score(c),
        )

        metadata = best_chunk.get(
            "metadata"
        ) or {}

        source = (
            best_chunk.get("source")
            or metadata.get("source")
            or "unknown"
        )

        content = (
            best_chunk.get("content")
            or best_chunk.get("text")
            or ""
        )

        content = str(content).strip()

        if not content:
            return SAFE_REFUSAL_MESSAGE

        # Keep the answer grounded in retrieved text.
        sentences = re.split(
            r"(?<=[.!?])\s+",
            content,
        )

        sentences = [
            sentence.strip()
            for sentence in sentences
            if sentence.strip()
        ]

        if not sentences:
            return SAFE_REFUSAL_MESSAGE

        # Return a small grounded excerpt rather than inventing facts.
        selected = " ".join(
            sentences[:3]
        )

        return (
            f"{selected} [1] "
            f"[Source: {source}]"
        )

    # -----------------------------------------------------
    # Score helper
    # -----------------------------------------------------

    @staticmethod
    def _get_score(
        chunk: Dict[str, Any]
    ) -> float:

        try:
            return float(
                chunk.get("score", 0.0)
            )
        except (
            TypeError,
            ValueError,
        ):
            return 0.0

    # -----------------------------------------------------
    # Guarded answer
    # -----------------------------------------------------

    def guarded_answer(
        self,
        question: str,
        k: int = 4,
        min_top_score: Optional[float] = None,
        min_supporting_chunks: Optional[int] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
        collection_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Complete RAG workflow:

        1. Retrieve chunks.
        2. Check retrieval quality.
        3. Refuse if context is weak.
        4. Generate grounded answer if context is strong.
        """

        threshold = (
            min_top_score
            if min_top_score is not None
            else self.min_top_score
        )

        minimum_chunks = (
            min_supporting_chunks
            if min_supporting_chunks is not None
            else self.min_supporting_chunks
        )

        # -------------------------------------------------
        # Retrieval
        # -------------------------------------------------

        try:

            chunks = self.retrieval_service.retrieve(
                query=question,
                k=k,
                metadata_filter=metadata_filter,
                collection_name=collection_name,
            )

        except TypeError:

            # Compatibility fallback for retrieval services
            # that don't accept optional parameters.
            chunks = self.retrieval_service.retrieve(
                query=question,
                k=k,
            )

        except Exception as exc:

            logger.exception(
                "Retrieval failed: %s",
                exc,
            )

            return {
                "answer": SAFE_REFUSAL_MESSAGE,
                "sources": [],
                "status": "retrieval_error",
                "top_score": 0.0,
                "supporting_chunks_count": 0,
                "total_retrieved": 0,
                "question": question,
            }

        if chunks is None:
            chunks = []

        # -------------------------------------------------
        # Score calculation
        # -------------------------------------------------

        scores = [
            self._get_score(chunk)
            for chunk in chunks
        ]

        top_score = max(
            scores,
            default=0.0,
        )

        strong_chunks = [
            chunk
            for chunk in chunks
            if self._get_score(chunk) >= threshold
        ]

        # -------------------------------------------------
        # Guardrail
        # -------------------------------------------------

        if not retrieval_is_strong(
            chunks,
            min_top_score=threshold,
            min_supporting_chunks=minimum_chunks,
        ):

            return {
                "answer": SAFE_REFUSAL_MESSAGE,
                "sources": [],
                "status": "refused_weak_context",
                "top_score": round(
                    top_score,
                    4,
                ),
                "supporting_chunks_count": len(
                    strong_chunks
                ),
                "total_retrieved": len(
                    chunks
                ),
                "question": question,
            }

        # -------------------------------------------------
        # Generate grounded answer
        # -------------------------------------------------

        answer = self.generate(
            query=question,
            chunks=strong_chunks,
        )

        # -------------------------------------------------
        # Source metadata
        # -------------------------------------------------

        sources = []

        for chunk in strong_chunks:

            metadata = chunk.get(
                "metadata"
            ) or {}

            source = (
                chunk.get("source")
                or metadata.get("source")
            )

            if source:
                sources.append(
                    {
                        **metadata,
                        "source": source,
                    }
                )

        return {
            "answer": answer,
            "sources": sources,
            "status": "answered",
            "top_score": round(
                top_score,
                4,
            ),
            "supporting_chunks_count": len(
                strong_chunks
            ),
            "total_retrieved": len(
                chunks
            ),
            "question": question,
        }

    # -----------------------------------------------------
    # Compatibility helper
    # -----------------------------------------------------

    def generate_with_context(
        self,
        query: str,
        context_chunks: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Compatibility method for API code that expects
        a dictionary response.
        """

        if not context_chunks:
            return {
                "query": query,
                "generated_answer": FALLBACK_REFUSAL_MESSAGE,
                "cited_sources": [],
                "context_chunks": [],
                "is_fallback": True,
            }

        answer = self.generate(
            query=query,
            chunks=context_chunks,
        )

        return {
            "query": query,
            "generated_answer": answer,
            "cited_sources": self.extract_citations(
                answer
            ),
            "context_chunks": context_chunks,
            "is_fallback": answer
            in {
                SAFE_REFUSAL_MESSAGE,
                FALLBACK_REFUSAL_MESSAGE,
            },
        }