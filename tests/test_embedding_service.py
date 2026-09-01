"""Unit tests for EmbeddingService."""

import pytest
from unittest.mock import MagicMock, patch
from src.services.embedding_service import EmbeddingService


def create_mock_embedding_response(texts, dim=1536):
    """Helper to create a mocked OpenAI embeddings response."""
    data = []
    for i, text in enumerate(texts):
        mock_item = MagicMock()
        # Deterministic dummy vector based on index and text length
        mock_item.embedding = [float(i + 1) * 0.01 + j * 0.001 for j in range(dim)]
        mock_item.index = i
        data.append(mock_item)
        
    mock_response = MagicMock()
    mock_response.data = data
    return mock_response


def test_init_with_defaults(monkeypatch):
    """Verify that EmbeddingService initializes with environment variables and defaults."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-openai-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    monkeypatch.setenv("EMBEDDING_MODEL", "text-embedding-3-small")

    service = EmbeddingService()
    assert service.api_key == "sk-test-openai-key"
    assert service.base_url == "https://api.openai.com/v1"
    assert service.model == "text-embedding-3-small"


def test_init_with_fallback_env(monkeypatch):
    """Verify fallback to API_KEY and API_BASE_URL when OPENAI_* are absent."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("EMBEDDING_MODEL", raising=False)
    monkeypatch.setenv("API_KEY", "custom-api-key")
    monkeypatch.setenv("API_BASE_URL", "https://custom.api.com/v1")

    service = EmbeddingService()
    assert service.api_key == "custom-api-key"
    assert service.base_url == "https://custom.api.com/v1"
    assert service.model == "text-embedding-3-small"


def test_missing_api_key_raises_error(monkeypatch):
    """Verify that attempting to get a client without any API key raises ValueError."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("API_KEY", raising=False)

    service = EmbeddingService(api_key=None)
    with pytest.raises(ValueError, match="API key not found"):
        service.get_client()


def test_embed_texts_mocked():
    """Verify batching and vector extraction in embed_texts."""
    mock_client = MagicMock()
    
    # 3 texts, batch size 2 -> 2 calls to client.embeddings.create
    texts = ["Text one", "Text two", "Text three"]
    
    mock_client.embeddings.create.side_effect = [
        create_mock_embedding_response(texts[:2], dim=1536),
        create_mock_embedding_response(texts[2:], dim=1536),
    ]

    service = EmbeddingService(client=mock_client, model="text-embedding-3-small")
    vectors = service.embed_texts(texts, batch_size=2)

    assert len(vectors) == 3
    assert len(vectors[0]) == 1536
    assert len(vectors[1]) == 1536
    assert len(vectors[2]) == 1536
    assert mock_client.embeddings.create.call_count == 2


def test_embed_chunks_preserves_metadata_and_text():
    """Verify embed_chunks attaches embeddings to source chunks with proper metadata."""
    mock_client = MagicMock()
    
    chunks = [
        {
            "text": "Password reset instructions for learner accounts.",
            "metadata": {"source": "account-guide.md", "chunk_index": 0}
        },
        {
            "text": "Learners can recover access using their registered email.",
            "metadata": {"source": "account-guide.md", "chunk_index": 1}
        }
    ]
    
    mock_client.embeddings.create.return_value = create_mock_embedding_response(
        [c["text"] for c in chunks], dim=1536
    )

    service = EmbeddingService(client=mock_client, model="text-embedding-3-small")
    records = service.embed_chunks(chunks)

    assert len(records) == 2
    
    # Verify record 0
    assert records[0]["text"] == "Password reset instructions for learner accounts."
    assert records[0]["metadata"]["source"] == "account-guide.md"
    assert records[0]["metadata"]["chunk_index"] == 0
    assert len(records[0]["embedding"]) == 1536
    assert records[0]["embedding_dim"] == 1536
    assert records[0]["model"] == "text-embedding-3-small"

    # Verify record 1
    assert records[1]["text"] == "Learners can recover access using their registered email."
    assert records[1]["metadata"]["chunk_index"] == 1


def test_embed_chunks_flat_format():
    """Verify embed_chunks handles flat chunk dicts produced by ChunkingService."""
    mock_client = MagicMock()
    
    chunks = [
        {
            "text": "Flexible Hours Program details.",
            "source": "work_hours.md",
            "index": 0,
            "token_count": 5,
            "start_token": 0,
            "end_token": 5
        }
    ]
    
    mock_client.embeddings.create.return_value = create_mock_embedding_response(
        [c["text"] for c in chunks], dim=1536
    )

    service = EmbeddingService(client=mock_client)
    records = service.embed_chunks(chunks)

    assert len(records) == 1
    assert records[0]["text"] == "Flexible Hours Program details."
    assert records[0]["metadata"]["source"] == "work_hours.md"
    assert records[0]["metadata"]["index"] == 0
    assert records[0]["metadata"]["token_count"] == 5
    assert len(records[0]["embedding"]) == 1536


def test_embed_query():
    """Verify embed_query returns a 1D vector using the configured model."""
    mock_client = MagicMock()
    mock_client.embeddings.create.return_value = create_mock_embedding_response(
        ["How do I reset password?"], dim=1536
    )

    service = EmbeddingService(client=mock_client, model="text-embedding-3-small")
    vector = service.embed_query("How do I reset password?")

    assert isinstance(vector, list)
    assert len(vector) == 1536
    mock_client.embeddings.create.assert_called_once_with(
        model="text-embedding-3-small",
        input=["How do I reset password?"]
    )


def test_embed_edge_cases():
    """Verify edge cases like empty texts, empty query, and invalid batch_size."""
    service = EmbeddingService(api_key="mock-key")
    
    assert service.embed_texts([]) == []
    assert service.embed_chunks([]) == []
    
    with pytest.raises(ValueError, match="batch_size must be positive"):
        service.embed_texts(["sample"], batch_size=0)

    with pytest.raises(ValueError, match="Query string cannot be empty"):
        service.embed_query("")

    with pytest.raises(ValueError, match="Query string cannot be empty"):
        service.embed_query("   ")


def test_cosine_similarity():
    """Verify cosine similarity calculation."""
    # Identical vectors -> 1.0
    v1 = [1.0, 2.0, 3.0]
    v2 = [1.0, 2.0, 3.0]
    assert pytest.approx(EmbeddingService.cosine_similarity(v1, v2), 0.0001) == 1.0

    # Orthogonal vectors -> 0.0
    v_orth1 = [1.0, 0.0]
    v_orth2 = [0.0, 1.0]
    assert pytest.approx(EmbeddingService.cosine_similarity(v_orth1, v_orth2), 0.0001) == 0.0

    # Opposites -> -1.0
    v_neg = [-1.0, -2.0, -3.0]
    assert pytest.approx(EmbeddingService.cosine_similarity(v1, v_neg), 0.0001) == -1.0

    # Dimension mismatch
    with pytest.raises(ValueError, match="Vector dimensions do not match"):
        EmbeddingService.cosine_similarity([1.0, 2.0], [1.0, 2.0, 3.0])
