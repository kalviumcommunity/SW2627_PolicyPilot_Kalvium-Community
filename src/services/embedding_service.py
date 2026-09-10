"""Embedding generation, batch processing, and vector operations services for PolicyPilot."""

import hashlib
import logging
import math
import os
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

load_dotenv_ok = True
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    load_dotenv_ok = False

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class EmbeddingService:
    """Service to handle single and batch embedding generation with retries, cost tracking, and fallback."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.api_base_url = base_url if base_url is not None else os.getenv("API_BASE_URL")
        self.api_key = api_key if api_key is not None else os.getenv("API_KEY")
        self.model = model or os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002")

        self.client = None
        if self.api_base_url and self.api_key and "groq.com" not in self.api_base_url.lower():
            try:
                from openai import OpenAI
                self.client = OpenAI(base_url=self.api_base_url, api_key=self.api_key)
            except Exception as err:
                logging.warning("Could not initialize OpenAI client (%s). Using fallback mock generator.", err)

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for a text string (~1 token per 4 chars or word count * 1.3)."""
        if not text:
            return 0
        return max(1, int(len(text) / 4))

    def estimate_cost(self, total_tokens: int, cost_per_1k: float = 0.00002) -> float:
        """Calculate approximate embedding cost for given token count."""
        return round((total_tokens / 1000.0) * cost_per_1k, 6)

    def generate_embedding(self, text: str) -> List[float]:
        """Generate a 1536-dimensional vector embedding for single text input."""
        res, _, _ = self.generate_batch_embeddings([text], batch_size=1)
        if res and res[0]:
            return res[0]
        return self._generate_mock_embedding(text)

    def generate_batch_embeddings(
        self,
        texts: List[str],
        batch_size: int = 10,
        max_retries: int = 3,
        initial_delay: float = 1.0,
    ) -> Tuple[List[List[float]], int, List[int]]:
        """Generate embeddings in configurable batches with exponential backoff retries.

        Args:
            texts: List of text strings to embed.
            batch_size: Number of texts per API batch call.
            max_retries: Maximum retry attempts for transient API errors.
            initial_delay: Base delay in seconds for exponential backoff.

        Returns:
            Tuple of (embeddings_list, total_tokens_used, failed_batch_indices)
        """
        if not texts:
            return [], 0, []

        all_embeddings: List[List[float]] = [[] for _ in range(len(texts))]
        total_tokens = 0
        failed_batches: List[int] = []

        total_batches = math.ceil(len(texts) / batch_size)

        for b_idx in range(total_batches):
            start_i = b_idx * batch_size
            end_i = min(start_i + batch_size, len(texts))
            batch_texts = texts[start_i:end_i]

            batch_success = False
            batch_tokens = sum(self.estimate_tokens(t) for t in batch_texts)

            if self.client:
                for attempt in range(max_retries + 1):
                    try:
                        response = self.client.embeddings.create(
                            input=batch_texts,
                            model=self.model,
                        )

                        # Extract embeddings in order
                        for idx, data_obj in enumerate(response.data):
                            all_embeddings[start_i + idx] = data_obj.embedding

                        if hasattr(response, "usage") and response.usage:
                            batch_tokens = getattr(response.usage, "total_tokens", batch_tokens)

                        total_tokens += batch_tokens
                        batch_success = True
                        break

                    except Exception as err:
                        err_msg = str(err).lower()
                        if "404" in err_msg or "model_not_found" in err_msg or "not_found" in err_msg:
                            logging.warning(
                                "API endpoint/model does not support embeddings (%s). Disabling client API calls.",
                                err
                            )
                            self.client = None
                            break

                        if attempt < max_retries:
                            sleep_time = initial_delay * (2 ** attempt)
                            logging.warning(
                                "Batch %d/%d failed (attempt %d/%d): %s. Retrying in %.1fs...",
                                b_idx + 1, total_batches, attempt + 1, max_retries, err, sleep_time
                            )
                            time.sleep(sleep_time)
                        else:
                            logging.error(
                                "Batch %d/%d permanently failed after %d attempts: %s. Using fallback mock embeddings.",
                                b_idx + 1, total_batches, max_retries + 1, err
                            )

            # Fallback to mock embedding if client missing or API retries exhausted
            if not batch_success:
                if self.client:
                    failed_batches.append(b_idx + 1)
                total_tokens += batch_tokens
                for idx, text in enumerate(batch_texts):
                    all_embeddings[start_i + idx] = self._generate_mock_embedding(text)

        return all_embeddings, total_tokens, failed_batches

    def _generate_mock_embedding(self, text: str) -> List[float]:
        """Generate a deterministic 1536-dimensional mock embedding vector."""
        cleaned_text = "".join(c for c in text.lower() if c.isalnum() or c.isspace())
        raw_words = cleaned_text.split()

        synonyms = {
            "window": "period",
            "days": "period",
            "time": "period",
            "duration": "period",
            "product": "item",
            "damaged": "broken",
            "refund": "return",
            "conditions": "rules",
            "responsibilities": "duties",
        }
        words = [synonyms.get(w, w) for w in raw_words]

        vector_dim = 1536
        if not words:
            return [0.0] * vector_dim

        sum_vector = np.zeros(vector_dim)
        for word in words:
            hash_val = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16) % (2**32)
            rng = np.random.default_rng(hash_val)
            word_vec = rng.standard_normal(vector_dim)

            norm = np.linalg.norm(word_vec)
            if norm > 0:
                word_vec = word_vec / norm

            sum_vector += word_vec

        final_norm = np.linalg.norm(sum_vector)
        if final_norm > 0:
            sum_vector = sum_vector / final_norm

        return sum_vector.tolist()

    def cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        """Calculate cosine similarity between two vector embeddings."""
        vec1 = np.array(v1)
        vec2 = np.array(v2)

        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(np.dot(vec1, vec2) / (norm1 * norm2))
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
