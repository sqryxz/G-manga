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

    def __init__(self, min_chapter_length: int = 1000):
        """Initialize Chapter Segmenter.
        
        Args:
            min_chapter_length: Minimum character length for a valid chapter
                                (filters out table of contents entries)
        """
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
        self.min_chapter_length = min_chapter_length

    def _is_table_of_contents_entry(self, text: str, start_line: int, end_line: int) -> bool:
        """
        Check if a segment is a table of contents entry rather than a real chapter.
        
        Heuristics:
        - Very short content (just a title line)
        - No substantial text content
        
        Args:
            text: Full text
            start_line: Start line of segment
            end_line: End line of segment
            
        Returns:
            True if this appears to be a TOC entry
        """
        lines = text.split("\n")
        segment_lines = lines[start_line:end_line]
        segment_text = "\n".join(segment_lines).strip()
        
        # If segment is very short, it's likely a TOC entry
        if len(segment_text) < self.min_chapter_length:
            return True
            
        # Check if it contains only the chapter title/header
        # and maybe a page number, but no substantial content
        non_empty_lines = [l for l in segment_lines if l.strip()]
        if len(non_empty_lines) <= 2:
            return True
            
        return False

    def _find_first_real_chapter_line(self, chapter_starts: List[Tuple[int, str, int]], text: str) -> int:
        """
        Find the line number of the first real chapter (Chapter I/1).
        
        This helps filter out table of contents entries that appear before
        the actual story content begins.
        
        A "real" chapter has substantial content (> min_chapter_length chars)
        and isn't just a TOC entry.
        
        Args:
            chapter_starts: List of (line_num, marker, pattern_idx) tuples
            text: Full text
            
        Returns:
            Line number of first real chapter, or 0 if not found
        """
        lines = text.split("\n")
        
        for i, (line_num, marker, _) in enumerate(chapter_starts):
            marker_upper = marker.upper().strip()
            # Look for Chapter I, Chapter 1, CHAPTER I., etc.
            if (marker_upper == "CHAPTER I" or 
                marker_upper == "CHAPTER I." or
                marker_upper == "CHAPTER 1" or
                marker_upper == "CHAPTER 1."):
                
                # Check if this chapter has substantial content
                # (i.e., it's not a TOC entry)
                if i + 1 < len(chapter_starts):
                    end_line = chapter_starts[i + 1][0]
                else:
                    end_line = len(lines)
                
                segment_text = "\n".join(lines[line_num:end_line]).strip()
                
                # If this CHAPTER I has substantial content, it's the real one
                if len(segment_text) >= self.min_chapter_length:
                    return line_num
                # Otherwise, keep looking for the next CHAPTER I
        
        return 0

    def segment(self, text: str) -> List[ChapterSegment]:
        """
        Segment text into chapters.

        Args:
            text: The cleaned text

        Returns:
            List of ChapterSegment objects (excluding table of contents entries)
        """
        lines = text.split("\n")
        segments = []

        # Find all chapter markers with their line numbers
        chapter_starts = []  # List of (line_num, marker, pattern_idx)

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

        # Find the first real chapter (Chapter I/1)
        first_chapter_line = self._find_first_real_chapter_line(
            [(ln, mk, 0) for ln, mk in chapter_starts], text
        )

        # Create segments and filter out table of contents entries
        valid_segments = []
        for i, (start_line, marker) in enumerate(chapter_starts):
            # Skip any chapter marker that appears before the first real Chapter I
            # (these are table of contents entries)
            if first_chapter_line > 0 and start_line < first_chapter_line:
                continue
            
            # Determine end line (next chapter start or end of text)
            if i + 1 < len(chapter_starts):
                end_line = chapter_starts[i + 1][0]
            else:
                end_line = len(lines)

            # Skip table of contents entries
            if self._is_table_of_contents_entry(text, start_line, end_line):
                continue

            # Extract title from marker
            title = self._extract_title(marker)

            # Create segment
            segment = ChapterSegment(
                chapter_number=len(valid_segments) + 1,
                title=title,
                start_line=start_line,
                end_line=end_line
            )
            valid_segments.append(segment)

        return valid_segments

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
