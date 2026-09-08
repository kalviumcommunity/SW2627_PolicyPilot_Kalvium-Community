"""Unit tests for PolicyPilot Filtered & Hybrid Retrieval functionality."""

import pytest
from src.services.retrieval_service import RetrievalService
from src.services.embedding_service import EmbeddingService


@pytest.fixture
def sample_vector_store():
    """Fixture providing a mock vector store with 5 indexed document chunks."""
    embedder = EmbeddingService()
    text_1 = "Company Remote Work Policy: Eligible employees are allowed to work remotely up to three days per week."
    text_2 = "Home Internet Allowance FAQ: Employees can claim up to $75 per month for home internet expenses."
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
            "doc_type": "txt",
            "content": text_1,
            "embedding": v1,
            "chunk_index": 0,
            "metadata": {"source": "remote_policy.txt", "chunk_index": 0, "token_count": 25, "doc_type": "txt"},
        },
        "chunk_2": {
            "chunk_id": "chunk_2",
            "source": "stipend_faq.html",
            "doc_type": "html",
            "content": text_2,
            "embedding": v2,
            "chunk_index": 0,
            "metadata": {"source": "stipend_faq.html", "chunk_index": 0, "token_count": 22, "doc_type": "html"},
        },
        "chunk_3": {
            "chunk_id": "chunk_3",
            "source": "work_hours.md",
            "doc_type": "md",
            "content": text_3,
            "embedding": v3,
            "chunk_index": 0,
            "metadata": {"source": "work_hours.md", "chunk_index": 0, "token_count": 20, "doc_type": "md"},
        },
        "chunk_4": {
            "chunk_id": "chunk_4",
            "source": "sample_policy.pdf",
            "doc_type": "pdf",
            "content": text_4,
            "embedding": v4,
            "chunk_index": 0,
            "metadata": {"source": "sample_policy.pdf", "chunk_index": 0, "token_count": 24, "doc_type": "pdf"},
        },
        "chunk_5": {
            "chunk_id": "chunk_5",
            "source": "stipend_faq.html",
            "doc_type": "html",
            "content": text_5,
            "embedding": v5,
            "chunk_index": 1,
            "metadata": {"source": "stipend_faq.html", "chunk_index": 1, "token_count": 19, "doc_type": "html"},
        },
    }


def test_metadata_filtering_single_attribute(sample_vector_store):
    """Task 1: Verify metadata filtering restricts retrieval pool to matching doc_type."""
    retriever = RetrievalService()
    query = "What is the internet allowance reimbursement policy?"
    
    # Restrict search pool to doc_type='html' (stipend_faq.html chunks)
    results = retriever.search_filtered(
        query=query,
        metadata_filter={"doc_type": "html"},
        top_k=5,
        vector_store=sample_vector_store,
    )

    assert len(results) == 2
    for r in results:
        assert r["metadata"]["doc_type"] == "html"
        assert r["source"] == "stipend_faq.html"


def test_metadata_filtering_by_source(sample_vector_store):
    """Verify metadata filtering by exact source document name."""
    retriever = RetrievalService()
    query = "What are the rules for travel and flights?"

    results = retriever.search_filtered(
        query=query,
        metadata_filter={"source": "sample_policy.pdf"},
        top_k=3,
        vector_store=sample_vector_store,
    )

    assert len(results) == 1
    assert results[0]["source"] == "sample_policy.pdf"


def test_compare_filtered_vs_unfiltered(sample_vector_store):
    """Task 2 & 4: Verify compare_filtered_vs_unfiltered calculates precision and target matches."""
    retriever = RetrievalService()
    query = "What is the maximum reimbursement amount for home internet allowance?"

    comparison = retriever.compare_filtered_vs_unfiltered(
        query=query,
        metadata_filter={"doc_type": "html"},
        top_k=3,
        vector_store=sample_vector_store,
    )

    assert comparison["query"] == query
    assert comparison["filtered_precision_percent"] == 100.0
    assert len(comparison["filtered_results"]) == 2
    assert len(comparison["unfiltered_results"]) == 3


def test_hybrid_search(sample_vector_store):
    """Task 3: Verify hybrid search combines vector similarity and keyword score boosting."""
    retriever = RetrievalService()
    query = "How much can I claim per month for home internet?"
    keywords = ["$75", "75", "internet"]

    hybrid_results = retriever.search_hybrid(
        query=query,
        alpha=0.5,
        keywords=keywords,
        top_k=3,
        vector_store=sample_vector_store,
    )

    assert len(hybrid_results) == 3
    # Check that chunk 2 containing $75 ranks #1 with highest hybrid score
    assert hybrid_results[0]["chunk_id"] == "chunk_2"
    assert "vector_score" in hybrid_results[0]
    assert "keyword_score" in hybrid_results[0]
    assert hybrid_results[0]["keyword_score"] > 0.0
