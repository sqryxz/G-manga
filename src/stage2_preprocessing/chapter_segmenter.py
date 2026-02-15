"""
Chapter Segmenter - Stage 2.1.3
Segments text into chapters using regex patterns.
Handles Table of Contents detection to avoid false positives.
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
    
    # TOC detection patterns
    TOC_MARKERS = [
        r"^[\s]*Contents[\s]*$",
        r"^[\s]*Table of Contents[\s]*$",
        r"^[\s]*CONTENTS[\s]*$",
    ]

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
            # "Chapter the First", etc.
            re.compile(r"^(Chapter\s+the\s+\w+)", re.MULTILINE | re.IGNORECASE),
            # Numero-style chapter markers
            re.compile(r"^(Chapter\s+\d+\s*:)", re.MULTILINE),
            # Scene markers (for screenplays)
            re.compile(r"^(INT\.|EXT\.|I\/N\/E\.)\s", re.MULTILINE),
            # Act markers
            re.compile(r"^(ACT\s+[IVXLCDM]+)", re.MULTILINE | re.IGNORECASE),
            # "Part I:", "Part One:", etc.
            re.compile(r"^(Part\s+[IVXLCDM]+:)", re.MULTILINE | re.IGNORECASE),
            # Just numbers (single digits or 1-2 digits at line start)
            re.compile(r"^(\d+)$", re.MULTILINE),
        ]
        self.min_chapter_length = min_chapter_length

    def segment(self, text: str, source: str = "unknown") -> List[ChapterSegment]:
        """Segment text into chapters.
        
        Args:
            text: The text to segment
            source: Source identifier for debugging
            
        Returns:
            List of ChapterSegment objects
        """
        lines = text.split('\n')
        chapters = []
        current_chapter = None
        
        # Detect if this is a TOC page
        in_toc = self._is_table_of_contents(lines)
        
        for i, line in enumerate(lines):
            chapter_match = self._match_chapter_marker(line)
            
            if chapter_match:
                # Save previous chapter
                if current_chapter:
                    current_chapter.text = '\n'.join(lines[current_chapter.start_line:current_chapter.end_line])
                    # Only add if long enough
                    if len(current_chapter.text) >= self.min_chapter_length:
                        chapters.append(current_chapter)
                
                # Start new chapter
                current_chapter = ChapterSegment(
                    chapter_number=len(chapters) + 1,
                    title=chapter_match.group(1).strip() if chapter_match.group(1) else None,
                    start_line=i,
                    end_line=min(i + self.min_chapter_length, len(lines))
                )
        
        # Don't forget the last chapter
        if current_chapter:
            current_chapter.text = '\n'.join(lines[current_chapter.start_line:current_chapter.end_line])
            if len(current_chapter.text) >= self.min_chapter_length:
                chapters.append(current_chapter)
        
        return chapters

    def _is_table_of_contents(self, lines: List[str]) -> bool:
        """Detect if the text starts with a Table of Contents."""
        toc_pattern = re.compile('|'.join(self.TOC_MARKERS))
        toc_count = 0
        for line in lines[:50]:  # Check first 50 lines
            if toc_pattern.match(line.strip()):
                toc_count += 1
            if toc_count >= 3:  # At least 3 TOC entries found
                return True
        return False

    def _match_chapter_marker(self, line: str) -> Optional[re.Match]:
        """Check if a line matches any chapter marker pattern."""
        for pattern in self.chapter_patterns:
            match = pattern.match(line)
            if match:
                return match
        return None


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python chapter_segmenter.py <text_file>")
        sys.exit(1)
    
    with open(sys.argv[1]) as f:
        text = f.read()
    
    segmenter = ChapterSegmenter()
    chapters = segmenter.segment(text, sys.argv[1])
    
    print(f"Found {len(chapters)} chapters:")
    for chapter in chapters:
        print(f"  Chapter {chapter.chapter_number}: {chapter.title} (lines {chapter.start_line}-{chapter.end_line})")
