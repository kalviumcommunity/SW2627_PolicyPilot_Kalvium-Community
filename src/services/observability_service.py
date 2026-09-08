"""Structured logging and observability service for PolicyPilot."""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# Configure standard Python logger
logger = logging.getLogger("PolicyPilot.Observability")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


class ObservabilityService:
    """Observability service to record structured request logs, usage metrics, and audit history."""

    def __init__(self):
        """Initialize ObservabilityService."""
        self.logs: List[Dict[str, Any]] = []

    def generate_request_id(self) -> str:
        """Generate a unique UUID4 request identifier.

        Returns:
            UUID4 string representation.
        """
        return str(uuid.uuid4())

    def log_request(
        self,
        question: str,
        answer: Optional[str] = None,
        sources: Optional[List[Any]] = None,
        cache_hit: bool = False,
        input_tokens: int = 0,
        output_tokens: int = 0,
        estimated_cost: float = 0.0,
        latency_ms: float = 0.0,
        error: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create and log a structured JSON-style request record.

        Args:
            question: User question text.
            answer: Generated answer text.
            sources: List of cited source documents or markers.
            cache_hit: Boolean indicating if response was served from cache.
            input_tokens: Input token count.
            output_tokens: Output token count.
            estimated_cost: Estimated request cost in USD.
            latency_ms: Execution latency in milliseconds.
            error: Optional error message string if request failed.
            request_id: Optional explicit request_id.

        Returns:
            Structured log record dictionary.
        """
        req_id = request_id or self.generate_request_id()
        timestamp = datetime.now(timezone.utc).isoformat()

        # Truncate answer preview to a max of 180 characters
        answer_str = str(answer) if answer is not None else ""
        answer_preview = answer_str[:180]

        normalized_sources = []
        if isinstance(sources, list):
            for s in sources:
                if isinstance(s, dict):
                    # Clean dictionary to avoid logging sensitive keys
                    clean_s = {
                        k: v
                        for k, v in s.items()
                        if not any(
                            sec in k.lower()
                            for sec in ("key", "secret", "password", "auth", "token")
                        )
                    }
                    normalized_sources.append(clean_s)
                elif s is not None:
                    normalized_sources.append(str(s))

        record = {
            "timestamp": timestamp,
            "request_id": req_id,
            "question": question or "",
            "answer_preview": answer_preview,
            "sources": normalized_sources,
            "cache_hit": bool(cache_hit),
            "input_tokens": int(input_tokens),
            "output_tokens": int(output_tokens),
            "estimated_cost": round(float(estimated_cost), 6),
            "latency_ms": round(float(latency_ms), 2),
            "error": error,
        }

        # Store in memory for usage reporting & testability
        self.logs.append(record)

        # Output structured JSON log message
        log_json = json.dumps(record)
        if error:
            logger.error(log_json)
        else:
            logger.info(log_json)

        return record

    def get_records(self) -> List[Dict[str, Any]]:
        """Get all recorded request logs.

        Returns:
            List of log record dicts.
        """
        return list(self.logs)

    def clear_logs(self) -> None:
        """Clear all stored log records."""
        self.logs.clear()
