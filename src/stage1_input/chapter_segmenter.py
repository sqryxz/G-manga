"""
Chapter Segmenter - Stage 1.1.4
Segments text into chapters with optional content detection.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from enum import Enum


class ContentType(Enum):
    """Types of content segments."""
    PREFACE = "preface"
    INTRODUCTION = "introduction"
    FOREWORD = "foreword"
    DEDICATION = "dedication"
    PROLOGUE = "prologue"
    CHAPTER = "chapter"
    EPILOGUE = "epilogue"
    AFTERWORD = "afterword"
    APPENDIX = "appendix"
    UNKNOWN = "unknown"


@dataclass
class Chapter:
    """Represents a chapter or content section."""
    number: int
    title: str
    text: str
    word_count: int
    content_type: ContentType = ContentType.CHAPTER
    start_position: int = 0
    end_position: int = 0
    is_optional: bool = False  # Prefaces, etc. are optional


@dataclass
class SegmentationResult:
    """Result of chapter segmentation."""
    chapters: List[Chapter]
    total_words: int
    has_chapter_markers: bool
    has_prefaces: bool
    segment_count: int


class ChapterSegmenter:
    """Segments text into chapters and other content sections."""

    # Chapter marker patterns (comprehensive)
    CHAPTER_PATTERNS = [
        # Roman numeral: CHAPTER I, Chapter V, Chapter I., etc.
        r'^\s*(?:CHAPTER|Chapter)\s+([IVXLC]+)\.?\s*$',
        # Arabic numeral: Chapter 1, CHAPTER 12, Chapter 1., etc.
        r'^\s*(?:CHAPTER|Chapter)\s+(\d+)\.?\s*$',
        # Named chapter: Chapter One, Chapter First
        r'^\s*(?:CHAPTER|Chapter)\s+(First|Second|Third|Fourth|Fifth|Sixth|Seventh|Eighth|Ninth|Tenth|One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten)\.?\s*$',
        # Book marker: BOOK I, Book One
        r'^\s*(?:BOOK|Book)\s+([IVXLC]+|\d+|[A-Za-z]+)\.?\s*$',
        # Part marker: PART I, Part One
        r'^\s*(?:PART|Part)\s+([IVXLC]+|\d+|[A-Za-z]+)\.?\s*$',
        # Section marker: Section 1
        r'^\s*(?:SECTION|Section)\s+(\d+)\.?\s*$',
        # Just a number on its own line
        r'^\s*(\d+)\s*$',
    ]

    # Optional content markers
    OPTIONAL_CONTENT_PATTERNS = [
        (ContentType.PREFACE, re.compile(r'^\s*(?:PREFACE|Preface)\s*$', re.IGNORECASE)),
        (ContentType.INTRODUCTION, re.compile(r'^\s*(?:INTRODUCTION|Introduction)\s*$', re.IGNORECASE)),
        (ContentType.FOREWORD, re.compile(r'^\s*(?:FOREWORD|Foreword)\s*$', re.IGNORECASE)),
        (ContentType.DEDICATION, re.compile(r'^\s*(?:DEDICATION|Dedication)\s*$', re.IGNORECASE)),
        (ContentType.PROLOGUE, re.compile(r'^\s*(?:PROLOGUE|Prologue)\s*$', re.IGNORECASE)),
        (ContentType.EPILOGUE, re.compile(r'^\s*(?:EPILOGUE|Epilogue)\s*$', re.IGNORECASE)),
        (ContentType.AFTERWORD, re.compile(r'^\s*(?:AFTERWORD|Afterword)\s*$', re.IGNORECASE)),
        (ContentType.APPENDIX, re.compile(r'^\s*(?:APPENDIX|Appendix)\s*$', re.IGNORECASE)),
    ]

    # Scene break patterns
    SCENE_BREAKS = [
        r'^[\*\+\-\=]{3,}\s*$',  # *** or --- or +++
        r'^\s*\*\s*\*\s*\*\s*$',  # * * *
        r'^\s*\+\s*\+\s*\+\s*$',  # + + +
        r'^\s*~\s*~\s*~\s*$',  # ~ ~ ~
        r'^\s*#\s*#\s*#\s*$',  # # # #
    ]

    def __init__(self, min_chapter_words: int = 100, max_chapter_words: int = 50000):
        """
        Initialize the Chapter Segmenter.

        Args:
            min_chapter_words: Minimum words to consider a valid chapter
            max_chapter_words: Maximum words before splitting (safety limit)
        """
        self.min_chapter_words = min_chapter_words
        self.max_chapter_words = max_chapter_words

        # Compile chapter patterns
        self.chapter_patterns = [re.compile(p, re.IGNORECASE) for p in self.CHAPTER_PATTERNS]
        
        # Compile scene break patterns
        self.scene_break_patterns = [re.compile(p) for p in self.SCENE_BREAKS]

        # Roman numeral conversion
        self._roman_to_int = self._build_roman_map()

    def _build_roman_map(self) -> dict:
        """Build Roman numeral to integer mapping."""
        romans = [
            ('M', 1000), ('CM', 900), ('D', 500), ('CD', 400),
            ('C', 100), ('XC', 90), ('L', 50), ('XL', 40),
            ('X', 10), ('IX', 9), ('V', 5), ('IV', 4), ('I', 1)
        ]
        return {k: v for k, v in romans}

    def _roman_to_arabic(self, roman: str) -> int:
        """Convert Roman numeral to Arabic number."""
        roman = roman.upper()
        result = 0
        i = 0
        while i < len(roman):
            if i + 1 < len(roman) and roman[i:i+2] in self._roman_to_int:
                result += self._roman_to_int[roman[i:i+2]]
                i += 2
            elif roman[i] in self._roman_to_int:
                result += self._roman_to_int[roman[i]]
                i += 1
            else:
                return 0
        return result

    def _word_count(self, text: str) -> int:
        """Count words in text."""
        words = text.split()
        return len([w for w in words if w.strip()])

    def _is_scene_break(self, line: str) -> bool:
        """Check if a line is a scene break."""
        stripped = line.strip()
        for pattern in self.scene_break_patterns:
            if pattern.match(stripped):
                return True
        return False

    def _is_chapter_marker(self, line: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Check if a line is a chapter marker.

        Args:
            line: A single line of text

        Returns:
            Tuple of (is_marker, chapter_number, original_marker)
        """
        for pattern in self.chapter_patterns:
            match = pattern.match(line)
            if match:
                group = match.group(1)
                # Convert to number
                try:
                    num = int(group)
                    return True, str(num), line.strip()
                except ValueError:
                    # Try Roman numeral
                    roman_num = self._roman_to_arabic(group)
                    if roman_num > 0:
                        return True, str(roman_num), line.strip()
                    # Named chapter
                    named_nums = {
                        'first': '1', 'second': '2', 'third': '3', 'fourth': '4',
                        'fifth': '5', 'sixth': '6', 'seventh': '7', 'eighth': '8',
                        'ninth': '9', 'tenth': '10', 'one': '1', 'two': '2',
                        'three': '3', 'four': '4', 'five': '5', 'six': '6',
                        'seven': '7', 'eight': '8', 'nine': '9', 'ten': '10'
                    }
                    if group.lower() in named_nums:
                        return True, named_nums[group.lower()], line.strip()

        return False, None, None

    def _is_optional_content(self, line: str) -> Tuple[bool, ContentType]:
        """
        Check if a line is optional content (preface, etc.).

        Args:
            line: A single line of text

        Returns:
            Tuple of (is_optional, content_type)
        """
        for content_type, pattern in self.OPTIONAL_CONTENT_PATTERNS:
            if pattern.match(line):
                return True, content_type
        return False, ContentType.UNKNOWN

    def _clean_chapter_title(self, title: str) -> str:
        """Clean up a chapter title."""
        # Remove common prefixes
        title = re.sub(r'^(?:CHAPTER|Chapter)\s+', '', title, flags=re.IGNORECASE)
        title = re.sub(r'^(?:BOOK|Book)\s+', '', title, flags=re.IGNORECASE)
        title = re.sub(r'^(?:PART|Part)\s+', '', title, flags=re.IGNORECASE)
        title = re.sub(r'^(?:SECTION|Section)\s+', '', title, flags=re.IGNORECASE)
        
        # Clean up
        title = title.strip().strip(':').strip()
        
        return title if title else "Untitled"

    def _segment_by_markers(self, lines: List[str]) -> SegmentationResult:
        """
        Segment text by chapter markers.

        Args:
            lines: List of text lines

        Returns:
            SegmentationResult with chapters
        """
        chapters: List[Chapter] = []
        current_chapter: Optional[Chapter] = None
        current_lines: List[str] = []
        chapter_number = 0
        has_chapter_markers = False
        has_prefaces = False

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Check for chapter marker
            is_marker, ch_num, original = self._is_chapter_marker(stripped)
            is_optional, content_type = self._is_optional_content(stripped)

            if is_marker:
                has_chapter_markers = True

                # Save previous chapter if exists
                if current_chapter is not None:
                    current_chapter.text = '\n'.join(current_lines)
                    current_chapter.word_count = self._word_count(current_chapter.text)
                    current_chapter.end_position = i
                    chapters.append(current_chapter)

                # Start new chapter
                chapter_number = int(ch_num) if ch_num else chapter_number + 1
                title = self._clean_chapter_title(original or stripped)

                current_chapter = Chapter(
                    number=chapter_number,
                    title=title,
                    text="",
                    word_count=0,
                    content_type=ContentType.CHAPTER,
                    start_position=i,
                    end_position=i
                )
                current_lines = []

            elif is_optional and current_chapter is None:
                # Optional content before first chapter
                has_prefaces = True
                if current_chapter is not None:
                    current_chapter.text = '\n'.join(current_lines)
                    current_chapter.word_count = self._word_count(current_chapter.text)
                    chapters.append(current_chapter)

                current_chapter = Chapter(
                    number=0,
                    title=stripped,
                    text="",
                    word_count=0,
                    content_type=content_type,
                    start_position=i,
                    end_position=i,
                    is_optional=True
                )
                current_lines = []

            elif current_chapter is not None:
                current_lines.append(line)

        # Save last chapter
        if current_chapter is not None:
            current_chapter.text = '\n'.join(current_lines)
            current_chapter.word_count = self._word_count(current_chapter.text)
            current_chapter.end_position = len(lines)
            chapters.append(current_chapter)

        # Filter out chapters with too few words (likely TOC markers)
        chapters = [c for c in chapters if c.word_count >= self.min_chapter_words]

        total_words = sum(c.word_count for c in chapters)

        return SegmentationResult(
            chapters=chapters,
            total_words=total_words,
            has_chapter_markers=has_chapter_markers,
            has_prefaces=has_prefaces,
            segment_count=len(chapters)
        )

    def _segment_by_scene_breaks(self, lines: List[str], max_chapters: int = 50) -> SegmentationResult:
        """
        Segment text by scene breaks when no chapter markers exist.

        Args:
            lines: List of text lines
            max_chapters: Maximum number of chapters to create

        Returns:
            SegmentationResult with chapters
        """
        chapters: List[Chapter] = []
        current_chapter_lines: List[str] = []
        chapter_number = 0
        scene_count = 0

        for line in lines:
            if self._is_scene_break(line):
                scene_count += 1
                # Start new chapter every N scene breaks or if chapter gets too long
                if scene_count >= 3 or len('\n'.join(current_chapter_lines)) > 10000:
                    if current_chapter_lines:
                        chapter_number += 1
                        text = '\n'.join(current_chapter_lines)
                        chapters.append(Chapter(
                            number=chapter_number,
                            title=f"Chapter {chapter_number}",
                            text=text,
                            word_count=self._word_count(text),
                            content_type=ContentType.CHAPTER,
                            is_optional=False
                        ))
                    current_chapter_lines = []
                    scene_count = 0
            else:
                current_chapter_lines.append(line)

        # Save last chapter
        if current_chapter_lines:
            chapter_number += 1
            text = '\n'.join(current_chapter_lines)
            chapters.append(Chapter(
                number=chapter_number,
                title=f"Chapter {chapter_number}",
                text=text,
                word_count=self._word_count(text),
                content_type=ContentType.CHAPTER
            ))

        total_words = sum(c.word_count for c in chapters)

        return SegmentationResult(
            chapters=chapters,
            total_words=total_words,
            has_chapter_markers=False,
            has_prefaces=False,
            segment_count=len(chapters)
        )

    def _segment_by_word_count(self, lines: List[str], words_per_chapter: int = 5000) -> SegmentationResult:
        """
        Segment text by word count as fallback.

        Args:
            lines: List of text lines
            words_per_chapter: Approximate words per chapter

        Returns:
            SegmentationResult with chapters
        """
        chapters: List[Chapter] = []
        current_chapter_lines: List[str] = []
        current_word_count = 0
        chapter_number = 0

        for line in lines:
            line_words = len(line.split())
            
            if current_word_count + line_words >= words_per_chapter and current_word_count > 0:
                # Start new chapter
                chapter_number += 1
                text = '\n'.join(current_chapter_lines)
                chapters.append(Chapter(
                    number=chapter_number,
                    title=f"Chapter {chapter_number}",
                    text=text,
                    word_count=current_word_count,
                    content_type=ContentType.CHAPTER
                ))
                current_chapter_lines = []
                current_word_count = 0
            
            current_chapter_lines.append(line)
            current_word_count += line_words

        # Save last chapter
        if current_chapter_lines:
            chapter_number += 1
            text = '\n'.join(current_chapter_lines)
            chapters.append(Chapter(
                number=chapter_number,
                title=f"Chapter {chapter_number}",
                text=text,
                word_count=self._word_count(text),
                content_type=ContentType.CHAPTER
            ))

        total_words = sum(c.word_count for c in chapters)

        return SegmentationResult(
            chapters=chapters,
            total_words=total_words,
            has_chapter_markers=False,
            has_prefaces=False,
            segment_count=len(chapters)
        )

    def segment(self, text: str, prefer_word_count: bool = False) -> SegmentationResult:
        """
        Segment text into chapters.

        Args:
            text: The cleaned text to segment
            prefer_word_count: If True, use word count segmentation even if markers exist

        Returns:
            SegmentationResult with chapters and statistics
        """
        lines = text.split('\n')

        # First, check for chapter markers
        has_chapter_markers = any(
            self._is_chapter_marker(line.strip())[0]
            for line in lines
        )

        if has_chapter_markers and not prefer_word_count:
            result = self._segment_by_markers(lines)
        else:
            # Try scene breaks first
            has_scene_breaks = any(
                self._is_scene_break(line)
                for line in lines
            )

            if has_scene_breaks:
                result = self._segment_by_scene_breaks(lines)
            else:
                # Fall back to word count
                result = self._segment_by_word_count(lines)

        return result


def main():
    """Test the Chapter Segmenter."""
    import sys
    sys.path.insert(0, '/home/clawd/projects/g-manga/src/stage1_input')

    # Load cached Dorian Gray text
    with open('/home/clawd/projects/g-manga/cache/downloads/abac0c091ac9399b223221e1ba974664.txt', 'r', encoding='utf-8') as f:
        text = f.read()

    from text_parser import TextParser
    from metadata_extractor import MetadataExtractor

    parser = TextParser()
    cleaned_text, _ = parser.parse(text)

    extractor = MetadataExtractor()
    metadata = extractor.extract(cleaned_text, source_url="https://www.gutenberg.org/files/174/174-0.txt")

    segmenter = ChapterSegmenter()
    result = segmenter.segment(cleaned_text)

    print(f"Title: {metadata.title}")
    print(f"Author: {metadata.author}")
    print(f"Year: {metadata.year}")
    print(f"Total words: {result.total_words}")
    print(f"Chapters: {len(result.chapters)}")
    print(f"Has chapter markers: {result.has_chapter_markers}")
    print(f"Has prefaces: {result.has_prefaces}")
    print()
    
    # Show first 5 chapters
    for i, chapter in enumerate(result.chapters[:5]):
        print(f"  Chapter {chapter.number}: {chapter.title}")
        print(f"    Words: {chapter.word_count}")
        print(f"    Optional: {chapter.is_optional}")
        print(f"    Content Type: {chapter.content_type.value}")
        print()

    if len(result.chapters) > 5:
        print(f"  ... and {len(result.chapters) - 5} more chapters")


if __name__ == "__main__":
    main()
