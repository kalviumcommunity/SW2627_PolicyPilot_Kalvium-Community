"""Document loading and preparation services for PolicyPilot."""

import os
from pathlib import Path
from typing import Dict, List, Any, Optional


class DocumentService:
    """Prepare knowledge-base documents for indexing and retrieval."""

    def __init__(self, data_dir: Optional[str] = None):
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            self.data_dir = Path(__file__).resolve().parents[2] / "data"

    def load_documents(self) -> List[Dict[str, Any]]:
        """Load all policy documents from the configured data directory."""
        documents = []
        if not self.data_dir.exists():
            return documents

        for file_path in self.data_dir.glob("*"):
            if file_path.suffix.lower() in [".md", ".txt"]:
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        text = f.read().strip()
                        if text:
                            documents.append({
                                "id": file_path.name,
                                "source": str(file_path),
                                "content": text,
                            })
                except Exception as err:
                    pass

        return documents

    def chunk_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Split documents into logical section or paragraph chunks."""
        chunks = []
        chunk_id = 1

        for doc in documents:
            paragraphs = doc["content"].split("\n\n")
            for para in paragraphs:
                para_clean = para.strip()
                if para_clean and not para_clean.startswith("# PolicyPilot"):
                    chunks.append({
                        "chunk_id": f"{doc['id']}_chunk_{chunk_id}",
                        "source": doc["source"],
                        "content": para_clean,
                    })
                    chunk_id += 1

        return chunks