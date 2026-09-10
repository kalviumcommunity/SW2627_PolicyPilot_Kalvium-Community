"""RAG Pipeline Architecture & Flow Design service for PolicyPilot."""

import json
from typing import Any, Dict, List, Optional
from src.services.embedding_service import EmbeddingService
from src.services.similarity_service import SimilarityService
from src.services.retrieval_service import RetrievalService
from src.services.response_service import ResponseService


class RAGPipelineService:
    """Orchestrates end-to-end Retrieval-Augmented Generation (RAG) pipeline stages."""

    def __init__(
        self,
        chunks: Optional[List[Dict[str, Any]]] = None,
        embedding_service: Optional[EmbeddingService] = None,
        similarity_service: Optional[SimilarityService] = None,
        retrieval_service: Optional[RetrievalService] = None,
        response_service: Optional[ResponseService] = None,
    ):
        """Initialize RAGPipelineService with candidate chunks and dependency services.

        Args:
            chunks: Optional default list of chunk dictionaries for retrieval.
            embedding_service: Optional EmbeddingService instance.
            similarity_service: Optional SimilarityService instance.
            retrieval_service: Optional RetrievalService instance.
            response_service: Optional ResponseService instance.
        """
        self.chunks = chunks or []
        self.embedding_service = embedding_service or EmbeddingService()
        self.similarity_service = similarity_service or SimilarityService(
            embedding_service=self.embedding_service
        )
        self.retrieval_service = retrieval_service or RetrievalService(
            embedding_service=self.embedding_service,
            similarity_service=self.similarity_service,
        )
        self.response_service = response_service or ResponseService()

    def embed_query(self, query: str) -> List[float]:
        """Convert a user query into a 1536-dimensional vector embedding."""
        if not query:
            return [0.0] * 1536
        return self.embedding_service.generate_embedding(query)

    def retrieve_context(
        self,
        query_vector: List[float],
        k: int = 4,
        chunks: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve the top-k most relevant candidate chunks for a query vector."""
        if isinstance(k, list):
            candidate_chunks = k
            effective_k = 4
        else:
            candidate_chunks = chunks if chunks is not None else self.chunks
            effective_k = k

        if not query_vector or not candidate_chunks:
            return []

        ranked_chunks = self.similarity_service.rank_chunks(
            query_vector, candidate_chunks
        )

        if effective_k is not None and effective_k > 0:
            return ranked_chunks[:effective_k]
        return ranked_chunks

    def assemble_context(self, chunks: List[Dict[str, Any]]) -> str:
        """Assemble retrieved chunks into a formatted context string with citations."""
        if not chunks:
            return ""

        formatted_blocks = []
        for idx, chunk in enumerate(chunks, 1):
            source = (
                chunk.get("source")
                or (
                    chunk.get("metadata", {}).get("source")
                    if isinstance(chunk.get("metadata"), dict)
                    else None
                )
                or "Unknown Source"
            )
            text = chunk.get("content") or chunk.get("text") or ""
            block = f"[{idx}] Source: {source}\n{text.strip()}"
            formatted_blocks.append(block)

        return "\n\n".join(formatted_blocks)

    def generate_answer(self, query: str, context: str) -> str:
        """Generate a policy response grounded strictly in the provided context."""
        fallback_msg = "I could not find relevant context for that question."
        if not context or not context.strip():
            return fallback_msg

        res = self.response_service.generate(query, context)
        raw_answer = res.get("answer", "")

        try:
            parsed = json.loads(raw_answer)
            if isinstance(parsed, dict) and "answer" in parsed:
                answer_str = str(parsed["answer"])
                if answer_str.startswith("I am unable to answer"):
                    return fallback_msg
                return answer_str
        except (json.JSONDecodeError, TypeError):
            pass

        if raw_answer:
            return str(raw_answer)

        return fallback_msg

    def answer_query(
        self,
        query: str,
        k: int = 4,
        chunks: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Orchestrate the complete end-to-end RAG pipeline."""
        fallback_response = {
            "answer": "I could not find relevant context for that question.",
            "sources": [],
        }

        if not query or not query.strip():
            return fallback_response

        query_vector = self.embed_query(query)
        retrieved_chunks = self.retrieve_context(query_vector, k=k, chunks=chunks)

        if not retrieved_chunks:
            return fallback_response

        context = self.assemble_context(retrieved_chunks)
        if not context or not context.strip():
            return fallback_response

        answer = self.generate_answer(query, context)

        sources = []
        for chunk in retrieved_chunks:
            src = (
                chunk.get("source")
                or (
                    chunk.get("metadata", {}).get("source")
                    if isinstance(chunk.get("metadata"), dict)
                    else None
                )
            )
            if src and str(src) not in sources:
                sources.append(str(src))

        return {
            "answer": answer,
            "sources": sources,
        }

    def conversational_query(
        self,
        query: str,
        history: Optional[List[Dict[str, str]]] = None,
        k: int = 4,
        chunks: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Orchestrate conversational RAG query with query rewriting based on history."""
        from src.services.conversational_rag_service import rewrite_followup

        active_history = history if history is not None else []
        standalone_query = rewrite_followup(active_history, query) if active_history else query
        result = self.answer_query(query=standalone_query, k=k, chunks=chunks)
        result["rewritten_query"] = standalone_query
        result["original_query"] = query

        active_history.append({"role": "user", "content": query})
        active_history.append({"role": "assistant", "content": result.get("answer", "")})
        result["history"] = active_history
        return result


# Alias for compatibility
RagPipelineService = RAGPipelineService

