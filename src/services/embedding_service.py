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
