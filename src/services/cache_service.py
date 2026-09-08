"""In-memory Query Cache service with TTL and SHA-256 key normalization for PolicyPilot."""

import hashlib
import json
import time
from typing import Any, Dict, Optional


class QueryCacheService:
    """In-memory key-value cache with TTL expiration and SHA-256 deterministic key generation."""

    def __init__(self, default_ttl: float = 900.0):
        """Initialize QueryCacheService.

        Args:
            default_ttl: Default time-to-live in seconds (default: 900s / 15 minutes).
        """
        self.default_ttl = default_ttl
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.hits: int = 0
        self.misses: int = 0

    def cache_key(
        self, question: str, filters: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate a deterministic SHA-256 key from normalized question and filters.

        Args:
            question: Query text string.
            filters: Optional dictionary of filter key-values.

        Returns:
            Hexadecimal SHA-256 string digest.
        """
        normalized_q = (question or "").strip().lower()
        filters_str = (
            json.dumps(filters, sort_keys=True) if isinstance(filters, dict) else ""
        )
        composite_str = f"{normalized_q}:{filters_str}"
        return hashlib.sha256(composite_str.encode("utf-8")).hexdigest()

    def get(
        self, question: str, filters: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Retrieve cached response data if key exists and has not expired.

        Args:
            question: Query string.
            filters: Optional filter dictionary.

        Returns:
            Cached response data dict if valid hit, else None.
        """
        if not question or not str(question).strip():
            return None

        key = self.cache_key(question, filters)
        entry = self._cache.get(key)

        if not entry:
            self.misses += 1
            return None

        now = time.time()
        if now > entry["expires_at"]:
            # Expired entry - purge and record as cache miss
            del self._cache[key]
            self.misses += 1
            return None

        self.hits += 1
        return entry["value"]

    def set(
        self,
        question: str,
        response_data: Dict[str, Any],
        filters: Optional[Dict[str, Any]] = None,
        ttl: Optional[float] = None,
    ) -> str:
        """Save a successful query response in cache.

        Args:
            question: Query string.
            response_data: Response payload dict.
            filters: Optional filter dictionary.
            ttl: Optional override TTL in seconds.

        Returns:
            Cache key hash.
        """
        key = self.cache_key(question, filters)
        effective_ttl = ttl if ttl is not None else self.default_ttl
        now = time.time()

        self._cache[key] = {
            "value": response_data,
            "created_at": now,
            "expires_at": now + effective_ttl,
        }
        return key

    def clear(self) -> None:
        """Clear all cached entries and reset statistics."""
        self._cache.clear()
        self.hits = 0
        self.misses = 0

    @property
    def hit_rate(self) -> float:
        """Calculate current cache hit rate ratio (0.0 to 1.0)."""
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return round(self.hits / total, 4)
