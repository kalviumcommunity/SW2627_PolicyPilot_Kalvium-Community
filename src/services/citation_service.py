"""Source Citation & Attribution service for PolicyPilot."""

from typing import Any, Dict, List, Optional
from src.services.retrieval_service import RetrievalService
from src.services.response_service import ResponseService
from src.services.rag_pipeline_service import RAGPipelineService


class CitationService:
    """Service to handle citation mapping, cited prompt construction, citation verification, and SSE streaming."""

    def __init__(
        self,
        chunks: Optional[List[Dict[str, Any]]] = None,
        retrieval_service: Optional[RetrievalService] = None,
        response_service: Optional[ResponseService] = None,
        rag_pipeline_service: Optional[RAGPipelineService] = None,
    ):
        """Initialize CitationService with optional default chunks and dependent services."""
        self.chunks = chunks or []
        self.retrieval_service = retrieval_service or RetrievalService()
        self.response_service = response_service or ResponseService()
        self.rag_pipeline_service = rag_pipeline_service or RAGPipelineService(
            chunks=self.chunks,
            retrieval_service=self.retrieval_service,
            response_service=self.response_service,
        )

    def build_citation_map(
        self, chunks: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """Build a citation mapping from chunk list to numerical markers ([1], [2], etc.)."""
        if not chunks:
            return {}

        citation_map = {}
        for idx, chunk in enumerate(chunks, start=1):
            marker = f"[{idx}]"
            meta = (
                chunk.get("metadata")
                if isinstance(chunk.get("metadata"), dict)
                else {}
            )

            source = meta.get("source") if "source" in meta else chunk.get("source")

            chunk_id = meta.get("chunk_id")
            if chunk_id is None:
                chunk_id = meta.get("id")
            if chunk_id is None:
                chunk_id = chunk.get("chunk_id")
            if chunk_id is None:
                chunk_id = chunk.get("id")

            chunk_index = (
                meta.get("chunk_index")
                if "chunk_index" in meta
                else chunk.get("chunk_index")
            )

            section = (
                meta.get("section") if "section" in meta else chunk.get("section")
            )

            text = (
                chunk.get("text")
                or chunk.get("content")
                or meta.get("text")
                or meta.get("content")
                or ""
            )

            citation_map[marker] = {
                "source": source,
                "chunk_id": chunk_id,
                "chunk_index": chunk_index,
                "section": section,
                "text": text,
            }

        return citation_map

    def build_cited_prompt(self, question: str, chunks: List[Dict[str, Any]]) -> str:
        """Build a structured prompt instructing the model to cite provided context chunks."""
        formatted_chunks = []
        for idx, chunk in enumerate(chunks, start=1):
            marker = f"[{idx}]"
            meta = (
                chunk.get("metadata")
                if isinstance(chunk.get("metadata"), dict)
                else {}
            )
            source = meta.get("source") or chunk.get("source") or "Unknown Source"
            text = (
                chunk.get("text")
                or chunk.get("content")
                or meta.get("text")
                or meta.get("content")
                or ""
            )
            formatted_chunks.append(f"{marker} Source: {source}\n{text.strip()}")

        context_text = "\n\n".join(formatted_chunks)

        prompt = (
            "Context:\n"
            f"{context_text}\n\n"
            "Instructions:\n"
            "- Answer using ONLY the provided context.\n"
            "- Cite every factual claim using markers such as [1] or [2].\n"
            "- Only use citation markers that exist in the provided context.\n"
            "- If the context does not support the answer, say there is not enough information.\n"
            "- Never invent citations.\n\n"
            f"Question: {question}"
        )
        return prompt

    def answer_with_citations(
        self,
        question: str,
        chunks: Optional[List[Dict[str, Any]]] = None,
        top_k: int = 4,
    ) -> Dict[str, Any]:
        """Execute end-to-end citation pipeline: retrieve -> build citation map -> build cited prompt -> generate answer."""
        fallback_empty = {
            "answer": "I don't have enough information in the provided context.",
            "citations": {},
        }

        if not question or not question.strip():
            return fallback_empty

        candidate_chunks = chunks if chunks is not None else self.chunks
        if not candidate_chunks:
            return fallback_empty

        retrieved_chunks = self.retrieval_service.retrieve_ranked_chunks(
            question, candidate_chunks, top_k=top_k
        )

        if not retrieved_chunks:
            return fallback_empty

        citations = self.build_citation_map(retrieved_chunks)
        cited_prompt = self.build_cited_prompt(question, retrieved_chunks)
        answer = self._generate_answer(question, retrieved_chunks, cited_prompt)

        if (
            "don't have enough information" in answer.lower()
            or "unable to answer" in answer.lower()
        ):
            return {
                "answer": "I don't have enough information in the provided context.",
                "citations": {},
            }

        return {
            "answer": answer,
            "citations": citations,
        }

    def stream_answer_with_citations(
        self,
        question: str,
        chunks: Optional[List[Dict[str, Any]]] = None,
        top_k: int = 4,
    ):
        """Stream RAG response events progressively (citations -> answer tokens -> done/error)."""
        import re

        if not question or not str(question).strip():
            yield {
                "type": "error",
                "message": "Question is required and cannot be empty.",
            }
            return

        try:
            res = self.answer_with_citations(str(question), chunks=chunks, top_k=top_k)
            citations = res.get("citations", {})

            sources_list = []
            for idx, (marker, meta) in enumerate(citations.items(), start=1):
                chunk_id = meta.get("chunk_id")
                if chunk_id is None:
                    chunk_id = meta.get("id") or f"chunk-{idx}"

                sources_list.append({
                    "id": f"source-{idx}",
                    "label": marker,
                    "document": meta.get("source") or "unknown",
                    "chunk_id": str(chunk_id),
                    "section": meta.get("section") or "",
                    "text": meta.get("text") or "",
                })

            yield {
                "type": "citations",
                "sources": sources_list,
            }

            answer_text = res.get("answer", "")
            if answer_text:
                tokens = re.findall(r"\S+\s*", answer_text)
                for token in tokens:
                    yield {
                        "type": "token",
                        "text": token,
                    }

            yield {
                "type": "done",
            }
        except Exception:
            yield {
                "type": "error",
                "message": "The answer stopped streaming. Please retry.",
            }

    def verify_citation(
        self, result: Dict[str, Any], citation_marker: str
    ) -> Optional[Dict[str, Any]]:
        """Verify whether a citation marker exists in the answer result and return mapped chunk details."""
        if not isinstance(result, dict) or "citations" not in result:
            return None
        citations = result.get("citations")
        if not isinstance(citations, dict):
            return None
        return citations.get(citation_marker)

    def _generate_answer(
        self,
        question: str,
        chunks: List[Dict[str, Any]],
        cited_prompt: str,
    ) -> str:
        """Generate answer using external LLM client if configured, otherwise simulated offline generator."""
        if self.response_service:
            client = getattr(self.response_service, "client", None)
            if client is None and hasattr(self.response_service, "get_client"):
                try:
                    client = self.response_service.get_client()
                except Exception:
                    client = None

            if client:
                try:
                    messages = [
                        {
                            "role": "system",
                            "content": (
                                "You are PolicyPilot, an internal e-commerce chatbot. "
                                "Answer questions using ONLY provided context and cite claims using markers like [1], [2]."
                            ),
                        },
                        {"role": "user", "content": cited_prompt},
                    ]
                    response = client.chat.completions.create(
                        model=self.response_service.model,
                        messages=messages,
                        temperature=0.0,
                    )
                    raw_ans = response.choices[0].message.content.strip()
                    if raw_ans:
                        return raw_ans
                except Exception:
                    pass

        return self._simulate_cited_answer(question, chunks)

    def _simulate_cited_answer(
        self, question: str, chunks: List[Dict[str, Any]]
    ) -> str:
        """Offline simulation helper that constructs grounded answers with citation markers."""
        import re

        q_lower = question.lower()
        q_words = set(re.findall(r"\b\w+\b", q_lower)) - {
            "what", "is", "are", "for", "the", "a", "an", "to", "in", "of", "and", "or",
            "how", "can", "i", "required", "my", "our", "do", "does", "should", "tell", "me", "about"
        }

        matching_sentences = []

        for idx, chunk in enumerate(chunks, start=1):
            marker = f"[{idx}]"
            text = chunk.get("text") or chunk.get("content") or ""
            if not text:
                continue

            text_lower = text.lower()
            if q_words and any(w in text_lower for w in q_words):
                cleaned_text = text.strip()
                first_sentence = cleaned_text.split(".")[0].strip()
                if first_sentence:
                    matching_sentences.append(f"{first_sentence}. {marker}")

        if matching_sentences:
            return " ".join(matching_sentences)

        return "I don't have enough information in the provided context."
