"""Document loading and preparation services for PolicyPilot RAG Assistant.

Extracts text from multiple formats (PDF, HTML, MD, TXT), handles failures,
and tracks document metadata.
"""

import logging
from pathlib import Path
from pypdf import PdfReader
from bs4 import BeautifulSoup
from src.services.cleaning_service import TextCleaningService
from src.services.chunking_service import ChunkingService

logger = logging.getLogger(__name__)


class DocumentService:
    """Prepare knowledge-base documents for indexing."""

    def __init__(self):
        self.cleaner = TextCleaningService()
        self.chunker = ChunkingService()

    def load_text(self, path: Path) -> str:
        """Extract plain text from a supported file format.

        Supported formats: .pdf, .txt, .md, .html, .htm.
        """
        suffix = path.suffix.lower()
        
        if suffix == ".pdf":
            reader = PdfReader(path)
            text_parts = []
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            return "\n".join(text_parts)
            
        elif suffix in (".txt", ".md"):
            return path.read_text(encoding="utf-8", errors="ignore")
            
        elif suffix in (".html", ".htm"):
            raw_html = path.read_text(encoding="utf-8", errors="ignore")
            soup = BeautifulSoup(raw_html, "html.parser")
            # Decompose script and style tags to avoid raw code/styles in text representation
            for element in soup(["script", "style"]):
                element.decompose()
            return soup.get_text(" ")
            
        else:
            raise ValueError(f"Unsupported file format: {suffix}")

    def load_documents(self, data_dir: str = "data", clean: bool = True) -> list:
        """Load documents from the configured data directory.

        Robustly handles missing, corrupt, or unsupported files by logging
        and skipping them instead of crashing.
        """
        docs = []
        path_dir = Path(data_dir)
        
        if not path_dir.exists() or not path_dir.is_dir():
            logger.error("Data directory does not exist or is not a directory: %s", data_dir)
            return docs
            
        # Iterate recursively over all files in the directory
        for path in sorted(path_dir.rglob("*")):
            if not path.is_file():
                continue
                
            # Skip hidden files and gitkeeps
            if path.name.startswith(".") or path.name == ".gitkeep":
                continue
                
            try:
                # Check for existence (handling missing file edge cases)
                if not path.exists():
                    raise FileNotFoundError(f"File not found: {path.name}")
                    
                text = self.load_text(path)
                if text is None:
                    text = ""
                
                if clean:
                    text = self.cleaner.clean_text(text)
                    
                doc_info = {
                    "source": path.name,
                    "text": text,
                    "char_count": len(text)
                }
                docs.append(doc_info)
                
                # Preview sample (first 60 characters)
                sample = text[:60].replace("\n", " ").strip()
                print(f"OK {path.name}: {len(text)} chars | {sample!r}")
                
            except Exception as e:
                # Handle error gracefully by printing standard failure message and continuing
                print(f"SKIP {path.name}: {e}")
                logger.warning("Failed to load document %s: %s", path.name, e)
                
        return docs

    def load_and_chunk_documents(
        self,
        data_dir: str = "data",
        clean: bool = True,
        chunk_size: int = 400,
        chunk_overlap: int = 60
    ) -> list:
        """Load documents, clean them, and split them into token-aware chunks.

        Robustly handles loader issues and chunks each successfully loaded document.
        """
        docs = self.load_documents(data_dir=data_dir, clean=clean)
        all_chunks = []
        for doc in docs:
            chunks = self.chunker.chunk_document(doc, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
            all_chunks.extend(chunks)
        return all_chunks