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
"""Unit and integration tests for RetrievalService and retrieval evaluation pipeline."""

import pytest
import chromadb
from src.services.vector_store_service import VectorStoreService
from src.services.retrieval_service import RetrievalService, generate_deterministic_vector


@pytest.fixture
def in_memory_vector_service():
    """Provide an isolated in-memory VectorStoreService fixture."""
    client = chromadb.EphemeralClient()
    service = VectorStoreService(client=client, dimension=1536)
    yield service
    # Teardown
    for col in client.list_collections():
        col_name = col.name if hasattr(col, "name") else str(col)
        try:
            client.delete_collection(col_name)
        except Exception:
            pass


@pytest.fixture
def populated_retrieval_service(in_memory_vector_service):
    """Provide a populated RetrievalService with sample documents and metadata."""
    col_name = "test_retrieval_col"
    in_memory_vector_service.get_or_create_collection(name=col_name, dimension=1536)

    records = [
        {
            "id": "account-guide.md:0",
            "text": "How can a learner reset their password? Reset password by clicking forgot password.",
            "metadata": {"source": "account-guide.md", "doc_type": "guide", "category": "auth"},
        },
        {
            "id": "campus-guide.md:0",
            "text": "When does the cafeteria menu change? The campus cafeteria menu changes every Monday.",
            "metadata": {"source": "campus-guide.md", "doc_type": "guide", "category": "campus"},
        },
        {
            "id": "submission-rubric.md:0",
            "text": "What evidence is required for project submission? Code commits, unit test reports, demo video.",
            "metadata": {"source": "submission-rubric.md", "doc_type": "rubric", "category": "academics"},
        },
        {
            "id": "remote_policy.txt:0",
            "text": "Company Remote Work Policy: Eligible employees may work remotely up to three days per week.",
            "metadata": {"source": "remote_policy.txt", "doc_type": "policy", "category": "workplace"},
        },
    ]

    for rec in records:
        rec["vector"] = generate_deterministic_vector(rec["text"], dim=1536)

    in_memory_vector_service.upsert_records(records, collection_name=col_name)

    retrieval_service = RetrievalService(
        vector_service=in_memory_vector_service,
        default_collection=col_name,
        dimension=1536,
        embedding_fn=lambda q: generate_deterministic_vector(q, dim=1536),
    )
    return retrieval_service


def test_retrieval_service_initialization(in_memory_vector_service):
    """Verify RetrievalService initializes with default or custom parameters."""
    service = RetrievalService(
        vector_service=in_memory_vector_service,
        default_collection="custom_col",
        dimension=1536,
    )
    assert service.default_collection == "custom_col"
    assert service.dimension == 1536
    assert service.vector_service is in_memory_vector_service


def test_embed_query_validation(populated_retrieval_service):
    """Verify embed_query rejects empty or whitespace strings with ValueError."""
    with pytest.raises(ValueError, match="Query string cannot be empty"):
        populated_retrieval_service.embed_query("")

    with pytest.raises(ValueError, match="Query string cannot be empty"):
        populated_retrieval_service.embed_query("   \t\n  ")


def test_embed_query_dimension_and_repeatability(populated_retrieval_service):
    """Verify embed_query produces repeatable vectors with matching 1536 dimension."""
    q = "How can a learner reset their password?"
    vec1 = populated_retrieval_service.embed_query(q)
    vec2 = populated_retrieval_service.embed_query(q)

    assert len(vec1) == 1536
    assert vec1 == vec2


def test_retrieve_invalid_k(populated_retrieval_service):
    """Verify retrieve raises ValueError when k is non-positive."""
    with pytest.raises(ValueError, match="k must be a positive integer"):
        populated_retrieval_service.retrieve("test query", k=0)

    with pytest.raises(ValueError, match="k must be a positive integer"):
        populated_retrieval_service.retrieve("test query", k=-5)


def test_retrieve_empty_query(populated_retrieval_service):
    """Verify retrieve returns empty list when query is empty."""
    results = populated_retrieval_service.retrieve("")
    assert results == []


def test_retrieve_top_k_limiting(populated_retrieval_service):
    """Verify retrieve respects the k parameter limit."""
    query = "How can a learner reset their password?"
    results_k1 = populated_retrieval_service.retrieve(query, k=1)
    assert len(results_k1) == 1
    assert results_k1[0]["metadata"]["source"] == "account-guide.md"
    assert results_k1[0]["rank"] == 1

    results_k3 = populated_retrieval_service.retrieve(query, k=3)
    assert len(results_k3) == 3
    assert [r["rank"] for r in results_k3] == [1, 2, 3]


def test_retrieve_metadata_filtering(populated_retrieval_service):
    """Verify retrieve filters results based on metadata criteria."""
    query = "guidelines and policies"
    
    # Filter strictly for doc_type == 'rubric'
    filtered_results = populated_retrieval_service.retrieve(
        query=query,
        k=4,
        metadata_filter={"doc_type": "rubric"},
    )
    assert len(filtered_results) == 1
    assert filtered_results[0]["metadata"]["doc_type"] == "rubric"
    assert filtered_results[0]["metadata"]["source"] == "submission-rubric.md"


def test_retrieve_min_score_threshold(populated_retrieval_service):
    """Verify retrieve filters out chunks below the min_score cutoff."""
    query = "How can a learner reset their password?"
    
    # Low threshold: returns matches
    results_low = populated_retrieval_service.retrieve(query, k=4, min_score=0.20)
    assert len(results_low) >= 1
    assert results_low[0]["metadata"]["source"] == "account-guide.md"

    # Impossible threshold: returns 0 chunks
    results_high = populated_retrieval_service.retrieve(query, k=4, min_score=0.999)
    assert len(results_high) == 0


def test_evaluate_setting(populated_retrieval_service):
    """Verify evaluate_setting correctly computes hits, top-1 hits, and reciprocal ranks."""
    test_queries = [
        {"query": "How can a learner reset their password?", "expected_source": "account-guide.md"},
        {"query": "When does the cafeteria menu change?", "expected_source": "campus-guide.md"},
    ]

    setting = {"name": "test_k2", "k": 2, "filter": None, "min_score": 0.0}
    rows = populated_retrieval_service.evaluate_setting(setting, test_queries)

    assert len(rows) == 2
    assert rows[0]["hit"] is True
    assert rows[0]["top_1_hit"] is True
    assert rows[0]["rank"] == 1
    assert rows[0]["reciprocal_rank"] == 1.0
    assert rows[0]["expected_source"] == "account-guide.md"
    assert rows[0]["returned_sources"][0] == "account-guide.md"


def test_compute_metrics():
    """Verify compute_metrics calculates Hit Rate, Top-1 Hit, MRR, and averages accurately."""
    mock_rows = [
        {"hit": True, "top_1_hit": True, "reciprocal_rank": 1.0, "returned_count": 3},
        {"hit": True, "top_1_hit": False, "reciprocal_rank": 0.5, "returned_count": 3},
        {"hit": False, "top_1_hit": False, "reciprocal_rank": 0.0, "returned_count": 2},
        {"hit": True, "top_1_hit": True, "reciprocal_rank": 1.0, "returned_count": 3},
    ]

    metrics = RetrievalService.compute_metrics(mock_rows)
    assert metrics["total_queries"] == 4
    assert metrics["hits"] == 3
    assert metrics["hit_rate"] == 0.75
    assert metrics["top_1_hits"] == 2
    assert metrics["top_1_hit_rate"] == 0.50
    assert metrics["mrr"] == round((1.0 + 0.5 + 0.0 + 1.0) / 4, 4)
    assert metrics["avg_returned_chunks"] == 2.75


def test_compute_metrics_empty():
    """Verify compute_metrics handles empty evaluation rows gracefully."""
    metrics = RetrievalService.compute_metrics([])
    assert metrics["total_queries"] == 0
    assert metrics["hit_rate"] == 0.0
    assert metrics["mrr"] == 0.0


def test_evaluate_all_settings(populated_retrieval_service):
    """Verify evaluate_all_settings compares multiple configurations in batch."""
    test_queries = [
        {"query": "How can a learner reset their password?", "expected_source": "account-guide.md"},
        {"query": "When does the cafeteria menu change?", "expected_source": "campus-guide.md"},
    ]

    settings = [
        {"name": "k1", "k": 1, "filter": None, "min_score": 0.0},
        {"name": "k3", "k": 3, "filter": None, "min_score": 0.0},
        {"name": "filtered_guides", "k": 3, "filter": {"doc_type": "guide"}, "min_score": 0.0},
    ]

    summaries = populated_retrieval_service.evaluate_all_settings(settings, test_queries)
    assert len(summaries) == 3
    assert summaries[0]["setting"] == "k1"
    assert summaries[0]["hit_rate"] == 1.0
    assert summaries[1]["setting"] == "k3"
    assert summaries[1]["hit_rate"] == 1.0
    assert summaries[2]["setting"] == "filtered_guides"
    assert summaries[2]["hit_rate"] == 1.0


def test_custom_embedding_fn_dimension_mismatch(in_memory_vector_service):
    """Verify custom embedding function raises ValueError if returned dimension is invalid."""
    bad_fn = lambda q: [0.1, 0.2, 0.3]  # Dim 3 instead of 1536
    service = RetrievalService(
        vector_service=in_memory_vector_service,
        dimension=1536,
        embedding_fn=bad_fn,
    )
    with pytest.raises(ValueError, match="Custom embedding_fn returned dimension"):
        service.embed_query("test query")
