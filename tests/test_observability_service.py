"""Unit tests for ObservabilityService."""

import pytest
from src.services.observability_service import ObservabilityService


def test_generate_request_id():
    obs = ObservabilityService()
    id1 = obs.generate_request_id()
    id2 = obs.generate_request_id()

    assert isinstance(id1, str)
    assert len(id1) > 0
    assert id1 != id2


def test_log_request_structure():
    obs = ObservabilityService()
    record = obs.log_request(
        question="What is the refund period?",
        answer="Eligible items can be returned within 30 days of purchase. [1]",
        sources=["RETURN_POLICY"],
        cache_hit=False,
        input_tokens=15,
        output_tokens=12,
        estimated_cost=0.00005,
        latency_ms=45.5,
    )

    assert "timestamp" in record
    assert "request_id" in record
    assert record["question"] == "What is the refund period?"
    assert record["answer_preview"].startswith("Eligible items")
    assert record["cache_hit"] is False
    assert record["input_tokens"] == 15
    assert record["output_tokens"] == 12
    assert record["estimated_cost"] == 0.00005
    assert record["latency_ms"] == 45.5
    assert record["error"] is None

    assert len(obs.get_records()) == 1


def test_answer_preview_truncation():
    obs = ObservabilityService()
    long_answer = "A" * 300  # 300 characters long

    record = obs.log_request(
        question="Long answer test",
        answer=long_answer,
    )

    assert len(record["answer_preview"]) == 180
    assert record["answer_preview"] == "A" * 180


def test_log_error_recording():
    obs = ObservabilityService()
    record = obs.log_request(
        question="Invalid question",
        error="Question is required and cannot be empty.",
    )

    assert record["error"] == "Question is required and cannot be empty."
    assert record["cache_hit"] is False


def test_secrets_suppression_in_sources():
    obs = ObservabilityService()
    sensitive_source = {
        "source": "RETURN_POLICY.md",
        "api_key": "secret_key_12345",
        "password": "my_password",
    }

    record = obs.log_request(
        question="Test secrets",
        sources=[sensitive_source],
    )

    logged_source = record["sources"][0]
    assert "source" in logged_source
    assert "api_key" not in logged_source
    assert "password" not in logged_source


def test_clear_logs():
    obs = ObservabilityService()
    obs.log_request("Q1", answer="A1")
    obs.log_request("Q2", answer="A2")

    assert len(obs.get_records()) == 2
    obs.clear_logs()
    assert len(obs.get_records()) == 0
