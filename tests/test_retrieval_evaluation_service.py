"""Unit tests for Retrieval Evaluation Service."""

import pytest
from src.services.retrieval_evaluation_service import (
    RetrievalEvaluationService,
    extract_chunk_id,
)
from src.services.retrieval_service import RetrievalService


@pytest.fixture
def eval_service():
    return RetrievalEvaluationService()


def test_extract_chunk_id():
    """Test chunk ID extraction from various dict formats and strings."""
    assert extract_chunk_id("doc1:0") == "doc1:0"
    assert extract_chunk_id({"id": "chunk_101"}) == "chunk_101"
    assert extract_chunk_id({"chunk_id": "chunk_102"}) == "chunk_102"
    assert extract_chunk_id({"source": "account-guide.md", "chunk_index": 0}) == "account-guide.md:0"
    assert extract_chunk_id({"content": "some text content"}) == "some text content"


def test_perfect_recall_and_precision(eval_service):
    """Verify perfect recall (1.0) and precision (1.0) when retrieved items match relevant items exactly."""
    query = "How can a learner reset their password?"
    relevant_chunk_ids = {"account-guide.md:0", "account-guide.md:1"}
    retrieved_ids = ["account-guide.md:0", "account-guide.md:1"]

    res = eval_service.evaluate_query(query, relevant_chunk_ids, retrieved_chunks=retrieved_ids)

    assert res["recall"] == 1.0
    assert res["precision"] == 1.0
    assert set(res["hits"]) == relevant_chunk_ids


def test_partial_recall(eval_service):
    """Verify partial recall when only a subset of relevant chunks is retrieved."""
    query = "What evidence is required for submission?"
    relevant_chunk_ids = {"rubric.md:1", "rubric.md:2", "rubric.md:3"}
    retrieved_ids = ["rubric.md:1", "guide.md:0"]

    res = eval_service.evaluate_query(query, relevant_chunk_ids, retrieved_chunks=retrieved_ids)

    # hits = 1 ("rubric.md:1"), total_relevant = 3 => recall = 1/3 = 0.3333
    assert res["recall"] == pytest.approx(1 / 3, abs=1e-4)
    # hits = 1, retrieved = 2 => precision = 1/2 = 0.5
    assert res["precision"] == 0.5
    assert res["hits"] == ["rubric.md:1"]


def test_zero_recall(eval_service):
    """Verify zero recall when no relevant chunks are retrieved."""
    query = "What is the return period?"
    relevant_chunk_ids = {"return-policy.md:0"}
    retrieved_ids = ["account-guide.md:0", "shipping.md:1"]

    res = eval_service.evaluate_query(query, relevant_chunk_ids, retrieved_chunks=retrieved_ids)

    assert res["recall"] == 0.0
    assert res["precision"] == 0.0
    assert res["hits"] == []


def test_precision_calculation(eval_service):
    """Verify precision calculation when top-k retrieval contains irrelevant chunks alongside relevant ones."""
    query = "How to submit project?"
    relevant_chunk_ids = {"submission-rubric.md:2"}
    # 1 relevant chunk retrieved out of 4 total retrieved chunks
    retrieved_ids = [
        "submission-rubric.md:2",
        "account-guide.md:0",
        "account-guide.md:1",
        "shipping.md:0",
    ]

    res = eval_service.evaluate_query(query, relevant_chunk_ids, retrieved_chunks=retrieved_ids)

    # hits = 1, total_relevant = 1 => recall = 1.0
    assert res["recall"] == 1.0
    # hits = 1, total_retrieved = 4 => precision = 1/4 = 0.25
    assert res["precision"] == 0.25


def test_empty_retrieval_results(eval_service):
    """Verify metrics calculation when retrieval returns empty results (0 chunks)."""
    query = "Nonexistent query topic"
    relevant_chunk_ids = {"policy.md:1"}
    retrieved_ids = []

    res = eval_service.evaluate_query(query, relevant_chunk_ids, retrieved_chunks=retrieved_ids)

    assert res["recall"] == 0.0
    assert res["precision"] == 0.0
    assert res["hits"] == []


def test_empty_relevant_chunk_ids(eval_service):
    """Verify safe metric calculation when ground truth relevant_chunk_ids is empty."""
    query = "Query with no relevant documents defined"
    relevant_chunk_ids = set()
    retrieved_ids = ["policy.md:1", "policy.md:2"]

    res = eval_service.evaluate_query(query, relevant_chunk_ids, retrieved_chunks=retrieved_ids)

    assert res["recall"] == 0.0
    assert res["precision"] == 0.0
    assert res["hits"] == []


def test_multiple_queries_aggregate(eval_service):
    """Verify dataset aggregate evaluation metrics across multiple queries."""
    labelled_queries = [
        {
            "query": "How can a learner reset their password?",
            "relevant_chunk_ids": {"account-guide.md:0", "account-guide.md:1"},
            "retrieved_ids": ["account-guide.md:0", "account-guide.md:1"],
        },
        {
            "query": "What evidence is required for project submission?",
            "relevant_chunk_ids": {"submission-rubric.md:2"},
            "retrieved_ids": ["submission-rubric.md:2", "account-guide.md:0"],
        },
        {
            "query": "Where can I view my grades?",
            "relevant_chunk_ids": {"grading-policy.md:0"},
            "retrieved_ids": ["other.md:0"],
        },
    ]

    aggregate = eval_service.evaluate_dataset(labelled_queries)

    assert aggregate["number_of_queries"] == 3
    assert aggregate["total_queries"] == 3

    # Query 1: recall=1.0, precision=1.0
    # Query 2: recall=1.0, precision=0.5
    # Query 3: recall=0.0, precision=0.0
    # Expected avg recall = (1.0 + 1.0 + 0.0) / 3 = 2/3 = 0.6667
    # Expected avg precision = (1.0 + 0.5 + 0.0) / 3 = 1.5/3 = 0.5000
    assert aggregate["average_recall"] == pytest.approx(2 / 3, abs=1e-4)
    assert aggregate["average_precision"] == pytest.approx(0.5, abs=1e-4)


def test_failure_detection(eval_service):
    """Verify that queries with recall < 1.0 are correctly flagged in failed_queries."""
    labelled_queries = [
        {
            "query": "How to reset password?",
            "relevant_chunk_ids": {"account-guide.md:0"},
            "retrieved_ids": ["account-guide.md:0"],
        },
        {
            "query": "Submission evidence needed?",
            "relevant_chunk_ids": {"submission-rubric.md:2", "submission-rubric.md:3"},
            "retrieved_ids": ["submission-rubric.md:2"],  # recall = 0.5 < 1.0
        },
    ]

    aggregate = eval_service.evaluate_dataset(labelled_queries)
    failures = eval_service.inspect_failures(aggregate)

    assert len(failures) == 1
    failed = failures[0]
    assert failed["query"] == "Submission evidence needed?"
    assert failed["recall"] == 0.5
    assert failed["precision"] == 1.0
    assert "submission-rubric.md:2" in failed["retrieved_chunk_ids"]
    assert "submission-rubric.md:3" in failed["expected_chunk_ids"]


def test_top_k_cutoff(eval_service):
    """Verify that top_k parameter correctly truncates retrieved items before metric calculation."""
    query = "Sample query"
    relevant_chunk_ids = {"doc:1", "doc:3"}
    # doc:3 is at index 2 (position 3)
    retrieved_ids = ["doc:1", "doc:2", "doc:3", "doc:4"]

    # When top_k=2, only ["doc:1", "doc:2"] are evaluated.
    # hits = ["doc:1"], total_relevant = 2 => recall = 0.5, precision = 0.5
    res_k2 = eval_service.evaluate_query(
        query, relevant_chunk_ids, retrieved_chunks=retrieved_ids, top_k=2
    )

    assert res_k2["retrieved_ids"] == ["doc:1", "doc:2"]
    assert res_k2["recall"] == 0.5
    assert res_k2["precision"] == 0.5


def test_integration_with_retrieval_service():
    """Verify evaluation end-to-end using candidate chunks and RetrievalService."""
    retrieval_service = RetrievalService()
    eval_service = RetrievalEvaluationService(retrieval_service=retrieval_service)

    candidate_chunks = [
        {
            "id": "account-guide.md:0",
            "source": "account-guide.md",
            "chunk_index": 0,
            "content": "To reset your password click forgot password on the login page.",
        },
        {
            "id": "account-guide.md:1",
            "source": "account-guide.md",
            "chunk_index": 1,
            "content": "Follow the link sent to your registered email address to set a new password.",
        },
        {
            "id": "submission-rubric.md:2",
            "source": "submission-rubric.md",
            "chunk_index": 2,
            "content": "Project submission requires test results and code documentation evidence.",
        },
    ]

    labelled_queries = [
        {
            "query": "How can a learner reset their password?",
            "relevant_chunk_ids": {"account-guide.md:0", "account-guide.md:1"},
        },
        {
            "query": "What evidence is required for project submission?",
            "relevant_chunk_ids": {"submission-rubric.md:2"},
        },
    ]

    eval_result = eval_service.evaluate_dataset(labelled_queries, candidate_chunks=candidate_chunks, top_k=2)

    assert eval_result["number_of_queries"] == 2
    assert eval_result["average_recall"] > 0.0
    assert eval_result["average_precision"] > 0.0
