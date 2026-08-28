"""Unit tests for prompt construction, context limit checking, and policy-grounded response generation."""

import pytest
from src.services.response_service import ResponseService, SYSTEM_PROMPT_TEMPLATE

FALLBACK_MSG = "I am unable to answer this question as it is not specified in the official policy guidelines."


def test_prompt_construction():
    """Verify that construct_prompt builds standard system and user dictionary roles."""
    service = ResponseService()
    messages = service.construct_prompt("Test Question", "Test Context")

    assert len(messages) == 2
    assert messages[0] == {"role": "system", "content": SYSTEM_PROMPT_TEMPLATE}
    assert "Test Context" in messages[1]["content"]
    assert "Test Question" in messages[1]["content"]


def test_context_window_truncation():
    """Verify that context is truncated safely to fit inside strict token limits."""
    service = ResponseService()
    context = "word " * 100  # large context

    # Test with normal large limit (no truncation)
    res_normal = service.generate("What is the policy?", context, max_context_limit=1000)
    assert res_normal["context_truncated"] is False

    # Test with very strict limit (forces truncation)
    res_trunc = service.generate("What is the policy?", context, max_context_limit=180)
    assert res_trunc["context_truncated"] is True
    assert res_trunc["input_tokens"] <= 180


def test_handling_missing_information():
    """Verify that chatbot refuses to answer out-of-scope questions and returns fallback."""
    service = ResponseService()
    # Context contains return period policy, user asks about FIFA World Cup
    context = (
        "Customers can request a return for standard catalog items within a return "
        "period of 30 days from delivery date."
    )
    res = service.generate("Who won the 2022 FIFA World Cup?", context)
    assert res["answer"] == FALLBACK_MSG


def test_preventing_unsupported_answers():
    """Verify that chatbot refuses questions when policy details are absent from context."""
    service = ResponseService()
    # Context contains return period, but user asks about seller authentications
    context = (
        "Customers can request a return for standard catalog items within a return "
        "period of 30 days from delivery date."
    )
    res = service.generate("What are the seller's responsibilities?", context)
    assert res["answer"] == FALLBACK_MSG
