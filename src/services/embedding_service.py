"""Embedding generation and vector operations services for PolicyPilot."""

import os
import hashlib
import numpy as np
from typing import List, Dict, Any
from openai import OpenAI


class EmbeddingService:
    """Service to handle embedding generation and vector similarity calculations."""

    def __init__(self):
        # Load environment variables
        self.api_base_url = os.getenv("API_BASE_URL")
        self.api_key = os.getenv("API_KEY")
        self.model = os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002")

        self.client = None
        if self.api_base_url and self.api_key:
            try:
                self.client = OpenAI(
                    base_url=self.api_base_url, api_key=self.api_key
                )
            except Exception:
                self.client = None

    def generate_embedding(self, text: str) -> List[float]:
        """Generate a 1536-dimensional vector embedding for the input text.
        
        Uses the OpenAI API if configured, otherwise falls back to a deterministic 
        local mock embedding generator.
        """
        if not text:
            return [0.0] * 1536

        if self.client:
            try:
                response = self.client.embeddings.create(
                    input=[text],
                    model=self.model
                )
                return response.data[0].embedding
            except Exception:
                # Fallback to local mock on API failures
                return self._generate_mock_embedding(text)
        else:
            return self._generate_mock_embedding(text)

    def _generate_mock_embedding(self, text: str) -> List[float]:
        """Generate a deterministic 1536-dimensional mock embedding vector.
        
        To simulate semantic understanding offline, we normalize synonyms/related words
        to canonical roots, generate deterministic unit vectors for each word via MD5 seeding,
        and normalize their sum.
        """
        # 1. Clean and tokenize text
        cleaned_text = "".join(c for c in text.lower() if c.isalnum() or c.isspace())
        raw_words = cleaned_text.split()

        # 2. Map synonyms for mock semantic grouping
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

        if not words:
            return [0.0] * 1536

        # 3. Sum up deterministic word vectors
        vector_dim = 1536
        sum_vector = np.zeros(vector_dim)

        for word in words:
            # Seed generator using a deterministic MD5 hash of the word
            hash_val = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16) % (2**32)
            rng = np.random.default_rng(hash_val)
            word_vec = rng.standard_normal(vector_dim)
            
            # Normalize the word vector to a unit vector
            norm = np.linalg.norm(word_vec)
            if norm > 0:
                word_vec = word_vec / norm
                
            sum_vector += word_vec

        # 4. Normalize the final sentence vector
        final_norm = np.linalg.norm(sum_vector)
        if final_norm > 0:
            sum_vector = sum_vector / final_norm

        return sum_vector.tolist()

    def cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        """Calculate the cosine similarity between two 1536-dimensional vectors."""
        vec1 = np.array(v1)
        vec2 = np.array(v2)
        
        dot_product = np.dot(vec1, vec2)
        norm_v1 = np.linalg.norm(vec1)
        norm_v2 = np.linalg.norm(vec2)
        
        if norm_v1 == 0 or norm_v2 == 0:
            return 0.0
            
        return float(dot_product / (norm_v1 * norm_v2))
