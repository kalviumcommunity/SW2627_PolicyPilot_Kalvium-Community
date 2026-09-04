"""Unit tests for Metadata Filtering & Hybrid Search service."""

import pytest
from src.services.metadata_search_service import MetadataSearchService
from src.services.retrieval_service import RetrievalService


@pytest.fixture
def sample_chunks():
    return [
        {
            "chunk_index": 0,
            "source": "ACCOUNT_SECURITY_POLICY",
            "section": "Account access",
            "document_type": "security_guide",
            "user_group": "learners",
            "date": "2024-01-15",
            "content": "To reset your password, click 'Forgot Password' on the login page and enter your registered email address.",
        },
        {
            "chunk_index": 1,
            "source": "LEARNER_PORTAL_GUIDELINES",
            "section": "Student dashboard",
            "document_type": "user_guide",
            "user_group": "learners",
            "date": "2024-02-01",
            "content": "Learners can access online course materials, lecture recordings, and track assignment submission deadlines.",
        },
        {
            "chunk_index": 2,
            "source": "RETURN_AND_REFUND_POLICY",
            "section": "Refund conditions",
            "document_type": "policy",
            "user_group": "customers",
            "date": "2023-11-10",
            "content": "Customers can request a refund for eligible catalog items within 30 days of delivery.",
        },
    ]


def test_no_metadata_filter(sample_chunks):
    """Verify that omitting metadata filter (or filter=None/{}) returns all candidate chunks."""
    service = MetadataSearchService()
    query = "password reset"

    # Test None filter
    results_none = service.search(query, sample_chunks, metadata_filter=None)
    assert len(results_none) == 3

    # Test empty dict filter
    results_empty = service.search(query, sample_chunks, metadata_filter={})
    assert len(results_empty) == 3


def test_filtering_by_section(sample_chunks):
    """Verify filtering chunks specifically by section metadata field."""
    service = MetadataSearchService()
    query = "password reset"

    filter_criteria = {"section": "Account access"}
    results = service.search(query, sample_chunks, metadata_filter=filter_criteria)

    assert len(results) == 1
    assert results[0]["section"] == "Account access"
    assert results[0]["source"] == "ACCOUNT_SECURITY_POLICY"


def test_filtering_by_source(sample_chunks):
    """Verify filtering chunks by source metadata field."""
    service = MetadataSearchService()
    query = "course materials"

    filter_criteria = {"source": "LEARNER_PORTAL_GUIDELINES"}
    results = service.search(query, sample_chunks, metadata_filter=filter_criteria)

    assert len(results) == 1
    assert results[0]["source"] == "LEARNER_PORTAL_GUIDELINES"


def test_filtering_by_user_group_and_date(sample_chunks):
    """Verify filtering by multiple metadata fields (user_group, document_type, date)."""
    service = MetadataSearchService()
    query = "policy guidelines"

    filter_criteria = {
        "user_group": "learners",
        "document_type": "security_guide",
        "date": "2024-01-15",
    }
    results = service.search(query, sample_chunks, metadata_filter=filter_criteria)

    assert len(results) == 1
    assert results[0]["chunk_index"] == 0


def test_empty_results_after_filtering(sample_chunks):
    """Verify that filtering with non-matching criteria returns an empty list."""
    service = MetadataSearchService()
    query = "password reset"

    filter_criteria = {"section": "Nonexistent Section"}
    results = service.search(query, sample_chunks, metadata_filter=filter_criteria)

    assert results == []


def test_keyword_scoring():
    """Verify exact keyword occurrence calculation."""
    service = MetadataSearchService()
    text = "To reset your password, click 'Forgot Password' on the login page."

    # Matching keywords
    score_match = service.calculate_keyword_score("What are the password reset steps?", text)
    assert score_match > 0.0

    # Unmatched query
    score_unmatched = service.calculate_keyword_score("refund return policy duration", text)
    assert score_unmatched == 0.0

    # Empty inputs
    assert service.calculate_keyword_score("", text) == 0.0
    assert service.calculate_keyword_score("query", "") == 0.0


def test_hybrid_score_calculation(sample_chunks):
    """Verify hybrid score combining vector similarity and keyword score with default weights (0.8, 0.2)."""
    service = MetadataSearchService()
    query = "password reset"

    results = service.search(
        query,
        sample_chunks,
        enable_hybrid=True,
        vector_weight=0.8,
        keyword_weight=0.2,
    )

    assert len(results) == 3
    for res in results:
        assert "similarity_score" in res
        assert "keyword_score" in res
        assert "hybrid_score" in res

        expected_hybrid = round(
            (0.8 * res["similarity_score"]) + (0.2 * res["keyword_score"]), 6
        )
        assert pytest.approx(res["hybrid_score"], abs=1e-5) == expected_hybrid


def test_hybrid_ranking_order(sample_chunks):
    """Verify that results in hybrid search are sorted strictly in descending order of hybrid_score."""
    service = MetadataSearchService()
    query = "password reset steps"

    results = service.search(query, sample_chunks, enable_hybrid=True)

    hybrid_scores = [r["hybrid_score"] for r in results]
    assert hybrid_scores == sorted(hybrid_scores, reverse=True)


def test_configurable_weights(sample_chunks):
    """Verify hybrid search with custom vector_weight and keyword_weight."""
    service = MetadataSearchService()
    query = "password reset"

    # Pure keyword weighting (vector_weight=0.0, keyword_weight=1.0)
    results_kw = service.search(
        query,
        sample_chunks,
        enable_hybrid=True,
        vector_weight=0.0,
        keyword_weight=1.0,
    )

    for res in results_kw:
        assert pytest.approx(res["hybrid_score"], abs=1e-5) == res["keyword_score"]

    # 50/50 weighting
    results_half = service.search(
        query,
        sample_chunks,
        enable_hybrid=True,
        vector_weight=0.5,
        keyword_weight=0.5,
    )

    for res in results_half:
        expected = round((0.5 * res["similarity_score"]) + (0.5 * res["keyword_score"]), 6)
        assert pytest.approx(res["hybrid_score"], abs=1e-5) == expected


def test_metadata_preservation(sample_chunks):
    """Verify that all original metadata fields are preserved in returned chunk objects."""
    service = MetadataSearchService()
    query = "password reset"

    results = service.search(query, sample_chunks, enable_hybrid=True)

    top_result = results[0]
    assert "chunk_index" in top_result
    assert "source" in top_result
    assert "section" in top_result
    assert "document_type" in top_result
    assert "user_group" in top_result
    assert "date" in top_result
    assert "content" in top_result


def test_compatibility_with_retrieval_service(sample_chunks):
    """Verify that RetrievalService seamlessly supports optional metadata filtering."""
    retrieval_service = RetrievalService()
    query = "password reset"

    # Unfiltered retrieval via RetrievalService
    unfiltered = retrieval_service.retrieve_ranked_chunks(query, sample_chunks)
    assert len(unfiltered) == 3

    # Filtered retrieval via RetrievalService
    filtered = retrieval_service.retrieve_ranked_chunks(
        query, sample_chunks, metadata_filter={"section": "Account access"}
    )
    assert len(filtered) == 1
    assert filtered[0]["section"] == "Account access"
