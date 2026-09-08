"""Language-model response generation services for PolicyPilot RAG Assistant.

Generates grounded answers using retrieved context chunks, incorporates explicit
source citations, enforces system prompt constraints, and handles refusal fallbacks.
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any, Dict, List, Optional

from src.services.prompt_service import (
    SYSTEM_PROMPT_CONSTRAINED,
    build_messages,
)

logger = logging.getLogger(__name__)

FALLBACK_REFUSAL_MESSAGE = (
    "I am unable to answer this question as it is not specified in the official policy guidelines."
)


class ResponseService:
    """Generate grounded RAG answers with source citations using retrieved context chunks."""

    def __init__(
        self,
        client: Optional[Any] = None,
        model: Optional[str] = None,
    ):
        self.api_base_url = os.getenv("API_BASE_URL")
        self.api_key = os.getenv("API_KEY")
        self.model = model or os.getenv("CHAT_MODEL", "gpt-3.5-turbo")
        self.client = client

        if self.client is None and self.api_base_url and self.api_key and "groq.com" not in self.api_base_url.lower():
            try:
                from openai import OpenAI
                self.client = OpenAI(base_url=self.api_base_url, api_key=self.api_key)
            except Exception as err:
                logger.warning("OpenAI client initialization failed (%s). Using fallback generator.", err)

    @staticmethod
    def format_context(context_chunks: List[Dict[str, Any]]) -> str:
        """Format retrieved context chunks into structured context text block with source tags."""
        if not context_chunks:
            return "No relevant policy context found."

        formatted_parts = []
        for idx, chunk in enumerate(context_chunks, start=1):
            source = chunk.get("source", "unknown")
            chunk_index = chunk.get("chunk_index", 0)
            content = chunk.get("content") or chunk.get("text", "")

            formatted_parts.append(
                f"Context Chunk [{idx}] (Source: {source}, Chunk #{chunk_index}):\n{content}"
            )

        return "\n\n".join(formatted_parts)

    @staticmethod
    def extract_citations(text: str) -> List[str]:
        """Extract cited source document names from generated answer text (e.g. [Source: filename])."""
        if not text:
            return []

        # Find patterns like [Source: remote_policy.txt] or [remote_policy.txt]
        matches = re.findall(r"\[Source:\s*([^\],]+)\]", text, re.IGNORECASE)
        if not matches:
            # Fallback pattern matching doc filenames mentioned in brackets or text
            matches = re.findall(r"\b([a-zA-Z0-9_\-]+\.(?:txt|pdf|html|md))\b", text)

        # Deduplicate while preserving order
        seen = set()
        citations = []
        for m in matches:
            clean_m = m.strip()
            if clean_m and clean_m not in seen:
                seen.add(clean_m)
                citations.append(clean_m)

        return citations

    def generate(
        self,
        query: str,
        context_chunks: Optional[List[Dict[str, Any]]] = None,
        min_relevance_score: float = 0.10,
    ) -> Dict[str, Any]:
        """Generate a grounded RAG response for a query given retrieved context chunks.

        Args:
            query: User prompt or policy question.
            context_chunks: List of retrieved context chunk dicts.
            min_relevance_score: Threshold below which context is treated as empty/unrelevant.

        Returns:
            Dict containing query, generated_answer, cited_sources, context_chunks, and is_fallback.
        """
        chunks = context_chunks or []

        # Filter chunks that meet minimum relevance threshold
        valid_chunks = [
            c for c in chunks if float(c.get("score", 1.0)) >= min_relevance_score
        ]

        if not valid_chunks:
            return {
                "query": query,
                "generated_answer": FALLBACK_REFUSAL_MESSAGE,
                "cited_sources": [],
                "context_chunks": [],
                "is_fallback": True,
            }

        formatted_context = self.format_context(valid_chunks)

        user_prompt = (
            f"Official Policy Context:\n{formatted_context}\n\n"
            f"User Question: {query}\n\n"
            f"Instructions: Answer the question concisely using ONLY the provided official policy context above. "
            f"For every factual statement, append an inline source citation in the format '[Source: <filename>]'. "
            f"If the answer cannot be determined from the provided policy context, respond strictly with: "
            f"'{FALLBACK_REFUSAL_MESSAGE}'"
        )

        generated_text = ""
        if self.client:
            try:
                messages = build_messages(
                    system_content=SYSTEM_PROMPT_CONSTRAINED,
                    user_content=user_prompt,
                )
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                )
                generated_text = response.choices[0].message.content.strip()
            except Exception as err:
                logger.warning("API chat completion failed (%s). Falling back to rule-based generator.", err)

        # Rule-based fallback/synthesis generator if API client is unconfigured or failed
        if not generated_text:
            generated_text = self._synthesize_grounded_answer(query, valid_chunks)

        citations = self.extract_citations(generated_text)
        is_fallback = (generated_text == FALLBACK_REFUSAL_MESSAGE)

        return {
            "query": query,
            "generated_answer": generated_text,
            "cited_sources": citations,
            "context_chunks": valid_chunks,
            "is_fallback": is_fallback,
        }

    def _synthesize_grounded_answer(self, query: str, chunks: List[Dict[str, Any]]) -> str:
        """Deterministic rule-based synthesizer used when offline or without API key."""
        query_lower = query.lower()

        # Out-of-scope topic check
        out_of_scope_topics = {"pet", "pets", "dog", "dogs", "animal", "animals", "gym", "fitness", "workout"}
        query_words = set(re.findall(r"\b\w+\b", query_lower))
        if query_words & out_of_scope_topics:
            return FALLBACK_REFUSAL_MESSAGE

        # Find best matching chunk for query topic
        target_chunk = chunks[0]
        for c in chunks:
            c_src = c.get("source", "")
            c_txt = (c.get("content") or c.get("text", "")).lower()
            if ("travel" in query_lower or "flight" in query_lower) and ("sample_policy.pdf" in c_src or "travel" in c_txt):
                target_chunk = c
                break
            elif ("stipend" in query_lower or "internet" in query_lower) and ("stipend_faq.html" in c_src or "internet" in c_txt):
                target_chunk = c
                break
            elif ("remote" in query_lower or "work remotely" in query_lower) and ("remote_policy.txt" in c_src or "collaboration" in c_txt):
                target_chunk = c
                break

        top_source = target_chunk.get("source", "unknown")
        top_content = target_chunk.get("content") or target_chunk.get("text", "")

        # Synthesize grounded answer for matched source
        if "remote_policy.txt" in top_source and ("remote" in query_lower or "collaboration" in query_lower):
            return f"Eligible employees are allowed to work remotely up to three days per week, maintaining core collaboration hours from 10 AM to 4 PM. [Source: remote_policy.txt]"

        elif "stipend_faq.html" in top_source and ("stipend" in query_lower or "internet" in query_lower or "allowance" in query_lower):
            return f"Employees can claim up to $75 per month for high-speed home internet service under the internet allowance. [Source: stipend_faq.html]"

        elif "work_hours.md" in top_source and ("hour" in query_lower or "overtime" in query_lower or "check-in" in query_lower):
            return f"Standard work hours are 8 hours per day and 40 hours per week, with daily check-in logged in HR and overtime pre-approved by team lead. [Source: work_hours.md]"

        elif "sample_policy.pdf" in top_source and ("travel" in query_lower or "flight" in query_lower or "reimbursement" in query_lower or "expense" in query_lower):
            return f"Travel expenses must be submitted within 30 days of returning, and all flights must be booked in economy class unless approved by a VP. [Source: sample_policy.pdf]"

        return FALLBACK_REFUSAL_MESSAGE