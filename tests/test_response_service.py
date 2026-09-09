"""Unit tests for response generation service and grounded answer verification (Concept 3.39)."""

import pytest
from unittest.mock import MagicMock

from src.services.response_service import (
    call_llm,
    generate_grounded_answer,
    generate_ungrounded_answer,
    answer_query,
    verify_grounding,
    compare_grounded_vs_ungrounded,
    print_grounding_check,
    ResponseService,
    FALLBACK_RESPONSE,
)


@pytest.fixture
def sample_chunks():
    return [
        {
            "id": "submission-rubric.md:0",
            "text": "Academic Project Submission Rubric: What evidence is required for project submission? Students must submit a public GitHub repository link containing clean modular code, passing automated unit test suites, clear commit history, an architecture walkthrough, and a 3-5 minute screen recording demo.",
            "metadata": {
                "source": "submission-rubric.md",
                "doc_type": "rubric",
                "chunk_index": 0,
            },
            "score": 0.92,
        },
        {
            "id": "account-guide.md:0",
            "text": "How can a learner reset their password? Learners can reset their password by clicking 'Forgot Password' on the login portal, entering their registered email, and following the secure reset link sent to their inbox.",
            "metadata": {
                "source": "account-guide.md",
                "doc_type": "guide",
                "chunk_index": 0,
            },
            "score": 0.75,
        },
    ]


@pytest.fixture
def mock_client():
    client = MagicMock()
    choice = MagicMock()
    choice.message.content = "Project submission requires a public GitHub repository link, clean code, passing unit tests, commit history, and a 3-5 minute demo video [1]."
    response = MagicMock()
    response.choices = [choice]
    client.chat.completions.create.return_value = response
    return client


def test_call_llm_with_mock(mock_client):
    """Verify call_llm executes chat completion and cleans output."""
    answer = call_llm("What is required?", client=mock_client, model="test-model")
    assert "GitHub repository link" in answer
    mock_client.chat.completions.create.assert_called_once()


def test_call_llm_offline_fallback():
    """Verify call_llm returns deterministic response when client is False (offline mode)."""
    answer = call_llm(
        "Context:\nWhat evidence is required for project submission?\nQuestion: What evidence is required?",
        client=False,
    )
    assert "GitHub repository link" in answer


def test_generate_grounded_answer_with_chunks(sample_chunks, mock_client):
    """Verify generate_grounded_answer builds augmented prompt and returns grounded result."""
    question = "What evidence is required for project submission?"
    result = generate_grounded_answer(
        question=question,
        retrieved_chunks=sample_chunks,
        client=mock_client,
    )

    assert result["question"] == question
    assert "GitHub repository link" in result["answer"]
    assert "Context:" in result["context"]
    assert result["is_grounded"] is True
    assert result["fallback_triggered"] is False
    assert len(result["sources"]) == 2
    assert result["sources"][0]["source"] == "submission-rubric.md"


def test_generate_grounded_answer_empty_chunks_fallback():
    """Verify generate_grounded_answer returns fallback when chunks are empty."""
    result = generate_grounded_answer(
        question="What is the tuition reimbursement policy?",
        retrieved_chunks=[],
    )

    assert result["answer"] == FALLBACK_RESPONSE
    assert result["sources"] == []
    assert result["is_grounded"] is False
    assert result["fallback_triggered"] is True


def test_generate_ungrounded_answer(mock_client):
    """Verify generate_ungrounded_answer calls model without context."""
    choice = MagicMock()
    choice.message.content = "Project submission usually requires documentation and code files."
    mock_client.chat.completions.create.return_value.choices = [choice]

    result = generate_ungrounded_answer(
        question="What evidence is required for project submission?",
        client=mock_client,
    )

    assert result["question"] == "What evidence is required for project submission?"
    assert result["sources"] == []
    assert result["is_grounded"] is False
    assert result["fallback_triggered"] is False


def test_answer_query_with_retrieval(sample_chunks, mock_client):
    """Verify answer_query retrieves chunks and generates grounded answer."""
    mock_retrieval = MagicMock()
    mock_retrieval.retrieve.return_value = sample_chunks

    result = answer_query(
        question="What evidence is required for project submission?",
        k=2,
        retrieval_service=mock_retrieval,
        client=mock_client,
    )

    mock_retrieval.retrieve.assert_called_once_with(
        query="What evidence is required for project submission?",
        k=2,
        metadata_filter=None,
        min_score=None,
    )
    assert result["is_grounded"] is True
    assert len(result["sources"]) == 2


def test_answer_query_empty_retrieval_fallback():
    """Verify answer_query returns fallback when retrieval yields no chunks."""
    mock_retrieval = MagicMock()
    mock_retrieval.retrieve.return_value = []

    result = answer_query(
        question="Unknown query with zero hits",
        retrieval_service=mock_retrieval,
    )

    assert result["answer"] == FALLBACK_RESPONSE
    assert result["sources"] == []
    assert result["is_grounded"] is False
    assert result["fallback_triggered"] is True


def test_verify_grounding_supported_answer(sample_chunks):
    """Verify verify_grounding scores high for faithful answers with citations."""
    answer = "Students must submit a public GitHub repository link with clean modular code and passing unit test suites [1]."
    verification = verify_grounding(answer=answer, retrieved_chunks=sample_chunks)

    assert verification["is_grounded"] is True
    assert verification["grounding_score"] >= 0.70
    assert len(verification["citations_found"]) >= 1
    assert verification["verification_status"] == "PASSED"
    assert len(verification["unsupported_claims"]) == 0


def test_verify_grounding_unsupported_claims(sample_chunks):
    """Verify verify_grounding detects unsupported claims and flags warnings."""
    hallucinated_answer = "Students must physically mail three certified copies of their passport and a signed notarized affidavit to the central registrar office."
    verification = verify_grounding(answer=hallucinated_answer, retrieved_chunks=sample_chunks)

    assert verification["is_grounded"] is False
    assert verification["grounding_score"] < 0.60
    assert len(verification["unsupported_claims"]) > 0
    assert verification["verification_status"] == "WARNING_UNSUPPORTED_CLAIMS"


def test_verify_grounding_fallback_response():
    """Verify verify_grounding recognizes valid fallback refusal."""
    verification = verify_grounding(answer=FALLBACK_RESPONSE, retrieved_chunks=[])

    assert verification["is_grounded"] is True
    assert verification["grounding_score"] == 1.0
    assert verification["fallback_detected"] is True
    assert verification["verification_status"] == "PASSED_FALLBACK"


def test_compare_grounded_vs_ungrounded(sample_chunks, mock_client):
    """Verify compare_grounded_vs_ungrounded constructs side-by-side analysis."""
    comparison = compare_grounded_vs_ungrounded(
        question="What evidence is required for project submission?",
        retrieved_chunks=sample_chunks,
        client=mock_client,
    )

    assert "without_retrieval" in comparison
    assert "with_retrieval" in comparison
    assert comparison["without_retrieval"]["sources"] == []
    assert len(comparison["with_retrieval"]["sources"]) == 2
    assert len(comparison["supporting_chunks"]) == 2


def test_print_grounding_check(capsys):
    """Verify print_grounding_check outputs answer and sources trace."""
    res = {
        "answer": "Grounded answer text [1].",
        "sources": [{"source": "submission-rubric.md", "chunk_index": 0}],
    }
    print_grounding_check(res)
    captured = capsys.readouterr()
    assert "answer: Grounded answer text [1]." in captured.out
    assert "submission-rubric.md" in captured.out


def test_response_service_class(sample_chunks, mock_client):
    """Verify ResponseService class methods."""
    mock_retrieval = MagicMock()
    mock_retrieval.retrieve.return_value = sample_chunks

    service = ResponseService(
        client=mock_client,
        retrieval_service=mock_retrieval,
    )

    # 1. generate_grounded
    g_res = service.generate_grounded("What is required?", retrieved_chunks=sample_chunks)
    assert g_res["is_grounded"] is True

    # 2. generate_ungrounded
    u_res = service.generate_ungrounded("What is required?")
    assert u_res["is_grounded"] is False

    # 3. answer_query
    q_res = service.answer_query("What is required?")
    assert q_res["is_grounded"] is True

    # 4. compare
    comp = service.compare("What is required?", retrieved_chunks=sample_chunks)
    assert "without_retrieval" in comp
    assert "with_retrieval" in comp

    # 5. verify
    v_res = service.verify("Students must submit a public GitHub link [1]", sample_chunks)
    assert v_res["grounding_score"] > 0
