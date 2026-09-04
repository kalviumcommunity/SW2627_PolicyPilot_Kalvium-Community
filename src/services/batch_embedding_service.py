"""Batch Embedding & Rate/Cost Management service for PolicyPilot."""

import time
from typing import List, Dict, Any, Optional, Callable
from src.services.embedding_service import EmbeddingService
from src.services.token_service import get_token_count


class BatchEmbeddingService:
    """Service to handle batch embedding generation with rate limiting, retry handling, and cost estimation."""

    def __init__(
        self,
        embedding_service: Optional[EmbeddingService] = None,
        batch_size: int = 10,
        max_retries: int = 3,
        initial_delay: float = 0.1,
        backoff_factor: float = 2.0,
        cost_per_1k_tokens: float = 0.0001,
        sleep_fn: Optional[Callable[[float], None]] = None,
    ):
        """Initialize the BatchEmbeddingService.

        Args:
            embedding_service: EmbeddingService instance. If None, creates a default instance.
            batch_size: Default batch size for chunk processing.
            max_retries: Maximum retry attempts for failed requests.
            initial_delay: Initial delay in seconds for exponential backoff.
            backoff_factor: Multiplier factor for backoff delay.
            cost_per_1k_tokens: Embedding cost per 1,000 input tokens (default $0.0001).
            sleep_fn: Function used to pause execution for retry backoff (defaults to time.sleep).
        """
        self.embedding_service = embedding_service or EmbeddingService()
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.backoff_factor = backoff_factor
        self.cost_per_1k_tokens = cost_per_1k_tokens
        self.sleep_fn = sleep_fn if sleep_fn is not None else time.sleep

    def calculate_embedding_cost(
        self, input_tokens: int, cost_per_1k_tokens: Optional[float] = None
    ) -> float:
        """Calculate approximate embedding cost for input tokens.

        Args:
            input_tokens: Number of input tokens.
            cost_per_1k_tokens: Custom rate per 1k tokens, if None uses service default.

        Returns:
            Calculated cost rounded to 8 decimal places.
        """
        if input_tokens <= 0:
            return 0.0
        rate = (
            cost_per_1k_tokens
            if cost_per_1k_tokens is not None
            else self.cost_per_1k_tokens
        )
        cost = (input_tokens / 1000.0) * rate
        return round(cost, 8)

    def generate_embedding_with_retry(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text with exponential backoff retries.

        Args:
            text: Text to generate embedding for.

        Returns:
            List of floats representing the embedding vector, or None if retries failed.
        """
        for attempt in range(self.max_retries + 1):
            try:
                embedding = self.embedding_service.generate_embedding(text)
                if embedding and isinstance(embedding, list) and len(embedding) > 0:
                    return embedding
                raise ValueError("Embedding service returned empty or invalid vector.")
            except Exception as e:
                if attempt < self.max_retries:
                    delay = self.initial_delay * (self.backoff_factor**attempt)
                    self.sleep_fn(delay)
                else:
                    return None
        return None

    def process_chunks(
        self,
        chunks: List[Dict[str, Any]],
        batch_size: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Process a list of text chunks in batches to generate missing embeddings.

        Resumable / Safe for partial runs:
        - Chunks that already contain a valid 'embedding' vector are skipped.
        - Un-embedded chunks are processed in batches with exponential backoff retries.
        - Calculates metrics: total, skipped, embedded, failed, input tokens, and estimated cost.

        Args:
            chunks: List of chunk dictionaries containing text content (and optional existing embeddings).
            batch_size: Optional batch size override for this run.

        Returns:
            Dictionary containing metrics and processed chunks:
            {
                "total_chunks": int,
                "skipped_chunks": int,
                "embedded_chunks": int,
                "failed_chunks": int,
                "input_tokens": int,
                "estimated_cost": float,
                "chunks": List[Dict[str, Any]]
            }
        """
        if not chunks:
            return {
                "total_chunks": 0,
                "skipped_chunks": 0,
                "embedded_chunks": 0,
                "failed_chunks": 0,
                "input_tokens": 0,
                "estimated_cost": 0.0,
                "chunks": [],
            }

        effective_batch_size = (
            batch_size if batch_size is not None and batch_size > 0 else self.batch_size
        )
        total_chunks = len(chunks)
        skipped_chunks = 0
        embedded_chunks = 0
        failed_chunks = 0
        total_input_tokens = 0

        # Partition chunks into batches for batch processing
        num_batches = (total_chunks + effective_batch_size - 1) // effective_batch_size

        for b_idx in range(num_batches):
            batch = chunks[b_idx * effective_batch_size : (b_idx + 1) * effective_batch_size]

            for chunk in batch:
                # Skip chunk if it already has a non-empty embedding
                existing_emb = chunk.get("embedding")
                if existing_emb is not None and isinstance(existing_emb, list) and len(existing_emb) > 0:
                    skipped_chunks += 1
                    continue

                text_content = chunk.get("content") or chunk.get("text", "")
                tokens = get_token_count(text_content)

                embedding = self.generate_embedding_with_retry(text_content)

                if embedding is not None:
                    chunk["embedding"] = embedding
                    embedded_chunks += 1
                    total_input_tokens += tokens
                else:
                    failed_chunks += 1

        estimated_cost = self.calculate_embedding_cost(total_input_tokens)

        return {
            "total_chunks": total_chunks,
            "skipped_chunks": skipped_chunks,
            "embedded_chunks": embedded_chunks,
            "failed_chunks": failed_chunks,
            "input_tokens": total_input_tokens,
            "estimated_cost": estimated_cost,
            "chunks": chunks,
        }
