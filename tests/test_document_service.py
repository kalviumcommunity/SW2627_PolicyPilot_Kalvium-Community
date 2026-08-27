"""Unit tests for DocumentService, verifying loader and error handling behaviors."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from src.services.document_service import DocumentService


def test_load_text_plain_and_markdown(tmp_path):
    """Verify load_text correctly extracts text from txt and md files."""
    txt_file = tmp_path / "test.txt"
    txt_file.write_text("Hello, this is a plain text file.", encoding="utf-8")
    
    md_file = tmp_path / "test.md"
    md_file.write_text("# Markdown Title\nThis is markdown.", encoding="utf-8")
    
    service = DocumentService()
    assert service.load_text(txt_file) == "Hello, this is a plain text file."
    assert service.load_text(md_file) == "# Markdown Title\nThis is markdown."


def test_load_text_html(tmp_path):
    """Verify load_text strips tags and script/style tags from HTML files."""
    html_file = tmp_path / "test.html"
    html_file.write_text(
        "<html><body><h1>Title</h1><p>Paragraph text.</p>"
        "<style>body {color: red;}</style>"
        "<script>console.log('hello');</script></body></html>", 
        encoding="utf-8"
    )
    
    service = DocumentService()
    text = service.load_text(html_file)
    assert "Title" in text
    assert "Paragraph text." in text
    assert "color: red" not in text
    assert "console.log" not in text


@patch("src.services.document_service.PdfReader")
def test_load_text_pdf(mock_pdf_reader, tmp_path):
    """Verify load_text utilizes pypdf PdfReader and extracts page texts."""
    pdf_file = tmp_path / "test.pdf"
    pdf_file.write_text("fake pdf content", encoding="utf-8")
    
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "Extracted PDF Page Text"
    
    mock_reader_instance = MagicMock()
    mock_reader_instance.pages = [mock_page]
    mock_pdf_reader.return_value = mock_reader_instance
    
    service = DocumentService()
    assert service.load_text(pdf_file) == "Extracted PDF Page Text"
    mock_pdf_reader.assert_called_once_with(pdf_file)


def test_load_text_unsupported(tmp_path):
    """Verify load_text raises ValueError for unsupported file extensions."""
    unsupported_file = tmp_path / "test.png"
    unsupported_file.write_text("fake png bytes", encoding="utf-8")
    
    service = DocumentService()
    with pytest.raises(ValueError, match="Unsupported file format"):
        service.load_text(unsupported_file)


def test_load_documents(tmp_path, capsys):
    """Verify load_documents processes directory, loads valid files, and skips bad ones."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    
    # 1. Valid TXT file
    f1 = data_dir / "doc1.txt"
    f1.write_text("Text content of document 1.", encoding="utf-8")
    
    # 2. Valid HTML file
    f2 = data_dir / "doc2.html"
    f2.write_text("<p>HTML content.</p>", encoding="utf-8")
    
    # 3. Unsupported PNG file (should be gracefully skipped)
    f3 = data_dir / "doc3.png"
    f3.write_text("unsupported data", encoding="utf-8")
    
    service = DocumentService()
    docs = service.load_documents(data_dir=str(data_dir))
    
    assert len(docs) == 2
    sources = [d["source"] for d in docs]
    assert "doc1.txt" in sources
    assert "doc2.html" in sources
    assert "doc3.png" not in sources
    
    # Verify console output logs printed OK and SKIP
    captured = capsys.readouterr().out
    assert "OK doc1.txt: 27 chars" in captured
    assert "OK doc2.html: 13 chars" in captured
    assert "SKIP doc3.png: Unsupported file format" in captured
