"""Document loading and preparation services."""

import os
from pathlib import Path


class DocumentService:
    """Prepare knowledge-base documents for indexing."""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)

    def load_documents(self) -> str:
        """Load documents from the configured data directory."""
        if not self.data_dir.exists():
            return ""

        documents = []
        # Support running from tests directory or project root
        search_path = self.data_dir
        if not search_path.is_absolute():
            # Try to resolve relative to current work dir or file parent
            if not search_path.exists():
                search_path = Path(__file__).resolve().parents[2] / self.data_dir

        if not search_path.exists():
            return ""

        for file_path in search_path.glob("*.txt"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    documents.append(f.read())
            except Exception as e:
                print(f"Error reading file {file_path}: {e}")

        return "\n\n".join(documents)