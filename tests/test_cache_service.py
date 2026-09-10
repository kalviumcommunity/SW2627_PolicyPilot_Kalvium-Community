"""Unit tests for QueryCacheService."""

import time
import pytest
from src.services.cache_service import QueryCacheService


def test_cache_key_normalization():
    cache = QueryCacheService()

    key1 = cache.cache_key("What is the return period?")
    key2 = cache.cache_key("  WHAT IS THE RETURN PERIOD?  ")

    # Identical questions with different casing and whitespace should produce identical cache key
    assert key1 == key2


def test_cache_key_filters_sensitivity():
    cache = QueryCacheService()

    key1 = cache.cache_key("Shipping time?", filters={"category": "electronics"})
    key2 = cache.cache_key("Shipping time?", filters={"category": "apparel"})
    key3 = cache.cache_key("Shipping time?")

    # Different filters produce different cache keys
    assert key1 != key2
    assert key1 != key3


def test_cache_set_and_get_hit():
    cache = QueryCacheService()
    question = "Can I return catalog items?"
    response = {"answer": "Yes, within 30 days.", "citations": {}}

    # Set cache entry
    cache.set(question, response)

    # Retrieval should be a cache hit
    res = cache.get(question)
    assert res == response
    assert cache.hits == 1
    assert cache.misses == 0
    assert cache.hit_rate == 1.0


def test_cache_miss():
    cache = QueryCacheService()

    # Query not in cache
    res = cache.get("Unknown question?")
    assert res is None
    assert cache.hits == 0
    assert cache.misses == 1
    assert cache.hit_rate == 0.0


def test_cache_ttl_expiration():
    cache = QueryCacheService(default_ttl=0.1)  # 100ms TTL
    question = "Fast expiring query"
    cache.set(question, {"answer": "Temporary answer"})

    # Immediate get should hit
    assert cache.get(question) is not None

    # Wait for TTL to expire
    time.sleep(0.15)

    # Should now be a cache miss and purged
    assert cache.get(question) is None
    assert cache.misses == 1


def test_cache_clear():
    cache = QueryCacheService()
    cache.set("Q1", {"ans": 1})
    cache.set("Q2", {"ans": 2})

    assert cache.get("Q1") is not None
    assert cache.hits == 1

    cache.clear()
    assert cache.hits == 0
    assert cache.misses == 0
    assert cache.get("Q1") is None


def test_empty_question_not_cached():
    cache = QueryCacheService()
    assert cache.get("") is None
    assert cache.get("   ") is None
