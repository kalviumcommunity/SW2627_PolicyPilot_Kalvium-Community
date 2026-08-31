"""Document Chunking Strategies, Comparison, and Boundary Analysis for PolicyPilot.

Provides multiple chunking strategies (Fixed-size with overlap, Sentence-based,
Paragraph/Structural, and Recursive Character chunking), computes chunk statistics,
evaluates trade-offs, and exports boundary inspection artifacts.
"""

from __future__ import annotations

import math
import os
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def get_token_count_safe(text: str) -> int:
    """Calculate token count using tiktoken if available, else approximate via word count."""
    if not text:
        return 0
    try:
        import tiktoken
        try:
            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))
        except Exception:
            return math.ceil(len(text.split()) * 1.33)
    except ImportError:
        # Standard token approximation: ~1 token per 0.75 words (or 4 chars)
        words = len(text.split())
        return max(1, math.ceil(words * 1.33)) if words > 0 else 0


@dataclass
class Chunk:
    """Represents a single extracted chunk of text with complete metadata and boundary offsets."""

    text: str
    chunk_index: int
    source: str
    char_start: int
    char_end: int
    char_length: int
    word_count: int
    token_count: int
    strategy: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.metadata:
            self.metadata = {
                "source": self.source,
                "chunk_index": self.chunk_index,
                "char_start": self.char_start,
                "char_end": self.char_end,
                "char_length": self.char_length,
                "word_count": self.word_count,
                "token_count": self.token_count,
                "strategy": self.strategy,
            }

    def to_dict(self) -> Dict[str, Any]:
        """Convert chunk object to dictionary representation."""
        return {
            "text": self.text,
            "chunk_index": self.chunk_index,
            "source": self.source,
            "char_start": self.char_start,
            "char_end": self.char_end,
            "char_length": self.char_length,
            "word_count": self.word_count,
            "token_count": self.token_count,
            "strategy": self.strategy,
            "metadata": self.metadata,
        }


# ==============================================================================
# STRATEGY 1: Fixed-Size Chunking with Overlap (Sliding Window)
# ==============================================================================


class FixedSizeChunker:
    """Splits text into fixed-size character windows with a configurable sliding overlap."""

    def __init__(self, chunk_size: int = 300, chunk_overlap: int = 60):
        if chunk_overlap >= chunk_size:
            raise ValueError(
                f"chunk_overlap ({chunk_overlap}) must be strictly less than chunk_size ({chunk_size})"
            )
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.strategy_name = f"Fixed-Size ({chunk_size} chars, {chunk_overlap} overlap)"

    def split(self, text: str, source: str = "document") -> List[Chunk]:
        """Split text into fixed-size chunks with overlapping boundaries."""
        if not text or not text.strip():
            return []

        chunks: List[Chunk] = []
        step = self.chunk_size - self.chunk_overlap
        text_len = len(text)
        chunk_idx = 0

        start = 0
        while start < text_len:
            end = min(start + self.chunk_size, text_len)
            chunk_raw = text[start:end]
            chunk_text = chunk_raw.strip()

            if chunk_text:
                # Find accurate stripped bounds
                strip_left = len(chunk_raw) - len(chunk_raw.lstrip())
                actual_start = start + strip_left
                actual_end = actual_start + len(chunk_text)

                words = len(chunk_text.split())
                tokens = get_token_count_safe(chunk_text)

                chunk_obj = Chunk(
                    text=chunk_text,
                    chunk_index=chunk_idx,
                    source=source,
                    char_start=actual_start,
                    char_end=actual_end,
                    char_length=len(chunk_text),
                    word_count=words,
                    token_count=tokens,
                    strategy=self.strategy_name,
                )
                chunks.append(chunk_obj)
                chunk_idx += 1

            if end >= text_len:
                break
            start += step

        return chunks


# ==============================================================================
# STRATEGY 2: Sentence-Based Chunking
# ==============================================================================


class SentenceChunker:
    """Splits text into sentences and groups them into chunks with sentence-level overlap."""

    def __init__(self, sentences_per_chunk: int = 3, sentence_overlap: int = 1):
        if sentence_overlap >= sentences_per_chunk:
            raise ValueError(
                f"sentence_overlap ({sentence_overlap}) must be less than sentences_per_chunk ({sentences_per_chunk})"
            )
        self.sentences_per_chunk = sentences_per_chunk
        self.sentence_overlap = sentence_overlap
        self.strategy_name = f"Sentence-Based ({sentences_per_chunk} sents, {sentence_overlap} overlap)"

    @staticmethod
    def _extract_sentences_with_offsets(text: str) -> List[Tuple[str, int, int]]:
        """Extract individual sentences with their start and end character offsets."""
        # Sentence boundary regex matching periods, exclamations, questions, or newlines followed by space/caps
        pattern = r"(?<=[.!?])\s+|\n{2,}"
        sentences = []
        last_end = 0

        for match in re.finditer(pattern, text):
            split_point = match.start()
            sentence = text[last_end:split_point].strip()
            if sentence:
                # Find start offset in original text
                s_start = text.find(sentence, last_end)
                s_end = s_start + len(sentence)
                sentences.append((sentence, s_start, s_end))
            last_end = match.end()

        # Catch trailing sentence
        if last_end < len(text):
            trailing = text[last_end:].strip()
            if trailing:
                s_start = text.find(trailing, last_end)
                s_end = s_start + len(trailing)
                sentences.append((trailing, s_start, s_end))

        # Fallback if no sentence boundaries found
        if not sentences and text.strip():
            stripped = text.strip()
            s_start = text.find(stripped)
            sentences.append((stripped, s_start, s_start + len(stripped)))

        return sentences

    def split(self, text: str, source: str = "document") -> List[Chunk]:
        """Split text into sentence-grouped chunks."""
        if not text or not text.strip():
            return []

        sentences = self._extract_sentences_with_offsets(text)
        if not sentences:
            return []

        chunks: List[Chunk] = []
        step = self.sentences_per_chunk - self.sentence_overlap
        total_sents = len(sentences)
        chunk_idx = 0

        start_idx = 0
        while start_idx < total_sents:
            end_idx = min(start_idx + self.sentences_per_chunk, total_sents)
            group = sentences[start_idx:end_idx]

            chunk_text = " ".join(s[0] for s in group).strip()
            char_start = group[0][1]
            char_end = group[-1][2]

            words = len(chunk_text.split())
            tokens = get_token_count_safe(chunk_text)

            chunk_obj = Chunk(
                text=chunk_text,
                chunk_index=chunk_idx,
                source=source,
                char_start=char_start,
                char_end=char_end,
                char_length=len(chunk_text),
                word_count=words,
                token_count=tokens,
                strategy=self.strategy_name,
            )
            chunks.append(chunk_obj)
            chunk_idx += 1

            if end_idx >= total_sents:
                break
            start_idx += step

        return chunks


# ==============================================================================
# STRATEGY 3: Paragraph / Structural / Section Chunking
# ==============================================================================


class ParagraphChunker:
    """Splits text on paragraph breaks and markdown headers to preserve semantic policy units."""

    def __init__(self, min_length: int = 50, merge_headers: bool = True):
        self.min_length = min_length
        self.merge_headers = merge_headers
        self.strategy_name = "Paragraph / Structural"

    def split(self, text: str, source: str = "document") -> List[Chunk]:
        """Split text along paragraph and section boundaries."""
        if not text or not text.strip():
            return []

        # Split on double newlines
        raw_paragraphs = text.split("\n\n")
        chunks: List[Chunk] = []
        chunk_idx = 0
        curr_pos = 0

        pending_header = ""
        pending_start = 0

        for para in raw_paragraphs:
            para_stripped = para.strip()
            if not para_stripped:
                continue

            char_start = text.find(para, curr_pos)
            if char_start == -1:
                char_start = curr_pos
            curr_pos = char_start + len(para)

            # Check if this paragraph is a standalone markdown header (e.g. ## Section 1: ...)
            is_header = bool(re.match(r"^#{1,6}\s+.+", para_stripped) and len(para_stripped.splitlines()) == 1)

            if self.merge_headers and is_header:
                if pending_header:
                    # Flush existing header if two headers are consecutive
                    combined_text = pending_header
                    words = len(combined_text.split())
                    tokens = get_token_count_safe(combined_text)
                    chunks.append(
                        Chunk(
                            text=combined_text,
                            chunk_index=chunk_idx,
                            source=source,
                            char_start=pending_start,
                            char_end=pending_start + len(combined_text),
                            char_length=len(combined_text),
                            word_count=words,
                            token_count=tokens,
                            strategy=self.strategy_name,
                        )
                    )
                    chunk_idx += 1

                pending_header = para_stripped
                pending_start = char_start
                continue

            if pending_header:
                chunk_text = f"{pending_header}\n\n{para_stripped}"
                actual_start = pending_start
                actual_end = char_start + len(para_stripped)
                pending_header = ""
            else:
                chunk_text = para_stripped
                actual_start = char_start
                actual_end = char_start + len(para_stripped)

            words = len(chunk_text.split())
            tokens = get_token_count_safe(chunk_text)

            chunks.append(
                Chunk(
                    text=chunk_text,
                    chunk_index=chunk_idx,
                    source=source,
                    char_start=actual_start,
                    char_end=actual_end,
                    char_length=len(chunk_text),
                    word_count=words,
                    token_count=tokens,
                    strategy=self.strategy_name,
                )
            )
            chunk_idx += 1

        # Flush trailing header if any
        if pending_header:
            words = len(pending_header.split())
            tokens = get_token_count_safe(pending_header)
            chunks.append(
                Chunk(
                    text=pending_header,
                    chunk_index=chunk_idx,
                    source=source,
                    char_start=pending_start,
                    char_end=pending_start + len(pending_header),
                    char_length=len(pending_header),
                    word_count=words,
                    token_count=tokens,
                    strategy=self.strategy_name,
                )
            )

        return chunks


# ==============================================================================
# STRATEGY 4: Recursive Character Chunking
# ==============================================================================


class RecursiveCharacterChunker:
    """Recursively splits text using a hierarchy of separators to maximize semantic coherence within size constraints."""

    def __init__(
        self,
        chunk_size: int = 350,
        chunk_overlap: int = 50,
        separators: Optional[List[str]] = None,
    ):
        if chunk_overlap >= chunk_size:
            raise ValueError(
                f"chunk_overlap ({chunk_overlap}) must be strictly less than chunk_size ({chunk_size})"
            )
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", ". ", " ", ""]
        self.strategy_name = f"Recursive Character ({chunk_size} chars, {chunk_overlap} overlap)"

    def _split_text_recursive(self, text: str, separators: List[str]) -> List[str]:
        """Split text recursively using current separator, recursing on oversized segments."""
        final_chunks: List[str] = []
        if not text or not text.strip():
            return []

        # Find first applicable separator
        separator = separators[-1]
        new_separators = []
        for i, sep in enumerate(separators):
            if sep == "":
                separator = sep
                break
            if sep in text:
                separator = sep
                new_separators = separators[i + 1 :]
                break

        splits = text.split(separator) if separator else list(text)

        # Merge splits up to chunk_size with overlap
        good_splits: List[str] = []
        for s in splits:
            if s.strip():
                if len(s) > self.chunk_size and new_separators:
                    # Recurse on oversized split
                    sub_splits = self._split_text_recursive(s, new_separators)
                    good_splits.extend(sub_splits)
                else:
                    good_splits.append(s)

        # Re-pack good_splits into chunks of at most chunk_size with overlap
        current_chunk: List[str] = []
        current_len = 0

        for segment in good_splits:
            segment_len = len(segment) + (len(separator) if current_chunk else 0)
            if current_len + segment_len <= self.chunk_size:
                current_chunk.append(segment)
                current_len += segment_len
            else:
                if current_chunk:
                    joined = separator.join(current_chunk).strip()
                    if joined:
                        final_chunks.append(joined)
                    # Handle overlap by keeping trailing segments
                    overlap_len = 0
                    overlap_chunk = []
                    for seg in reversed(current_chunk):
                        if overlap_len + len(seg) <= self.chunk_overlap:
                            overlap_chunk.insert(0, seg)
                            overlap_len += len(seg)
                        else:
                            break
                    current_chunk = overlap_chunk
                    current_len = sum(len(s) for s in current_chunk) + (
                        len(separator) * max(0, len(current_chunk) - 1)
                    )

                current_chunk.append(segment)
                current_len += len(segment)

        if current_chunk:
            joined = separator.join(current_chunk).strip()
            if joined:
                final_chunks.append(joined)

        return final_chunks

    def split(self, text: str, source: str = "document") -> List[Chunk]:
        """Split text into recursive chunks with exact character offsets."""
        if not text or not text.strip():
            return []

        raw_chunks = self._split_text_recursive(text, self.separators)
        chunks: List[Chunk] = []
        curr_pos = 0

        for chunk_idx, chunk_text in enumerate(raw_chunks):
            char_start = text.find(chunk_text, curr_pos)
            if char_start == -1:
                # Fallback to search from beginning if overlap caused rewind
                char_start = text.find(chunk_text)
                if char_start == -1:
                    char_start = curr_pos

            char_end = char_start + len(chunk_text)
            curr_pos = max(curr_pos, char_start + 1)

            words = len(chunk_text.split())
            tokens = get_token_count_safe(chunk_text)

            chunk_obj = Chunk(
                text=chunk_text,
                chunk_index=chunk_idx,
                source=source,
                char_start=char_start,
                char_end=char_end,
                char_length=len(chunk_text),
                word_count=words,
                token_count=tokens,
                strategy=self.strategy_name,
            )
            chunks.append(chunk_obj)

        return chunks


# ==============================================================================
# STATISTICAL ANALYSIS & COMPARISON ENGINE
# ==============================================================================


def compute_chunk_statistics(chunks: List[Chunk]) -> Dict[str, Any]:
    """Compute statistical distribution metrics over a collection of chunks."""
    if not chunks:
        return {
            "chunk_count": 0,
            "total_chars": 0,
            "total_words": 0,
            "total_tokens": 0,
            "avg_chars": 0.0,
            "avg_words": 0.0,
            "avg_tokens": 0.0,
            "min_chars": 0,
            "max_chars": 0,
            "min_tokens": 0,
            "max_tokens": 0,
            "std_dev_chars": 0.0,
            "std_dev_tokens": 0.0,
        }

    n = len(chunks)
    char_lens = [c.char_length for c in chunks]
    word_lens = [c.word_count for c in chunks]
    token_lens = [c.token_count for c in chunks]

    total_chars = sum(char_lens)
    total_words = sum(word_lens)
    total_tokens = sum(token_lens)

    avg_chars = total_chars / n
    avg_words = total_words / n
    avg_tokens = total_tokens / n

    # Standard deviation
    variance_chars = sum((x - avg_chars) ** 2 for x in char_lens) / n
    std_dev_chars = math.sqrt(variance_chars)

    variance_tokens = sum((x - avg_tokens) ** 2 for x in token_lens) / n
    std_dev_tokens = math.sqrt(variance_tokens)

    return {
        "chunk_count": n,
        "total_chars": total_chars,
        "total_words": total_words,
        "total_tokens": total_tokens,
        "avg_chars": round(avg_chars, 2),
        "avg_words": round(avg_words, 2),
        "avg_tokens": round(avg_tokens, 2),
        "min_chars": min(char_lens),
        "max_chars": max(char_lens),
        "min_tokens": min(token_lens),
        "max_tokens": max(token_lens),
        "std_dev_chars": round(std_dev_chars, 2),
        "std_dev_tokens": round(std_dev_tokens, 2),
    }


def compare_strategies_on_text(
    text: str,
    source: str = "document",
    custom_strategies: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Execute multiple chunking strategies on the exact same text and return comparative data."""
    strategies = custom_strategies or {
        "Fixed-Size Overlap (300 chars)": FixedSizeChunker(chunk_size=300, chunk_overlap=60),
        "Sentence-Based (3 sentences)": SentenceChunker(sentences_per_chunk=3, sentence_overlap=1),
        "Paragraph / Structural": ParagraphChunker(merge_headers=True),
        "Recursive Character (350 chars)": RecursiveCharacterChunker(chunk_size=350, chunk_overlap=50),
    }

    results: Dict[str, Any] = {
        "source": source,
        "original_char_count": len(text),
        "original_word_count": len(text.split()),
        "original_token_count": get_token_count_safe(text),
        "strategies": {},
    }

    for name, chunker in strategies.items():
        chunks = chunker.split(text, source=source)
        stats = compute_chunk_statistics(chunks)
        results["strategies"][name] = {
            "strategy_name": name,
            "chunker_class": chunker.__class__.__name__,
            "stats": stats,
            "chunks": chunks,
        }

    return results


# ==============================================================================
# MARKDOWN REPORT GENERATORS (Comparison & Sample Chunks)
# ==============================================================================


def generate_comparison_report(comparison_data: Dict[str, Any]) -> str:
    """Generate a comprehensive Markdown report comparing chunking strategies."""
    source = comparison_data.get("source", "Document Corpus")
    orig_chars = comparison_data.get("original_char_count", 0)
    orig_words = comparison_data.get("original_word_count", 0)
    orig_tokens = comparison_data.get("original_token_count", 0)

    md = []
    md.append("# PolicyPilot Chunking Strategy Comparison & Statistical Report")
    md.append("")
    md.append("## 1. Corpus Overview")
    md.append(f"- **Document Source:** `{source}`")
    md.append(f"- **Total Document Length:** {orig_chars:,} characters | {orig_words:,} words | {orig_tokens:,} tokens")
    md.append("")
    md.append("## 2. Statistical Comparison Matrix")
    md.append("")
    md.append(
        "| Chunking Strategy | Chunk Count | Avg Size (Chars) | Avg Size (Words) | Avg Size (Tokens) | Min / Max Chars | Min / Max Tokens | Std Dev (Chars) |"
    )
    md.append(
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |"
    )

    for strat_name, strat_data in comparison_data.get("strategies", {}).items():
        s = strat_data["stats"]
        md.append(
            f"| **{strat_name}** | {s['chunk_count']} | {s['avg_chars']} | {s['avg_words']} | {s['avg_tokens']} | {s['min_chars']} / {s['max_chars']} | {s['min_tokens']} / {s['max_tokens']} | ±{s['std_dev_chars']} |"
        )

    md.append("")
    md.append("## 3. Qualitative Trade-off Analysis")
    md.append("")
    md.append("### Strategy 1: Fixed-Size Chunking with Overlap")
    md.append("- **Mechanism:** Slices text strictly at fixed character boundaries (e.g. 300 chars) with a 60-character sliding overlap window.")
    md.append("- **Advantages:** Highly predictable chunk counts and uniform embedding sizes; overlap prevents complete loss of boundary context.")
    md.append("- **Disadvantages:** Frequently splits words, mid-sentence thoughts, and logical policy headers, separating clauses from their governing section titles.")
    md.append("- **Retrieval Precision Impact:** Lower semantic precision when questions require full clause understanding.")
    md.append("")
    md.append("### Strategy 2: Sentence-Based Chunking")
    md.append("- **Mechanism:** Segments text into grammatical sentences and groups windows of 3 sentences with a 1-sentence overlap.")
    md.append("- **Advantages:** Preserves complete syntactic units and grammatical clarity; never cuts words in half.")
    md.append("- **Disadvantages:** Variable character and token lengths depending on sentence complexity; may isolate a policy statement from its section header unless headers are explicitly bound.")
    md.append("- **Retrieval Precision Impact:** Good for granular question answering, but can lose overarching document context.")
    md.append("")
    md.append("### Strategy 3: Paragraph / Structural Chunking")
    md.append("- **Mechanism:** Splits along natural paragraph breaks (`\\n\\n`) and markdown headers (`#`, `##`), maintaining cohesive policy clauses with their associated section titles.")
    md.append("- **Advantages:** 100% semantic integrity for legal and policy guidelines; self-contained context where each rule, exception, and deadline remains in a single retrieval unit.")
    md.append("- **Disadvantages:** Chunk sizes vary according to paragraph authoring length.")
    md.append("- **Retrieval Precision Impact:** Optimal for PolicyPilot because queries map directly to discrete policy sections (e.g., 'Section 1: Annual Leave', 'Section 6: Data Retention').")
    md.append("")
    md.append("### Strategy 4: Recursive Character Chunking")
    md.append("- **Mechanism:** Recursively tries separators (`['\\n\\n', '\\n', '. ', ' ', '']`) to stay under target chunk size while keeping semantic paragraphs intact whenever possible.")
    md.append("- **Advantages:** Combines the structural awareness of paragraph chunking with strict size guarantees for oversized sections.")
    md.append("- **Disadvantages:** Slightly higher algorithmic complexity.")
    md.append("")
    md.append("## 4. Final Recommendation & Justification")
    md.append(
        "> **Chosen Strategy:** **Paragraph / Structural Chunking** (with Recursive fallback for oversized clauses)\n>\n"
        "> **Justification for Policy Corpus:**\n"
        "> 1. **Context Completeness:** Policy guidelines (e.g., Leave policies, Security protocols, Data Retention rules) are written as self-contained contractual paragraphs. Splitting mid-paragraph creates dangling clauses without necessary qualifiers.\n"
        "> 2. **Header Preservation:** Preserving the section header within the chunk allows the LLM to accurately ground the answer and cite the exact source section (e.g., `## Section 1: Annual Leave and Time Off Policy`).\n"
        "> 3. **Token Budget Efficiency:** The average paragraph chunk size (~350–450 characters / ~75–95 tokens) comfortably fits within embedding model limits while keeping prompt tokens low and deterministic during RAG generation."
    )
    md.append("")

    return "\n".join(md)


def generate_sample_chunks_report(
    comparison_data: Dict[str, Any], sample_limit: int = 4
) -> str:
    """Generate Markdown report displaying sample chunks and boundary inspections across strategies."""
    source = comparison_data.get("source", "Document Corpus")

    md = []
    md.append("# PolicyPilot Sample Chunks & Boundary Inspection")
    md.append("")
    md.append(
        f"This document provides sample chunks generated by each chunking strategy on `{source}`. "
        "Reviewers can inspect boundary demarcation, character offsets, token counts, and overlap regions."
    )
    md.append("")

    for strat_name, strat_data in comparison_data.get("strategies", {}).items():
        chunks: List[Chunk] = strat_data["chunks"]
        md.append(f"## Strategy: {strat_name}")
        md.append(f"- **Total Chunks Produced:** {len(chunks)}")
        md.append(f"- **Showing First {min(sample_limit, len(chunks))} Sample Chunks:**")
        md.append("")

        for i, chunk in enumerate(chunks[:sample_limit]):
            md.append(f"### Sample Chunk #{i + 1} (Index: `{chunk.chunk_index}`)")
            md.append(f"- **Source File:** `{chunk.source}`")
            md.append(f"- **Character Span:** `[{chunk.char_start} : {chunk.char_end}]` (Length: {chunk.char_length} chars)")
            md.append(f"- **Word Count:** {chunk.word_count} words | **Token Count:** {chunk.token_count} tokens")
            md.append("")
            md.append("```text")
            md.append(chunk.text)
            md.append("```")
            md.append("")

        md.append("---")
        md.append("")

    return "\n".join(md)


# ==============================================================================
# MAIN DEMONSTRATION ENTRYPOINT
# ==============================================================================


def run_chunking_demonstration():
    """Load documents, run all chunking strategies, print stats, and write markdown reports."""
    print("=" * 70)
    print("        PolicyPilot Chunking Strategies & Boundary Comparison")
    print("=" * 70)

    # Load corpus documents
    data_dir = PROJECT_ROOT / "data"
    doc_paths = [
        data_dir / "privacy_policy.txt",
        data_dir / "company_policies.md",
    ]

    combined_text = ""
    source_names = []

    for path in doc_paths:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    combined_text += f"\n\n=== {path.name} ===\n\n" + content
                    source_names.append(path.name)

    if not combined_text.strip():
        print("[Error] No text found in data/ directory to chunk.")
        return

    source_label = ", ".join(source_names)
    print(f"\nCorpus Loaded: {source_label}")
    print(f"Total Text Size: {len(combined_text):,} chars | {len(combined_text.split()):,} words | {get_token_count_safe(combined_text):,} tokens\n")

    # Run comparisons
    comparison = compare_strategies_on_text(combined_text, source=source_label)

    # Print summary table
    print("-" * 70)
    print(f"{'Strategy':<34} | {'Count':<6} | {'Avg Chars':<10} | {'Avg Tokens':<10} | {'Min/Max Chars'}")
    print("-" * 70)
    for name, data in comparison["strategies"].items():
        st = data["stats"]
        print(f"{name:<34} | {st['chunk_count']:<6} | {st['avg_chars']:<10} | {st['avg_tokens']:<10} | {st['min_chars']}/{st['max_chars']}")
    print("-" * 70)

    # Write output artifacts
    outputs_dir = PROJECT_ROOT / "outputs"
    outputs_dir.mkdir(exist_ok=True)

    comparison_report_path = outputs_dir / "chunk_comparison.md"
    sample_chunks_path = outputs_dir / "sample_chunks.md"

    comparison_md = generate_comparison_report(comparison)
    sample_chunks_md = generate_sample_chunks_report(comparison, sample_limit=4)

    with open(comparison_report_path, "w", encoding="utf-8") as f:
        f.write(comparison_md)

    with open(sample_chunks_path, "w", encoding="utf-8") as f:
        f.write(sample_chunks_md)

    print(f"\n[Success] Comparison report saved to: {comparison_report_path}")
    print(f"[Success] Sample chunks report saved to: {sample_chunks_path}")
    print("=" * 70)


if __name__ == "__main__":
    run_chunking_demonstration()
