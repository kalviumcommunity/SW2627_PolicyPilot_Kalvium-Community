"""Unit tests for PolicyPilot RAG Evaluation Service."""

import pytest
from pathlib import Path
from src.services.response_service import ResponseService, FALLBACK_REFUSAL_MESSAGE
from src.services.evaluation_service import EvaluationService


@pytest.fixture
def sample_context():
    """Fixture providing sample context chunks."""
    return [
        {
            "chunk_id": "c1",
            "source": "remote_policy.txt",
            "chunk_index": 0,
            "content": "Eligible employees are allowed to work remotely up to three days per week.",
            "score": 0.45,
            "metadata": {"source": "remote_policy.txt", "doc_type": "txt"},
        }
    ]


def test_response_service_generate_grounded_answer(sample_context):
    """Task 2: Verify ResponseService generates grounded answers with inline citations."""
    resp_service = ResponseService()
    query = "How many days per week can employees work remotely?"

    result = resp_service.generate(query, context_chunks=sample_context)

    assert isinstance(result, dict)
    assert result["is_fallback"] is False
    assert len(result["generated_answer"]) > 0
    assert "three days per week" in result["generated_answer"].lower() or "3 days" in result["generated_answer"].lower()
    assert "remote_policy.txt" in result["cited_sources"] or len(result["cited_sources"]) > 0


def test_response_service_fallback_on_empty_context():
    """Verify ResponseService outputs fallback refusal when context is empty."""
    resp_service = ResponseService()
    query = "Are pets allowed in the office?"

    result = resp_service.generate(query, context_chunks=[])

    assert result["is_fallback"] is True
    assert result["generated_answer"] == FALLBACK_REFUSAL_MESSAGE
    assert result["cited_sources"] == []


def test_score_correctness_and_grounding():
    """Task 2: Verify scoring correctness and grounding functions."""
    eval_service = EvaluationService()

    # Case 1: Grounded correct answer
    corr = eval_service.score_correctness(
        generated_answer="Eligible employees can work remotely up to 3 days per week. [Source: remote_policy.txt]",
        expected_answer="Eligible employees are allowed to work remotely up to three days per week.",
        expected_claims=["three days per week", "work remotely"],
        is_fallback=False,
        expect_fallback=False,
    )
    assert corr >= 0.70

    # Case 2: Out of scope refusal
    refusal_corr = eval_service.score_correctness(
        generated_answer=FALLBACK_REFUSAL_MESSAGE,
        expected_answer=FALLBACK_REFUSAL_MESSAGE,
        expected_claims=["not specified"],
        is_fallback=True,
        expect_fallback=True,
    )
    assert refusal_corr == 1.0


def test_score_citations():
    """Task 3: Verify citation accuracy scoring for valid, missing, and refusal cases."""
    eval_service = EvaluationService()

    # Valid citation
    cite_eval = eval_service.score_citations(
        cited_sources=["remote_policy.txt"],
        expected_sources=["remote_policy.txt"],
        retrieved_sources=["remote_policy.txt"],
        expect_fallback=False,
    )
    assert cite_eval["citation_score"] == 1.0
    assert cite_eval["precision"] == 1.0
    assert cite_eval["recall"] == 1.0
    assert cite_eval["status"] == "EXACT_CITATION_MATCH"

    # Refusal with no citation
    refusal_cite = eval_service.score_citations(
        cited_sources=[],
        expected_sources=[],
        retrieved_sources=[],
        expect_fallback=True,
    )
    assert refusal_cite["citation_score"] == 1.0
    assert refusal_cite["status"] == "CORRECT_NO_CITATION"


def test_full_rag_evaluation():
    """Task 1-4: Verify evaluate_rag_system runs benchmark suite and produces scorecard metrics."""
    eval_service = EvaluationService()
    project_root = Path(__file__).resolve().parents[1]
    testset_path = project_root / "data" / "rag_eval_testset.json"

    summary = eval_service.evaluate_rag_system(test_set_path=testset_path)

    assert summary["total_tests_evaluated"] == 8
    assert summary["passed_tests_count"] >= 6
    assert summary["overall_quality_score_percent"] >= 75.0
    assert summary["average_correctness_percent"] > 0.0
    assert summary["average_grounding_percent"] > 0.0
    assert summary["average_citation_accuracy_percent"] > 0.0
    assert "results" in summary and len(summary["results"]) == 8
