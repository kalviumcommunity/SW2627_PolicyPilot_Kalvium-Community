"""OpenAI-compatible embeddings service for PolicyPilot RAG Assistant.

Generates dense vector embeddings for document chunks and user queries using
OpenAI or OpenAI-compatible embedding APIs (e.g. text-embedding-3-small).
Attaches vectors to source chunk text and retrieval metadata.
"""

import os
import math
import logging
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service to generate and manage text embeddings for document chunks and queries."""

    DEFAULT_MODEL = "text-embedding-3-small"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        client: Optional[OpenAI] = None,
    ):
        """Initialize the embedding service with environment variables or explicit config.

        Args:
            api_key: Optional OpenAI/compatible API key. Falls back to OPENAI_API_KEY or API_KEY in env.
            base_url: Optional API base URL. Falls back to OPENAI_BASE_URL or API_BASE_URL in env.
            model: Optional embedding model name. Falls back to EMBEDDING_MODEL in env or DEFAULT_MODEL.
            client: Optional pre-configured OpenAI client instance (e.g., for testing or mocks).
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or os.getenv("API_KEY")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL") or os.getenv("API_BASE_URL")
        self.model = model or os.getenv("EMBEDDING_MODEL") or self.DEFAULT_MODEL
        
        self._client = client

    def get_client(self) -> OpenAI:
        """Get or initialize the OpenAI client instance."""
        if self._client is None:
            if not self.api_key:
                raise ValueError(
                    "API key not found. Please set API_KEY in your environment or .env file."
                )
            
            client_kwargs: Dict[str, Any] = {"api_key": self.api_key}
            if self.base_url:
                client_kwargs["base_url"] = self.base_url
                
            self._client = OpenAI(**client_kwargs)
            
        return self._client

    def embed_texts(
        self,
        texts: List[str],
        model: Optional[str] = None,
        batch_size: int = 64,
    ) -> List[List[float]]:
        """Generate embedding vectors for a list of text strings in batches.

        Args:
            texts: List of text strings to embed.
            model: Embedding model name. Defaults to configured service model.
            batch_size: Maximum number of texts sent in a single API call.

        Returns:
            List of embedding vectors (floats), matching the order of input texts.
        """
        if not texts:
            return []

        if batch_size <= 0:
            raise ValueError(f"batch_size must be positive, got {batch_size}")

        active_model = model or self.model
        client = self.get_client()
        all_embeddings: List[List[float]] = []

        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i : i + batch_size]
            try:
                response = client.embeddings.create(
                    model=active_model,
                    input=batch_texts,
                )
                # Extract embeddings in matching order
                batch_vectors = [item.embedding for item in response.data]
                all_embeddings.extend(batch_vectors)
            except Exception as e:
                logger.error("Error creating embeddings for batch [%d:%d]: %s", i, i + len(batch_texts), e)
                raise

        return all_embeddings

    def embed_chunks(
        self,
        chunks: List[Dict[str, Any]],
        model: Optional[str] = None,
        batch_size: int = 64,
    ) -> List[Dict[str, Any]]:
        """Generate embeddings for document chunks and store vectors with metadata and source text.

        Args:
            chunks: List of chunk dictionaries. Each chunk must contain 'text' and optional metadata.
            model: Embedding model name. Defaults to configured service model.
            batch_size: Batch size for API requests.

        Returns:
            List of stored records, each containing:
                - text: The original chunk text.
                - metadata: Dictionary containing source document, chunk index, token counts, etc.
                - embedding: The dense embedding vector.
                - embedding_dim: Dimensionality of the vector.
                - model: Model name used to produce the embedding.
        """
        if not chunks:
            return []

        active_model = model or self.model
        texts = [chunk.get("text", "") for chunk in chunks]
        
        vectors = self.embed_texts(texts=texts, model=active_model, batch_size=batch_size)

        records: List[Dict[str, Any]] = []
        for chunk, vector in zip(chunks, vectors):
            # Extract metadata: preserve nested 'metadata' if present, or collect non-text keys
            if "metadata" in chunk and isinstance(chunk["metadata"], dict):
                metadata = dict(chunk["metadata"])
            else:
                metadata = {k: v for k, v in chunk.items() if k != "text"}

            records.append({
                "text": chunk.get("text", ""),
                "metadata": metadata,
                "embedding": vector,
                "embedding_dim": len(vector),
                "model": active_model,
            })

        return records

    def embed_query(self, query: str, model: Optional[str] = None) -> List[float]:
        """Generate an embedding vector for a single user search query using the identical model.

        Args:
            query: The user query string.
            model: Model name. Defaults to configured service model.

        Returns:
            Embedding vector (List[float]) for the query.
        """
        if not query or not query.strip():
            raise ValueError("Query string cannot be empty or blank")

        active_model = model or self.model
        vectors = self.embed_texts([query], model=active_model, batch_size=1)
        if not vectors:
            raise RuntimeError("Embeddings API returned empty response for query")
        return vectors[0]

    @staticmethod
    def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two dense embedding vectors.

        Returns:
            Cosine similarity score between -1.0 and 1.0 (typically 0.0 to 1.0 for normalized embeddings).
        """
        if not vec1 or not vec2:
            return 0.0
        if len(vec1) != len(vec2):
            raise ValueError(f"Vector dimensions do not match: {len(vec1)} vs {len(vec2)}")

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm_a = math.sqrt(sum(a * a for a in vec1))
        norm_b = math.sqrt(sum(b * b for b in vec2))

        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0

        return dot_product / (norm_a * norm_b)
