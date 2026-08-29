import pytest
from src.services.cleaning_service import TextCleaningService


def test_normalize_encoding():
    cleaner = TextCleaningService()
    # Test standard NFKC conversions and mojibake
    text = "Microsoftâ€™s Windows OS"
    cleaned = cleaner.normalize_encoding(text)
    # â€™ contains encoding artifacts that NFKC maps to standard forms or cleans up
    assert "â€™" not in cleaned

    # Test decomposed unicode (e.g. e + acute accent)
    text = "cafe\u0301"
    cleaned = cleaner.normalize_encoding(text)
    assert cleaned == "café"


def test_remove_boilerplate():
    cleaner = TextCleaningService()
    # Test Page X of Y (any case)
    assert cleaner.remove_boilerplate("Content Page 3 of 10 More Content").strip() == "Content  More Content"
    assert cleaner.remove_boilerplate("Content PAGE 12 of 15").strip() == "Content"
    
    # Test Page X (any case)
    assert cleaner.remove_boilerplate("Document Header\nPage 4\nDocument Footer").strip() == "Document Header\n\nDocument Footer"
    assert cleaner.remove_boilerplate("page 42").strip() == ""


def test_normalize_line_wraps_hyphen():
    cleaner = TextCleaningService()
    # Test hyphenated line wraps (mid-word)
    text = "We are working on the co-\nllaboration platform for de-\nvelopment."
    cleaned = cleaner.clean_text(text)
    assert "collaboration" in cleaned
    assert "development" in cleaned


def test_normalize_line_wraps_paragraphs_and_lists():
    cleaner = TextCleaningService()
    # Test joining paragraphs and keeping lists intact
    text = (
        "This is a long sentence that has a single\n"
        "line break in the middle of it.\n\n"
        "Here is a list:\n"
        "- Item one has a single\n"
        "  wrap.\n"
        "- Item two.\n\n"
        "Here is a table:\n"
        "| Col 1 | Col 2 |\n"
        "|---|---|\n"
        "| val1 | val2 |"
    )
    cleaned = cleaner.clean_text(text)
    
    # Check that paragraph line was joined
    assert "single line break" in cleaned
    # Check that list items are preserved on separate lines
    assert "- Item two." in cleaned
    # Check that table rows are kept separate
    assert "| Col 1 | Col 2 |" in cleaned
    assert "| val1 | val2 |" in cleaned


def test_normalize_whitespace():
    cleaner = TextCleaningService()
    # Test collapsing extra spaces/tabs
    text = "Too    many    spaces \t and tabs."
    assert cleaner.normalize_whitespace(text) == "Too many spaces and tabs."

    # Test collapsing multiple newlines
    text = "Line 1\n\n\n\nLine 2\n\n\nLine 3"
    assert cleaner.normalize_whitespace(text) == "Line 1\n\nLine 2\n\nLine 3"


def test_clean_text_orchestration():
    cleaner = TextCleaningService()
    text = (
        "PolicyPilot Official Guidelines\n"
        "Page 1 of 5\n\n"
        "This is an example of a policy de-\n"
        "tail that is split by lines.\n\n"
        "Enjoy    your    read!   "
    )
    cleaned = cleaner.clean_text(text)
    assert "PolicyPilot Official Guidelines" in cleaned
    assert "Page 1 of 5" not in cleaned
    assert "policy detail" in cleaned
    assert "Enjoy your read!" in cleaned
