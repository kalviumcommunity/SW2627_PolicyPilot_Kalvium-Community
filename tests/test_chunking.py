"""Unit tests for chunking strategies, statistical computation, and boundary inspection."""

import pytest
from src.chunking import (
    Chunk,
    FixedSizeChunker,
    SentenceChunker,
    ParagraphChunker,
    RecursiveCharacterChunker,
    compute_chunk_statistics,
    compare_strategies_on_text,
    generate_comparison_report,
    generate_sample_chunks_report,
    get_token_count_safe,
)


# ==============================================================================
# 1. Chunk Data Model Tests
# ==============================================================================


def test_chunk_creation_and_metadata():
    """Verify that Chunk correctly initializes and formats default metadata."""
    chunk = Chunk(
        text="Sample policy clause.",
        chunk_index=0,
        source="test_policy.txt",
        char_start=0,
        char_end=21,
        char_length=21,
        word_count=3,
        token_count=4,
        strategy="Test-Strategy",
    )

    assert chunk.text == "Sample policy clause."
    assert chunk.metadata["source"] == "test_policy.txt"
    assert chunk.metadata["chunk_index"] == 0
    assert chunk.metadata["char_start"] == 0
    assert chunk.metadata["char_end"] == 21
    assert chunk.metadata["char_length"] == 21
    assert chunk.metadata["word_count"] == 3
    assert chunk.metadata["token_count"] == 4
    assert chunk.metadata["strategy"] == "Test-Strategy"

    d = chunk.to_dict()
    assert isinstance(d, dict)
    assert d["text"] == "Sample policy clause."
    assert d["metadata"]["strategy"] == "Test-Strategy"


# ==============================================================================
# 2. Fixed-Size Chunking Tests
# ==============================================================================


def test_fixed_size_chunker_basic():
    """Verify that FixedSizeChunker splits text into fixed character windows with overlap."""
    text = "0123456789" * 10  # 100 characters
    chunker = FixedSizeChunker(chunk_size=30, chunk_overlap=10)
    chunks = chunker.split(text, source="test.txt")

    # Step size is 30 - 10 = 20. Total length is 100 -> 5 chunks (0..30, 20..50, 40..70, 60..90, 80..100)
    assert len(chunks) == 5
    assert chunks[0].char_length == 30
    assert chunks[0].char_start == 0
    assert chunks[0].char_end == 30
    assert chunks[1].char_start == 20
    assert chunks[1].char_end == 50
    assert chunks[-1].char_start == 80
    assert chunks[-1].char_end == 100


def test_fixed_size_chunker_invalid_overlap():
    """Verify that overlap >= chunk_size raises ValueError."""
    with pytest.raises(ValueError, match="strictly less than"):
        FixedSizeChunker(chunk_size=50, chunk_overlap=50)

    with pytest.raises(ValueError, match="strictly less than"):
        FixedSizeChunker(chunk_size=50, chunk_overlap=60)


def test_fixed_size_chunker_empty_and_short():
    """Verify handling of empty or very short strings."""
    chunker = FixedSizeChunker(chunk_size=100, chunk_overlap=20)
    assert chunker.split("") == []
    assert chunker.split("   ") == []

    short = chunker.split("Short text.", source="short.txt")
    assert len(short) == 1
    assert short[0].text == "Short text."
    assert short[0].char_start == 0
    assert short[0].char_end == 11


# ==============================================================================
# 3. Sentence-Based Chunking Tests
# ==============================================================================


def test_sentence_chunker_basic():
    """Verify that SentenceChunker groups sentences according to configuration and overlap."""
    text = "First sentence. Second sentence! Third sentence? Fourth sentence. Fifth sentence."
    chunker = SentenceChunker(sentences_per_chunk=3, sentence_overlap=1)
    chunks = chunker.split(text, source="sentences.txt")

    # 5 sentences total. Window=3, step=2 -> [s0, s1, s2], [s2, s3, s4] -> 2 chunks
    assert len(chunks) == 2
    assert "First sentence." in chunks[0].text
    assert "Third sentence?" in chunks[0].text
    assert "Fourth sentence." not in chunks[0].text

    assert "Third sentence?" in chunks[1].text
    assert "Fifth sentence." in chunks[1].text


def test_sentence_chunker_invalid_overlap():
    """Verify that sentence_overlap >= sentences_per_chunk raises ValueError."""
    with pytest.raises(ValueError, match="must be less than"):
        SentenceChunker(sentences_per_chunk=2, sentence_overlap=2)


def test_sentence_chunker_empty_and_single():
    """Verify sentence chunker handles empty text and single sentences."""
    chunker = SentenceChunker(sentences_per_chunk=3, sentence_overlap=1)
    assert chunker.split("") == []
    assert chunker.split("   ") == []

    single = chunker.split("Only one sentence.", source="one.txt")
    assert len(single) == 1
    assert single[0].text == "Only one sentence."


# ==============================================================================
# 4. Paragraph / Structural Chunking Tests
# ==============================================================================


def test_paragraph_chunker_basic():
    """Verify that ParagraphChunker splits on double newlines."""
    text = "Paragraph One is here.\n\nParagraph Two is here.\n\nParagraph Three is here."
    chunker = ParagraphChunker(merge_headers=False)
    chunks = chunker.split(text, source="paras.txt")

    assert len(chunks) == 3
    assert chunks[0].text == "Paragraph One is here."
    assert chunks[1].text == "Paragraph Two is here."
    assert chunks[2].text == "Paragraph Three is here."
    assert chunks[0].char_start == 0
    assert chunks[1].char_start > chunks[0].char_end


def test_paragraph_chunker_merge_headers():
    """Verify that markdown headers are merged with their following paragraph body."""
    text = (
        "## Section 1: Annual Leave\n\n"
        "Employees get 20 days paid leave.\n\n"
        "## Section 2: Sick Leave\n\n"
        "Employees get 10 days sick leave."
    )
    chunker = ParagraphChunker(merge_headers=True)
    chunks = chunker.split(text, source="policies.md")

    assert len(chunks) == 2
    assert "## Section 1: Annual Leave" in chunks[0].text
    assert "Employees get 20 days paid leave." in chunks[0].text
    assert "## Section 2: Sick Leave" in chunks[1].text
    assert "Employees get 10 days sick leave." in chunks[1].text


def test_paragraph_chunker_empty():
    """Verify empty and whitespace inputs."""
    chunker = ParagraphChunker()
    assert chunker.split("") == []
    assert chunker.split("\n\n\n  \n") == []


# ==============================================================================
# 5. Recursive Character Chunking Tests
# ==============================================================================


def test_recursive_character_chunker_basic():
    """Verify that RecursiveCharacterChunker splits within target bounds."""
    text = (
        "Heading One\n\n"
        "This is paragraph one with several interesting points. It has enough words.\n\n"
        "This is paragraph two with more details and specific policy rules."
    )
    chunker = RecursiveCharacterChunker(chunk_size=80, chunk_overlap=15)
    chunks = chunker.split(text, source="recursive.txt")

    assert len(chunks) >= 2
    for c in chunks:
        # Chunks should respect reasonable size constraint
        assert len(c.text) > 0
        assert c.token_count > 0


def test_recursive_character_chunker_empty():
    """Verify empty text handling in recursive chunker."""
    chunker = RecursiveCharacterChunker(chunk_size=100, chunk_overlap=20)
    assert chunker.split("") == []
    assert chunker.split("   ") == []


# ==============================================================================
# 6. Statistical Analysis & Comparison Engine Tests
# ==============================================================================


def test_compute_chunk_statistics_empty():
    """Verify that stats computation on an empty list returns default zeros."""
    stats = compute_chunk_statistics([])
    assert stats["chunk_count"] == 0
    assert stats["avg_chars"] == 0.0
    assert stats["min_chars"] == 0
    assert stats["max_chars"] == 0


def test_compute_chunk_statistics_values():
    """Verify statistical metrics calculation."""
    c1 = Chunk("Short text", 0, "s.txt", 0, 10, 10, 2, 3, "Strat")
    c2 = Chunk("A slightly longer text snippet", 1, "s.txt", 11, 41, 30, 5, 7, "Strat")

    stats = compute_chunk_statistics([c1, c2])
    assert stats["chunk_count"] == 2
    assert stats["total_chars"] == 40
    assert stats["avg_chars"] == 20.0
    assert stats["min_chars"] == 10
    assert stats["max_chars"] == 30
    assert stats["avg_words"] == 3.5
    assert stats["avg_tokens"] == 5.0
    assert stats["std_dev_chars"] == 10.0


def test_compare_strategies_on_text():
    """Verify that compare_strategies_on_text executes all strategies and formats output."""
    sample_text = (
        "## Policy 1: Return Period\n\n"
        "Customers have 30 calendar days to initiate a return on standard merchandise. "
        "Items must be in original condition with intact packaging.\n\n"
        "## Policy 2: Refund Processing\n\n"
        "Approved refunds are credited to the original payment method within 5 to 7 business days."
    )

    res = compare_strategies_on_text(sample_text, source="sample.txt")

    assert res["source"] == "sample.txt"
    assert res["original_char_count"] == len(sample_text)
    assert "Fixed-Size Overlap (300 chars)" in res["strategies"]
    assert "Sentence-Based (3 sentences)" in res["strategies"]
    assert "Paragraph / Structural" in res["strategies"]
    assert "Recursive Character (350 chars)" in res["strategies"]

    for strat_data in res["strategies"].values():
        assert "stats" in strat_data
        assert "chunks" in strat_data
        assert strat_data["stats"]["chunk_count"] > 0


def test_generate_markdown_reports():
    """Verify that report generation functions output valid Markdown with required sections."""
    sample_text = "## Test Section\n\nSample sentence 1. Sample sentence 2.\n\nAnother paragraph."
    comparison = compare_strategies_on_text(sample_text, source="report_test.txt")

    comp_report = generate_comparison_report(comparison)
    assert "# PolicyPilot Chunking Strategy Comparison & Statistical Report" in comp_report
    assert "| Chunking Strategy |" in comp_report
    assert "Final Recommendation & Justification" in comp_report

    sample_report = generate_sample_chunks_report(comparison, sample_limit=2)
    assert "# PolicyPilot Sample Chunks & Boundary Inspection" in sample_report
    assert "Character Span:" in sample_report
    assert "Word Count:" in sample_report
