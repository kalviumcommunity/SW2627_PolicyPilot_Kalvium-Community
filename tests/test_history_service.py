"""Unit tests for history service, verifying token counting, trimming, and summarization."""

import pytest
from unittest.mock import MagicMock
from src.services.history_service import count_tokens, total_tokens, trim, summarize_history


def test_count_tokens():
    """Verify count_tokens returns correct integer types and handles empty strings."""
    assert count_tokens("") == 0
    assert count_tokens("Hello world") > 0
    assert isinstance(count_tokens("Test string"), int)


def test_total_tokens():
    """Verify total_tokens correctly sums up individual message token counts."""
    messages = [
        {"role": "system", "content": "You are helpful."},
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"}
    ]
    expected = count_tokens("You are helpful.") + count_tokens("Hello") + count_tokens("Hi there!")
    assert total_tokens(messages) == expected


def test_trim_no_overflow():
    """Verify trimming doesn't affect messages when total tokens are within budget."""
    messages = [
        {"role": "system", "content": "Sys"},
        {"role": "user", "content": "User"}
    ]
    trim(messages, budget=1000)
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["content"] == "User"


def test_trim_overflow():
    """Verify trimming drops the oldest non-system messages until under budget."""
    messages = [
        {"role": "system", "content": "Sys"},       # ~1 token
        {"role": "user", "content": "Message One"},  # ~3 tokens
        {"role": "assistant", "content": "Two"},     # ~1 token
        {"role": "user", "content": "Message Three"} # ~3 tokens
    ]
    
    # We set a budget that triggers trimming
    # total_tokens: Sys(1) + One(3) + Two(1) + Three(3) = 8
    # Budget of 5 will require dropping 'Message One'
    # remaining: Sys(1) + Two(1) + Three(3) = 5
    trim(messages, budget=5)
    
    assert len(messages) == 3
    assert messages[0]["role"] == "system"
    assert messages[0]["content"] == "Sys"
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"] == "Two"
    assert messages[2]["role"] == "user"
    assert messages[2]["content"] == "Message Three"


def test_summarize_fallback_to_trim():
    """Verify summarization falls back to trimming if history is too short."""
    messages = [
        {"role": "system", "content": "Sys"},
        {"role": "user", "content": "Hello"}
    ]
    mock_client = MagicMock()
    # History too short to summarize (len <= 4 when keep_turns=1), should fallback to trim
    summarize_history(messages, mock_client, "dummy-model", budget=1, keep_turns=1)
    
    # Under trim, we stop trimming when len(messages) <= 2
    assert len(messages) == 2
    assert messages[0]["content"] == "Sys"
    assert messages[1]["content"] == "Hello"


def test_summarize_success():
    """Verify summarization calls the LLM, creates a summary, and reconstructs history."""
    messages = [
        {"role": "system", "content": "You are a helpful assistant for policy questions."},
        {"role": "user", "content": "What is the policy for annual leaves and how do I request it from my manager?"},
        {"role": "assistant", "content": "You can request annual leaves through the HR portal. Your manager needs to approve it at least two weeks in advance."},
        {"role": "user", "content": "Is there any carryover policy for unused annual leaves to the next calendar year?"},
        {"role": "assistant", "content": "Yes, you can carry over up to 5 unused annual leave days to the next calendar year. Any additional days will expire."},
        {"role": "user", "content": "Can I request parental leave as well?"},
        {"role": "assistant", "content": "Parental leave policies depend on your tenure. Please check the parental leave section in the HR portal."}
    ]
    
    # Mock LLM client
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Mocked Summary of earlier conversation."
    mock_client.chat.completions.create.return_value = mock_response
    
    # We want to keep last 1 turn (Query 3 + Answer 3). Summarize turns 1 and 2.
    # We dynamically calculate a budget that triggers summarization but does not trim active messages.
    orig_total = total_tokens(messages)
    summary_content = "Summary of previous conversation: Mocked Summary of earlier conversation."
    post_total = (
        count_tokens(messages[0]["content"]) + 
        count_tokens(summary_content) + 
        count_tokens(messages[-2]["content"]) + 
        count_tokens(messages[-1]["content"])
    )
    # Budget set to exactly the post-summary total
    budget = post_total
    result = summarize_history(messages, mock_client, "dummy-model", budget=budget, keep_turns=1)
    
    assert len(result) == 4
    assert result[0]["content"] == "You are a helpful assistant for policy questions."
    assert "Mocked Summary" in result[1]["content"]
    assert result[2]["content"] == "Can I request parental leave as well?"
    assert result[3]["content"] == "Parental leave policies depend on your tenure. Please check the parental leave section in the HR portal."
    
    mock_client.chat.completions.create.assert_called_once()
