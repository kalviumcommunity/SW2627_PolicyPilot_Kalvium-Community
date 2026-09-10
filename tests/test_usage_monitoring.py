"""Unit tests for usage monitoring and metrics summarization."""

import pytest
from src.services.token_service import estimate_cost
from src.services.usage_monitoring_service import summarize_usage


def test_estimate_cost_calculation():
    cost = estimate_cost(
        input_tokens=1000,
        output_tokens=1000,
        input_price_per_1k=0.0015,
        output_price_per_1k=0.0020,
    )

    assert cost["input_cost"] == 0.0015
    assert cost["output_cost"] == 0.0020
    assert cost["total_cost"] == 0.0035


def test_summarize_usage_empty_records():
    summary = summarize_usage([])

    assert summary["total_requests"] == 0
    assert summary["cache_hits"] == 0
    assert summary["cache_hit_rate"] == 0.0
    assert summary["total_estimated_cost"] == 0.0
    assert summary["average_latency_ms"] == 0.0
    assert summary["total_errors"] == 0


def test_summarize_usage_metrics():
    records = [
        {
            "cache_hit": False,
            "estimated_cost": 0.0010,
            "latency_ms": 100.0,
            "error": None,
        },
        {
            "cache_hit": True,
            "estimated_cost": 0.0,
            "latency_ms": 10.0,
            "error": None,
        },
        {
            "cache_hit": True,
            "estimated_cost": 0.0,
            "latency_ms": 10.0,
            "error": None,
        },
        {
            "cache_hit": False,
            "estimated_cost": 0.0020,
            "latency_ms": 200.0,
            "error": "Pipeline error",
        },
    ]

    summary = summarize_usage(records)

    assert summary["total_requests"] == 4
    assert summary["cache_hits"] == 2
    assert summary["cache_hit_rate"] == 0.5
    assert summary["total_estimated_cost"] == 0.0030
    assert summary["average_latency_ms"] == 80.0
    assert summary["total_errors"] == 1
