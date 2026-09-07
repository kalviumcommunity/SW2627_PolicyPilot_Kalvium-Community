"""Unit and integration tests for ResponseService and hallucination guardrails."""

import pytest
from unittest.mock import MagicMock, patch

from src.services.response_service import (
    ResponseService,
    retrieval_is_strong,
    DEFAULT_MIN_TOP_SCORE,
    DEFAULT_MIN_SUPPORTING_CHUNKS,
    SAFE_REFUSAL_MESSAGE,
)


def test_retrieval_is_strong_empty_chunks():
    """Verify that empty chunk lists evaluate to False."""
    assert retrieval_is_strong([]) is False
    assert retrieval_is_strong(None) is False


def test_retrieval_is_strong_below_threshold():
    """Verify that chunks with scores below threshold evaluate to False."""
    chunks = [
        {"text": "Sample text", "score": 0.20, "metadata": {"source": "doc1.md"}},
        {"text": "Another text", "score": 0.35, "metadata": {"source": "doc2.md"}},
    ]
    # Default threshold is 0.40
    assert retrieval_is_strong(chunks, min_top_score=0.40) is False


def test_retrieval_is_strong_insufficient_count():
    """Verify that having fewer chunks than min_supporting_chunks evaluates to False."""
    chunks = [
        {"text": "Sample text", "score": 0.85, "metadata": {"source": "doc1.md"}},
        {"text": "Another text", "score": 0.20, "metadata": {"source": "doc2.md"}},
    ]
    # Requires 2 strong chunks, but only 1 qualifies
    assert retrieval_is_strong(chunks, min_top_score=0.50, min_supporting_chunks=2) is False


def test_retrieval_is_strong_success():
    """Verify that valid chunks exceeding threshold and count evaluate to True."""
    chunks = [
        {"text": "Sample text", "score": 0.75, "metadata": {"source": "doc1.md"}},
        {"text": "Another text", "score": 0.65, "metadata": {"source": "doc2.md"}},
    ]
    assert retrieval_is_strong(chunks, min_top_score=0.40, min_supporting_chunks=1) is True
    assert retrieval_is_strong(chunks, min_top_score=0.60, min_supporting_chunks=2) is True


def test_response_service_init_defaults():
    """Verify default initialization parameters."""
    service = ResponseService(api_key="mock_key")
    assert service.min_top_score == DEFAULT_MIN_TOP_SCORE
    assert service.min_supporting_chunks == DEFAULT_MIN_SUPPORTING_CHUNKS


def test_response_service_generate_deterministic_fallback():
    """Verify deterministic grounded synthesis when LLM is unavailable or unconfigured."""
    service = ResponseService(api_key="")
    chunks = [
        {
            "text": "Password resets require submitting an official ticket. Follow the portal guide.",
            "score": 0.80,
            "metadata": {"source": "account-guide.md", "chunk_index": 0},
        }
    ]
    answer = service.generate("How do I reset password?", chunks)
    assert "[1]" in answer
    assert "Password resets require" in answer


def test_response_service_generate_empty_fallback():
    """Verify fallback response on empty chunks."""
    service = ResponseService(api_key="")
    answer = service.generate("Empty query", [])
    assert answer == SAFE_REFUSAL_MESSAGE


def test_response_service_generate_strips_thinking_tags():
    """Verify that internal thinking tags (<think>...</think>) are stripped from LLM output."""
    mock_client = MagicMock()
    mock_completion = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "<think>\nThinking through the policy steps...\n</think>\nHere is the answer: [1] account-guide.md."
    mock_completion.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_completion

    service = ResponseService(client=mock_client, api_key="valid-mock-key")
    chunks = [{"text": "Guide text", "score": 0.9, "metadata": {"source": "account-guide.md"}}]

    answer = service.generate("How to reset password?", chunks)
    assert "<think>" not in answer
    assert "</think>" not in answer
    assert "Thinking through" not in answer
    assert "Here is the answer: [1] account-guide.md." in answer


def test_guarded_answer_refusal_on_empty_retrieval():
    """Verify safe refusal when retrieval returns empty candidate list."""
    mock_retrieval = MagicMock()
    mock_retrieval.retrieve.return_value = []

    service = ResponseService(retrieval_service=mock_retrieval, min_top_score=0.40)
    result = service.guarded_answer("What is the refund policy for unindexed product?")

    assert result["status"] == "refused_weak_context"
    assert result["answer"] == SAFE_REFUSAL_MESSAGE
    assert result["sources"] == []
    assert result["top_score"] == 0.0
    assert result["supporting_chunks_count"] == 0
    assert result["total_retrieved"] == 0


def test_guarded_answer_refusal_on_weak_scores():
    """Verify safe refusal when retrieval returns candidates below threshold."""
    mock_retrieval = MagicMock()
    mock_retrieval.retrieve.return_value = [
        {"text": "Irrelevant cafeteria info", "score": 0.18, "metadata": {"source": "campus-guide.md"}},
        {"text": "Random holiday dates", "score": 0.22, "metadata": {"source": "academic-calendar.md"}},
    ]

    service = ResponseService(retrieval_service=mock_retrieval, min_top_score=0.40)
    result = service.guarded_answer("How do I file for international tax deductions?")

    assert result["status"] == "refused_weak_context"
    assert result["answer"] == SAFE_REFUSAL_MESSAGE
    assert result["sources"] == []
    assert result["top_score"] == 0.22
    assert result["supporting_chunks_count"] == 0
    assert result["total_retrieved"] == 2


def test_guarded_answer_success_on_strong_scores():
    """Verify successful grounded answer when retrieval returns strong candidates."""
    mock_retrieval = MagicMock()
    mock_retrieval.retrieve.return_value = [
        {
            "text": "Project submissions must include a Git repository link and video demo.",
            "score": 0.88,
            "metadata": {"source": "submission-rubric.md", "chunk_index": 0},
        },
        {
            "text": "Submissions are graded against rubrics A through D.",
            "score": 0.65,
            "metadata": {"source": "grading-policy.md", "chunk_index": 1},
        },
    ]

    service = ResponseService(retrieval_service=mock_retrieval, min_top_score=0.40, api_key="")
    result = service.guarded_answer("What evidence is required for project submission?")

    assert result["status"] == "answered"
    assert result["answer"] != SAFE_REFUSAL_MESSAGE
    assert len(result["sources"]) == 2
    assert result["top_score"] == 0.88
    assert result["supporting_chunks_count"] == 2
    assert result["total_retrieved"] == 2


def test_guarded_answer_custom_threshold_override():
    """Verify dynamic threshold override at query execution time."""
    mock_retrieval = MagicMock()
    mock_retrieval.retrieve.return_value = [
        {"text": "Moderate relevance chunk", "score": 0.55, "metadata": {"source": "doc1.md"}}
    ]

    service = ResponseService(retrieval_service=mock_retrieval, min_top_score=0.40, api_key="")

    # With default threshold 0.40 -> passes
    res_pass = service.guarded_answer("Query", min_top_score=0.40)
    assert res_pass["status"] == "answered"

    # With stricter threshold 0.70 -> refused
    res_fail = service.guarded_answer("Query", min_top_score=0.70)
    assert res_fail["status"] == "refused_weak_context"
