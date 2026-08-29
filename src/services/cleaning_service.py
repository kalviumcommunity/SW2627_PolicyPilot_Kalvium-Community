import re
import unicodedata

class TextCleaningService:
    """Service to clean and normalise raw extracted text for RAG indexing."""

    def clean_text(self, text: str) -> str:
        """Apply all text cleaning and normalisation steps in order.

        Steps:
        1. Normalise Unicode characters (NFKC)
        2. Normalise line endings (\r\n -> \n)
        3. Remove repeated page headers, footers, and boilerplate
        4. Resolve mid-word hyphenated line wraps
        5. Normalise line wraps (joining paragraph lines while keeping lists/tables intact)
        6. Collapse excessive spaces/tabs and empty lines
        """
        if not text:
            return ""

        text = self.normalize_encoding(text)
        text = text.replace("\r\n", "\n")
        text = self.remove_boilerplate(text)
        text = self.normalize_line_wraps(text)
        text = self.normalize_whitespace(text)
        return text.strip()

    def normalize_encoding(self, text: str) -> str:
        """Fix encoding artifacts using NFKC normalization."""
        # This resolves issues like â€™ to ' and other mojibake/Unicode inconsistencies
        return unicodedata.normalize("NFKC", text)

    def remove_boilerplate(self, text: str) -> str:
        """Strip repeated headers, footers, or boilerplate lines."""
        # 1. Remove Page X of Y footers
        text = re.sub(r"(?i)\bpage\s+\d+\s+of\s+\d+\b", "", text)
        # 2. Remove Page X footers
        text = re.sub(r"(?i)\bpage\s+\d+\b", "", text)
        return text

    def normalize_line_wraps(self, text: str) -> str:
        """Join mid-word line wraps and single newlines inside paragraphs,

        while preserving lists, code blocks, or table rows.
        """
        # Join hyphenated line breaks (e.g., co-\nllaboration -> collaboration)
        text = re.sub(r"(\w+)-\n\s*(\w+)", r"\1\2", text)

        # Split into paragraphs by double newlines or more
        paragraphs = re.split(r"\n{2,}", text)
        cleaned_paragraphs = []

        for para in paragraphs:
            lines = para.split("\n")
            joined_lines = []
            for line in lines:
                stripped = line.strip()
                if not stripped:
                    continue

                # Check if this line starts a list item or table row
                # e.g. bullet points (- or *), numbered lists (1., 2.), or table separators (|)
                is_list_or_table = bool(re.match(r"^(\s*[-*+]\s|\s*\d+\.\s|\s*\|)", line))

                if is_list_or_table:
                    # Keep lists/tables on new lines
                    joined_lines.append(line)
                else:
                    if joined_lines and not re.match(r"^(\s*[-*+]\s|\s*\d+\.\s|\s*\|)", joined_lines[-1]):
                        # Join with the previous line if it was also a normal line
                        joined_lines[-1] = joined_lines[-1].rstrip() + " " + stripped
                    else:
                        joined_lines.append(line)

            cleaned_paragraphs.append("\n".join(joined_lines))

        return "\n\n".join(cleaned_paragraphs)

    def normalize_whitespace(self, text: str) -> str:
        """Collapse runaway spaces/tabs and consecutive empty lines."""
        # Collapse multiple spaces and tabs to a single space
        text = re.sub(r"[ \t]+", " ", text)
        # Collapse three or more consecutive newlines to two newlines
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text
