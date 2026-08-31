"""Unit tests for ChunkingService, verifying token counting, chunking, and parameter validation."""

import pytest
from src.services.chunking_service import ChunkingService
from src.services.document_service import DocumentService


def test_count_tokens():
    """Verify that token counting works correctly for text and empty strings."""
    service = ChunkingService()
    
    # Empty cases
    assert service.count_tokens("") == 0
    assert service.count_tokens(None) == 0
    
    # Simple sentences (cl100k_base encoding)
    # "Hello" is 1 token, "world" is 1 token, "!" is 1 token, total 3 tokens (might vary slightly depending on punctuation encoding, let's verify it counts > 0)
    tokens_hello = service.count_tokens("Hello world!")
    assert tokens_hello > 0
    
    # Standard text matching tiktoken's expectation
    text = "The core team operates under the Flexible Hours Program."
    assert service.count_tokens(text) == len(service.encoding.encode(text))


def test_chunk_text_basic():
    """Verify that chunking splits text into chunks with the correct attributes."""
    service = ChunkingService()
    
    text = (
        "The quick brown fox jumps over the lazy dog. "
        "A fast-paced work environment requires constant adaptation. "
        "PolicyPilot helps teams navigate policy changes easily."
    )
    
    # We choose chunk_size of 10 and overlap of 2
    chunks = service.chunk_text(text, chunk_size=10, chunk_overlap=2)
    
    assert len(chunks) > 1
    
    for i, chunk in enumerate(chunks):
        assert "text" in chunk
        assert "token_count" in chunk
        assert "index" in chunk
        assert "start_token" in chunk
        assert "end_token" in chunk
        
        assert chunk["index"] == i
        assert chunk["token_count"] <= 10
        assert len(chunk["text"]) > 0
        
        # Verify slice matches start/end token indices
        all_tokens = service.encoding.encode(text, disallowed_special=())
        chunk_tokens = all_tokens[chunk["start_token"]:chunk["end_token"]]
        assert len(chunk_tokens) == chunk["token_count"]
        assert service.encoding.decode(chunk_tokens) == chunk["text"]


def test_chunk_text_overlap():
    """Verify that controlled overlap between chunks duplicates tokens correctly."""
    service = ChunkingService()
    
    text = (
        "This is statement one. This is statement two. This is statement three."
    )
    # Get total tokens
    tokens = service.encoding.encode(text)
    
    # Chunk with overlap
    chunk_size = 5
    chunk_overlap = 2
    chunks = service.chunk_text(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    
    # Check that the last 2 tokens of chunk index 0 are the first 2 tokens of chunk index 1
    # We can verify this via the token ranges:
    # Chunk 0 tokens are [0:5], Chunk 1 starts at 5 - 2 = 3, so its tokens are [3:8]
    # Overlap is index 3 and 4
    assert chunks[0]["start_token"] == 0
    assert chunks[0]["end_token"] == 5
    assert chunks[1]["start_token"] == 3
    assert chunks[1]["end_token"] == 8
    
    # Verify exact decoded overlapping text is identical
    overlap_tokens = tokens[3:5]
    overlap_text = service.encoding.decode(overlap_tokens)
    assert overlap_text in chunks[0]["text"]
    assert overlap_text in chunks[1]["text"]


def test_chunk_text_edge_cases():
    """Verify chunker edge cases and invalid parameters."""
    service = ChunkingService()
    
    # Empty text
    assert service.chunk_text("") == []
    assert service.chunk_text("   ") == []
    
    # Small input: total tokens fit within chunk_size
    text = "Short text."
    chunks = service.chunk_text(text, chunk_size=100, chunk_overlap=10)
    assert len(chunks) == 1
    assert chunks[0]["text"] == text
    assert chunks[0]["token_count"] < 100
    
    # Validation errors
    with pytest.raises(ValueError, match="chunk_size must be positive"):
        service.chunk_text("Some text", chunk_size=0)
        
    with pytest.raises(ValueError, match="chunk_size must be positive"):
        service.chunk_text("Some text", chunk_size=-10)
        
    with pytest.raises(ValueError, match="chunk_overlap must be non-negative"):
        service.chunk_text("Some text", chunk_size=10, chunk_overlap=-1)
        
    with pytest.raises(ValueError, match="chunk_overlap.*must be strictly less than chunk_size"):
        service.chunk_text("Some text", chunk_size=10, chunk_overlap=10)
        
    with pytest.raises(ValueError, match="chunk_overlap.*must be strictly less than chunk_size"):
        service.chunk_text("Some text", chunk_size=10, chunk_overlap=12)


def test_chunk_document():
    """Verify that chunking a document dictionary preserves metadata."""
    service = ChunkingService()
    
    doc = {
        "source": "remote_policy.txt",
        "text": "This is remote work policy guidelines. Work from anywhere."
    }
    
    chunks = service.chunk_document(doc, chunk_size=5, chunk_overlap=1)
    
    assert len(chunks) > 0
    for chunk in chunks:
        assert chunk["source"] == "remote_policy.txt"
        assert "text" in chunk
        assert "index" in chunk


def test_load_and_chunk_documents(tmp_path):
    """Verify that DocumentService's load_and_chunk_documents works end-to-end."""
    # Setup temporary directory and files
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    
    f1 = data_dir / "policy1.txt"
    f1.write_text("This is policy one. It contains guidelines for flexible hours.", encoding="utf-8")
    
    f2 = data_dir / "policy2.md"
    f2.write_text("# Reimbursement\nSubmit claims by the 5th of each month.", encoding="utf-8")
    
    doc_service = DocumentService()
    chunks = doc_service.load_and_chunk_documents(
        data_dir=str(data_dir),
        clean=True,
        chunk_size=6,
        chunk_overlap=2
    )
    
    assert len(chunks) > 0
    
    # Check that sources are tracked correctly
    sources = {c["source"] for c in chunks}
    assert "policy1.txt" in sources
    assert "policy2.md" in sources
    
    # Check chunk schema
    for c in chunks:
        assert "text" in c
        assert "source" in c
        assert "token_count" in c
        assert "index" in c
