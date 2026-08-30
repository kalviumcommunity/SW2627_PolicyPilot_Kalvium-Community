"""Knowledge-base retrieval services."""


class RetrievalService:
    """Find relevant documents for a user question."""

    def search(self, query: str, chunks: list) -> list:
        """Return sections of chunks relevant to a query.

        Filters chunks based on matching keywords from the query, preserving metadata.
        """
        if not chunks or not query:
            return []

        # Normalize query and extract keywords
        query_words = set(query.lower().replace("?", "").replace(".", "").split())
        stop_words = {
            "what",
            "is",
            "our",
            "the",
            "a",
            "an",
            "can",
            "i",
            "for",
            "to",
            "are",
            "under",
            "with",
            "in",
            "of",
            "and",
            "on",
            "it",
            "do",
            "does",
            "should",
        }
        keywords = query_words - stop_words
        relevant_chunks = []

        for chunk in chunks:
            text_lower = chunk["text"].lower()
            matches = sum(1 for kw in keywords if kw in text_lower)
            if matches > 0:
                relevant_chunks.append((chunk, matches))

        if relevant_chunks:
            # Sort chunks by keyword match density descending
            relevant_chunks.sort(key=lambda x: x[1], reverse=True)
            return [item[0] for item in relevant_chunks]

        # If no specific matches, return empty list
        return []