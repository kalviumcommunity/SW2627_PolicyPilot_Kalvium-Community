"""Knowledge-base retrieval services."""


class RetrievalService:
    """Find relevant documents for a user question."""

    def search(self, query):
        """Return documents relevant to a query."""
        raise NotImplementedError