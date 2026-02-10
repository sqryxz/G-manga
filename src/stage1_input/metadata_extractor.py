"""
Metadata Extractor - Stage 1.1.3
Extracts metadata from Project Gutenberg content.
"""

import re
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class Metadata:
    """Metadata for a Project Gutenberg text."""
    title: str
    author: str
    year: Optional[int] = None
    language: str = "en"
    gutenberg_id: Optional[int] = None
    source_url: Optional[str] = None


class MetadataExtractor:
    """Extracts metadata from Project Gutenberg content."""

    def __init__(self):
        """Initialize the Metadata Extractor."""
        # Title patterns (first non-empty line, "Title:" prefix, etc.)
        self.title_patterns = [
            re.compile(r"Title:\s*(.+)", re.IGNORECASE),
            re.compile(r"\b(?:The|A|An)\s+[A-Z][^\n]+", re.MULTILINE),
        ]

        # Author patterns (various formats)
        self.author_patterns = [
            re.compile(r"Author:\s*(.+)", re.IGNORECASE),
            re.compile(r"by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)"),
            re.compile(r"\*\*\*\s+START OF.*?\*\*\*\s*\n\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)"),
        ]

        # Year patterns
        self.year_patterns = [
            re.compile(r"Release Date:\s*[\w\s,]+\s+(\d{4})"),
            re.compile(r"\b(18|19|20)\d{2}\b"),
        ]

        # Language patterns
        self.language_patterns = [
            re.compile(r"Language:\s*(\w{2,3})", re.IGNORECASE),
        ]

        # Gutenberg ID pattern
        self.gutenberg_id_pattern = re.compile(r"gutenberg\.org/files/(\d+)/")

    def extract_title(self, content: str) -> str:
        """
        Extract the title from content.

        Args:
            content: The cleaned content

        Returns:
            Extracted title
        """
        lines = content.split("\n")

        # First, try explicit "Title:" pattern
        for line in lines[:50]:  # Check first 50 lines
            for pattern in self.title_patterns[:1]:  # Only explicit patterns first
                match = pattern.search(line)
                if match:
                    title = match.group(1).strip()
                    if len(title) > 3 and len(title) < 200:
                        return title

        # Fallback: first non-empty, non-trivial line
        for line in lines[:30]:
            stripped = line.strip()
            if stripped and not stripped.startswith("*") and not stripped.startswith("Chapter"):
                if len(stripped) > 3 and len(stripped) < 200:
                    # Remove common prefixes
                    title = stripped
                    title = re.sub(r"^The\s+", "", title, count=1, flags=re.IGNORECASE)
                    return title

        return "Unknown Title"

    def extract_author(self, content: str) -> str:
        """
        Extract the author from content.

        Args:
            content: The cleaned content

        Returns:
            Extracted author
        """
        lines = content.split("\n")

        # Try explicit "Author:" pattern first
        for line in lines[:50]:
            for pattern in self.author_patterns[:1]:
                match = pattern.search(line)
                if match:
                    author = match.group(1).strip()
                    if len(author) > 2 and len(author) < 100:
                        # Remove common suffixes
                        author = re.sub(r"\s+\(.+\)$", "", author)
                        return author

        # Try other patterns
        for line in lines[:100]:
            for pattern in self.author_patterns[1:]:
                match = pattern.search(line)
                if match:
                    author = match.group(1).strip()
                    if len(author) > 2 and len(author) < 100:
                        return author

        return "Unknown Author"

    def extract_year(self, content: str) -> Optional[int]:
        """
        Extract the publication year from content.

        Args:
            content: The cleaned content

        Returns:
            Publication year or None
        """
        # Try "Release Date:" pattern first (most reliable for Gutenberg)
        for pattern in self.year_patterns[:1]:
            match = pattern.search(content)
            if match:
                try:
                    year = int(match.group(1))
                    # Validate year range
                    if 1400 <= year <= 2030:
                        return year
                except ValueError:
                    pass

        # Fallback: first valid year
        for pattern in self.year_patterns[1:]:
            matches = pattern.finditer(content)
            for match in matches:
                try:
                    year = int(match.group(0))
                    if 1400 <= year <= 2030:
                        return year
                except ValueError:
                    pass

        return None

    def extract_language(self, content: str) -> str:
        """
        Extract the language from content.

        Args:
            content: The cleaned content

        Returns:
            Language code (e.g., "en", "fr")
        """
        for pattern in self.language_patterns:
            match = pattern.search(content)
            if match:
                language = match.group(1).strip().lower()
                if len(language) >= 2:
                    return language

        return "en"  # Default to English

    def extract(self, content: str, source_url: str = None) -> Metadata:
        """
        Extract all metadata from content.

        Args:
            content: The cleaned content
            source_url: Optional source URL for extracting Gutenberg ID

        Returns:
            Metadata object
        """
        title = self.extract_title(content)
        author = self.extract_author(content)
        year = self.extract_year(content)
        language = self.extract_language(content)

        # Extract Gutenberg ID from URL
        gutenberg_id = None
        if source_url:
            match = self.gutenberg_id_pattern.search(source_url)
            if match:
                gutenberg_id = int(match.group(1))

        return Metadata(
            title=title,
            author=author,
            year=year,
            language=language,
            gutenberg_id=gutenberg_id,
            source_url=source_url
        )


def main():
    """Test the Metadata Extractor."""
    import sys
    sys.path.insert(0, '/home/clawd/projects/g-manga/src/stage1_input')

    from url_fetcher import URLFetcher
    from text_parser import TextParser

    test_url = "https://www.gutenberg.org/files/174/174-0.txt"

    fetcher = URLFetcher()
    raw_content = fetcher.fetch(test_url)

    parser = TextParser()
    cleaned_text, _ = parser.parse(raw_content)

    extractor = MetadataExtractor()
    metadata = extractor.extract(cleaned_text, source_url=test_url)

    print("Extracted Metadata:")
    print(f"  Title: {metadata.title}")
    print(f"  Author: {metadata.author}")
    print(f"  Year: {metadata.year}")
    print(f"  Language: {metadata.language}")
    print(f"  Gutenberg ID: {metadata.gutenberg_id}")
    print(f"  Source URL: {metadata.source_url}")


if __name__ == "__main__":
    main()
