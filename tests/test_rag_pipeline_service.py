"""Unit tests for RAG Pipeline Architecture & Flow Design service."""

import pytest
from unittest.mock import MagicMock
from src.services.rag_pipeline_service import RAGPipelineService, RagPipelineService
from src.services.embedding_service import EmbeddingService
from src.services.similarity_service import SimilarityService
from src.services.response_service import ResponseService


@pytest.fixture
def sample_chunks():
    return [
        {
            "chunk_index": 0,
            "source": "submission-rubric.md",
            "content": "Project submission requires evidence of unit tests passing and comprehensive documentation.",
        },
        {
            "chunk_index": 1,
            "source": "account-guide.md",
            "content": "To reset your password, click 'Forgot Password' on the login page and enter your registered email.",
        },
        {
            "chunk_index": 2,
            "source": "return-policy.md",
            "content": "Eligible catalog products can be returned within 30 days of initial delivery date.",
        },
    ]


def test_alias_class_name():
    """Verify that RagPipelineService is an alias for RAGPipelineService."""
    assert RagPipelineService is RAGPipelineService


def test_embed_query():
    """Verify that embed_query converts user query into a 1536-dim vector embedding."""
    service = RAGPipelineService()
    embedding = service.embed_query("What is the return policy?")

    assert isinstance(embedding, list)
    assert len(embedding) == 1536
    assert all(isinstance(val, float) for val in embedding)


def test_retrieve_context(sample_chunks):
    """Verify retrieve_context ranks candidate chunks against a query vector."""
    service = RAGPipelineService(chunks=sample_chunks)
    query = "What evidence is required for project submission?"
    query_vector = service.embed_query(query)

    retrieved = service.retrieve_context(query_vector, k=2)

    assert len(retrieved) == 2
    assert retrieved[0]["source"] == "submission-rubric.md"
    assert "submission" in retrieved[0]["content"].lower()


def test_assemble_context(sample_chunks):
    """Verify assemble_context formats chunks with numerical index labels and source citations."""
    service = RAGPipelineService()
    formatted_context = service.assemble_context(sample_chunks[:2])

    assert "[1] Source: submission-rubric.md" in formatted_context
    assert "Project submission requires evidence" in formatted_context
    assert "[2] Source: account-guide.md" in formatted_context
    assert "To reset your password" in formatted_context


def test_citation_formatting():
    """Verify citation formatting structure strictly follows '[idx] Source: <source>'."""
    service = RAGPipelineService()
    chunks = [
        {"source": "policy-doc-a.pdf", "content": "First sentence of policy."},
        {"source": "policy-doc-b.pdf", "content": "Second sentence of policy."},
    ]
    context = service.assemble_context(chunks)

    expected_part_1 = "[1] Source: policy-doc-a.pdf\nFirst sentence of policy."
    expected_part_2 = "[2] Source: policy-doc-b.pdf\nSecond sentence of policy."

    assert expected_part_1 in context
    assert expected_part_2 in context
    assert context == f"{expected_part_1}\n\n{expected_part_2}"


def test_generate_answer(sample_chunks):
    """Verify generate_answer returns grounded answer from context."""
    service = RAGPipelineService()
    context = service.assemble_context([sample_chunks[0]])
    query = "What evidence is required for project submission?"

    answer = service.generate_answer(query, context)

    assert isinstance(answer, str)
    assert len(answer) > 0
    assert "evidence" in answer.lower() or "submission" in answer.lower()


def test_complete_end_to_end_pipeline(sample_chunks):
    """Verify answer_query orchestrates complete RAG pipeline and returns answer + sources."""
    service = RAGPipelineService(chunks=sample_chunks)
    query = "What evidence is required for project submission?"

    result = service.answer_query(query, k=2)

    assert isinstance(result, dict)
    assert "answer" in result
    assert "sources" in result
    assert isinstance(result["answer"], str)
    assert isinstance(result["sources"], list)
    assert "submission-rubric.md" in result["sources"]


def test_custom_top_k(sample_chunks):
    """Verify custom top-k limits the number of retrieved chunks and returned sources."""
    service = RAGPipelineService(chunks=sample_chunks)
    query = "What is the return policy?"

    res_k1 = service.answer_query(query, k=1)
    assert len(res_k1["sources"]) == 1

    res_k3 = service.answer_query(query, k=3)
    assert len(res_k3["sources"]) <= 3


def test_empty_retrieval():
    """Verify answer_query returns standard refusal when no context chunks are retrieved."""
    service = RAGPipelineService(chunks=[])
    query = "What is the return period?"

    result = service.answer_query(query, k=4)

    assert result == {
        "answer": "I could not find relevant context for that question.",
        "sources": [],
    }


def test_no_generation_call_when_retrieval_empty():
    """Verify that generate_answer is NOT called when retrieval yields empty chunks."""
    service = RAGPipelineService(chunks=[])
    service.generate_answer = MagicMock()

    result = service.answer_query("Unrelated question", k=4)

    assert result["answer"] == "I could not find relevant context for that question."
    assert result["sources"] == []
    service.generate_answer.assert_not_called()


def test_answer_and_sources_structure(sample_chunks):
    """Verify the exact dictionary structure returned by answer_query."""
    service = RAGPipelineService(chunks=sample_chunks)
    res = service.answer_query("What is the return policy?", k=2)

    assert set(res.keys()) == {"answer", "sources"}
    assert isinstance(res["answer"], str)
    assert isinstance(res["sources"], list)


def test_offline_mock_generation(sample_chunks):
    """Verify that generation functions deterministically offline without API keys."""
    response_service = ResponseService()
    response_service.client = None  # Ensure offline mode

    service = RAGPipelineService(chunks=sample_chunks, response_service=response_service)
    res = service.answer_query("What evidence is required for project submission?", k=2)

    assert isinstance(res["answer"], str)
    assert len(res["answer"]) > 0
    assert "submission-rubric.md" in res["sources"]
