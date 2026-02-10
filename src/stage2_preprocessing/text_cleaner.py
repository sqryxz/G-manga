"""
Text Cleaner - Stage 2.1.1
Cleans and normalizes text content.
"""

import re
import unicodedata
from typing import List


class TextCleaner:
    """Cleans and normalizes text content."""

    def __init__(self):
        """Initialize Text Cleaner."""
        # Patterns to clean
        self.boilerplate_patterns = [
            # Gutenberg boilerplate patterns (redundant, after text_parser)
            r"^Produced by .*?gutenberg\.org",
            r"^Project Gutenberg-tm.*?\n",
            r"^End of the Project Gutenberg",
            # Page numbers
            r"\n\s*\d+\s*\n",
            # Multiple spaces
            r"  +",
            # Multiple newlines (3+ → 2)
            r"\n{3,}",
        ]

        # Compile patterns
        self.patterns = [re.compile(p, re.MULTILINE | re.IGNORECASE) for p in self.boilerplate_patterns]

    def normalize_unicode(self, text: str) -> str:
        """
        Normalize Unicode characters to NFC form.

        Args:
            text: Input text

        Returns:
            Normalized text
        """
        return unicodedata.normalize("NFC", text)

    def remove_boilerplate(self, text: str) -> str:
        """
        Remove remaining boilerplate patterns.

        Args:
            text: Input text

        Returns:
            Text with boilerplate removed
        """
        cleaned = text

        for pattern in self.patterns:
            cleaned = pattern.sub(" ", cleaned)

        return cleaned

    def fix_whitespace(self, text: str) -> str:
        """
        Fix whitespace issues.

        Args:
            text: Input text

        Returns:
            Text with fixed whitespace
        """
        # Replace multiple spaces with single space
        text = re.sub(r"  +", " ", text)

        # Replace multiple newlines (3+ → 2)
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Remove leading/trailing whitespace from lines
        lines = text.split("\n")
        lines = [line.strip() for line in lines]
        text = "\n".join(lines)

        # Remove empty paragraphs (double newlines with only spaces)
        text = re.sub(r"\n[ \t]+\n", "\n\n", text)

        return text

    def fix_paragraphs(self, text: str) -> str:
        """
        Fix broken paragraphs (lines that should be together).

        Args:
            text: Input text

        Returns:
            Text with fixed paragraphs
        """
        # Detect if a line ends mid-sentence (no period, question mark, exclamation)
        # and join with the next line
        lines = text.split("\n")
        fixed_lines = []

        for i, line in enumerate(lines):
            if not line.strip():
                # Empty line - preserve as paragraph break
                fixed_lines.append(line)
            elif i > 0 and not lines[i-1].strip():
                # Previous line was empty - preserve as paragraph break
                fixed_lines.append(line)
            elif self._is_mid_sentence(line):
                # Mid-sentence - append to previous line
                if fixed_lines:
                    fixed_lines[-1] += " " + line
                else:
                    fixed_lines.append(line)
            else:
                # End of sentence - new line
                fixed_lines.append(line)

        return "\n".join(fixed_lines)

    def _is_mid_sentence(self, line: str) -> bool:
        """
        Check if line ends mid-sentence.

        Args:
            line: Line to check

        Returns:
            True if mid-sentence, False otherwise
        """
        line = line.strip()

        if not line:
            return False

        # End punctuation
        end_punct = {'.', '!', '?', '"', "'", ')', ']'}

        if line[-1] in end_punct:
            return False

        # Check for abbreviations at end
        abbreviations = {'mr.', 'mrs.', 'dr.', 'ms.', 'prof.', 'sr.', 'jr.'}
        for abbr in abbreviations:
            if line.lower().endswith(abbr):
                return False

        return True

    def preserve_chapter_markers(self, text: str) -> str:
        """
        Ensure chapter markers are preserved and formatted.

        Args:
            text: Input text

        Returns:
            Text with preserved chapter markers
        """
        # Common chapter marker patterns
        chapter_patterns = [
            r"(CHAPTER\s+[IVXLCDM]+)",  # Roman numerals
            r"(Chapter\s+\d+)",          # Arabic numerals
            r"(CHAPTER\s+\w+)",           # Spelled out
        ]

        # Ensure chapter markers have proper spacing
        for pattern in chapter_patterns:
            text = re.sub(r"\n" + pattern + r"\n", r"\n\1\n\n", text)

        return text

    def clean(self, text: str, preserve_paragraphs: bool = True) -> str:
        """
        Apply all cleaning operations.

        Args:
            text: Input text
            preserve_paragraphs: Whether to fix broken paragraphs

        Returns:
            Cleaned text
        """
        # Step 1: Normalize Unicode
        text = self.normalize_unicode(text)

        # Step 2: Remove remaining boilerplate
        text = self.remove_boilerplate(text)

        # Step 3: Fix whitespace
        text = self.fix_whitespace(text)

        # Step 4: Fix paragraphs
        if preserve_paragraphs:
            text = self.fix_paragraphs(text)

        # Step 5: Preserve chapter markers
        text = self.preserve_chapter_markers(text)

        return text


def main():
    """Test Text Cleaner."""
    import sys
    sys.path.insert(0, '/home/clawd/projects/g-manga/src/stage1_input')

    from url_fetcher import URLFetcher
    from text_parser import TextParser

    # Get test text
    test_url = "https://www.gutenberg.org/files/174/174-0.txt"

    fetcher = URLFetcher()
    raw_content = fetcher.fetch(test_url)

    parser = TextParser()
    cleaned, _ = parser.parse(raw_content)

    # Clean it
    cleaner = TextCleaner()
    super_clean = cleaner.clean(cleaned)

    print(f"Original length: {len(cleaned):,}")
    print(f"Cleaned length: {len(super_clean):,}")
    print(f"Difference: {len(cleaned) - len(super_clean):,}")

    # Show sample
    print(f"\nFirst 500 characters:")
    print(super_clean[:500])


if __name__ == "__main__":
    main()
