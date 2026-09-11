"""Consistent online/offline embeddings for PolicyPilot."""

from __future__ import annotations

import hashlib
import logging
import math
import os
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:  # pragma: no cover - dotenv is optional at import time
    pass

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Generate document and query vectors with one shared model/fallback."""

    DEFAULT_MODEL = "text-embedding-3-small"
    DIMENSION = 1536

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        client: Optional[Any] = None,
    ):
        self.api_key = api_key if api_key is not None else (
            os.getenv("OPENAI_API_KEY") or os.getenv("API_KEY")
        )
        self.base_url = base_url if base_url is not None else (
            os.getenv("OPENAI_BASE_URL") or os.getenv("API_BASE_URL")
        )
        self.model = model or os.getenv("EMBEDDING_MODEL") or self.DEFAULT_MODEL
        self._client = client
        self.use_remote = os.getenv("POLICYPILOT_ENABLE_REMOTE", "false").lower() in {"1", "true", "yes"}

    @property
    def client(self) -> Optional[Any]:
        return self._client

    @client.setter
    def client(self, value: Optional[Any]) -> None:
        self._client = value

    def get_client(self) -> Any:
        """Return an OpenAI-compatible client, or raise when explicitly requested."""
        if self._client is not None:
            return self._client
        if not self.api_key:
            raise ValueError("API key not found. Please set API_KEY in your environment or .env file.")
        from openai import OpenAI

        kwargs: Dict[str, Any] = {"api_key": self.api_key}
        if self.base_url:
            kwargs["base_url"] = self.base_url
        self._client = OpenAI(**kwargs)
        return self._client

    @staticmethod
    def estimate_tokens(text: str) -> int:
        return 0 if not text else max(1, int(len(text) / 4))

    @staticmethod
    def estimate_cost(total_tokens: int, cost_per_1k: float = 0.00002) -> float:
        return round((total_tokens / 1000.0) * cost_per_1k, 6)

    @staticmethod
    def _normalise_words(text: str) -> List[str]:
        synonyms = {
            "window": "period", "days": "period", "time": "period",
            "duration": "period", "product": "item", "damaged": "broken",
            "conditions": "rules", "responsibilities": "duties",
            "hours": "hour", "working": "work", "bookings": "book",
            "booked": "book", "submitted": "submit", "submission": "submit",
        }
        words = "".join(c.lower() if c.isalnum() or c.isspace() else " " for c in text).split()
        return [synonyms.get(word, word) for word in words]

    def _offline_embedding(self, text: str) -> List[float]:
        """Stable feature-hash embedding used identically for docs and queries."""
        words = self._normalise_words(text)
        if not words:
            return [0.0] * self.DIMENSION
        vector = np.zeros(self.DIMENSION, dtype=np.float64)
        for word in words:
            seed = int(hashlib.sha256(word.encode("utf-8")).hexdigest()[:16], 16)
            rng = np.random.default_rng(seed)
            word_vector = rng.standard_normal(self.DIMENSION)
            norm = np.linalg.norm(word_vector)
            if norm:
                vector += word_vector / norm
        norm = np.linalg.norm(vector)
        return (vector / norm if norm else vector).tolist()

    def embed_texts(
        self,
        texts: List[str],
        model: Optional[str] = None,
        batch_size: int = 64,
        max_retries: int = 3,
        initial_delay: float = 1.0,
    ) -> List[List[float]]:
        if not texts:
            return []
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")

        if self._client is None and (not self.api_key or not self.use_remote):
            return [self._offline_embedding(text) for text in texts]

        try:
            client = self.get_client()
        except Exception:
            return [self._offline_embedding(text) for text in texts]

        vectors: List[List[float]] = []
        active_model = model or self.model
        self._last_request_failed = False
        for start in range(0, len(texts), batch_size):
            batch = texts[start:start + batch_size]
            response = None
            for attempt in range(max_retries + 1):
                try:
                    response = client.embeddings.create(model=active_model, input=batch)
                    break
                except Exception as exc:
                    error_text = str(exc).lower()
                    if "404" in error_text or "not found" in error_text or "model_not_found" in error_text:
                        logger.warning("Embedding model unavailable; using offline fallback: %s", exc)
                        self._last_request_failed = True
                        response = None
                        break
                    if attempt >= max_retries:
                        logger.warning("Embedding API unavailable; using offline fallback: %s", exc)
                        self._last_request_failed = True
                        response = None
                        break
                    time.sleep(initial_delay * (2 ** attempt))
            if response is None:
                vectors.extend(self._offline_embedding(text) for text in batch)
            else:
                vectors.extend(item.embedding for item in response.data)
        return vectors

    def embed_chunks(self, chunks: List[Dict[str, Any]], model: Optional[str] = None,
                     batch_size: int = 64) -> List[Dict[str, Any]]:
        texts = [str(chunk.get("text") or chunk.get("content") or "") for chunk in chunks]
        vectors = self.embed_texts(texts, model=model, batch_size=batch_size)
        active_model = model or self.model
        records = []
        for chunk, text, vector in zip(chunks, texts, vectors):
            metadata = dict(chunk.get("metadata", {})) if isinstance(chunk.get("metadata"), dict) else {
                key: value for key, value in chunk.items() if key not in {"text", "content", "embedding"}
            }
            records.append({
                "text": text, "metadata": metadata, "embedding": vector,
                "embedding_dim": len(vector), "model": active_model,
            })
        return records

    def embed_query(self, query: str, model: Optional[str] = None) -> List[float]:
        if not query or not query.strip():
            raise ValueError("Query string cannot be empty or blank")
        return self.embed_texts([query], model=model, batch_size=1)[0]

    def generate_embedding(self, text: str) -> List[float]:
        if not text or not text.strip():
            return [0.0] * self.DIMENSION
        return self.embed_query(text)

    def generate_batch_embeddings(
        self, texts: List[str], batch_size: int = 10, max_retries: int = 3,
        initial_delay: float = 1.0,
    ) -> Tuple[List[List[float]], int, List[int]]:
        if not texts:
            return [], 0, []
        total_tokens = sum(self.estimate_tokens(text) for text in texts)
        failed_batches: List[int] = []
        if self._client is None and not self.api_key:
            return self.embed_texts(texts, batch_size=batch_size), total_tokens, failed_batches
        vectors: List[List[float]] = []
        for batch_index, start in enumerate(range(0, len(texts), batch_size), start=1):
            batch = texts[start:start + batch_size]
            try:
                vectors.extend(self.embed_texts(batch, batch_size=len(batch),
                                                max_retries=max_retries,
                                                initial_delay=initial_delay))
                if getattr(self, "_last_request_failed", False):
                    failed_batches.append(batch_index)
            except Exception:
                failed_batches.append(batch_index)
                vectors.extend(self._offline_embedding(text) for text in batch)
        return vectors, total_tokens, failed_batches

    @staticmethod
    def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        if not vec1 or not vec2:
            return 0.0
        if len(vec1) != len(vec2):
            raise ValueError(f"Vector dimensions do not match: {len(vec1)} vs {len(vec2)}")
        norm_a = math.sqrt(sum(value * value for value in vec1))
        norm_b = math.sqrt(sum(value * value for value in vec2))
        if not norm_a or not norm_b:
            return 0.0
        return sum(a * b for a, b in zip(vec1, vec2)) / (norm_a * norm_b)
