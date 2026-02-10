"""
Text Parser - Stage 1.1.2
Parses Project Gutenberg content and extracts main text.
"""

import html
import logging
import re
from pathlib import Path
from typing import Tuple

from common.logging import get_logger


class TextParser:
    """Parses and cleans Project Gutenberg content."""

    # Gutenberg boilerplate markers
    START_MARKERS = [
        r"\*\*\* START OF (THIS )?PROJECT GUTENBERG EBOOK",
        r"START OF THE PROJECT GUTENBERG EBOOK",
    ]

    END_MARKERS = [
        r"\*\*\* END OF (THIS )?PROJECT GUTENBERG EBOOK",
        r"END OF THE PROJECT GUTENBERG EBOOK",
        r"End of (the )?Project Gutenberg EBook",
    ]

    def __init__(self):
        """Initialize the Text Parser."""
        self.logger = get_logger(__name__)
        # Compile regex patterns for efficiency
        self.start_patterns = [re.compile(marker, re.IGNORECASE) for marker in self.START_MARKERS]
        self.end_patterns = [re.compile(marker, re.IGNORECASE) for marker in self.END_MARKERS]

    def detect_content_type(self, content: str) -> str:
        """
        Detect if content is HTML or plain text.

        Args:
            content: The raw content

        Returns:
            "html" or "txt"
        """
        if "<html" in content.lower() or "<!DOCTYPE" in content.lower():
            return "html"
        return "txt"

    def _find_start_index(self, content: str) -> int:
        """Find the start of main content by looking for Gutenberg markers."""
        lines = content.split("\n")

        for i, line in enumerate(lines):
            for pattern in self.start_patterns:
                if pattern.search(line):
                    # Skip this line and return index of next line
                    return i + 1

        # No marker found - try to detect first actual content line
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped and not stripped.startswith("*"):
                return i

        # Default to start
        return 0

    def _find_end_index(self, content: str) -> int:
        """Find the end of main content by looking for Gutenberg markers."""
        lines = content.split("\n")

        # Search from the end backwards
        for i in range(len(lines) - 1, -1, -1):
            line = lines[i]
            for pattern in self.end_patterns:
                if pattern.search(line):
                    return i - 1  # Return index of line before the marker

        # No marker found - return end
        return len(lines) - 1

    def _strip_html(self, content: str) -> str:
        """
        Remove HTML tags and decode entities.

        Args:
            content: HTML content

        Returns:
            Plain text content
        """
        # Remove script and style elements
        content = re.sub(r'<(script|style).*?>.*?</\1>', '', content, flags=re.DOTALL)

        # Remove HTML tags
        content = re.sub(r'<[^>]+>', ' ', content)

        # Decode HTML entities using standard library
        content = html.unescape(content)

        return content

    def parse(self, raw_content: str) -> Tuple[str, str]:
        """
        Parse raw content and extract main text.

        Args:
            raw_content: Raw content from URL fetcher

        Returns:
            Tuple of (cleaned_text, content_type)
        """
        self.logger.info(f"Parsing content ({len(raw_content):,} characters)")

        # Detect content type
        content_type = self.detect_content_type(raw_content)
        self.logger.debug(f"Detected content type: {content_type}")

        # Strip HTML if necessary
        content = raw_content
        if content_type == "html":
            content = self._strip_html(content)
            self.logger.debug("Stripped HTML tags")

        # Find main content boundaries
        start_idx = self._find_start_index(content)
        end_idx = self._find_end_index(content)

        # Extract main content
        lines = content.split("\n")
        main_lines = lines[start_idx:end_idx + 1]
        cleaned_text = "\n".join(main_lines)

        # Preserve multiple newlines (they often indicate section breaks)
        cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)

        chars_removed = len(raw_content) - len(cleaned_text)
        self.logger.info(
            f"Parsed text: {len(cleaned_text):,} characters "
            f"({chars_removed:,} removed)"
        )

        return cleaned_text, content_type


def main():
    """Test the Text Parser."""
    test_url = "https://www.gutenberg.org/files/174/174-0.txt"

    # Import directly for testing
    from pathlib import Path
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from stage1_input.url_fetcher import URLFetcher

    fetcher = URLFetcher()
    raw_content = fetcher.fetch(test_url)

    parser = TextParser()
    cleaned_text, content_type = parser.parse(raw_content)

    print(f"Content type: {content_type}")
    print(f"Original length: {len(raw_content)} characters")
    print(f"Cleaned length: {len(cleaned_text)} characters")
    print(f"Removed: {len(raw_content) - len(cleaned_text)} characters")
    print(f"\nFirst 300 characters of cleaned text:\n{cleaned_text[:300]}")
    print(f"\nLast 300 characters of cleaned text:\n{cleaned_text[-300:]}")


if __name__ == "__main__":
    main()
