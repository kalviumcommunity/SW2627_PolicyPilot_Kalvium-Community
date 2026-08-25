"""Unit tests for prompt service module."""

import pytest
from src.services.prompt_service import (
    build_messages,
    get_vague_prompt,
    get_constrained_prompt,
    get_json_constrained_prompt,
    compare_prompt_structures,
    SYSTEM_PROMPT_CONSTRAINED,
    SYSTEM_PROMPT_VAGUE,
)


def test_build_messages_structure():
    """Verify build_messages creates expected system and user dict structure."""
    sys_text = "System role statement"
    usr_text = "User question"
    messages = build_messages(sys_text, usr_text)

    assert len(messages) == 2
    assert messages[0] == {"role": "system", "content": sys_text}
    assert messages[1] == {"role": "user", "content": usr_text}


def test_get_vague_prompt():
    """Verify get_vague_prompt utilizes the vague system message."""
    query = "Explain our refund policy."
    messages = get_vague_prompt(query)

    assert messages[0]["role"] == "system"
    assert messages[0]["content"] == SYSTEM_PROMPT_VAGUE
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == query


def test_get_constrained_prompt_components():
    """Verify get_constrained_prompt includes role, scope, length, tone, and fallback rules."""
    query = "What is our software refund window?"
    messages = get_constrained_prompt(query)

    sys_content = messages[0]["content"]

    # Role
    assert "PolicyPilot" in sys_content
    # Scope
    assert "official company policy guidelines" in sys_content
    # Constraints (length/tone)
    assert "maximum 2 sentences" in sys_content
    assert "factual" in sys_content
    # Fallback rule
    assert "unable to answer this question" in sys_content


def test_get_json_constrained_prompt():
    """Verify get_json_constrained_prompt includes JSON schema instructions."""
    query = "What is the policy?"
    messages = get_json_constrained_prompt(query)

    sys_content = messages[0]["content"]
    assert "JSON object" in sys_content
    assert '"answer"' in sys_content
    assert '"confidence"' in sys_content


def test_compare_prompt_structures():
    """Verify structural comparison dictionary contains vague and constrained traits."""
    query = "Test question"
    comparison = compare_prompt_structures(query)

    assert comparison["user_query"] == query
    assert "variation_1_vague" in comparison
    assert "variation_2_constrained" in comparison

    vague_traits = comparison["variation_1_vague"]["characteristics"]
    constrained_traits = comparison["variation_2_constrained"]["characteristics"]

    assert any("Vague system role" in t for t in vague_traits)
    assert any("refusal fallback" in t.lower() for t in constrained_traits)
