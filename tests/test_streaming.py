import json
import sys
from pathlib import Path
import pytest

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.api import QueryRequestHandler, create_mock_handler
from src.services.citation_service import CitationService


def parse_sse_events(raw_bytes: bytes):
    """Utility to parse SSE string response into list of JSON event dicts."""
    text = raw_bytes.decode("utf-8")
    blocks = text.split("\n\n")
    events = []
    for block in blocks:
        lines = [line.strip() for line in block.split("\n") if line.strip()]
        for line in lines:
            if line.startswith("data:"):
                json_str = line[5:].strip()
                if json_str:
                    events.append(json.loads(json_str))
    return events


def test_post_query_stream_success():
    handler = create_mock_handler(
        "POST", "/query/stream", body={"question": "What is the return period?"}
    )
    handler.do_POST()

    assert handler.response_code == 200
    assert handler.response_headers.get("Content-Type") == "text/event-stream"
    assert handler.response_headers.get("Access-Control-Allow-Origin") == "*"

    events = parse_sse_events(handler.wfile.getvalue())
    assert len(events) >= 3  # citations, token(s), done

    event_types = [e.get("type") for e in events]
    assert "citations" in event_types
    assert "token" in event_types
    assert "done" in event_types

    # First event should be citations
    citations_event = events[0]
    assert citations_event["type"] == "citations"
    assert "sources" in citations_event
    assert isinstance(citations_event["sources"], list)

    if citations_event["sources"]:
        src = citations_event["sources"][0]
        assert "id" in src
        assert "label" in src
        assert "document" in src
        assert "chunk_id" in src
        assert "section" in src
        assert "text" in src

    # Verify done event is last
    assert events[-1]["type"] == "done"


def test_post_query_stream_empty_question():
    handler = create_mock_handler("POST", "/query/stream", body={"question": "   "})
    handler.do_POST()

    assert handler.response_code == 400
    res_body = json.loads(handler.wfile.getvalue().decode("utf-8"))
    assert "error" in res_body
    assert "required" in res_body["error"].lower()


def test_citation_service_stream_generator_empty_question():
    svc = CitationService()
    events = list(svc.stream_answer_with_citations(""))

    assert len(events) == 1
    assert events[0]["type"] == "error"
    assert "empty" in events[0]["message"].lower()


def test_citation_service_stream_generator_error_handling(monkeypatch):
    svc = CitationService()

    def mock_answer_failure(*args, **kwargs):
        raise RuntimeError("Simulated LLM pipeline failure")

    monkeypatch.setattr(svc, "answer_with_citations", mock_answer_failure)

    events = list(svc.stream_answer_with_citations("What is the return policy?"))
    assert len(events) == 1
    assert events[0]["type"] == "error"
    assert "stopped streaming" in events[0]["message"]


def test_citation_service_stream_preserves_metadata():
    custom_chunks = [
        {
            "id": "policy-chunk-99",
            "source": "REFUND_DOC.md",
            "chunk_index": 5,
            "section": "Eligibility Criteria",
            "text": "Eligible catalog items can be returned within 30 days.",
        }
    ]
    svc = CitationService(chunks=custom_chunks)
    events = list(svc.stream_answer_with_citations("Can I return catalog items?", chunks=custom_chunks))

    citations_event = next(e for e in events if e["type"] == "citations")
    assert len(citations_event["sources"]) > 0

    src = citations_event["sources"][0]
    assert src["document"] == "REFUND_DOC.md"
    assert src["chunk_id"] == "policy-chunk-99"
    assert src["section"] == "Eligibility Criteria"
    assert "30 days" in src["text"]
