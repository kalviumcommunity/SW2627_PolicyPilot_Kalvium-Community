"""Usage and cost monitoring metrics aggregation service for PolicyPilot."""

from typing import Any, Dict, List


def summarize_usage(log_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Summarize request logs into aggregate usage and performance metrics.

    Args:
        log_records: List of structured log record dictionaries.

    Returns:
        Dictionary containing aggregate summary metrics:
        - total_requests (int)
        - cache_hits (int)
        - cache_hit_rate (float ratio 0.0 to 1.0)
        - total_estimated_cost (float USD)
        - average_latency_ms (float ms)
        - total_errors (int)
    """
    empty_summary = {
        "total_requests": 0,
        "cache_hits": 0,
        "cache_hit_rate": 0.0,
        "total_estimated_cost": 0.0,
        "average_latency_ms": 0.0,
        "total_errors": 0,
    }

    if not log_records:
        return empty_summary

    total_requests = len(log_records)
    cache_hits = 0
    total_cost = 0.0
    total_latency = 0.0
    total_errors = 0

    for rec in log_records:
        if not isinstance(rec, dict):
            continue

        if rec.get("cache_hit") is True:
            cache_hits += 1

        cost = rec.get("estimated_cost", 0.0)
        if isinstance(cost, (int, float)):
            total_cost += float(cost)

        latency = rec.get("latency_ms", 0.0)
        if isinstance(latency, (int, float)):
            total_latency += float(latency)

        err = rec.get("error")
        if err is not None and str(err).strip():
            total_errors += 1

    cache_hit_rate = round(cache_hits / total_requests, 4) if total_requests > 0 else 0.0
    avg_latency = round(total_latency / total_requests, 2) if total_requests > 0 else 0.0

    return {
        "total_requests": total_requests,
        "cache_hits": cache_hits,
        "cache_hit_rate": cache_hit_rate,
        "total_estimated_cost": round(total_cost, 6),
        "average_latency_ms": avg_latency,
        "total_errors": total_errors,
    }
