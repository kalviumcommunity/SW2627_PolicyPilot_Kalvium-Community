"""Unit tests for prompt construction, context limit checking, and policy-grounded response generation."""

import json
import pytest
from unittest.mock import MagicMock
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

    # Test with strict limit that forces truncation but covers base system prompt tokens
    from src.services.token_service import get_token_count
    base_overhead = get_token_count(service.system_prompt) + get_token_count("What is the policy?") + 20
    limit = base_overhead + 30

    res_trunc = service.generate("What is the policy?", context, max_context_limit=limit)
    assert res_trunc["context_truncated"] is True
    assert res_trunc["input_tokens"] <= limit


def test_handling_missing_information():
    """Verify that chatbot refuses to answer out-of-scope questions and returns fallback."""
    service = ResponseService()
    # Context contains return period policy, user asks about FIFA World Cup
    context = (
        "Customers can request a return for standard catalog items within a return "
        "period of 30 days from delivery date."
    )
    res = service.generate("Who won the 2022 FIFA World Cup?", context)
    data = json.loads(res["answer"])
    assert data["answer"] == FALLBACK_MSG
    assert data["source"] == "None"


def test_preventing_unsupported_answers():
    """Verify that chatbot refuses questions when policy details are absent from context."""
    service = ResponseService()
    # Context contains return period, but user asks about seller authentications
    context = (
        "Customers can request a return for standard catalog items within a return "
        "period of 30 days from delivery date."
    )
    res = service.generate("What are the seller's responsibilities?", context)
    data = json.loads(res["answer"])
    assert data["answer"] == FALLBACK_MSG
    assert data["source"] == "None"


def test_parse_and_validate_json_valid():
    """Verify that parse_and_validate_json parses a valid JSON string successfully."""
    service = ResponseService()
    valid_json = '{"answer": "Standard return period is 30 days.", "source": "RETURN PERIOD POLICY"}'
    parsed = service.parse_and_validate_json(valid_json)
    assert parsed["answer"] == "Standard return period is 30 days."
    assert parsed["source"] == "RETURN PERIOD POLICY"


def test_parse_and_validate_json_markdown():
    """Verify that parse_and_validate_json strips markdown code block ticks if present."""
    service = ResponseService()
    markdown_json = (
        "```json\n"
        '{\n  "answer": "Standard return period is 30 days.",\n  "source": "RETURN PERIOD POLICY"\n}\n'
        "```"
    )
    parsed = service.parse_and_validate_json(markdown_json)
    assert parsed["answer"] == "Standard return period is 30 days."
    assert parsed["source"] == "RETURN PERIOD POLICY"


def test_parse_and_validate_json_missing_fields():
    """Verify that missing required fields throws a ValueError."""
    service = ResponseService()
    # Missing 'source'
    invalid_json = '{"answer": "Standard return period is 30 days."}'
    with pytest.raises(ValueError, match="Missing required fields"):
        service.parse_and_validate_json(invalid_json)


def test_parse_and_validate_json_malformed():
    """Verify that completely malformed JSON throws an exception."""
    service = ResponseService()
    malformed = '{"answer": "Standard return period is 30 days.", "source": "RETURN PERIOD POLICY"'
    with pytest.raises(json.JSONDecodeError):
        service.parse_and_validate_json(malformed)


def test_successful_recovery_retry():
    """Verify that the model response is successfully recovered/retried if the first response is malformed."""
    service = ResponseService()
    mock_client = MagicMock()
    service.client = mock_client
    service.model = "gpt-3.5-turbo"

    # Set up mock response objects
    # 1st call returns malformed text
    mock_choice_1 = MagicMock()
    mock_choice_1.message.content = "Here is your response: this is not JSON!"
    mock_response_1 = MagicMock()
    mock_response_1.choices = [mock_choice_1]

    # 2nd call (retry) returns valid JSON
    mock_choice_2 = MagicMock()
    mock_choice_2.message.content = '{"answer": "Standard return period is 30 days.", "source": "RETURN PERIOD POLICY"}'
    mock_response_2 = MagicMock()
    mock_response_2.choices = [mock_choice_2]

    # Configure mock API client to return response 1 and then response 2
    mock_client.chat.completions.create.side_effect = [mock_response_1, mock_response_2]

    res = service.generate("What is the return period?", "Customers can return items in 30 days.")

    # Call count must be 2
    assert mock_client.chat.completions.create.call_count == 2
    data = json.loads(res["answer"])
    assert data["answer"] == "Standard return period is 30 days."
    assert data["source"] == "RETURN PERIOD POLICY"
    assert res["simulated"] is False


def test_failed_retry_fallback():
    """Verify that when both initial and retry calls are malformed, it falls back to a graceful refusal."""
    service = ResponseService()
    mock_client = MagicMock()
    service.client = mock_client
    service.model = "gpt-3.5-turbo"

    mock_choice = MagicMock()
    mock_choice.message.content = "Malformed response"
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    mock_client.chat.completions.create.side_effect = [mock_response, mock_response]

    res = service.generate("What is the return period?", "Some context.")

    assert mock_client.chat.completions.create.call_count == 2
    data = json.loads(res["answer"])
    assert data["answer"] == FALLBACK_MSG
    assert data["source"] == "None"


def test_grounded_answer_and_source():
    """Verify that the source field is correctly grounded in retrieved policy context headers."""
    service = ResponseService()

    # Return Period
    res1 = service.generate(
        "What is the return period?",
        "[RETURN PERIOD POLICY]\nCustomers can request a return for standard catalog items within 30 days."
    )
    data1 = json.loads(res1["answer"])
    assert "30 days" in data1["answer"]
    assert data1["source"] == "RETURN PERIOD POLICY"

    # Damaged Products
    res2 = service.generate(
        "Can I return a damaged product?",
        "[DAMAGED PRODUCT POLICY]\nCustomers can return a damaged product only if they report it in 48 hours."
    )
    data2 = json.loads(res2["answer"])
    assert "48 hours" in data2["answer"]
    assert data2["source"] == "DAMAGED PRODUCT POLICY"

