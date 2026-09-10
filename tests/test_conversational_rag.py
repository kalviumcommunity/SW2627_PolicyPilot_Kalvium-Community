"""Unit and integration tests for Conversational RAG & Follow-Up Context (CSA 3.42)."""

import pytest
from unittest.mock import MagicMock, patch

from src.services.conversational_rag_service import (
    format_history_for_prompt,
    rewrite_followup,
    conversational_answer,
    ConversationalRAGService,
    get_deterministic_rewrite_fallback,
)
from src.services.history_service import (
    count_tokens,
    total_tokens,
    trim,
    summarize_history,
)
from src.services.response_service import (
    SAFE_REFUSAL_MESSAGE,
    DEFAULT_MIN_TOP_SCORE,
)


@pytest.fixture
def sample_chunks():
    return [
        {
            "id": "submission-rubric.md:0",
            "text": "Academic Project Submission Rubric: What evidence is required for project submission? Students must submit a public GitHub repository link containing clean modular code, passing automated unit test suites, clear commit history, an architecture walkthrough, and a 3-5 minute screen recording video demo explaining key concepts.",
            "metadata": {
                "source": "submission-rubric.md",
                "doc_type": "rubric",
                "chunk_index": 0,
            },
            "score": 0.94,
        },
        {
            "id": "work_hours.md:0",
            "text": "Remote Work and Collaboration Policy: Employees may work remotely up to three days per week with manager approval. Core collaboration hours are 10 AM to 4 PM.",
            "metadata": {
                "source": "work_hours.md",
                "doc_type": "policy",
                "chunk_index": 0,
            },
            "score": 0.88,
        },
    ]


# ============================================================================
# Task 1 Tests: Track Conversation History
# ============================================================================

def test_track_conversation_history_basic():
    """Verify tracking user and assistant turns across multiple dialogue turns."""
    history = []
    
    # Turn 1
    history.append({"role": "user", "content": "What evidence is required for project submission?"})
    history.append({
        "role": "assistant",
        "content": "The submission needs a PR link, sample output, and a video explanation with source evidence."
    })
    
    # Turn 2
    history.append({"role": "user", "content": "What about the video?"})
    history.append({
        "role": "assistant",
        "content": "The video must be 3-5 minutes long and explain key code architectures."
    })

    assert len(history) == 4
    assert history[0]["role"] == "user"
    assert history[1]["role"] == "assistant"
    assert history[2]["role"] == "user"
    assert history[3]["role"] == "assistant"
    assert "evidence" in history[0]["content"]
    assert "video" in history[2]["content"]


def test_format_history_for_prompt():
    """Verify formatting conversation turns into prompt transcript."""
    history = [
        {"role": "user", "content": "What evidence is required for project submission?"},
        {"role": "assistant", "content": "The submission needs a PR link and video explanation."},
    ]
    formatted = format_history_for_prompt(history)
    assert "User: What evidence is required" in formatted
    assert "Assistant: The submission needs" in formatted


def test_format_history_empty():
    """Verify format_history_for_prompt handles empty history."""
    assert "(No prior conversation history)" in format_history_for_prompt([])


# ============================================================================
# Task 2 Tests: Rewrite Follow-Up Questions
# ============================================================================

def test_rewrite_followup_empty_history():
    """Verify that an initial question with no history returns the query directly."""
    q = "What evidence is required for project submission?"
    rewritten = rewrite_followup([], q)
    assert rewritten == q


def test_rewrite_followup_with_mock_client():
    """Verify rewrite_followup calls LLM and parses rewritten query."""
    mock_client = MagicMock()
    choice = MagicMock()
    choice.message.content = "What video explanation is required for project submission?"
    response = MagicMock()
    response.choices = [choice]
    mock_client.chat.completions.create.return_value = response

    history = [
        {"role": "user", "content": "What evidence is required for project submission?"},
        {"role": "assistant", "content": "A PR link and a video demo."},
    ]
    rewritten = rewrite_followup(history, "What about the video?", client=mock_client)
    assert rewritten == "What video explanation is required for project submission?"
    mock_client.chat.completions.create.assert_called_once()


def test_rewrite_followup_deterministic_fallback():
    """Verify rewrite_followup offline fallback resolves references deterministically."""
    history = [
        {"role": "user", "content": "What evidence is required for project submission?"},
        {"role": "assistant", "content": "A public repository link and a 3-5 minute video explanation."},
    ]
    
    # Follow-up 1: "What about the video?"
    rewritten1 = rewrite_followup(history, "What about the video?", client=False)
    assert "video" in rewritten1.lower()
    assert "project submission" in rewritten1.lower()

    # Follow-up 2: "How long should it be?"
    rewritten2 = rewrite_followup(history, "How long should it be?", client=False)
    assert "duration" in rewritten2.lower() or "video" in rewritten2.lower()


def test_rewrite_followup_sprint_reference():
    """Verify rewriting questions with sprint references."""
    history = [
        {"role": "user", "content": "What is the policy for remote work?"},
        {"role": "assistant", "content": "Employees may work remotely up to 3 days per week."},
    ]
    rewritten = rewrite_followup(history, "Does it apply to Sprint 2?", client=False)
    assert "remote work" in rewritten.lower() or "sprint 2" in rewritten.lower()


# ============================================================================
# Task 3 Tests: Retrieve Using the Rewritten Query
# ============================================================================

def test_retrieval_comparison_naive_vs_rewritten(sample_chunks):
    """Verify that retrieval with rewritten query scores higher than naive follow-up query."""
    mock_retrieval = MagicMock()
    
    # Naive query "What about the video?" gets weak or low-scoring matches
    mock_retrieval.retrieve.side_effect = lambda query, k=4: (
        [dict(sample_chunks[0], score=0.95)] if "project submission" in query.lower()
        else [dict(sample_chunks[0], score=0.25)]
    )

    history = [
        {"role": "user", "content": "What evidence is required for project submission?"},
        {"role": "assistant", "content": "A repository link and video explanation."},
    ]

    service = ConversationalRAGService(retrieval_service=mock_retrieval, client=False)
    service.set_history(history, session_id="test_session")

    comp = service.compare_retrieval("What about the video?", session_id="test_session")
    
    assert comp["user_question"] == "What about the video?"
    assert "project submission" in comp["rewritten_query"].lower()
    assert comp["rewritten_retrieval"]["top_score"] > comp["naive_retrieval"]["top_score"]
    assert comp["score_improvement"] > 0.50


# ============================================================================
# Task 4 Tests: Demonstrate Multi-Turn Dialogue
# ============================================================================

def test_conversational_answer_multi_turn_flow(sample_chunks):
    """Verify multi-turn conversation flow where history is used to ground follow-up responses."""
    mock_retrieval = MagicMock()
    mock_retrieval.retrieve.return_value = [sample_chunks[0]]

    mock_response = MagicMock()
    mock_response.generate.return_value = "The video explanation must be 3-5 minutes long showcasing the code demo [1]."

    history = []

    # Turn 1: Initial Question
    turn1 = conversational_answer(
        history=history,
        user_question="What evidence is required for project submission?",
        retrieval_service=mock_retrieval,
        response_service=mock_response,
        client=False,
    )

    assert turn1["status"] == "answered"
    assert turn1["is_grounded"] is True
    assert len(history) == 2
    assert history[0]["content"] == "What evidence is required for project submission?"

    # Turn 2: Follow-up Question ("What about the video?")
    turn2 = conversational_answer(
        history=history,
        user_question="What about the video?",
        retrieval_service=mock_retrieval,
        response_service=mock_response,
        client=False,
    )

    assert turn2["status"] == "answered"
    assert "video" in turn2["rewritten_query"].lower()
    assert "project submission" in turn2["rewritten_query"].lower()
    assert len(history) == 4
    assert history[2]["content"] == "What about the video?"
    assert len(turn2["sources"]) > 0


def test_conversational_answer_weak_context_refusal():
    """Verify safe refusal when rewritten query yields weak or empty retrieved chunks."""
    mock_retrieval = MagicMock()
    # Return chunks below similarity threshold
    mock_retrieval.retrieve.return_value = [
        {"text": "Irrelevant cafeteria policy", "score": 0.15, "metadata": {"source": "cafeteria.md"}}
    ]

    history = [
        {"role": "user", "content": "What is the policy for project submission?"},
        {"role": "assistant", "content": "Submit a PR link and video."},
    ]

    res = conversational_answer(
        history=history,
        user_question="Does it cover parking reimbursements?",
        retrieval_service=mock_retrieval,
        min_top_score=0.40,
        client=False,
    )

    assert res["status"] == "refused_weak_context"
    assert res["answer"] == SAFE_REFUSAL_MESSAGE
    assert res["is_grounded"] is False
    assert len(res["sources"]) == 0
    # History was still updated with the turn
    assert len(history) == 4
    assert history[-1]["content"] == SAFE_REFUSAL_MESSAGE


# ============================================================================
# Task 5 Tests: ConversationalRAGService Session Management & Budgeting
# ============================================================================

def test_conversational_rag_service_sessions():
    """Verify session isolation in ConversationalRAGService."""
    mock_retrieval = MagicMock()
    mock_retrieval.retrieve.return_value = []

    service = ConversationalRAGService(retrieval_service=mock_retrieval, client=False)

    service.answer("Question in session A", session_id="session_a")
    service.answer("Question in session B", session_id="session_b")

    history_a = service.get_history("session_a")
    history_b = service.get_history("session_b")

    assert len(history_a) == 2
    assert len(history_b) == 2
    assert history_a[0]["content"] == "Question in session A"
    assert history_b[0]["content"] == "Question in session B"

    service.clear_history("session_a")
    assert len(service.get_history("session_a")) == 0
    assert len(service.get_history("session_b")) == 2


def test_history_token_trimming_during_conversation():
    """Verify that conversation history is automatically trimmed when exceeding budget."""
    mock_retrieval = MagicMock()
    mock_retrieval.retrieve.return_value = [
        {"text": "Sample policy chunk text", "score": 0.85, "metadata": {"source": "policy.md"}}
    ]

    history = [
        {"role": "system", "content": "You are PolicyPilot."},
    ]
    
    # Create 10 large turns
    for i in range(10):
        history.append({"role": "user", "content": f"User question turn #{i} with substantial detailed context and content " * 10})
        history.append({"role": "assistant", "content": f"Assistant response turn #{i} with substantial explanation and citations [1] " * 10})

    initial_tokens = total_tokens(history)
    assert initial_tokens > 1000

    # Execute answer with tight budget (e.g. 500 tokens)
    conversational_answer(
        history=history,
        user_question="New question",
        retrieval_service=mock_retrieval,
        budget=500,
        client=False,
    )

    final_tokens = total_tokens(history)
    assert final_tokens <= 500
    assert history[0]["role"] == "system"  # System prompt preserved
