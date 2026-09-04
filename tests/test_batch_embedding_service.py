"""Unit tests for Batch Embedding & Rate/Cost Management service."""

import pytest
from unittest.mock import MagicMock
from src.services.batch_embedding_service import BatchEmbeddingService
from src.services.embedding_service import EmbeddingService


def test_batch_processing_all_new_chunks():
    """Verify batch embedding generation for a list of new chunks without embeddings."""
    service = BatchEmbeddingService(batch_size=2)
    chunks = [
        {"chunk_index": 0, "content": "Return policy statement."},
        {"chunk_index": 1, "content": "Shipping fees and delivery times."},
        {"chunk_index": 2, "content": "Customer support contact info."},
    ]

    metrics = service.process_chunks(chunks)

    assert metrics["total_chunks"] == 3
    assert metrics["skipped_chunks"] == 0
    assert metrics["embedded_chunks"] == 3
    assert metrics["failed_chunks"] == 0
    assert metrics["input_tokens"] > 0
    assert metrics["estimated_cost"] > 0.0

    for chunk in chunks:
        assert "embedding" in chunk
        assert isinstance(chunk["embedding"], list)
        assert len(chunk["embedding"]) == 1536


def test_skip_already_embedded_chunks():
    """Verify that chunks with existing embeddings are skipped and not re-embedded."""
    service = BatchEmbeddingService()
    existing_vector = [0.5] * 1536

    chunks = [
        {"chunk_index": 0, "content": "Already embedded chunk.", "embedding": existing_vector.copy()},
        {"chunk_index": 1, "content": "New chunk needing embedding."},
        {"chunk_index": 2, "content": "Another pre-embedded chunk.", "embedding": existing_vector.copy()},
    ]

    metrics = service.process_chunks(chunks)

    assert metrics["total_chunks"] == 3
    assert metrics["skipped_chunks"] == 2
    assert metrics["embedded_chunks"] == 1
    assert metrics["failed_chunks"] == 0

    # Ensure pre-existing vectors remain unchanged
    assert chunks[0]["embedding"] == existing_vector
    assert chunks[2]["embedding"] == existing_vector
    # Ensure new chunk got embedded
    assert len(chunks[1]["embedding"]) == 1536


def test_retry_handling_exponential_backoff():
    """Verify retry handling with exponential backoff on transient failures."""
    sleep_calls = []

    def mock_sleep(delay: float):
        sleep_calls.append(delay)

    mock_embed = MagicMock()
    # Fail twice, then succeed on 3rd attempt
    mock_embed.generate_embedding.side_effect = [
        Exception("Rate limit exceeded"),
        Exception("Temporary 503 Server Error"),
        [0.1] * 1536,
    ]

    service = BatchEmbeddingService(
        embedding_service=mock_embed,
        max_retries=3,
        initial_delay=0.1,
        backoff_factor=2.0,
        sleep_fn=mock_sleep,
    )

    result = service.generate_embedding_with_retry("Test retry content")

    assert result == [0.1] * 1536
    assert len(sleep_calls) == 2
    # Verify exponential backoff delays: 0.1, 0.2
    assert pytest.approx(sleep_calls[0], abs=1e-5) == 0.1
    assert pytest.approx(sleep_calls[1], abs=1e-5) == 0.2


def test_retry_failure_max_retries_exceeded():
    """Verify that permanent failure increments failed_chunks count when retries exhaust."""
    sleep_calls = []

    def mock_sleep(delay: float):
        sleep_calls.append(delay)

    mock_embed = MagicMock()
    mock_embed.generate_embedding.side_effect = Exception("Persistent API Error")

    service = BatchEmbeddingService(
        embedding_service=mock_embed,
        max_retries=2,
        initial_delay=0.1,
        backoff_factor=2.0,
        sleep_fn=mock_sleep,
    )

    chunks = [{"chunk_index": 0, "content": "Faulty request text"}]
    metrics = service.process_chunks(chunks)

    assert metrics["total_chunks"] == 1
    assert metrics["skipped_chunks"] == 0
    assert metrics["embedded_chunks"] == 0
    assert metrics["failed_chunks"] == 1
    assert len(sleep_calls) == 2


def test_resumability_partial_runs():
    """Verify that batch processing is resumable after a partial run."""
    service = BatchEmbeddingService(batch_size=2)

    chunks = [
        {"chunk_index": 0, "content": "Chunk one text."},
        {"chunk_index": 1, "content": "Chunk two text."},
        {"chunk_index": 2, "content": "Chunk three text."},
        {"chunk_index": 3, "content": "Chunk four text."},
    ]

    # First run: manually simulate partial processing (chunks 0 and 1 embedded)
    chunks[0]["embedding"] = [0.1] * 1536
    chunks[1]["embedding"] = [0.2] * 1536

    # Second run: process entire list again
    metrics = service.process_chunks(chunks)

    assert metrics["total_chunks"] == 4
    assert metrics["skipped_chunks"] == 2
    assert metrics["embedded_chunks"] == 2
    assert metrics["failed_chunks"] == 0

    # Verify all 4 chunks now have embeddings
    for chunk in chunks:
        assert "embedding" in chunk
        assert len(chunk["embedding"]) == 1536


def test_cost_calculation():
    """Verify cost calculation math and custom rates."""
    service = BatchEmbeddingService(cost_per_1k_tokens=0.0001)

    assert service.calculate_embedding_cost(0) == 0.0
    assert service.calculate_embedding_cost(1000) == 0.0001
    assert service.calculate_embedding_cost(500) == 0.00005
    assert service.calculate_embedding_cost(10000) == 0.001
    # Custom rate override
    assert service.calculate_embedding_cost(2000, cost_per_1k_tokens=0.0015) == 0.003


def test_empty_chunks_input():
    """Verify service behavior when passed an empty list of chunks."""
    service = BatchEmbeddingService()
    metrics = service.process_chunks([])

    assert metrics["total_chunks"] == 0
    assert metrics["skipped_chunks"] == 0
    assert metrics["embedded_chunks"] == 0
    assert metrics["failed_chunks"] == 0
    assert metrics["input_tokens"] == 0
    assert metrics["estimated_cost"] == 0.0
    assert metrics["chunks"] == []
