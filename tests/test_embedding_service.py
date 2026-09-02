"""Unit tests for embedding service, batching, retries, and cost estimation."""

import os
from unittest.mock import MagicMock, patch
import pytest

from src.services.embedding_service import EmbeddingService
from src.run_batch_embeddings import compute_chunk_hash


def test_estimate_tokens_and_cost():
    """Verify token estimation and cost calculation formulas."""
    service = EmbeddingService()
    text = "This is a test sample text for token calculation."
    tokens = service.estimate_tokens(text)

    assert tokens > 0
    cost = service.estimate_cost(10000)
    assert cost == round((10000 / 1000.0) * 0.00002, 6)
    assert cost == 0.0002


def test_cosine_similarity_identical_vectors():
    """Verify cosine similarity between identical vectors is 1.0."""
    service = EmbeddingService()
    v1 = [1.0, 2.0, 3.0]
    v2 = [1.0, 2.0, 3.0]
    sim = service.cosine_similarity(v1, v2)

    assert pytest.approx(sim, 0.0001) == 1.0


def test_cosine_similarity_orthogonal_vectors():
    """Verify cosine similarity between orthogonal vectors is 0.0."""
    service = EmbeddingService()
    v1 = [1.0, 0.0, 0.0]
    v2 = [0.0, 1.0, 0.0]
    sim = service.cosine_similarity(v1, v2)

    assert pytest.approx(sim, 0.0001) == 0.0


def test_generate_batch_embeddings_fallback():
    """Verify batch embedding generation creates 1536-dim vectors in fallback mode."""
    service = EmbeddingService(base_url="", api_key="")
    texts = ["Sample chunk one text.", "Sample chunk two text.", "Sample chunk three text."]

    embeddings, total_tokens, failed_batches = service.generate_batch_embeddings(
        texts=texts, batch_size=2
    )

    assert len(embeddings) == 3
    assert len(embeddings[0]) == 1536
    assert len(embeddings[1]) == 1536
    assert len(embeddings[2]) == 1536
    assert total_tokens > 0
    assert failed_batches == []


def test_exponential_backoff_retry_handling():
    """Verify batch generator retries transient errors and logs failed batch if retries fail."""
    service = EmbeddingService(base_url="https://mock.api", api_key="mock-key")
    mock_client = MagicMock()

    # Simulate API error on all attempts
    mock_client.embeddings.create.side_effect = Exception("429 Rate Limit Exceeded")
    service.client = mock_client

    texts = ["Test retry chunk"]

    with patch("time.sleep") as mock_sleep:
        embeddings, tokens, failed_batches = service.generate_batch_embeddings(
            texts=texts, batch_size=1, max_retries=2, initial_delay=0.1
        )

        assert len(embeddings) == 1
        assert len(embeddings[0]) == 1536  # Mock fallback returned
        assert failed_batches == [1]
        assert mock_sleep.call_count == 2
        mock_sleep.assert_any_call(0.1)
        mock_sleep.assert_any_call(0.2)


def test_compute_chunk_hash_consistency():
    """Verify compute_chunk_hash generates consistent MD5 hashes."""
    text1 = "Policy text chunk"
    text2 = "Policy text chunk"
    text3 = "Different policy text"

    h1 = compute_chunk_hash(text1)
    h2 = compute_chunk_hash(text2)
    h3 = compute_chunk_hash(text3)

    assert h1 == h2
    assert h1 != h3
