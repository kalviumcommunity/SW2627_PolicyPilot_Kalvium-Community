"""Offline unit tests for backend API POST /query endpoint."""

import json
import pytest
from io import BytesIO
from src.api import QueryRequestHandler


class DummyWfile:
    """Mock wfile object to capture HTTP response bytes."""

    def __init__(self):
        self.bytes_written = bytearray()

    def write(self, b: bytes):
        self.bytes_written.extend(b)

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
