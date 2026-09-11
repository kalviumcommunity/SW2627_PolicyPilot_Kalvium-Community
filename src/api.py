"""FastAPI entry point for the PolicyPilot RAG pipeline.

The small ``QueryRequestHandler`` below is retained only for legacy unit tests
and scripts; production traffic uses the FastAPI application.
"""

from __future__ import annotations

import json
import logging
import os
import time
from functools import lru_cache
from http.server import BaseHTTPRequestHandler
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from src.services.cache_service import QueryCacheService
from src.services.citation_service import CitationService
from src.services.document_service import DocumentService
from src.services.response_service import (
    FALLBACK_REFUSAL_MESSAGE,
    SAFE_REFUSAL_MESSAGE,
    ResponseService,
)
from src.services.retrieval_service import RetrievalService
from src.services.token_service import estimate_cost, get_token_count

load_dotenv()
logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[1]

app = FastAPI(title="PolicyPilot RAG API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    top_k: Optional[int] = Field(default=None, ge=1, le=10)


def _source_records(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[str, Dict[str, Any]] = {}
    for chunk in chunks:
        metadata = chunk.get("metadata") if isinstance(chunk.get("metadata"), dict) else {}
        document = str(chunk.get("source") or metadata.get("source") or "unknown")
        index = int(chunk.get("chunk_index", metadata.get("chunk_index", 0)))
        record = grouped.setdefault(document, {
            "document": document, "score": float(chunk.get("score", 0.0)), "chunks": [],
        })
        record["score"] = max(record["score"], float(chunk.get("score", 0.0)))
        if index not in record["chunks"]:
            record["chunks"].append(index)
    return list(grouped.values())


@lru_cache(maxsize=1)
def get_pipeline() -> tuple[RetrievalService, ResponseService]:
    retrieval = RetrievalService()
    return retrieval, ResponseService(retrieval_service=retrieval, model=os.getenv("CHAT_MODEL"))


def _retrieve(retrieval: RetrievalService, question: str, top_k: int) -> List[Dict[str, Any]]:
    try:
        return retrieval.search(question, top_k=top_k, hybrid=True, alpha=0.4)
    except TypeError:
        return retrieval.search(question, top_k=top_k)


def _generate(response: ResponseService, question: str, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    result = response.generate(question, chunks)
    if isinstance(result, str):
        is_fallback = result in {SAFE_REFUSAL_MESSAGE, FALLBACK_REFUSAL_MESSAGE}
        return {
            "generated_answer": result,
            "context_chunks": [] if is_fallback else chunks,
            "is_fallback": is_fallback,
        }
    return result if isinstance(result, dict) else {
        "generated_answer": str(result),
        "context_chunks": chunks,
        "is_fallback": str(result) == "I don't have enough reliable context to answer that.",
    }


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "service": "PolicyPilot RAG API"}


@app.post("/query")
def query(request: QueryRequest) -> Dict[str, Any]:
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=422, detail="question must not be blank")
    top_k = request.top_k or int(os.getenv("RAG_TOP_K", "4"))
    started = time.perf_counter()
    try:
        retrieval, response = get_pipeline()
        chunks = _retrieve(retrieval, question, top_k)
        result = _generate(response, question, chunks)
    except Exception:
        logger.exception("RAG query failed")
        raise HTTPException(status_code=500, detail="The RAG pipeline could not process the question.") from None
    context = result.get("context_chunks", chunks)
    answer = str(result.get("generated_answer", "")).strip()
    fallback = bool(result.get("is_fallback", False))
    return {
        "status": "fallback" if fallback else "success",
        "question": question,
        "answer": answer,
        "sources": _source_records(context),
        "metadata": {
            "model": response.model,
            "top_k": top_k,
            "retrieved_chunks": len(context),
            "is_fallback": fallback,
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
        },
    }


@app.post("/query/stream")
def query_stream(request: QueryRequest) -> StreamingResponse:
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=422, detail="question must not be blank")

    def events():
        try:
            retrieval, response = get_pipeline()
            chunks = _retrieve(retrieval, question, request.top_k or 4)
            result = _generate(response, question, chunks)
            yield f"data: {json.dumps({'type': 'citations', 'sources': _source_records(chunks)})}\n\n"
            for token in str(result.get("generated_answer", "")).split():
                yield f"data: {json.dumps({'type': 'token', 'text': token + ' '})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except Exception:
            logger.exception("Streaming RAG query failed")
            yield f"data: {json.dumps({'type': 'error', 'message': 'The answer stopped streaming. Please retry.'})}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream")


def load_default_chunks() -> List[Dict[str, Any]]:
    """Load current policy files for the legacy handler."""
    documents = DocumentService().load_and_chunk_documents(data_dir=str(PROJECT_ROOT / "data"))
    return [
        {
            **chunk,
            "id": f"{chunk.get('source', 'document')}:{chunk.get('index', index)}",
            "text": chunk.get("text", ""),
        }
        for index, chunk in enumerate(documents)
    ]


class QueryRequestHandler(BaseHTTPRequestHandler):
    """Compatibility adapter for the original in-process HTTP-handler tests."""

    citation_service: Optional[CitationService] = None
    cache_service: Optional[QueryCacheService] = None

    def log_request(self, *args: Any, **kwargs: Any) -> None:
        """Avoid socket logging assumptions when used as an in-process adapter."""
        return None

    @classmethod
    def get_citation_service(cls) -> CitationService:
        if cls.citation_service is None:
            cls.citation_service = CitationService(chunks=load_default_chunks())
        return cls.citation_service

    @classmethod
    def get_cache_service(cls) -> QueryCacheService:
        if cls.cache_service is None:
            cls.cache_service = QueryCacheService()
        return cls.cache_service

    def _headers(self, content_type: str) -> None:
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self) -> None:
        if self.path not in ("/", "/health"):
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(200)
        self._headers("application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok"}).encode("utf-8"))

    def do_POST(self) -> None:
        if self.path not in ("/query", "/query/stream"):
            self.send_response(404)
            self._headers("application/json")
            self.end_headers()
            self.wfile.write(b'{"error":"Endpoint not found"}')
            return
        length = int(self.headers.get("Content-Length", 0))
        try:
            body = json.loads(self.rfile.read(length).decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            body = {}
        question = str(body.get("question", "")).strip() if isinstance(body, dict) else ""
        if not question:
            self.send_response(400)
            self._headers("application/json")
            self.end_headers()
            self.wfile.write(b'{"error":"Question is required and cannot be empty."}')
            return

        service = self.get_citation_service()
        if self.path == "/query/stream":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            for event in service.stream_answer_with_citations(question):
                self.wfile.write(f"data: {json.dumps(event)}\n\n".encode("utf-8"))
            return

        cache = self.get_cache_service()
        cached = cache.get(question)
        if cached is None:
            result = service.answer_with_citations(question)
            sources = []
            for marker, citation in result.get("citations", {}).items():
                sources.append({
                    "source": citation.get("source", "unknown"),
                    "text": citation.get("text", ""),
                    "citation": marker,
                })
            cached = {"answer": result.get("answer", ""), "citations": result.get("citations", {}), "sources": sources}
            cache.set(question, cached)
            cache_hit = False
        else:
            cache_hit = True
        answer = cached.get("answer", "")
        input_tokens = 0 if cache_hit else get_token_count(question)
        output_tokens = 0 if cache_hit else get_token_count(answer)
        usage = {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "estimated_cost": (
                {"total_cost": 0.0}
                if cache_hit
                else estimate_cost(input_tokens, output_tokens)
            ),
            "cache_hit": cache_hit,
        }
        payload = {**cached, "usage": usage}
        self.send_response(200)
        self._headers("application/json")
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode("utf-8"))


def create_mock_handler(method: str, path: str, body: Optional[dict] = None, headers: Optional[dict] = None):
    """Create a handler instance for legacy tests without opening a socket."""
    handler = QueryRequestHandler.__new__(QueryRequestHandler)
    raw = json.dumps(body).encode("utf-8") if body is not None else b""
    handler.rfile = BytesIO(raw)
    handler.wfile = BytesIO()
    handler.headers = {"Content-Length": str(len(raw)), **(headers or {})}
    handler.path = path
    handler.command = method
    handler.response_code = None
    handler.response_headers = {}

    def send_response(code: int, message: Optional[str] = None) -> None:
        handler.response_code = code

    def send_header(name: str, value: str) -> None:
        handler.response_headers[name] = value

    handler.send_response = send_response
    handler.send_header = send_header
    handler.end_headers = lambda: None
    return handler


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api:app", host=os.getenv("API_HOST", "127.0.0.1"), port=int(os.getenv("API_PORT", "8000")))
