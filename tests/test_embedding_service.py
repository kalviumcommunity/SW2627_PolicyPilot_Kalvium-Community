"""Unit tests for embedding generation and vector representation services."""

import pytest
import numpy as np
from src.services.embedding_service import EmbeddingService


def test_embedding_dimensions():
    """Verify that generated embeddings are list of floats of dimension 1536."""
    service = EmbeddingService()
    
    # Check default/mock generation dimensions
    vector = service.generate_embedding("Standard return period is 30 days.")
    assert isinstance(vector, list)
    assert len(vector) == 1536
    assert all(isinstance(val, float) for val in vector)


def test_embedding_determinism():
    """Verify that the mock embedding generator produces identical vectors for identical inputs."""
    service = EmbeddingService()
    
    vector1 = service.generate_embedding("Return window guidelines.")
    vector2 = service.generate_embedding("Return window guidelines.")
    
    assert vector1 == vector2


def test_cosine_similarity_basic():
    """Verify cosine_similarity performs correct vector space calculations."""
    service = EmbeddingService()
    
    # Perfect alignment (similarity = 1.0)
    v1 = [1.0, 0.0, 0.0]
    v2 = [1.0, 0.0, 0.0]
    assert pytest.approx(service.cosine_similarity(v1, v2), abs=1e-6) == 1.0
    
    # Orthogonal vectors (similarity = 0.0)
    v3 = [0.0, 1.0, 0.0]
    assert pytest.approx(service.cosine_similarity(v1, v3), abs=1e-6) == 0.0
    
    # Opposite direction (similarity = -1.0)
    v4 = [-1.0, 0.0, 0.0]
    assert pytest.approx(service.cosine_similarity(v1, v4), abs=1e-6) == -1.0


def test_semantic_vs_unrelated_similarity():
    """Verify that semantically similar sentences score higher than unrelated ones."""
    service = EmbeddingService()
    
    base_text = "What is the return period?"
    similar_text = "How long is the return window?"
    unrelated_text = "The seller must respond within 24 hours."
    
    v_base = service.generate_embedding(base_text)
    v_similar = service.generate_embedding(similar_text)
    v_unrelated = service.generate_embedding(unrelated_text)
    
    sim_similar = service.cosine_similarity(v_base, v_similar)
    sim_unrelated = service.cosine_similarity(v_base, v_unrelated)
    
    print(f"\nDebug Similarity - Similar: {sim_similar:.4f}, Unrelated: {sim_unrelated:.4f}")
    
    # Similar sentences must have higher score than unrelated ones
    assert sim_similar > sim_unrelated
    # Similar sentences should have positive correlation due to shared keywords
    assert sim_similar > 0.4
    # Unrelated sentences should have low correlation
    assert sim_unrelated < 0.4
