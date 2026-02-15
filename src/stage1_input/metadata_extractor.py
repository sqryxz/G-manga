"""
Metadata Extractor - Stage 1.1.3
Extracts metadata from Project Gutenberg content.
"""

import re
from typing import Dict, Optional
from dataclasses import dataclass, field


@dataclass
class Metadata:
    """Metadata for a Project Gutenberg text."""
    title: str
    author: str
    year: Optional[int] = None
    language: str = "en"
    gutenberg_id: Optional[int] = None
    source_url: Optional[str] = None
    subtitle: Optional[str] = None
    release_date: Optional[str] = None
    # Extra fields for validation
    _validation_warnings: list = field(default_factory=list)


class MetadataExtractor:
    """Extracts metadata from Project Gutenberg content."""

    # Language code mapping for common languages
    LANGUAGE_MAP = {
        'en': 'en', 'english': 'en',
        'fr': 'fr', 'french': 'fr',
        'de': 'de', 'german': 'de',
        'es': 'es', 'spanish': 'es',
        'it': 'it', 'italian': 'it',
        'pt': 'pt', 'portuguese': 'pt',
        'ru': 'ru', 'russian': 'ru',
        'ja': 'ja', 'japanese': 'ja',
        'zh': 'zh', 'chinese': 'zh',
        'nl': 'nl', 'dutch': 'nl',
        'pl': 'pl', 'polish': 'pl',
        'sv': 'sv', 'swedish': 'sv',
        'da': 'da', 'danish': 'da',
        'fi': 'fi', 'finnish': 'fi',
        'no': 'no', 'norwegian': 'no',
    }

    def __init__(self):
        """Initialize the Metadata Extractor."""
        # Title patterns (first non-empty line, "Title:" prefix, etc.)
        self.title_patterns = [
            re.compile(r"Title:\s*(.+)", re.IGNORECASE),
            re.compile(r"Subtitle:\s*(.+)", re.IGNORECASE),
            re.compile(r"\b(?:The|A|An)\s+[A-Z][^\n]{10,150}"),
        ]

        # Author patterns (various formats)
        self.author_patterns = [
            re.compile(r"Author:\s*(.+)", re.IGNORECASE),
            re.compile(r"by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)"),
            re.compile(r"\*\*\*\s+START OF.*?\*\*\*\s*\n\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)"),
        ]

        # Year patterns - more comprehensive
        self.year_patterns = [
            re.compile(r"Release\s+Date:\s*[\w\s,]+\s+(\d{4})", re.IGNORECASE),
            re.compile(r"Published\s*\s*(\d{4})", re.IGNORECASE),
            re.compile(r"Copyright\s+\D*(\d{4})", re.IGNORECASE),
            re.compile(r"\b(1[4-9]\d{2}|20[0-2]\d)\b"),  # Broad year search 1400-2029
        ]

        # Language patterns
        self.language_patterns = [
            re.compile(r"Language:\s*(\w{2,3})", re.IGNORECASE),
            re.compile(r"Language:\s*English", re.IGNORECASE),
            re.compile(r"Language:\s*French", re.IGNORECASE),
            re.compile(r"Language:\s*German", re.IGNORECASE),
        ]

        # Gutenberg ID patterns
        self.gutenberg_id_patterns = [
            re.compile(r"gutenberg\.org/files/(\d+)/"),
            re.compile(r"gutenberg\.org/ebooks/(\d+)"),
            re.compile(r"EBook\s+#?(\d+)"),
            re.compile(r"\*\*\*\s*START OF.*?EBOOK\s+(\d+)\s*\*\*\*"),
        ]

    def extract_title(self, content: str) -> tuple[str, Optional[str]]:
        """
        Extract the title from content.

        Args:
            content: The cleaned content

        Returns:
            Tuple of (title, subtitle)
        """
        lines = content.split("\n")

        # First, try explicit "Title:" pattern
        for line in lines[:100]:  # Check first 100 lines
            # Check for subtitle first
            subtitle_match = re.search(r"Subtitle:\s*(.+)", line, re.IGNORECASE)
            if subtitle_match:
                subtitle = subtitle_match.group(1).strip()
            else:
                subtitle = None

            for pattern in self.title_patterns[:1]:  # Only explicit patterns first
                match = pattern.search(line)
                if match:
                    title = match.group(1).strip()
                    # Clean up title
                    title = re.sub(r'\s+', ' ', title)
                    title = title.strip('"\'-')
                    
                    if len(title) > 3 and len(title) < 300:
                        return title, subtitle

        # Fallback: first non-empty, non-trivial line that's likely a title
        for line in lines[:50]:
            stripped = line.strip()
            if stripped and not stripped.startswith("*") and not stripped.startswith("Chapter"):
                if len(stripped) > 3 and len(stripped) < 200:
                    # Remove common prefixes and clean
                    title = stripped
                    title = re.sub(r"^The\s+", "", title, count=1, flags=re.IGNORECASE)
                    title = re.sub(r'\s+', ' ', title)
                    title = title.strip('"\'-')
                    
                    # Skip lines that are clearly not titles
                    skip_patterns = [
                        r'^\d+\s*$',  # Just a number
                        r'^Contents?$',
                        r'^Table of Contents',
                        r'^Preface',
                        r'^Introduction',
                    ]
                    skip = any(re.match(p, title, re.IGNORECASE) for p in skip_patterns)
                    
                    if not skip:
                        return title, None

        return "Unknown Title", None

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
        for line in lines[:100]:
            for pattern in self.author_patterns[:1]:
                match = pattern.search(line)
                if match:
                    author = match.group(1).strip()
                    # Remove common suffixes and parentheses content
                    author = re.sub(r"\s+\(.+\)$", "", author)
                    author = re.sub(r"^by\s+", "", author, flags=re.IGNORECASE)
                    author = re.sub(r'\s+', ' ', author)
                    author = author.strip()
                    
                    if len(author) > 2 and len(author) < 100:
                        return author

        # Try other patterns
        for line in lines[:150]:
            for pattern in self.author_patterns[1:]:
                match = pattern.search(line)
                if match:
                    author = match.group(1).strip()
                    author = re.sub(r'\s+', ' ', author)
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
        for pattern in self.year_patterns[:2]:
            match = pattern.search(content)
            if match:
                try:
                    year = int(match.group(1))
                    # Validate year range for reasonable publication dates
                    if 1400 <= year <= 2030:
                        return year
                except ValueError:
                    pass

        # Fallback: search for any 4-digit year
        for pattern in self.year_patterns[3:]:
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
                lang = match.group(1).strip().lower()
                # Map to standard code
                return self.LANGUAGE_MAP.get(lang, lang)

        # Try to detect language from content
        return self._detect_language_from_content(content)

    def _detect_language_from_content(self, content: str) -> str:
        """
        Simple language detection from content.

        Args:
            content: The text content

        Returns:
            Detected language code
        """
        # Very basic detection based on common words
        content_lower = content.lower()
        
        # Check for common words in different languages
        english_words = [' the ', ' be ', ' to ', ' of ', ' and ', ' a ', ' in ']
        french_words = [' le ', ' la ', ' les ', ' un ', ' une ', ' des ', ' et ', ' de ']
        german_words = [' der ', ' die ', ' das ', ' und ', ' ein ', ' eine ', ' zu ']
        spanish_words = [' el ', ' la ', ' los ', ' las ', ' un ', ' una ', ' y ', ' de ']
        
        eng_count = sum(content_lower.count(w) for w in english_words)
        fra_count = sum(content_lower.count(w) for w in french_words)
        ger_count = sum(content_lower.count(w) for w in german_words)
        spa_count = sum(content_lower.count(w) for w in spanish_words)
        
        counts = {'en': eng_count, 'fr': fra_count, 'de': ger_count, 'es': spa_count}
        detected = max(counts, key=counts.get)
        
        # Only return if we have reasonable confidence
        if counts[detected] > 10:
            return detected
        
        return "en"  # Default to English

    def extract_gutenberg_id(self, content: str, source_url: str = None) -> Optional[int]:
        """
        Extract the Gutenberg ID from content or URL.

        Args:
            content: The cleaned content
            source_url: Optional source URL

        Returns:
            Gutenberg ID or None
        """
        # Try to extract from URL first
        if source_url:
            for pattern in self.gutenberg_id_patterns[:1]:
                match = pattern.search(source_url)
                if match:
                    try:
                        return int(match.group(1))
                    except ValueError:
                        pass

        # Try to extract from content header
        lines = content.split("\n")[:50]
        for line in lines:
            for pattern in self.gutenberg_id_patterns[2:]:
                match = pattern.search(line)
                if match:
                    try:
                        return int(match.group(1))
                    except ValueError:
                        pass

        return None

    def validate_year(self, year: Optional[int], expected_range: tuple = (1400, 2030)) -> tuple[bool, Optional[int]]:
        """
        Validate and optionally correct a year.

        Args:
            year: The extracted year
            expected_range: Tuple of (min_year, max_year)

        Returns:
            Tuple of (is_valid, validated_year)
        """
        if year is None:
            return False, None
        
        min_year, max_year = expected_range
        
        if min_year <= year <= max_year:
            return True, year
        
        # Try to find a nearby valid year
        # For example, if 1890 was entered as 2890
        if year > max_year:
            # Try removing first digit
            potential = year % 10000
            if min_year <= potential <= max_year:
                return False, potential  # Flag as potentially corrected
        
        return False, year

    def extract(self, content: str, source_url: str = None) -> Metadata:
        """
        Extract all metadata from content.

        Args:
            content: The cleaned content
            source_url: Optional source URL for extracting Gutenberg ID

        Returns:
            Metadata object
        """
        title, subtitle = self.extract_title(content)
        author = self.extract_author(content)
        year = self.extract_year(content)
        language = self.extract_language(content)
        gutenberg_id = self.extract_gutenberg_id(content, source_url)

        # Validate year
        is_valid_year, validated_year = self.validate_year(year)

        # Create metadata with validation warnings
        warnings = []
        if not is_valid_year and year is not None:
            warnings.append(f"Year {year} may be outside expected range")

        metadata = Metadata(
            title=title,
            author=author,
            year=validated_year,
            language=language,
            gutenberg_id=gutenberg_id,
            source_url=source_url,
            subtitle=subtitle,
            _validation_warnings=warnings
        )

        return metadata


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
    if metadata.subtitle:
        print(f"  Subtitle: {metadata.subtitle}")
    print(f"  Author: {metadata.author}")
    print(f"  Year: {metadata.year}")
    print(f"  Language: {metadata.language}")
    print(f"  Gutenberg ID: {metadata.gutenberg_id}")
    print(f"  Source URL: {metadata.source_url}")
    if metadata._validation_warnings:
        print(f"  Warnings: {metadata._validation_warnings}")


if __name__ == "__main__":
    main()
