"""Backend API server exposing POST /query endpoint for PolicyPilot."""

import json
import os
import sys
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any, Dict, Optional, List

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.services.document_service import DocumentService
from src.services.citation_service import CitationService


def load_default_chunks() -> List[Dict[str, Any]]:
    """Load default policy documents and split into structured candidate chunks."""
    doc_service = DocumentService("data")
    policies = doc_service.load_documents()

    if not policies:
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

    @classmethod
    def get_citation_service(cls) -> CitationService:
        """Lazily initialize and return shared CitationService instance."""
        if cls.citation_service is None:
            chunks = load_default_chunks()
            cls.citation_service = CitationService(chunks=chunks)
        return cls.citation_service

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
        if self.path not in ("/query", "/query/stream"):
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode("utf-8"))
            return

        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Question is required and cannot be empty."}).encode("utf-8"))
            return

        raw_body = self.rfile.read(content_length)
        try:
            body = json.loads(raw_body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Invalid JSON payload"}).encode("utf-8"))
            return

        question = body.get("question") if isinstance(body, dict) else None
        if not question or not str(question).strip():
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Question is required and cannot be empty."}).encode("utf-8"))
            return

        citation_svc = self.get_citation_service()

        if self.path == "/query/stream":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self._set_cors_headers()
            self.end_headers()

            for event in citation_svc.stream_answer_with_citations(str(question)):
                sse_line = f"data: {json.dumps(event)}\n\n"
                self.wfile.write(sse_line.encode("utf-8"))
                if hasattr(self.wfile, "flush"):
                    try:
                        self.wfile.flush()
                    except Exception:
                        pass
            return

        # Execute citation RAG pipeline for non-streaming /query
        res = citation_svc.answer_with_citations(str(question))

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

        response_data = {
            "answer": res.get("answer", ""),
            "citations": citations,
            "sources": sources_list,
        }

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
