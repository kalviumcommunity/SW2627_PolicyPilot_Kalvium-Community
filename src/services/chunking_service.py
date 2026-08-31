"""Token-aware chunking service for PolicyPilot RAG Assistant.

Splits document texts into chunks of controlled token size with overlap
to preserve context at chunk boundaries.
"""

import logging
from typing import List, Dict, Any
import tiktoken

logger = logging.getLogger(__name__)


class ChunkingService:
    """Service to split cleaned text into token-based chunks with controlled overlap."""

    def __init__(self, encoding_name: str = "cl100k_base"):
        """Initialize the chunker with a specified tiktoken encoding."""
        try:
            self.encoding = tiktoken.get_encoding(encoding_name)
        except Exception as e:
            logger.error("Failed to load tiktoken encoding %s: %s. Falling back to cl100k_base.", encoding_name, e)
            self.encoding = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in a given text string.

        Safely handles special tokens by encoding them without raising errors.
        """
        if not text:
            return 0
        try:
            return len(self.encoding.encode(text, disallowed_special=()))
        except Exception as e:
            logger.warning("Error encoding text for token count: %s", e)
            return len(self.encoding.encode(text))

    def chunk_text(self, text: str, chunk_size: int = 400, chunk_overlap: int = 60) -> List[Dict[str, Any]]:
        """Split text into chunks of specified token count with controlled overlap.

        Args:
            text: The text to chunk.
            chunk_size: Maximum token count per chunk. Must be > 0.
            chunk_overlap: Overlap in tokens between adjacent chunks. Must be >= 0 and < chunk_size.

        Returns:
            A list of chunk dictionaries containing:
                - text: The decoded chunk string.
                - token_count: Token count of the chunk.
                - index: Sequential index of the chunk.
                - start_token: Start token index in the original text.
                - end_token: End token index in the original text.
        """
        # Validate inputs
        if chunk_size <= 0:
            raise ValueError(f"chunk_size must be positive, got {chunk_size}")
        if chunk_overlap < 0:
            raise ValueError(f"chunk_overlap must be non-negative, got {chunk_overlap}")
        if chunk_overlap >= chunk_size:
            raise ValueError(f"chunk_overlap ({chunk_overlap}) must be strictly less than chunk_size ({chunk_size})")

        if not text or not text.strip():
            return []

        # Encode text to tokens, allowing all special tokens (like <|endoftext|>)
        tokens = self.encoding.encode(text, disallowed_special=())
        num_tokens = len(tokens)

        if num_tokens == 0:
            return []

        chunks = []
        i = 0
        chunk_idx = 0

        while i < num_tokens:
            # Determine end index for this chunk
            end_idx = min(i + chunk_size, num_tokens)
            chunk_tokens = tokens[i:end_idx]

            # Decode tokens to get the text of this chunk
            chunk_text = self.encoding.decode(chunk_tokens)

            chunks.append({
                "text": chunk_text,
                "token_count": len(chunk_tokens),
                "index": chunk_idx,
                "start_token": i,
                "end_token": end_idx
            })

            # Check if this chunk reached the end of the text
            if end_idx == num_tokens:
                break

            # Advance starting point: step size is (chunk_size - chunk_overlap)
            chunk_idx += 1
            i += (chunk_size - chunk_overlap)

        return chunks

    def chunk_document(self, doc: Dict[str, Any], chunk_size: int = 400, chunk_overlap: int = 60) -> List[Dict[str, Any]]:
        """Chunk a document dictionary (as loaded by DocumentService) and include source metadata.

        Args:
            doc: A dictionary containing 'source' and 'text'.
            chunk_size: Maximum token count per chunk.
            chunk_overlap: Overlap in tokens between adjacent chunks.

        Returns:
            A list of chunk dictionaries with source document metadata.
        """
        source = doc.get("source", "unknown")
        text = doc.get("text", "")
        
        chunks = self.chunk_text(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        
        # Inject metadata into each chunk
        for chunk in chunks:
            chunk["source"] = source
            
        return chunks
