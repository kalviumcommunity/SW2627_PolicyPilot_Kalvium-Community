"""Unit tests for Similarity & Distance Metrics service and chunk ranking."""

import pytest
from src.services.embedding_service import EmbeddingService
from src.services.similarity_service import (
    SimilarityService,
    cosine_similarity,
    rank_chunks,
)


def test_cosine_similarity_basic():
    """Verify cosine_similarity performs correct vector space calculations."""
    service = SimilarityService()

    # Perfect alignment (similarity = 1.0)
    v1 = [1.0, 0.0, 0.0]
    v2 = [1.0, 0.0, 0.0]
    assert pytest.approx(service.cosine_similarity(v1, v2), abs=1e-6) == 1.0
    assert pytest.approx(cosine_similarity(v1, v2), abs=1e-6) == 1.0

    # Orthogonal vectors (similarity = 0.0)
    v3 = [0.0, 1.0, 0.0]
    assert pytest.approx(service.cosine_similarity(v1, v3), abs=1e-6) == 0.0
    assert pytest.approx(cosine_similarity(v1, v3), abs=1e-6) == 0.0

    # Opposite direction (similarity = -1.0)
    v4 = [-1.0, 0.0, 0.0]
    assert pytest.approx(service.cosine_similarity(v1, v4), abs=1e-6) == -1.0
    assert pytest.approx(cosine_similarity(v1, v4), abs=1e-6) == -1.0

    # Zero vector handling (similarity = 0.0)
    v_zero = [0.0, 0.0, 0.0]
    assert service.cosine_similarity(v1, v_zero) == 0.0


def test_semantic_vs_unrelated_similarity():
    """Verify that semantically similar sentences score higher than unrelated ones."""
    embed_service = EmbeddingService()
    sim_service = SimilarityService(embedding_service=embed_service)

    base_text = "What is the return period?"
    similar_text = "How long is the return window?"
    unrelated_text = "The seller must respond within 24 hours."

    v_base = embed_service.generate_embedding(base_text)
    v_similar = embed_service.generate_embedding(similar_text)
    v_unrelated = embed_service.generate_embedding(unrelated_text)

    score_similar = sim_service.cosine_similarity(v_base, v_similar)
    score_unrelated = sim_service.cosine_similarity(v_base, v_unrelated)

    assert score_similar > score_unrelated
    assert score_similar > 0.4
    assert score_unrelated < 0.4


def test_rank_chunks_descending_order():
    """Verify that rank_chunks orders chunks from highest to lowest similarity score."""
    embed_service = EmbeddingService()
    sim_service = SimilarityService(embedding_service=embed_service)

    query = "How can a learner reset their password?"
    query_embedding = embed_service.generate_embedding(query)

    chunks = [
        {
            "chunk_index": 0,
            "source": "ACCOUNT_SECURITY_POLICY",
            "content": "To reset your password, click Forgot Password on the login page and enter your email.",
        },
        {
            "chunk_index": 1,
            "source": "LEARNER_PORTAL_GUIDELINES",
            "content": "Learners can view course schedules and grade reports on the portal.",
        },
        {
            "chunk_index": 2,
            "source": "RETURN_AND_REFUND_POLICY",
            "content": "Returned items must be shipped back within 30 days in original packaging.",
        },
    ]

    ranked = sim_service.rank_chunks(query_embedding, chunks)

    assert len(ranked) == 3
    # Check descending order of similarity scores
    scores = [item["similarity_score"] for item in ranked]
    assert scores == sorted(scores, reverse=True)

    # Most relevant chunk should be the password reset policy
    assert ranked[0]["source"] == "ACCOUNT_SECURITY_POLICY"
    assert ranked[0]["chunk_index"] == 0

    # Least relevant chunk should be the return policy
    assert ranked[-1]["source"] == "RETURN_AND_REFUND_POLICY"
    assert ranked[-1]["chunk_index"] == 2


def test_rank_chunks_preserves_metadata():
    """Verify that existing metadata fields (source, chunk_index, custom fields) are preserved."""
    embed_service = EmbeddingService()
    sim_service = SimilarityService(embedding_service=embed_service)
    query_emb = embed_service.generate_embedding("reset password")

    chunks = [
        {
            "chunk_index": 42,
            "source": "AUTH_DOC",
            "content": "Reset your password via email.",
            "author": "Security Team",
            "version": "1.2",
        }
    ]

    ranked = sim_service.rank_chunks(query_emb, chunks)

    assert len(ranked) == 1
    assert ranked[0]["chunk_index"] == 42
    assert ranked[0]["source"] == "AUTH_DOC"
    assert ranked[0]["author"] == "Security Team"
    assert ranked[0]["version"] == "1.2"
    assert "similarity_score" in ranked[0]
    assert isinstance(ranked[0]["similarity_score"], float)


def test_rank_chunks_with_precomputed_embeddings():
    """Verify ranking works when chunk embeddings are already precomputed."""
    sim_service = SimilarityService()

    v_query = [1.0, 0.0, 0.0]
    chunks = [
        {"chunk_index": 0, "source": "A", "embedding": [0.0, 1.0, 0.0]},  # score 0.0
        {"chunk_index": 1, "source": "B", "embedding": [1.0, 0.0, 0.0]},  # score 1.0
        {"chunk_index": 2, "source": "C", "embedding": [0.7071, 0.7071, 0.0]},  # score ~0.7071
    ]

    ranked = sim_service.rank_chunks(v_query, chunks)

    assert [c["source"] for c in ranked] == ["B", "C", "A"]
    assert pytest.approx(ranked[0]["similarity_score"], abs=1e-4) == 1.0
    assert pytest.approx(ranked[1]["similarity_score"], abs=1e-4) == 0.7071
    assert pytest.approx(ranked[2]["similarity_score"], abs=1e-4) == 0.0


def test_rank_chunks_empty_inputs():
    """Verify that rank_chunks handles empty inputs gracefully without exceptions."""
    embed_service = EmbeddingService()
    sim_service = SimilarityService(embedding_service=embed_service)
    query_emb = embed_service.generate_embedding("sample query")

    assert sim_service.rank_chunks([], []) == []
    assert sim_service.rank_chunks(query_emb, []) == []
    assert sim_service.rank_chunks([], [{"chunk_index": 0, "content": "text"}]) == []
    assert rank_chunks([], []) == []


def test_retrieval_service_ranked_chunks_integration():
    """Verify that RetrievalService.retrieve_ranked_chunks works end-to-end with top_k."""
    from src.services.retrieval_service import RetrievalService

    retrieval_service = RetrievalService()
    chunks = [
        {"chunk_index": 0, "source": "PASS_POLICY", "content": "How to reset learner password step by step."},
        {"chunk_index": 1, "source": "COURSE_POLICY", "content": "Learner attendance and assignment submission rules."},
        {"chunk_index": 2, "source": "REFUND_POLICY", "content": "Refund requests are processed in 5-7 business days."},
    ]

    # Retrieve top 2
    top_2 = retrieval_service.retrieve_ranked_chunks(
        "How can a learner reset their password?", chunks, top_k=2
    )

    assert len(top_2) == 2
    assert top_2[0]["source"] == "PASS_POLICY"
    assert top_2[0]["similarity_score"] >= top_2[1]["similarity_score"]
