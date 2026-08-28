"""Unit tests for token counting, cost estimation, and message history service."""

import pytest
from src.services.token_service import get_token_count, estimate_cost
from src.services.history_service import ConversationHistory


def test_token_counting_basic():
    """Verify that get_token_count returns expected values for basic text."""
    assert get_token_count("") == 0
    assert get_token_count("Hello") > 0
    assert get_token_count("This is a simple sentence.") == 6


def test_cost_calculation():
    """Verify that cost estimation matches the formula: cost = tokens / 1000 * price."""
    # Input pricing: $0.0015/1k, Output pricing: $0.0020/1k
    costs = estimate_cost(2000, 1000, 0.0015, 0.0020)
    assert costs["input_cost"] == 0.003
    assert costs["output_cost"] == 0.002
    assert costs["total_cost"] == 0.005


def test_history_trimming_retains_system_prompt():
    """Verify that history trimming keeps system prompt even if token limits are exceeded."""
    history = ConversationHistory()
    system_prompt = "You are a policy assistant."
    history.add_message("user", "Hello there!")
    history.add_message("assistant", "How can I help you today?")

    # Under strict limit, everything except system prompt must be trimmed
    trimmed = history.trim_history(
        max_tokens=10,
        system_prompt=system_prompt,
        token_counter=get_token_count,
        new_query="Help",
    )
    assert len(trimmed) == 1
    assert trimmed[0]["role"] == "system"
    assert trimmed[0]["content"] == system_prompt


def test_history_trimming_keeps_recent_history():
    """Verify that older user-assistant turns are dropped before newer ones."""
    history = ConversationHistory()
    system_prompt = "Assistant prompt"  # ~2 tokens
    history.add_message("user", "First question text.")  # ~4 tokens
    history.add_message("assistant", "First reply text.")  # ~4 tokens
    history.add_message("user", "Second question text.")  # ~4 tokens
    history.add_message("assistant", "Second reply text.")  # ~4 tokens

    # Total tokens = system (2) + Q1 (4) + A1 (4) + Q2 (4) + A2 (4) + New Q (2) = ~20 tokens.
    # Set limit to 14 tokens. It must drop the first Q&A pair and keep the second.
    trimmed = history.trim_history(
        max_tokens=14,
        system_prompt=system_prompt,
        token_counter=get_token_count,
        new_query="Help me",
    )

    # We expect system prompt + Q2 + A2
    assert len(trimmed) == 3
    assert trimmed[0]["role"] == "system"
    assert trimmed[1]["role"] == "user"
    assert trimmed[1]["content"] == "Second question text."
    assert trimmed[2]["role"] == "assistant"
    assert trimmed[2]["content"] == "Second reply text."
