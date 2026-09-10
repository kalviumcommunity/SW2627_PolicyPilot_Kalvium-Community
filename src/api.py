"""HTTP API for the PolicyPilot retrieval-augmented generation pipeline."""

from __future__ import annotations

import logging
import os
import time
from functools import lru_cache
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.services.response_service import ResponseService
from src.services.retrieval_service import RetrievalService

load_dotenv()

logger = logging.getLogger(__name__)

app = FastAPI(
    title="PolicyPilot RAG API",
    description="Ask questions against the PolicyPilot policy knowledge base.",
    version="1.0.0",
)


class QueryRequest(BaseModel):
    """Request body accepted by the query endpoint."""

    question: str = Field(..., min_length=1, max_length=2000, description="Policy question")
    top_k: Optional[int] = Field(default=None, ge=1, le=10, description="Number of chunks to retrieve")


class Source(BaseModel):
    """A grounded source returned with an answer."""

    document: str
    score: float
    chunks: List[int]


@lru_cache(maxsize=1)
def get_pipeline() -> tuple[RetrievalService, ResponseService]:
    """Create the pipeline once per process using environment-based configuration."""
    return RetrievalService(), ResponseService(model=os.getenv("CHAT_MODEL"))


def _sources_from_chunks(chunks: List[Dict[str, Any]]) -> List[Source]:
    """Convert retrieved chunks into deduplicated, frontend-friendly source records."""
    grouped: Dict[str, Source] = {}
    for chunk in chunks:
        document = str(chunk.get("source", "unknown"))
        source = grouped.get(document)
        chunk_index = int(chunk.get("chunk_index", 0))
        score = float(chunk.get("score", 0.0))
        if source is None:
            grouped[document] = Source(document=document, score=score, chunks=[chunk_index])
        else:
            source.score = max(source.score, score)
            if chunk_index not in source.chunks:
                source.chunks.append(chunk_index)
    return list(grouped.values())


@app.get("/health")
def health() -> Dict[str, str]:
    """Return a lightweight liveness response."""
    return {"status": "ok"}


@app.post("/query")
def query(request: QueryRequest) -> Dict[str, Any]:
    """Run retrieval and grounded response generation for a policy question."""
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=422, detail="question must not be blank")

    top_k = request.top_k or int(os.getenv("RAG_TOP_K", "3"))
    started = time.perf_counter()

    try:
        retrieval_service, response_service = get_pipeline()
        chunks = retrieval_service.search(question, top_k=top_k)
        result = response_service.generate(question, context_chunks=chunks)
    except Exception:
        logger.exception("RAG query failed")
        raise HTTPException(
            status_code=500,
            detail="The RAG pipeline could not process the question.",
        ) from None

    answer = str(result.get("generated_answer", "")).strip()
    is_fallback = bool(result.get("is_fallback", False))
    return {
        "status": "fallback" if is_fallback else "success",
        "question": question,
        "answer": answer,
        "sources": [source.model_dump() for source in _sources_from_chunks(result.get("context_chunks", []))],
        "metadata": {
            "model": response_service.model,
            "top_k": top_k,
            "retrieved_chunks": len(result.get("context_chunks", [])),
            "is_fallback": is_fallback,
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api:app",
        host=os.getenv("API_HOST", "127.0.0.1"),
        port=int(os.getenv("API_PORT", "8000")),
        reload=False,
    )
