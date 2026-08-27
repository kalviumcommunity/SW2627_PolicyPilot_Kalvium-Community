"""Unit and integration tests for strict Policy-Only Answering and Relevance Grounding."""

import pytest
from src.services.response_service import ResponseService, FALLBACK_RESPONSE
from src.services.retrieval_service import RetrievalService


EXPECTED_EXACT_FALLBACK = "I am unable to answer this question as it is not specified in the official policy guidelines."


@pytest.fixture
def response_service():
    return ResponseService()


def test_fallback_constant_exact_match():
    """Verify fallback response constant matches exact expected wording."""
    assert FALLBACK_RESPONSE == EXPECTED_EXACT_FALLBACK


def test_category_1_valid_policy_question_supported(response_service):
    """Category 1: Valid policy question supported by official data."""
    query = "What is our annual leave allowance for full-time employees?"
    res = response_service.generate(query)

    assert res["is_grounded"] is True
    assert res["max_score"] > 0.25
    assert "20" in res["answer"] or "annual leave" in res["answer"].lower()


def test_category_2_unrelated_general_knowledge(response_service):
    """Category 2: Unrelated general knowledge question -> exact fallback, LLM blocked."""
    query = "Who won the FIFA 2024 World Cup?"
    res = response_service.generate(query)

    assert res["answer"] == EXPECTED_EXACT_FALLBACK
    assert res["llm_called"] is False


def test_category_3_general_programming_question(response_service):
    """Category 3: General programming question -> exact fallback, LLM blocked."""
    query = "What is Python?"
    res = response_service.generate(query)

    assert res["answer"] == EXPECTED_EXACT_FALLBACK
    assert res["llm_called"] is False


def test_category_4_casual_conversation(response_service):
    """Category 4: Casual conversation -> exact fallback, LLM blocked."""
    query = "Tell me a joke."
    res = response_service.generate(query)

    assert res["answer"] == EXPECTED_EXACT_FALLBACK
    assert res["llm_called"] is False


def test_category_5_out_of_domain_question(response_service):
    """Category 5: Out of domain question -> exact fallback, LLM blocked."""
    query = "What is the weather today?"
    res = response_service.generate(query)

    assert res["answer"] == EXPECTED_EXACT_FALLBACK
    assert res["llm_called"] is False


def test_category_6_policy_question_answer_missing(response_service):
    """Category 6: Policy-related question whose answer is missing in docs -> exact fallback, LLM blocked."""
    query = "What is our refund window for employee software tool purchases?"
    res = response_service.generate(query)

    assert res["answer"] == EXPECTED_EXACT_FALLBACK
    assert res["llm_called"] is False


def test_category_7_followup_question_insufficient_context(response_service):
    """Category 7: Follow-up question with insufficient context -> exact fallback sentence."""
    query = "Can I carry those days into next year?"
    res = response_service.generate(query)

    assert res["answer"] == EXPECTED_EXACT_FALLBACK
