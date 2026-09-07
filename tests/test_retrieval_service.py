"""Unit tests for PolicyPilot RetrievalService."""

import pytest
from pathlib import Path
from src.services.retrieval_service import RetrievalService
from src.services.embedding_service import EmbeddingService


@pytest.fixture
def sample_vector_store():
    """Fixture providing a mock vector store with 5 indexed document chunks."""
    embedder = EmbeddingService()
    text_1 = "Company Remote Work Policy: Eligible employees are allowed to work remotely up to three days per week."
    text_2 = "Home Internet Allowance FAQ: Employees can claim up to $50 per month for home internet expenses."
    text_3 = "Work Hours Policy: Core collaboration hours are from 10 AM to 4 PM Monday through Friday."
    text_4 = "Travel Expense Reimbursement: Flights must be booked in economy class at least 14 days in advance."
    text_5 = "Stipend FAQ: Internet stipend claims require itemized receipts submitted via expense portal."

    v1 = embedder.generate_embedding(text_1)
    v2 = embedder.generate_embedding(text_2)
    v3 = embedder.generate_embedding(text_3)
    v4 = embedder.generate_embedding(text_4)
    v5 = embedder.generate_embedding(text_5)

    return {
        "chunk_1": {
            "chunk_id": "chunk_1",
            "source": "remote_policy.txt",
            "content": text_1,
            "embedding": v1,
            "chunk_index": 0,
            "token_count": 25,
            "metadata": {"source": "remote_policy.txt", "chunk_index": 0, "token_count": 25, "doc_type": "txt"},
        },
        "chunk_2": {
            "chunk_id": "chunk_2",
            "source": "stipend_faq.html",
            "content": text_2,
            "embedding": v2,
            "chunk_index": 0,
            "token_count": 22,
            "metadata": {"source": "stipend_faq.html", "chunk_index": 0, "token_count": 22, "doc_type": "html"},
        },
        "chunk_3": {
            "chunk_id": "chunk_3",
            "source": "work_hours.md",
            "content": text_3,
            "embedding": v3,
            "chunk_index": 0,
            "token_count": 20,
            "metadata": {"source": "work_hours.md", "chunk_index": 0, "token_count": 20, "doc_type": "md"},
        },
        "chunk_4": {
            "chunk_id": "chunk_4",
            "source": "sample_policy.pdf",
            "content": text_4,
            "embedding": v4,
            "chunk_index": 0,
            "token_count": 24,
            "metadata": {"source": "sample_policy.pdf", "chunk_index": 0, "token_count": 24, "doc_type": "pdf"},
        },
        "chunk_5": {
            "chunk_id": "chunk_5",
            "source": "stipend_faq.html",
            "content": text_5,
            "embedding": v5,
            "chunk_index": 1,
            "token_count": 19,
            "metadata": {"source": "stipend_faq.html", "chunk_index": 1, "token_count": 19, "doc_type": "html"},
        },
    }


def test_embed_user_query():
    """Task 1: Verify user query is embedded using the exact same embedding model."""
    retriever = RetrievalService()
    query = "How many days per week can employees work remotely?"
    vec = retriever.embed_query(query)

    assert isinstance(vec, list)
    assert len(vec) == 1536
    assert all(isinstance(val, float) for val in vec)


def test_top_k_similarity_search(sample_vector_store):
    """Task 2: Verify top-k similarity search returns sorted relevant chunks."""
    retriever = RetrievalService()
    query = "How many days per week can employees work remotely?"
    results = retriever.search(query, top_k=3, vector_store=sample_vector_store)

    assert len(results) == 3
    # Check descending score order
    assert results[0]["score"] >= results[1]["score"] >= results[2]["score"]
    # Check top match is remote policy
    assert results[0]["source"] == "remote_policy.txt"
    assert results[0]["rank"] == 1


def test_include_scores_and_metadata(sample_vector_store):
    """Task 3: Verify retrieved chunks include similarity scores, source text, and metadata."""
    retriever = RetrievalService()
    query = "What is the monthly claim limit for home internet allowance?"
    results = retriever.search(query, top_k=2, vector_store=sample_vector_store)

    assert len(results) == 2
    for r in results:
        assert "score" in r and isinstance(r["score"], float)
        assert "content" in r and len(r["content"]) > 0
        assert "source" in r and isinstance(r["source"], str)
        assert "chunk_index" in r and isinstance(r["chunk_index"], int)
        assert "metadata" in r and isinstance(r["metadata"], dict)
        assert "source" in r["metadata"]
        assert "chunk_index" in r["metadata"]
        assert "doc_type" in r["metadata"]


def test_demonstrate_changing_k(sample_vector_store):
    """Task 4: Verify running search with different k values changes result count while preserving top ranks."""
    retriever = RetrievalService()
    query = "How many days per week can employees work remotely?"

    res_k2 = retriever.search(query, top_k=2, vector_store=sample_vector_store)
    res_k5 = retriever.search(query, top_k=5, vector_store=sample_vector_store)

    assert len(res_k2) == 2
    assert len(res_k5) == 5

    # Top-2 ranks in k=5 must match k=2 exactly
    assert res_k2[0]["chunk_id"] == res_k5[0]["chunk_id"]
    assert res_k2[1]["chunk_id"] == res_k5[1]["chunk_id"]

    # Test compare_k method
    comp = retriever.compare_k(query, k_values=[2, 5], vector_store=sample_vector_store)
    assert "k_2" in comp["comparisons"]
    assert "k_5" in comp["comparisons"]
    assert comp["comparisons"]["k_2"]["retrieved_count"] == 2
    assert comp["comparisons"]["k_5"]["retrieved_count"] == 5


def test_invalid_top_k():
    """Verify invalid top_k throws ValueError."""
    retriever = RetrievalService()
    with pytest.raises(ValueError):
        retriever.search("test query", top_k=0)


def test_empty_query():
    """Verify empty query returns empty results list."""
    retriever = RetrievalService()
    results = retriever.search("", top_k=3)
    assert results == []
