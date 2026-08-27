"""Unit tests for parameter service module."""

from unittest.mock import MagicMock
import pytest

from src.services.parameter_service import (
    get_grounded_config,
    prepare_completion_payload,
    execute_completion_with_params,
)


def test_get_grounded_config():
    """Verify grounded configuration parameters meet target specifications."""
    config = get_grounded_config()

    assert config["temperature"] == 0.0
    assert config["max_tokens"] == 150
    assert config["top_p"] == 0.1
    assert config["stop"] is None


def test_prepare_completion_payload_default():
    """Verify payload construction with default parameter values."""
    messages = [{"role": "user", "content": "Test prompt"}]
    model = "gpt-3.5-turbo"

    payload = prepare_completion_payload(messages=messages, model=model)

    assert payload["model"] == model
    assert payload["messages"] == messages
    assert payload["temperature"] == 0.0
    assert payload["max_tokens"] == 150
    assert "top_p" not in payload
    assert "stop" not in payload


def test_prepare_completion_payload_custom():
    """Verify payload construction with explicit custom parameters."""
    messages = [{"role": "user", "content": "Test prompt"}]
    model = "gpt-3.5-turbo"

    payload = prepare_completion_payload(
        messages=messages,
        model=model,
        temperature=0.7,
        max_tokens=40,
        top_p=0.9,
        stop=["."],
    )

    assert payload["temperature"] == 0.7
    assert payload["max_tokens"] == 40
    assert payload["top_p"] == 0.9
    assert payload["stop"] == ["."]


def test_execute_completion_with_params_structure():
    """Verify execute_completion_with_params builds response dictionary correctly."""
    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "Sample response content"
    mock_choice.finish_reason = "stop"

    mock_usage = MagicMock()
    mock_usage.prompt_tokens = 10
    mock_usage.completion_tokens = 20
    mock_usage.total_tokens = 30

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_response.usage = mock_usage

    mock_client.chat.completions.create.return_value = mock_response

    messages = [{"role": "user", "content": "Test prompt"}]

    result = execute_completion_with_params(
        client=mock_client,
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.0,
        max_tokens=100,
    )

    assert result["content"] == "Sample response content"
    assert result["finish_reason"] == "stop"
    assert result["usage"]["total_tokens"] == 30
    assert result["params"]["temperature"] == 0.0
    assert result["params"]["max_tokens"] == 100
