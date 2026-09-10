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


def test_count_tokens():
    """Verify count_tokens returns positive integer for text and 0 for empty string."""
    from src.services.prompt_service import count_tokens

    assert count_tokens("") == 0
    assert count_tokens("Hello world") >= 2


def test_format_chunk():
    """Verify format_chunk produces expected source citation marker and text."""
    from src.services.prompt_service import format_chunk

    chunk = {
        "text": "Learners can reset password via email.",
        "metadata": {"source": "account-guide.md", "chunk_index": 0},
    }
    formatted = format_chunk(1, chunk)
    assert formatted.startswith("[1] account-guide.md#0")
    assert "Learners can reset password via email." in formatted


def test_assemble_context_within_budget():
    """Verify assemble_context joins chunks within token budget."""
    from src.services.prompt_service import assemble_context

    chunks = [
        {"text": "Chunk 1 text", "metadata": {"source": "doc1.md", "chunk_index": 0}},
        {"text": "Chunk 2 text", "metadata": {"source": "doc2.md", "chunk_index": 0}},
    ]

    context, used_tokens, sources = assemble_context(chunks, max_context_tokens=1000)
    assert "[1] doc1.md#0" in context
    assert "[2] doc2.md#0" in context
    assert "---" in context
    assert used_tokens > 0
    assert len(sources) == 2


def test_assemble_context_overflow_cutoff():
    """Verify assemble_context stops packing when token budget is exceeded."""
    from src.services.prompt_service import assemble_context

    chunks = [
        {"text": "A very long chunk " * 20, "metadata": {"source": "doc1.md", "chunk_index": 0}},
        {"text": "Another long chunk " * 20, "metadata": {"source": "doc2.md", "chunk_index": 1}},
    ]

    # Extremely low budget: only 1st chunk can fit
    context, used_tokens, sources = assemble_context(chunks, max_context_tokens=30)
    assert len(sources) <= 1
    assert used_tokens <= 30


def test_build_augmented_prompt():
    """Verify build_augmented_prompt constructs complete grounded prompt with instructions and fallback."""
    from src.services.prompt_service import build_augmented_prompt

    chunks = [
        {"text": "Remote work allowed 3 days per week.", "metadata": {"source": "remote.txt", "chunk_index": 0}},
    ]
    query = "How many days can I work remotely?"

    res = build_augmented_prompt(question=query, retrieved_chunks=chunks)
    prompt = res["prompt"]

    assert "You are a grounded assistant." in prompt
    assert "Answer the question using only the provided context." in prompt
    assert "I don't have enough information in the provided context." in prompt
    assert "[1] remote.txt#0" in prompt
    assert "Question:\nHow many days can I work remotely?" in prompt
    assert res["num_chunks_included"] == 1
    assert len(res["sources_used"]) == 1
    assert res["total_prompt_tokens"] > 0

