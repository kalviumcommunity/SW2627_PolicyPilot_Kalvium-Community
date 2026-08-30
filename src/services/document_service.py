"""Document loading and preparation services."""

import os
from pathlib import Path


class DocumentService:
    """Prepare knowledge-base documents for indexing."""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)

    def load_documents(self) -> list:
        """Load documents from the configured data directory.

        Returns a list of dictionaries, each containing:
          - 'text': content of the file
          - 'source': filename of the file
        """
        if not self.data_dir.exists():
            return []

        documents = []
        # Support running from tests directory or project root
        search_path = self.data_dir
        if not search_path.is_absolute():
            # Try to resolve relative to current work dir or file parent
            if not search_path.exists():
                search_path = Path(__file__).resolve().parents[2] / self.data_dir

        if not search_path.exists():
            return []

        for file_path in search_path.glob("*.txt"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    documents.append({
                        "text": f.read(),
                        "source": file_path.name
                    })
            except Exception as e:
                print(f"Error reading file {file_path}: {e}")

        return documents

    def chunk_documents(self, documents: list) -> list:
        """Split documents into chunks by double newline, preserving metadata.

        Returns a list of chunk objects, each containing:
          - 'text': chunk text (stripped)
          - 'metadata': dict with 'source', 'chunk_index', and 'char_start'
        """
        chunks = []
        for doc in documents:
            text = doc["text"]
            source = doc["source"]

            curr_pos = 0
            raw_sections = text.split("\n\n")
            chunk_index = 0
            for sec in raw_sections:
                sec_stripped = sec.strip()
                if not sec_stripped:
                    continue

                char_start = text.find(sec, curr_pos)
                if char_start == -1:
                    char_start = curr_pos
                else:
                    curr_pos = char_start + len(sec)

                chunks.append({
                    "text": sec_stripped,
                    "metadata": {
                        "source": source,
                        "chunk_index": chunk_index,
                        "char_start": char_start
                    }
                })
                chunk_index += 1
        return chunks