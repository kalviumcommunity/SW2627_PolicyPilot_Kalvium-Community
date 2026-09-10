"""HTTP API for the PolicyPilot retrieval-augmented generation pipeline."""

from __future__ import annotations

import logging
import os
import time
import inspect
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.services.response_service import ResponseService
from src.services.retrieval_service import RetrievalService
from src.services.document_service import DocumentService

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
        metadata = chunk.get("metadata", {})
        if not isinstance(metadata, dict):
            metadata = {}
        document = str(chunk.get("source") or metadata.get("source") or chunk.get("id", "unknown"))
        source = grouped.get(document)
        chunk_index = int(chunk.get("chunk_index", metadata.get("chunk_index", 0)))
        score = float(chunk.get("score", 0.0))
        if source is None:
            grouped[document] = Source(document=document, score=score, chunks=[chunk_index])
        else:
            source.score = max(source.score, score)
            if chunk_index not in source.chunks:
                source.chunks.append(chunk_index)
    return list(grouped.values())


def _generate_response(
    response_service: ResponseService,
    question: str,
    chunks: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Generate an answer across the supported response service interfaces."""
    generate_parameters = inspect.signature(response_service.generate).parameters
    if "context_chunks" in generate_parameters:
        result = response_service.generate(question, context_chunks=chunks)
        if isinstance(result, dict):
            return result
        return {
            "generated_answer": str(result),
            "context_chunks": chunks,
            "is_fallback": False,
        }

    answer = response_service.generate(question, chunks)
    return {
        "generated_answer": str(answer),
        "context_chunks": chunks,
        "is_fallback": not bool(answer),
    }


def _retrieve_chunks(
    retrieval_service: RetrievalService,
    question: str,
    top_k: int,
) -> List[Dict[str, Any]]:
    """Retrieve chunks across the supported retrieval service interfaces."""
    try:
        search = getattr(retrieval_service, "search", None)
        if callable(search):
            chunks = search(question, top_k=top_k)
        else:
            retrieve = getattr(retrieval_service, "retrieve", None)
            if not callable(retrieve):
                raise AttributeError("RetrievalService must provide search or retrieve.")
            chunks = retrieve(question, k=top_k)
        if chunks:
            return chunks
    except (AttributeError, RuntimeError, ValueError) as exc:
        logger.warning("Primary retrieval unavailable (%s); using document fallback.", exc)

    return _retrieve_from_documents(question, top_k)


def _retrieve_from_documents(question: str, top_k: int) -> List[Dict[str, Any]]:
    """Provide lexical retrieval when generated/vector indexes are unavailable."""
    query_terms = set(re.findall(r"\b\w+\b", question.lower()))
    documents = DocumentService().load_and_chunk_documents(
        data_dir=str(Path(__file__).resolve().parents[1] / "data")
    )
    ranked: List[Dict[str, Any]] = []
    for index, chunk in enumerate(documents):
        text = chunk.get("text") or chunk.get("content") or ""
        terms = set(re.findall(r"\b\w+\b", text.lower()))
        score = len(query_terms & terms) / max(1, len(query_terms))
        if score <= 0:
            continue
        ranked.append({
            "id": chunk.get("chunk_id", f"fallback-{index}"),
            "score": score,
            "text": text,
            "content": text,
            "source": chunk.get("source", "unknown"),
            "chunk_index": chunk.get("index", index),
            "metadata": {"source": chunk.get("source", "unknown"), "chunk_index": chunk.get("index", index)},
        })
    ranked.sort(key=lambda item: item["score"], reverse=True)
    return ranked[:top_k]


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
        chunks = _retrieve_chunks(retrieval_service, question, top_k)
        result = _generate_response(response_service, question, chunks)
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
"""Backend API server exposing POST /query and POST /query/stream endpoints for PolicyPilot."""

import json
import os
import sys
import time
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any, Dict, Optional, List

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.services.document_service import DocumentService
from src.services.citation_service import CitationService
from src.services.cache_service import QueryCacheService
from src.services.observability_service import ObservabilityService
from src.services.token_service import get_token_count, estimate_cost


def load_default_chunks() -> List[Dict[str, Any]]:
    """Load default policy documents and split into structured candidate chunks."""
    doc_service = DocumentService()

    policies = ""
    data_dir = PROJECT_ROOT / "data"
    if data_dir.exists():
        for file_path in data_dir.glob("*.*"):
            if file_path.suffix.lower() in (".txt", ".md", ".pdf", ".html", ".htm"):
                try:
                    txt = doc_service.load_text(file_path)
                    if txt:
                        policies += f"\n\n# {file_path.name}\n{txt}"
                except Exception:
                    pass

    if not policies or not policies.strip():
        # Fallback sample policy chunks if data files are missing
        return [
            {
                "id": "return-policy:0",
                "source": "RETURN_AND_REFUND_POLICY",
                "chunk_index": 0,
                "section": "Return Window",
                "text": "Customers can request a refund for eligible catalog items within 30 days of delivery.",
            },
            {
                "id": "return-policy:1",
                "source": "RETURN_AND_REFUND_POLICY",
                "chunk_index": 1,
                "section": "Damaged Products",
                "text": "Damaged products must be reported within 48 hours of delivery to initiate a return.",
            },
            {
                "id": "seller-policy:0",
                "source": "SELLER_RESPONSIBILITIES_POLICY",
                "chunk_index": 2,
                "section": "Dispatch SLAs",
                "text": "Sellers are required to dispatch ordered items within 2 business days.",
            },
        ]

    # Convert text policies into chunk dictionaries for citation service
    blocks = [b.strip() for b in policies.split("\n\n") if b.strip()]
    chunks = []
    for idx, block in enumerate(blocks):
        lines = block.splitlines()
        first_line = lines[0].strip() if lines else "Policy Guidelines"
        section = first_line.replace("#", "").strip() if first_line.startswith("#") or "POLICY" in first_line else "General Guidelines"
        chunks.append({
            "id": f"policy-doc:{idx}",
            "source": "official_ecommerce_policies.txt",
            "chunk_index": idx,
            "section": section,
            "text": block,
        })
    return chunks


class QueryRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for PolicyPilot RAG API endpoints."""

    citation_service: Optional[CitationService] = None
    cache_service: Optional[QueryCacheService] = None
    observability_service: Optional[ObservabilityService] = None

    @classmethod
    def get_citation_service(cls) -> CitationService:
        """Lazily initialize and return shared CitationService instance."""
        if cls.citation_service is None:
            chunks = load_default_chunks()
            cls.citation_service = CitationService(chunks=chunks)
        return cls.citation_service

    @classmethod
    def get_cache_service(cls) -> QueryCacheService:
        """Lazily initialize and return shared QueryCacheService instance."""
        if cls.cache_service is None:
            cls.cache_service = QueryCacheService()
        return cls.cache_service

    @classmethod
    def get_observability_service(cls) -> ObservabilityService:
        """Lazily initialize and return shared ObservabilityService instance."""
        if cls.observability_service is None:
            cls.observability_service = ObservabilityService()
        return cls.observability_service

    def _set_cors_headers(self):
        """Set CORS headers on the HTTP response."""
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(204)
        self._set_cors_headers()
        self.end_headers()

    def do_GET(self):
        """Handle health check endpoint."""
        if self.path in ("/", "/health"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._set_cors_headers()
            self.end_headers()
            response_body = json.dumps({
                "status": "ok",
                "service": "PolicyPilot RAG API",
            }).encode("utf-8")
            self.wfile.write(response_body)
        else:
            self.send_response(404)
            self._set_cors_headers()
            self.end_headers()

    def do_POST(self):
        """Handle POST /query and POST /query/stream endpoints."""
        start_time = time.time()
        obs_svc = self.get_observability_service()
        cache_svc = self.get_cache_service()
        req_id = obs_svc.generate_request_id()

        if self.path not in ("/query", "/query/stream"):
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode("utf-8"))
            return

        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            err_msg = "Question is required and cannot be empty."
            obs_svc.log_request(
                question="",
                error=err_msg,
                latency_ms=(time.time() - start_time) * 1000.0,
                request_id=req_id,
            )
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"error": err_msg}).encode("utf-8"))
            return

        raw_body = self.rfile.read(content_length)
        try:
            body = json.loads(raw_body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            err_msg = "Invalid JSON payload"
            obs_svc.log_request(
                question="",
                error=err_msg,
                latency_ms=(time.time() - start_time) * 1000.0,
                request_id=req_id,
            )
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"error": err_msg}).encode("utf-8"))
            return

        question = body.get("question") if isinstance(body, dict) else None
        if not question or not str(question).strip():
            err_msg = "Question is required and cannot be empty."
            obs_svc.log_request(
                question=str(question or ""),
                error=err_msg,
                latency_ms=(time.time() - start_time) * 1000.0,
                request_id=req_id,
            )
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"error": err_msg}).encode("utf-8"))
            return

        q_str = str(question).strip()
        citation_svc = self.get_citation_service()

        if self.path == "/query/stream":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self._set_cors_headers()
            self.end_headers()

            for event in citation_svc.stream_answer_with_citations(q_str):
                sse_line = f"data: {json.dumps(event)}\n\n"
                self.wfile.write(sse_line.encode("utf-8"))
                if hasattr(self.wfile, "flush"):
                    try:
                        self.wfile.flush()
                    except Exception:
                        pass
            return

        # Check query cache for non-streaming /query
        cached_res = cache_svc.get(q_str)
        if cached_res is not None:
            latency_ms = (time.time() - start_time) * 1000.0
            usage_data = {
                "input_tokens": 0,
                "output_tokens": 0,
                "estimated_cost": 0.0,
                "cache_hit": True,
                "latency_ms": round(latency_ms, 2),
            }
            response_data = {
                "answer": cached_res.get("answer", ""),
                "citations": cached_res.get("citations", {}),
                "sources": cached_res.get("sources", []),
                "usage": usage_data,
            }
            obs_svc.log_request(
                question=q_str,
                answer=cached_res.get("answer", ""),
                sources=cached_res.get("sources", []),
                cache_hit=True,
                input_tokens=0,
                output_tokens=0,
                estimated_cost=0.0,
                latency_ms=latency_ms,
                request_id=req_id,
            )
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode("utf-8"))
            return

        # Execute citation RAG pipeline on cache miss
        res = citation_svc.answer_with_citations(q_str)

        citations = res.get("citations", {})
        sources_list = [
            {
                "marker": marker,
                "source": meta.get("source"),
                "chunk_id": meta.get("chunk_id"),
                "chunk_index": meta.get("chunk_index"),
                "section": meta.get("section"),
                "text": meta.get("text"),
            }
            for marker, meta in citations.items()
        ]

        answer_text = res.get("answer", "")

        # Usage and cost calculations
        input_tokens = get_token_count(q_str) + sum(
            get_token_count(str(s.get("text") or "")) for s in sources_list
        )
        output_tokens = get_token_count(answer_text)
        cost_dict = estimate_cost(input_tokens, output_tokens)
        total_cost = cost_dict.get("total_cost", 0.0)

        latency_ms = (time.time() - start_time) * 1000.0

        # Save successful result in cache
        cached_payload = {
            "answer": answer_text,
            "citations": citations,
            "sources": sources_list,
        }
        cache_svc.set(q_str, cached_payload)

        usage_data = {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "estimated_cost": total_cost,
            "cache_hit": False,
            "latency_ms": round(latency_ms, 2),
        }

        response_data = {
            "answer": answer_text,
            "citations": citations,
            "sources": sources_list,
            "usage": usage_data,
        }

        obs_svc.log_request(
            question=q_str,
            answer=answer_text,
            sources=sources_list,
            cache_hit=False,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost=total_cost,
            latency_ms=latency_ms,
            request_id=req_id,
        )

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self._set_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(response_data).encode("utf-8"))


class DummyWfile:
    """Mock wfile object to capture HTTP response bytes for offline handler testing."""

    def __init__(self):
        self.bytes_written = bytearray()

    def write(self, b: bytes):
        self.bytes_written.extend(b)

    def flush(self):
        pass

    def getvalue(self) -> bytes:
        return bytes(self.bytes_written)


def create_mock_handler(method: str, path: str, body: dict = None, headers: dict = None):
    """Helper to instantiate and invoke QueryRequestHandler with mock request data."""
    from io import BytesIO

    handler = QueryRequestHandler.__new__(QueryRequestHandler)

    body_bytes = json.dumps(body).encode("utf-8") if body is not None else b""
    handler.rfile = BytesIO(body_bytes)
    handler.wfile = DummyWfile()

    req_headers = {"Content-Length": str(len(body_bytes))}
    if headers:
        req_headers.update(headers)
    handler.headers = req_headers

    handler.path = path
    handler.command = method

    handler.response_code = None
    handler.response_headers = {}

    def mock_send_response(code, message=None):
        handler.response_code = code

    def mock_send_header(keyword, value):
        handler.response_headers[keyword] = value

    def mock_end_headers():
        pass

    handler.send_response = mock_send_response
    handler.send_header = mock_send_header
    handler.end_headers = mock_end_headers

    return handler


def run_server(host: str = "0.0.0.0", port: int = 8000):
    """Run the PolicyPilot API HTTP server."""
    server_address = (host, port)
    httpd = HTTPServer(server_address, QueryRequestHandler)
    print(f"PolicyPilot RAG API Server listening at http://{host}:{port}/query")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down API server...")
        httpd.server_close()


if __name__ == "__main__":
    port_env = int(os.getenv("PORT", "8000"))
    run_server(port=port_env)
