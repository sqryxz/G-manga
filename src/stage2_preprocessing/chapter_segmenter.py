"""
Chapter Segmenter - Stage 2.1.2
Segments text into chapters using regex patterns.
"""

import re
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ChapterSegment:
    """A detected chapter segment."""
    chapter_number: int
    title: Optional[str]
    start_line: int
    end_line: int
    text: Optional[str] = None


class ChapterSegmenter:
    """Segments text into chapters using regex patterns."""

    def __init__(self):
        """Initialize Chapter Segmenter."""
        # Chapter marker patterns (in order of specificity)
        self.chapter_patterns = [
            # "CHAPTER I.", "CHAPTER II.", etc.
            re.compile(r"^(CHAPTER\s+[IVXLCDM]+\.)", re.MULTILINE),
            # "Chapter I", "Chapter 2", etc.
            re.compile(r"^(Chapter\s+\d+)", re.MULTILINE),
            # "CHAPTER ONE", "CHAPTER TWO", etc.
            re.compile(r"^(CHAPTER\s+[A-Z]+)", re.MULTILINE),
            # "Part I", "Part 2", etc.
            re.compile(r"^(Part\s+[IVXLCDM]+|\d+)", re.MULTILINE),
        ]

    def segment(self, text: str) -> List[ChapterSegment]:
        """
        Segment text into chapters.

        Args:
            text: The cleaned text

        Returns:
            List of ChapterSegment objects
        """
        lines = text.split("\n")
        segments = []

        # Find all chapter markers with their line numbers
        chapter_starts = []  # List of (line_num, marker)

        for pattern_idx, pattern in enumerate(self.chapter_patterns):
            # Only use the most specific pattern that matched
            # Skip if we already have a match near this line (within 10 lines)
            last_line = chapter_starts[-1][0] if chapter_starts else -1

            for match in pattern.finditer(text):
                line_num = text[:match.start()].count('\n')
                marker = match.group(0)

                # Check if this is too close to an existing match
                if last_line >= 0 and line_num - last_line < 10:
                    continue

                chapter_starts.append((line_num, marker, pattern_idx))

        # Sort by line number, then by pattern specificity (earlier patterns are more specific)
        chapter_starts.sort(key=lambda x: (x[0], x[2]))

        # Remove line number duplicates (keep first match)
        unique_starts = {}
        for line_num, marker, pattern_idx in chapter_starts:
            if line_num not in unique_starts:
                unique_starts[line_num] = (line_num, marker)
        chapter_starts = list(unique_starts.values())

        # Create segments
        for i, (start_line, marker) in enumerate(chapter_starts):
            # Determine end line (next chapter start or end of text)
            if i + 1 < len(chapter_starts):
                end_line = chapter_starts[i + 1][0]
            else:
                end_line = len(lines)

            # Extract title from marker
            title = self._extract_title(marker)

            # Create segment
            segment = ChapterSegment(
                chapter_number=i + 1,
                title=title,
                start_line=start_line,
                end_line=end_line
            )
            segments.append(segment)

        return segments

    def _extract_title(self, marker: str) -> Optional[str]:
        """
        Extract chapter title from marker.

        Args:
            marker: The matched chapter marker text

        Returns:
            Chapter title or None
        """
        # Remove "CHAPTER" prefix
        marker = re.sub(r"^CHAPTER\s+", "", marker, flags=re.IGNORECASE)
        marker = re.sub(r"^Chapter\s+", "", marker, flags=re.IGNORECASE)
        marker = re.sub(r"^Part\s+", "", marker, flags=re.IGNORECASE)

        # Clean up
        title = marker.strip()

        if title:
            return title

        return None

    def extract_text(self, segments: List[ChapterSegment], full_text: str) -> List[ChapterSegment]:
        """
        Extract text for each chapter segment.

        Args:
            segments: List of chapter segments (without text)
            full_text: The full cleaned text

        Returns:
            List of ChapterSegment objects with text populated
        """
        lines = full_text.split("\n")

        for segment in segments:
            # Extract text for this chapter
            chapter_lines = lines[segment.start_line:segment.end_line]
            segment.text = "\n".join(chapter_lines)

        return segments


def main():
    """Test Chapter Segmenter."""
    import sys
    sys.path.insert(0, '/home/clawd/projects/g-manga/src/stage1_input')

    from url_fetcher import URLFetcher
    from text_parser import TextParser

    # Get test text
    test_url = "https://www.gutenberg.org/files/174/174-0.txt"

    fetcher = URLFetcher()
    raw = fetcher.fetch(test_url)

    parser = TextParser()
    cleaned, _ = parser.parse(raw)

    # Segment into chapters
    segmenter = ChapterSegmenter()
    segments = segmenter.segment(cleaned)
    segments = segmenter.extract_text(segments, cleaned)

    print(f"Found {len(segments)} chapters")
    print()

    for i, seg in enumerate(segments[:5]):  # Show first 5
        print(f"Chapter {seg.chapter_number}: {seg.title or '(Untitled)'}")
        print(f"  Lines: {seg.start_line} - {seg.end_line}")
        print(f"  Length: {len(seg.text):,} characters")
        if seg.text:
            preview = seg.text[:100].replace('\n', ' ')
            print(f"  Preview: {preview}...")
        print()


if __name__ == "__main__":
    main()
