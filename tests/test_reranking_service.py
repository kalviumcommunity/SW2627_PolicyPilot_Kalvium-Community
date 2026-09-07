"""Unit and integration tests for RerankingService and two-stage retrieval pipeline."""

import pytest
import chromadb
from unittest.mock import MagicMock
from src.services.vector_store_service import VectorStoreService
from src.services.retrieval_service import RetrievalService, generate_deterministic_vector
from src.services.reranking_service import (
    RerankingService,
    compute_cross_relevance_score,
    show,
)


@pytest.fixture
def in_memory_vector_service():
    """Provide an ephemeral VectorStoreService fixture for test isolation."""
    client = chromadb.EphemeralClient()
    service = VectorStoreService(client=client, dimension=1536)
    yield service
    for col in client.list_collections():
        col_name = col.name if hasattr(col, "name") else str(col)
        try:
            client.delete_collection(col_name)
        except Exception:
            pass


@pytest.fixture
def populated_reranking_service(in_memory_vector_service):
    """Provide a populated RerankingService with sample candidate corpus."""
    col_name = "test_rerank_collection"
    in_memory_vector_service.get_or_create_collection(name=col_name, dimension=1536)

    records = [
        {
            "id": "submission-rubric.md:0",
            "text": "Academic Project Submission Rubric: What evidence is required for project submission? Required evidence includes a public GitHub repository link, test reports, and video demo.",
            "metadata": {"source": "submission-rubric.md", "section": "evidence"},
        },
        {
            "id": "submission-rubric.md:1",
            "text": "Project Submission Deadlines and Extensions: Submissions uploaded after Sunday 11:59 PM IST incur a 10% penalty per calendar day.",
            "metadata": {"source": "submission-rubric.md", "section": "deadlines"},
        },
        {
            "id": "grading-guidelines.md:0",
            "text": "Project Grading Criteria: 100 points total. Code Quality (30%), Testing (25%), Architecture (20%), Documentation (15%), Demo (10%).",
            "metadata": {"source": "grading-guidelines.md", "section": "grading"},
        },
        {
            "id": "campus-guide.md:0",
            "text": "Campus Facilities: The cafeteria menu changes every Monday morning.",
            "metadata": {"source": "campus-guide.md", "section": "dining"},
        },
        {
            "id": "account-guide.md:0",
            "text": "Learner Account Access: Password reset via forgot password link.",
            "metadata": {"source": "account-guide.md", "section": "auth"},
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

    return RerankingService(
        retrieval_service=retrieval_service,
        method="cross_attention",
    )


def test_compute_cross_relevance_score():
    """Verify compute_cross_relevance_score produces high scores for matching text and low for unrelated."""
    query = "What evidence is required for project submission?"
    matching_text = "What evidence is required for project submission? GitHub repo, tests, video demo."
    unrelated_text = "Campus cafeteria menu rotates every Monday morning."

    high_score = compute_cross_relevance_score(query, matching_text)
    low_score = compute_cross_relevance_score(query, unrelated_text)

    assert high_score >= 6.0
    assert low_score <= 2.0
    assert high_score > low_score


def test_compute_cross_relevance_score_empty():
    """Verify empty query or empty text returns 0.0."""
    assert compute_cross_relevance_score("", "some text") == 0.0
    assert compute_cross_relevance_score("some query", "") == 0.0


def test_rerank_scoring_and_sorting(populated_reranking_service):
    """Verify rerank calculates scores and sorts chunks in descending order."""
    query = "What evidence is required for project submission?"
    candidates = [
        {"id": "doc_unrelated", "text": "Cafeteria dining menu details.", "score": 0.30, "metadata": {"source": "campus.md"}},
        {"id": "doc_target", "text": "Evidence required for project submission includes GitHub code and unit test reports.", "score": 0.20, "metadata": {"source": "rubric.md"}},
    ]

    reranked = populated_reranking_service.rerank(query, candidates, top_n=2)
    assert len(reranked) == 2
    assert reranked[0]["id"] == "doc_target"
    assert reranked[0]["rerank_score"] > reranked[1]["rerank_score"]
    assert reranked[0]["rerank_rank"] == 1
    assert reranked[1]["rerank_rank"] == 2


def test_rerank_candidate_size_top_n(populated_reranking_service):
    """Verify rerank top_n truncates candidate list properly."""
    query = "project"
    candidates = [
        {"id": f"chunk_{i}", "text": f"Project chunk number {i}", "score": 0.1 * i, "metadata": {}}
        for i in range(5)
    ]

    top_2 = populated_reranking_service.rerank(query, candidates, top_n=2)
    assert len(top_2) == 2

    all_items = populated_reranking_service.rerank(query, candidates, top_n=None)
    assert len(all_items) == 5


def test_rerank_empty_candidates(populated_reranking_service):
    """Verify rerank handles empty candidates list gracefully."""
    result = populated_reranking_service.rerank("some query", [])
    assert result == []


def test_retrieve_and_rerank_pipeline(populated_reranking_service):
    """Verify complete two-stage retrieve and rerank pipeline execution."""
    query = "What evidence is required for project submission?"
    res = populated_reranking_service.retrieve_and_rerank(
        query=query,
        candidate_k=5,
        final_k=2,
    )

    assert res["query"] == query
    assert res["candidate_k"] == 5
    assert res["final_k"] == 2
    assert len(res["candidates"]) == 5
    assert len(res["final_context"]) == 2
    assert res["final_context"][0]["id"] == "submission-rubric.md:0"
    assert "rerank_score" in res["final_context"][0]
    assert res["latency_retrieval_ms"] >= 0.0
    assert res["latency_rerank_ms"] >= 0.0
    assert res["total_latency_ms"] >= 0.0


def test_retrieve_and_rerank_invalid_k(populated_reranking_service):
    """Verify retrieve_and_rerank raises ValueError when candidate_k < final_k."""
    with pytest.raises(ValueError, match="candidate_k .* must be greater than or equal to final_k"):
        populated_reranking_service.retrieve_and_rerank(
            query="test",
            candidate_k=2,
            final_k=5,
        )


def test_custom_scoring_function():
    """Verify RerankingService respects custom scoring function."""
    custom_fn = lambda q, chunk: 9.99 if "magic" in chunk.get("text", "") else 1.0

    service = RerankingService(scoring_fn=custom_fn)
    candidates = [
        {"id": "c1", "text": "normal text", "metadata": {}},
        {"id": "c2", "text": "magic text", "metadata": {}},
    ]

    reranked = service.rerank("query", candidates)
    assert reranked[0]["id"] == "c2"
    assert reranked[0]["rerank_score"] == 9.99


def test_rerank_score_llm_parsing():
    """Verify rerank_score_llm regex extraction handles various LLM score outputs."""
    mock_client = MagicMock()

    service = RerankingService(client=mock_client, api_key="fake_key", method="llm")

    # Case 1: Simple number
    mock_response1 = MagicMock()
    mock_response1.choices = [MagicMock(message=MagicMock(content="8.5"))]
    mock_client.chat.completions.create.return_value = mock_response1
    assert service.rerank_score_llm("q", {"text": "txt"}) == 8.5

    # Case 2: Number embedded in text
    mock_response2 = MagicMock()
    mock_response2.choices = [MagicMock(message=MagicMock(content="The relevance score is 9 out of 10"))]
    mock_client.chat.completions.create.return_value = mock_response2
    assert service.rerank_score_llm("q", {"text": "txt"}) == 9.0


def test_show_output_helper(capsys):
    """Verify show helper function prints formatted rows without exceptions."""
    rows = [
        {"id": "c1", "score": 0.85, "rerank_score": 9.2, "metadata": {"source": "test.md"}, "text": "Sample text content"}
    ]
    show("test label", rows)
    captured = capsys.readouterr()
    assert "test label" in captured.out
    assert "vector_score: 0.85" in captured.out
    assert "rerank_score: 9.2" in captured.out
    assert "source: test.md" in captured.out
