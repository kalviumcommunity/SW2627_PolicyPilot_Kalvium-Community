<<<<<<< HEAD
"""FastAPI entry point for the PolicyPilot RAG pipeline.

The small ``QueryRequestHandler`` below is retained only for legacy unit tests
and scripts; production traffic uses the FastAPI application.
=======
"""Backend API server exposing POST /query and POST /query/stream for the PolicyPilot RAG pipeline.

Usage:
    python -m src.api           (starts HTTP server on port 8000)
    python src/api.py           (same)
>>>>>>> e2a059e (working on frontend)
"""

from __future__ import annotations

import json
import logging
import os
<<<<<<< HEAD
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
=======
import sys
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional

# ── Ensure project root is importable ──────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.services.citation_service import CitationService
from src.services.cache_service import QueryCacheService
from src.services.observability_service import ObservabilityService
from src.services.token_service import get_token_count, estimate_cost
from src.services.document_service import DocumentService
>>>>>>> e2a059e (working on frontend)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


# ── Policy document loader ──────────────────────────────────────────────────────

def load_default_chunks() -> List[Dict[str, Any]]:
<<<<<<< HEAD
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
=======
    """Load all policy documents from the data/ directory and return structured chunks."""
    doc_service = DocumentService()
    policies = ""
    data_dir = PROJECT_ROOT / "data"

    if data_dir.exists():
        for file_path in sorted(data_dir.glob("*.*")):
            if file_path.suffix.lower() in (".txt", ".md", ".pdf", ".html", ".htm"):
                try:
                    txt = doc_service.load_text(file_path)
                    if txt and txt.strip():
                        policies += f"\n\n# {file_path.name}\n{txt}"
                        logger.info("Loaded policy file: %s", file_path.name)
                except Exception as exc:
                    logger.warning("Could not load %s: %s", file_path.name, exc)

    if not policies.strip():
        # Fallback built-in policy chunks if no data files found
        logger.warning("No data files found — using built-in fallback policy chunks.")
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
            {
                "id": "shipping-policy:0",
                "source": "SHIPPING_POLICY",
                "chunk_index": 3,
                "section": "Standard Delivery",
                "text": "Standard delivery takes 4-7 business days. Free shipping on orders above ₹499.",
            },
            {
                "id": "cancel-policy:0",
                "source": "CANCELLATION_POLICY",
                "chunk_index": 4,
                "section": "Order Cancellation",
                "text": "Orders can be cancelled within 1 hour of placement at no charge.",
            },
        ]

    # Split policies text into paragraph-level chunks
    blocks = [b.strip() for b in policies.split("\n\n") if b.strip()]
    chunks = []
    for idx, block in enumerate(blocks):
        lines = block.splitlines()
        first_line = lines[0].strip() if lines else "Policy Guidelines"
        if first_line.startswith("#"):
            section = first_line.lstrip("#").strip()
        elif "POLICY" in first_line.upper() or "SECTION" in first_line.upper():
            section = first_line
        else:
            section = "General Guidelines"
        chunks.append({
            "id": f"policy-doc:{idx}",
            "source": "shopverse_policies.md",
            "chunk_index": idx,
            "section": section,
            "text": block,
        })

    logger.info("Loaded %d policy chunks from data files.", len(chunks))
    return chunks
>>>>>>> e2a059e (working on frontend)


# ── HTTP Request Handler ────────────────────────────────────────────────────────

class QueryRequestHandler(BaseHTTPRequestHandler):
    """Compatibility adapter for the original in-process HTTP-handler tests."""

<<<<<<< HEAD
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
=======
    _citation_service: Optional[CitationService] = None
    _cache_service: Optional[QueryCacheService] = None
    _obs_service: Optional[ObservabilityService] = None

    def log_message(self, format, *args):  # noqa: A002
        logger.info("%s - %s", self.address_string(), format % args)

    @classmethod
    def get_citation_service(cls) -> CitationService:
        if cls._citation_service is None:
            chunks = load_default_chunks()
            cls._citation_service = CitationService(chunks=chunks)
        return cls._citation_service

    @classmethod
    def get_cache_service(cls) -> QueryCacheService:
        if cls._cache_service is None:
            cls._cache_service = QueryCacheService()
        return cls._cache_service

    @classmethod
    def get_obs_service(cls) -> ObservabilityService:
        if cls._obs_service is None:
            cls._obs_service = ObservabilityService()
        return cls._obs_service

    # ── CORS ───────────────────────────────────────────────────────────────────
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    # ── GET /health ────────────────────────────────────────────────────────────
    def do_GET(self):
        if self.path in ("/", "/health"):
            body = json.dumps({"status": "ok", "service": "PolicyPilot RAG API"}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self._cors()
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self._cors()
>>>>>>> e2a059e (working on frontend)
            self.end_headers()
            return
        self.send_response(200)
        self._headers("application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok"}).encode("utf-8"))

<<<<<<< HEAD
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
=======
    # ── POST /query  /query/stream ─────────────────────────────────────────────
    def do_POST(self):
        start_time = time.time()
        obs = self.get_obs_service()
        cache = self.get_cache_service()
        req_id = obs.generate_request_id()

        # Route check
        if self.path not in ("/query", "/query/stream"):
            self._json_error(404, "Endpoint not found")
            return

        # Parse body
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            self._json_error(400, "Question is required and cannot be empty.")
            return

        try:
            body = json.loads(self.rfile.read(content_length).decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._json_error(400, "Invalid JSON payload")
            return

        question = body.get("question") if isinstance(body, dict) else None
        if not question or not str(question).strip():
            self._json_error(400, "Question is required and cannot be empty.")
            return

        q = str(question).strip()
        citation_svc = self.get_citation_service()

        # ── Streaming path ─────────────────────────────────────────────────────
        if self.path == "/query/stream":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self._cors()
            self.end_headers()
            try:
                for event in citation_svc.stream_answer_with_citations(q):
                    line = f"data: {json.dumps(event)}\n\n".encode("utf-8")
                    self.wfile.write(line)
                    try:
                        self.wfile.flush()
                    except Exception:
                        pass
            except Exception as exc:
                logger.exception("Streaming error: %s", exc)
            return

        # ── Non-streaming path: check cache ────────────────────────────────────
        cached = cache.get(q)
        if cached is not None:
            latency = (time.time() - start_time) * 1000
            resp = {
                "answer": cached.get("answer", ""),
                "citations": cached.get("citations", {}),
                "sources": cached.get("sources", []),
                "usage": {"cache_hit": True, "latency_ms": round(latency, 2)},
            }
            obs.log_request(
                question=q, answer=cached.get("answer", ""),
                sources=cached.get("sources", []), cache_hit=True,
                input_tokens=0, output_tokens=0, estimated_cost=0.0,
                latency_ms=latency, request_id=req_id,
            )
            self._json_ok(resp)
            return

        # ── Non-streaming path: RAG pipeline ──────────────────────────────────
        try:
            res = citation_svc.answer_with_citations(q)
        except Exception as exc:
            logger.exception("RAG pipeline error: %s", exc)
            self._json_error(500, "The RAG pipeline could not process the question.")
            return

        citations = res.get("citations", {})
        sources = [
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
        answer = res.get("answer", "")
        input_tokens = get_token_count(q) + sum(
            get_token_count(str(s.get("text") or "")) for s in sources
        )
        output_tokens = get_token_count(answer)
        cost = estimate_cost(input_tokens, output_tokens).get("total_cost", 0.0)
        latency = (time.time() - start_time) * 1000

        payload = {"answer": answer, "citations": citations, "sources": sources}
        cache.set(q, payload)

        obs.log_request(
            question=q, answer=answer, sources=sources, cache_hit=False,
            input_tokens=input_tokens, output_tokens=output_tokens,
            estimated_cost=cost, latency_ms=latency, request_id=req_id,
        )

        self._json_ok({
            **payload,
            "usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "estimated_cost": cost,
                "cache_hit": False,
                "latency_ms": round(latency, 2),
            },
        })

    # ── Helpers ────────────────────────────────────────────────────────────────
    def _json_ok(self, data: dict):
        body = json.dumps(data).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def _json_error(self, code: int, message: str):
        body = json.dumps({"error": message}).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self._cors()
        self.end_headers()
        self.wfile.write(body)


# ── Server entrypoint ───────────────────────────────────────────────────────────

def run_server(host: str = "0.0.0.0", port: int = 8000):
    """Start the PolicyPilot HTTP API server."""
    server = HTTPServer((host, port), QueryRequestHandler)
    logger.info("PolicyPilot RAG API listening at http://%s:%d/query", host, port)
    logger.info("Policy data loaded from: %s", PROJECT_ROOT / "data")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down server.")
        server.server_close()


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    run_server(port=port)
>>>>>>> e2a059e (working on frontend)
