"""Language-model response generation services."""


class ResponseService:
    """Generate an answer using retrieved context."""

    def generate(self, query, context):
        """Generate a response from a query and retrieved context."""
        raise NotImplementedError