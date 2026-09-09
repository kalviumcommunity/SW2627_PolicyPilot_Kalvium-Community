import json
import sys
from pathlib import Path
import pytest
from io import BytesIO

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.api import QueryRequestHandler


class DummyWfile:
    """Mock wfile object to capture HTTP response bytes."""

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

    # Header capture
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


def test_post_query_success():
    handler = create_mock_handler("POST", "/query", body={"question": "What is the return period?"})
    handler.do_POST()

    assert handler.response_code == 200
    assert handler.response_headers.get("Content-Type") == "application/json"
    assert handler.response_headers.get("Access-Control-Allow-Origin") == "*"

    res_body = json.loads(handler.wfile.getvalue().decode("utf-8"))
    assert "answer" in res_body
    assert "citations" in res_body
    assert "sources" in res_body
    assert "usage" in res_body
    assert isinstance(res_body["sources"], list)

    if res_body["sources"]:
        src = res_body["sources"][0]
        assert "source" in src
        assert "text" in src


def test_post_query_empty_question():
    handler = create_mock_handler("POST", "/query", body={"question": "   "})
    handler.do_POST()

    assert handler.response_code == 400
    res_body = json.loads(handler.wfile.getvalue().decode("utf-8"))
    assert "error" in res_body
    assert "required" in res_body["error"].lower()


def test_options_query_cors():
    handler = create_mock_handler("OPTIONS", "/query")
    handler.do_OPTIONS()

    assert handler.response_code == 204
    assert handler.response_headers.get("Access-Control-Allow-Origin") == "*"
    assert "POST" in handler.response_headers.get("Access-Control-Allow-Methods", "")


def test_get_health():
    handler = create_mock_handler("GET", "/health")
    handler.do_GET()

    assert handler.response_code == 200
    res_body = json.loads(handler.wfile.getvalue().decode("utf-8"))
    assert res_body["status"] == "ok"


def test_post_query_caching_and_usage():
    # Clear cache before test
    cache_svc = QueryRequestHandler.get_cache_service()
    cache_svc.clear()

    q_text = "What is the dispatch SLA for sellers?"

    # First request: Cache Miss
    h1 = create_mock_handler("POST", "/query", body={"question": q_text})
    h1.do_POST()

    assert h1.response_code == 200
    res1 = json.loads(h1.wfile.getvalue().decode("utf-8"))
    assert "usage" in res1
    assert res1["usage"]["cache_hit"] is False
    assert res1["usage"]["input_tokens"] >= 0
    assert res1["usage"]["output_tokens"] >= 0

    # Second request with different casing/whitespace: Cache Hit
    h2 = create_mock_handler("POST", "/query", body={"question": f"   {q_text.upper()}   "})
    h2.do_POST()

    assert h2.response_code == 200
    res2 = json.loads(h2.wfile.getvalue().decode("utf-8"))
    assert "usage" in res2
    assert res2["usage"]["cache_hit"] is True
    assert res2["usage"]["input_tokens"] == 0
    assert res2["usage"]["output_tokens"] == 0
    assert res1["answer"] == res2["answer"]
