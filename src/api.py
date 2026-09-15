"""Backend API server exposing POST /query and POST /query/stream for the PolicyPilot RAG pipeline.

Usage:
    python -m src.api           (starts HTTP server on port 8000)
    python src/api.py           (same)
"""

from __future__ import annotations

import json
import logging
import os
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

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


# ── Policy document loader ──────────────────────────────────────────────────────

def load_default_chunks() -> List[Dict[str, Any]]:
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


# ── HTTP Request Handler ────────────────────────────────────────────────────────

class QueryRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for PolicyPilot RAG API endpoints."""

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
            self.end_headers()

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
