"""Offline unit tests for CitationService in PolicyPilot."""

import pytest
from unittest.mock import MagicMock
from src.services.citation_service import CitationService
from src.services.retrieval_service import RetrievalService
from src.services.rag_pipeline_service import RAGPipelineService
from src.services.response_service import ResponseService


@pytest.fixture
def sample_chunks():
    return [
        {
            "id": "doc1:0",
            "source": "RETURN_POLICY.md",
            "chunk_index": 0,
            "section": "Return Window",
            "text": "Customers can return standard catalog items within 30 days of delivery.",
        },
        {
            "id": "doc1:1",
            "source": "RETURN_POLICY.md",
            "chunk_index": 1,
            "section": "Packaging Requirements",
            "text": "Items must be returned unused, in original packaging with tags intact.",
        },
        {
            "metadata": {
                "chunk_id": "doc2:0",
                "source": "SELLER_POLICY.md",
                "chunk_index": 2,
                "section": "Dispatch SLAs",
            },
            "content": "Sellers are required to dispatch orders within 2 business days.",
        },
    ]


def test_build_citation_map_sequential_markers_and_mapping(sample_chunks):
    service = CitationService()
    citation_map = service.build_citation_map(sample_chunks)

    assert len(citation_map) == 3
    assert "[1]" in citation_map
    assert "[2]" in citation_map
    assert "[3]" in citation_map

    # Check [1] mapping
    c1 = citation_map["[1]"]
    assert c1["source"] == "RETURN_POLICY.md"
    assert c1["chunk_id"] == "doc1:0"
    assert c1["chunk_index"] == 0
    assert c1["section"] == "Return Window"
    assert c1["text"] == "Customers can return standard catalog items within 30 days of delivery."

    # Check [3] mapping with nested metadata
    c3 = citation_map["[3]"]
    assert c3["source"] == "SELLER_POLICY.md"
    assert c3["chunk_id"] == "doc2:0"
    assert c3["chunk_index"] == 2
    assert c3["section"] == "Dispatch SLAs"
    assert c3["text"] == "Sellers are required to dispatch orders within 2 business days."


def test_build_citation_map_missing_optional_metadata():
    minimal_chunk = [
        {
            "text": "Only text provided without extra metadata.",
        }
    ]
    service = CitationService()
    citation_map = service.build_citation_map(minimal_chunk)

    assert "[1]" in citation_map
    c = citation_map["[1]"]
    assert c["text"] == "Only text provided without extra metadata."
    assert c["source"] is None
    assert c["chunk_id"] is None
    assert c["chunk_index"] is None
    assert c["section"] is None


def test_build_cited_prompt_instructions_and_context(sample_chunks):
    service = CitationService()
    question = "What is the return period for catalog items?"
    prompt = service.build_cited_prompt(question, sample_chunks)

    # Check prompt contains strict required rules
    assert "Answer using ONLY the provided context." in prompt
    assert "Cite every factual claim using markers such as [1] or [2]." in prompt
    assert "Only use citation markers that exist in the provided context." in prompt
    assert "If the context does not support the answer, say there is not enough information." in prompt
    assert "Never invent citations." in prompt

    # Check context markers and text inclusion
    assert "[1] Source: RETURN_POLICY.md" in prompt
    assert "Customers can return standard catalog items within 30 days of delivery." in prompt
    assert f"Question: {question}" in prompt


def test_answer_with_citations_success(sample_chunks):
    service = CitationService(chunks=sample_chunks)
    question = "What is the return period?"
    result = service.answer_with_citations(question)

    assert "answer" in result
    assert "citations" in result
    assert len(result["citations"]) > 0
    assert "[1]" in result["citations"]
    assert "30 days" in result["answer"]
    assert "[1]" in result["answer"]


def test_answer_with_citations_empty_retrieval():
    service = CitationService(chunks=[])
    result = service.answer_with_citations("What is the return period?")

    expected_answer = "I don't have enough information in the provided context."
    assert result["answer"] == expected_answer
    assert result["citations"] == {}


def test_answer_with_citations_no_fabricated_citations():
    # Chunks unrelated to question
    unrelated_chunks = [
        {
            "id": "u1",
            "source": "ASTROPHYSICS.txt",
            "text": "Galaxies contain billions of stellar systems.",
        }
    ]
    service = CitationService(chunks=unrelated_chunks)
    result = service.answer_with_citations("What is the product return window?")

    assert result["answer"] == "I don't have enough information in the provided context."
    assert result["citations"] == {}


def test_answer_with_citations_multiple_citations(sample_chunks):
    service = CitationService(chunks=sample_chunks)
    question = "What are the rules for returns and seller SLAs?"
    result = service.answer_with_citations(question, top_k=3)

    assert "answer" in result
    assert "citations" in result
    assert len(result["citations"]) >= 2
    assert "[1]" in result["citations"]
    assert "[2]" in result["citations"]


def test_verify_citation_valid_marker(sample_chunks):
    service = CitationService(chunks=sample_chunks)
    result = service.answer_with_citations("What is the return period?")

    verified = service.verify_citation(result, "[1]")
    assert verified is not None
    assert verified["source"] == "RETURN_POLICY.md"
    assert verified["chunk_id"] == "doc1:0"
    assert verified["text"] == "Customers can return standard catalog items within 30 days of delivery."


def test_verify_citation_invalid_marker(sample_chunks):
    service = CitationService(chunks=sample_chunks)
    result = service.answer_with_citations("What is the return period?")

    verified = service.verify_citation(result, "[99]")
    assert verified is None


def test_integration_with_retrieval_and_rag_pipeline(sample_chunks):
    retrieval_svc = RetrievalService()
    rag_pipeline_svc = RAGPipelineService(chunks=sample_chunks)
    service = CitationService(
        chunks=sample_chunks,
        retrieval_service=retrieval_svc,
        rag_pipeline_service=rag_pipeline_svc,
    )

    question = "How quickly must sellers dispatch orders?"
    result = service.answer_with_citations(question, top_k=2)

    assert "answer" in result
    assert "citations" in result
    assert len(result["citations"]) > 0

    # Verify citation details for the retrieved chunk
    marker = list(result["citations"].keys())[0]
    verified = service.verify_citation(result, marker)
    assert verified is not None
    assert verified["text"] is not None


def test_answer_with_citations_mocked_llm(sample_chunks):
    mock_response_service = ResponseService()
    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "Catalog items can be returned within 30 days [1]."
    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_completion
    mock_response_service.client = mock_client

    service = CitationService(
        chunks=sample_chunks, response_service=mock_response_service
    )
    result = service.answer_with_citations("What is the return period?")

    assert result["answer"] == "Catalog items can be returned within 30 days [1]."
    assert "[1]" in result["citations"]
    assert result["citations"]["[1]"]["source"] == "RETURN_POLICY.md"
    mock_client.chat.completions.create.assert_called_once()
