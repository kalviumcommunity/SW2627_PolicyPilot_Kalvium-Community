"""Knowledge-base retrieval services."""


class RetrievalService:
    """Find relevant documents for a user question."""

    def search(self, query: str, context_documents: str) -> str:
        """Return sections of context_documents relevant to a query.

        Splits context_documents by section blocks and filters based on
        matching keywords from the query.
        """
        if not context_documents or not query:
            return ""

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

        # Split into distinct policy blocks
        sections = [
            sec.strip() for sec in context_documents.split("\n\n") if sec.strip()
        ]
        relevant_sections = []

        for section in sections:
            section_lower = section.lower()
            matches = sum(1 for kw in keywords if kw in section_lower)
            if matches > 0:
                relevant_sections.append((section, matches))

        if relevant_sections:
            # Sort sections by keyword match density descending
            relevant_sections.sort(key=lambda x: x[1], reverse=True)
            return "\n\n".join([sec[0] for sec in relevant_sections])

        # If no specific matches, return empty so grounding failure is triggered correctly
        return ""