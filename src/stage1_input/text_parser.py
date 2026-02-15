"""
Text Parser - Stage 1.1.2
Parses Project Gutenberg content and extracts main text.
"""

import html
import logging
import re
from pathlib import Path
from typing import Tuple, Optional

from common.logging import get_logger


class TextParser:
    """Parses and cleans Project Gutenberg content."""

    # Gutenberg boilerplate markers (start)
    START_MARKERS = [
        r"\*\*\*\s*START OF (?:THE\s+)?PROJECT GUTENBERG EBOOK\s+[0-9]+\s*\*\*\*",
        r"\*\*\*\s*START OF (?:THIS\s+)?PROJECT GUTENBERG EBOOK\s*\*\*\*",
        r"START OF THE PROJECT GUTENBERG EBOOK",
        r"\*\*\*\s*START OF THE PROJECT GUTENBERG EBOOK",
    ]

    # Gutenberg boilerplate markers (end)
    END_MARKERS = [
        r"\*\*\*\s*END OF (?:THE\s+)?PROJECT GUTENBERG EBOOK\s+[0-9]+\s*\*\*\*",
        r"\*\*\*\s*END OF (?:THIS\s+)?PROJECT GUTENBERG EBOOK\s*\*\*\*",
        r"END OF THE PROJECT GUTENBERG EBOOK",
        r"End of (?:the\s+)?Project Gutenberg EBook",
        r"\*\*\*\s*END OF THE PROJECT GUTENBERG EBOOK",
    ]

    # Chapter marker patterns (various formats)
    CHAPTER_PATTERNS = [
        r"^\s*(?:CHAPTER|Chapter)\s+([IVXLC0-9]+|[A-Z]+)\s*$",  # CHAPTER I, Chapter 1, etc.
        r"^\s*(?:Chapter|Chapters)\s+[0-9]+\s*$",  # Chapter 1, Chapters 1-3
        r"^\s*(?:Section|SECTION)\s+[0-9]+\s*$",  # Section 1
        r"^\s*(?:BOOK|Book)\s+[IVXLC0-9]+\s*$",  # BOOK I
        r"^\s*(?:Part|PART)\s+[IVXLC0-9A-Z]+\s*$",  # Part I
        r"^\s*[0-9]+\s*$",  # Just a number
    ]

    # Preface/intro marker patterns
    PREFACE_MARKERS = [
        r"^\s*(?:PREFACE|Preface)\s*$",
        r"^\s*(?:INTRODUCTION|Introduction)\s*$",
        r"^\s*(?:FOREWORD|Foreword)\s*$",
        r"^\s*(?:PROLOGUE|Prologue)\s*$",
        r"^\s*(?:DEDICATION|Dedication)\s*$",
        r"^\s*(?:ACKNOWLEDGEMENTS|Acknowledgements|Acknowledgments)\s*$",
    ]

    def __init__(self):
        """Initialize the Text Parser."""
        self.logger = get_logger(__name__)
        # Compile regex patterns for efficiency
        self.start_patterns = [re.compile(marker, re.IGNORECASE) for marker in self.START_MARKERS]
        self.end_patterns = [re.compile(marker, re.IGNORECASE) for marker in self.END_MARKERS]
        self.chapter_patterns = [re.compile(p, re.IGNORECASE) for p in self.CHAPTER_PATTERNS]
        self.preface_patterns = [re.compile(p, re.IGNORECASE) for p in self.PREFACE_MARKERS]

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

    def _is_chapter_marker(self, line: str) -> bool:
        """
        Check if a line is a chapter marker.

        Args:
            line: A single line of text

        Returns:
            True if this looks like a chapter marker
        """
        for pattern in self.chapter_patterns:
            if pattern.match(line):
                return True
        return False

    def _is_preface_marker(self, line: str) -> bool:
        """
        Check if a line is a preface/intro marker.

        Args:
            line: A single line of text

        Returns:
            True if this looks like a preface marker
        """
        for pattern in self.preface_patterns:
            if pattern.match(line):
                return True
        return False

    def _extract_chapter_title(self, line: str) -> Optional[str]:
        """
        Extract clean chapter title from a marker line.

        Args:
            line: Chapter marker line

        Returns:
            Clean chapter title or None
        """
        # Remove common prefixes
        title = line.strip()
        title = re.sub(r'^(?:CHAPTER|Chapter)\s+', '', title, flags=re.IGNORECASE)
        title = re.sub(r'^(?:BOOK|Book)\s+', '', title, flags=re.IGNORECASE)
        title = re.sub(r'^(?:PART|Part)\s+', '', title, flags=re.IGNORECASE)
        title = re.sub(r'^(?:SECTION|Section)\s+', '', title, flags=re.IGNORECASE)
        title = re.sub(r'^(?:PREFACE|Preface|INTRODUCTION|Introduction)\s*:?\s*$', '', title, flags=re.IGNORECASE)
        
        # Clean up the title
        title = title.strip().strip(':').strip()
        
        if title:
            return title
        return None

    def _normalize_whitespace(self, text: str) -> str:
        """
        Normalize whitespace in text.

        Args:
            text: Raw text

        Returns:
            Text with normalized whitespace
        """
        # Replace multiple spaces with single space
        text = re.sub(r' +', ' ', text)
        # Replace multiple newlines with double newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        # Remove leading/trailing whitespace from each line
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)
        return text

    def _remove_gutenberg_boilerplate(self, text: str) -> str:
        """
        Additional cleaning for Gutenberg-specific boilerplate.

        Args:
            text: Raw text

        Returns:
            Cleaned text
        """
        # Remove common Gutenberg header lines before the actual content
        lines = text.split('\n')
        cleaned_lines = []
        content_started = False
        
        for line in lines:
            # Check if we've hit the main content
            if self._is_chapter_marker(line) or self._is_preface_marker(line):
                content_started = True
                cleaned_lines.append(line)
            elif content_started:
                cleaned_lines.append(line)
        
        # If no chapter markers found, return original text
        # This handles books with title-based chapters (e.g., Jekyll and Hyde)
        if not content_started:
            return text
        
        return '\n'.join(cleaned_lines)

    def parse(self, raw_content: str, preserve_original: bool = False) -> Tuple[str, str, Optional[str]]:
        """
        Parse raw content and extract main text.

        Args:
            raw_content: Raw content from URL fetcher
            preserve_original: If True, return original text as third element

        Returns:
            Tuple of (cleaned_text, content_type, original_text_if_preserved)
        """
        self.logger.info(f"Parsing content ({len(raw_content):,} characters)")

        # Detect content type
        content_type = self.detect_content_type(raw_content)
        self.logger.debug(f"Detected content type: {content_type}")

        # Store original if requested
        original_text = raw_content if preserve_original else None

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

        # Normalize whitespace
        cleaned_text = self._normalize_whitespace(cleaned_text)

        # Additional boilerplate removal
        cleaned_text = self._remove_gutenberg_boilerplate(cleaned_text)

        # Final normalization
        cleaned_text = self._normalize_whitespace(cleaned_text)

        chars_removed = len(raw_content) - len(cleaned_text)
        self.logger.info(
            f"Parsed text: {len(cleaned_text):,} characters "
            f"({chars_removed:,} removed)"
        )

        return cleaned_text, content_type, original_text


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
    cleaned_text, content_type, original = parser.parse(raw_content, preserve_original=True)

    print(f"Content type: {content_type}")
    print(f"Original length: {len(raw_content)} characters")
    print(f"Cleaned length: {len(cleaned_text)} characters")
    print(f"Removed: {len(raw_content) - len(cleaned_text)} characters")
    print(f"\nFirst 500 characters of cleaned text:\n{cleaned_text[:500]}")
    print(f"\n--- Sample chapter markers found ---")
    lines = cleaned_text.split('\n')
    for i, line in enumerate(lines[:30]):
        if parser._is_chapter_marker(line) or parser._is_preface_marker(line):
            print(f"  Line {i}: {line[:60]}")


if __name__ == "__main__":
    main()
