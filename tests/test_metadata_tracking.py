"""Unit tests for chunk metadata creation, source tracking, and retrieval preservation."""

import json
import pytest
from src.services.document_service import DocumentService
from src.services.retrieval_service import RetrievalService
from src.services.response_service import ResponseService


def test_metadata_creation_and_contents():
    """Verify that chunk metadata contains source, chunk_index, and char_start fields."""
    doc_service = DocumentService("data")
    mock_docs = [
        {
            "text": "First section.\n\nSecond section of text.",
            "source": "test_policy.txt"
        }
    ]
    chunks = doc_service.chunk_documents(mock_docs)

    assert len(chunks) == 2
    
    # Check Metadata Fields
    for chunk in chunks:
        assert "source" in chunk["metadata"]
        assert "chunk_index" in chunk["metadata"]
        assert "char_start" in chunk["metadata"]


def test_source_tracking():
    """Verify that every chunk tracks the correct source document name."""
    doc_service = DocumentService("data")
    mock_docs = [
        {"text": "Policy content A.", "source": "policy_a.txt"},
        {"text": "Policy content B.", "source": "policy_b.txt"}
    ]
    chunks = doc_service.chunk_documents(mock_docs)

    assert len(chunks) == 2
    assert chunks[0]["metadata"]["source"] == "policy_a.txt"
    assert chunks[1]["metadata"]["source"] == "policy_b.txt"


def test_chunk_index_tracking():
    """Verify that chunk indexes are ordered sequentially within a document."""
    doc_service = DocumentService("data")
    mock_docs = [
        {
            "text": "Block one.\n\nBlock two.\n\nBlock three.",
            "source": "sequential.txt"
        }
    ]
    chunks = doc_service.chunk_documents(mock_docs)

    assert len(chunks) == 3
    assert chunks[0]["metadata"]["chunk_index"] == 0
    assert chunks[1]["metadata"]["chunk_index"] == 1
    assert chunks[2]["metadata"]["chunk_index"] == 2

    # Check char_start offsets are sequential and correct
    assert chunks[0]["metadata"]["char_start"] == 0
    assert chunks[1]["metadata"]["char_start"] > 0
    assert chunks[2]["metadata"]["char_start"] > chunks[1]["metadata"]["char_start"]


def test_retrieval_preserving_metadata():
    """Verify that retrieval filtering retains the full chunk metadata structure."""
    retrieval_service = RetrievalService()
    
    mock_chunks = [
        {
            "text": "Standard return period is 30 days.",
            "metadata": {
                "source": "returns.txt",
                "chunk_index": 0,
                "char_start": 0
            }
        },
        {
            "text": "Sellers must ship in 2 business days.",
            "metadata": {
                "source": "sellers.txt",
                "chunk_index": 0,
                "char_start": 0
            }
        }
    ]

    # Search for returns
    results = retrieval_service.search("return period", mock_chunks)
    assert len(results) == 1
    
    retrieved_chunk = results[0]
    assert retrieved_chunk["text"] == "Standard return period is 30 days."
    assert retrieved_chunk["metadata"]["source"] == "returns.txt"
    assert retrieved_chunk["metadata"]["chunk_index"] == 0
    assert retrieved_chunk["metadata"]["char_start"] == 0


def test_correct_source_appears_in_response():
    """Verify that ResponseService outputs the document source filename in the JSON response."""
    service = ResponseService()
    
    mock_retrieved_chunks = [
        {
            "text": "The return period is 30 days.",
            "metadata": {
                "source": "ecommerce_policies.txt",
                "chunk_index": 0,
                "char_start": 0
            }
        }
    ]

    res = service.generate("What is the return period?", mock_retrieved_chunks)
    data = json.loads(res["answer"])
    
    # Grounded answer check
    assert "30 days" in data["answer"]
    # Source mapping filename check
    assert data["source"] == "ecommerce_policies.txt"
