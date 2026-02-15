"""
Ingestion State - Stage 1.1.6
Tracks ingestion progress and outputs structured state for next module.
"""

import json
import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

from common.logging import get_logger


class IngestionStatus(Enum):
    """Status of the ingestion process."""
    PENDING = "pending"
    FETCHING = "fetching"
    PARSING = "parsing"
    EXTRACTING_METADATA = "extracting_metadata"
    SEGMENTING = "segmenting"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ChapterState:
    """State for a single chapter."""
    number: int
    title: str
    word_count: int
    content_type: str = "chapter"
    is_optional: bool = False
    text_preview: str = ""
    validation_status: str = "pending"
    issues: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "number": self.number,
            "title": self.title,
            "word_count": self.word_count,
            "content_type": self.content_type,
            "is_optional": self.is_optional,
            "text_preview": self.text_preview[:500] if self.text_preview else "",
            "validation_status": self.validation_status,
            "issues": self.issues
        }


@dataclass
class IngestionStatistics:
    """Statistics for the ingestion process."""
    total_words: int = 0
    chapter_count: int = 0
    preface_count: int = 0
    total_characters: int = 0
    processing_time_seconds: float = 0.0
    characters_removed: int = 0
    gutenberg_header_size: int = 0
    gutenberg_footer_size: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_words": self.total_words,
            "chapter_count": self.chapter_count,
            "preface_count": self.preface_count,
            "total_characters": self.total_characters,
            "processing_time_seconds": self.processing_time_seconds,
            "characters_removed": self.characters_removed,
            "gutenberg_header_size": self.gutenberg_header_size,
            "gutenberg_footer_size": self.gutenberg_footer_size
        }


@dataclass
class IngestionState:
    """
    Complete ingestion state tracking.
    
    This class tracks the entire ingestion process and produces
    a structured output for the next module.
    """
    # Metadata
    title: str
    author: str
    source_url: Optional[str] = None
    
    # Processing state
    status: IngestionStatus = IngestionStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Content details
    language: str = "en"
    year: Optional[int] = None
    gutenberg_id: Optional[int] = None
    
    # Chapters and content
    chapters: List[ChapterState] = field(default_factory=list)
    
    # Statistics
    statistics: IngestionStatistics = field(default_factory=lambda: IngestionStatistics())
    
    # Validation
    validation_passed: bool = False
    validation_issues: List[str] = field(default_factory=list)
    
    # Output info
    checksum: str = ""
    version: str = "1.0.0"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "metadata": {
                "title": self.title,
                "author": self.author,
                "source_url": self.source_url,
                "language": self.language,
                "year": self.year,
                "gutenberg_id": self.gutenberg_id,
                "version": self.version
            },
            "status": self.status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "chapters": [ch.to_dict() for ch in self.chapters],
            "statistics": self.statistics.to_dict(),
            "validation": {
                "passed": self.validation_passed,
                "issues": self.validation_issues
            },
            "checksum": self.checksum
        }

    def to_framework_output(self) -> Dict[str, Any]:
        """
        Convert to the framework spec output format.
        
        Returns:
            Dictionary matching the framework specification
        """
        return {
            "title": self.title,
            "author": self.author,
            "year": self.year or 0,
            "language": self.language,
            "gutenberg_id": self.gutenberg_id,
            "chapters": [
                {
                    "number": ch.number,
                    "title": ch.title,
                    "text": ch.text_preview,
                    "word_count": ch.word_count
                }
                for ch in self.chapters
            ],
            "total_words": self.statistics.total_words
        }

    def _compute_checksum(self) -> str:
        """Compute checksum of the ingestion state."""
        data = f"{self.title}{self.author}{len(self.chapters)}{self.statistics.total_words}{self.version}"
        return hashlib.md5(data.encode()).hexdigest()

    def validate(self) -> bool:
        """
        Validate the ingestion state.
        
        Returns:
            True if validation passed
        """
        issues = []
        
        # Check required fields
        if not self.title or self.title == "Unknown Title":
            issues.append("Title is missing or invalid")
        
        if not self.author or self.author == "Unknown Author":
            issues.append("Author is missing or invalid")
        
        if not self.chapters:
            issues.append("No chapters were extracted")
        
        # Check chapter word counts
        for ch in self.chapters:
            if ch.word_count < 100:
                issues.append(f"Chapter {ch.number} has unusually low word count ({ch.word_count})")
        
        # Check year
        if self.year:
            if self.year < 1400 or self.year > 2030:
                issues.append(f"Year {self.year} is outside expected range")
        
        self.validation_issues = issues
        self.validation_passed = len(issues) == 0
        
        return self.validation_passed


class IngestionStateManager:
    """Manages ingestion state tracking and persistence."""

    def __init__(self, output_dir: str = "./output"):
        """
        Initialize the state manager.
        
        Args:
            output_dir: Directory for output files
        """
        self.logger = get_logger(__name__)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.current_state: Optional[IngestionState] = None

    def create_state(
        self,
        title: str,
        author: str,
        source_url: Optional[str] = None
    ) -> IngestionState:
        """
        Create a new ingestion state.
        
        Args:
            title: Book title
            author: Book author
            source_url: Source URL if applicable

        Returns:
            New IngestionState object
        """
        self.current_state = IngestionState(
            title=title,
            author=author,
            source_url=source_url,
            started_at=datetime.now(),
            status=IngestionStatus.PENDING
        )
        
        self.logger.info(f"Created ingestion state for '{title}' by {author}")
        return self.current_state

    def update_status(self, status: IngestionStatus) -> None:
        """Update the current status."""
        if self.current_state:
            self.current_state.status = status
            self.logger.debug(f"Status updated to {status.value}")

    def add_chapter(
        self,
        number: int,
        title: str,
        word_count: int,
        content_type: str = "chapter",
        is_optional: bool = False,
        text_preview: str = ""
    ) -> None:
        """Add a chapter to the state."""
        if self.current_state:
            chapter = ChapterState(
                number=number,
                title=title,
                word_count=word_count,
                content_type=content_type,
                is_optional=is_optional,
                text_preview=text_preview
            )
            self.current_state.chapters.append(chapter)

    def set_metadata(
        self,
        language: str = None,
        year: int = None,
        gutenberg_id: int = None
    ) -> None:
        """Set metadata fields."""
        if self.current_state:
            if language:
                self.current_state.language = language
            if year:
                self.current_state.year = year
            if gutenberg_id:
                self.current_state.gutenberg_id = gutenberg_id

    def set_statistics(
        self,
        total_words: int = None,
        total_characters: int = None,
        characters_removed: int = None
    ) -> None:
        """Set statistics fields."""
        if self.current_state:
            stats = self.current_state.statistics
            if total_words is not None:
                stats.total_words = total_words
            if total_characters is not None:
                stats.total_characters = total_characters
            if characters_removed is not None:
                stats.characters_removed = characters_removed

    def finalize(self) -> IngestionState:
        """
        Finalize the ingestion state.
        
        Returns:
            The finalized IngestionState
        """
        if not self.current_state:
            raise ValueError("No current state to finalize")

        # Update statistics
        stats = self.current_state.statistics
        stats.chapter_count = len([c for c in self.current_state.chapters if not c.is_optional])
        stats.preface_count = len([c for c in self.current_state.chapters if c.is_optional])

        # Compute checksum
        self.current_state.checksum = self.current_state._compute_checksum()

        # Validate
        self.current_state.validate()

        # Mark completed
        self.current_state.completed_at = datetime.now()
        self.current_state.status = IngestionStatus.COMPLETED

        self.logger.info(
            f"Ingestion completed for '{self.current_state.title}'. "
            f"Chapters: {stats.chapter_count}, Words: {stats.total_words}"
        )

        return self.current_state

    def save_state(self, filename: str = None) -> Path:
        """
        Save the current state to a file.
        
        Args:
            filename: Output filename (auto-generated if None)

        Returns:
            Path to saved file
        """
        if not self.current_state:
            raise ValueError("No current state to save")

        if filename is None:
            # Generate filename from title
            safe_title = re.sub(r'[^\w\-]', '_', self.current_state.title[:30])
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ingestion_{safe_title}_{timestamp}.json"

        output_path = self.output_dir / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.current_state.to_dict(), f, indent=2, ensure_ascii=False)

        self.logger.info(f"Saved ingestion state to {output_path}")
        return output_path

    def save_framework_output(self, filename: str = None) -> Path:
        """
        Save the framework spec output format.
        
        Args:
            filename: Output filename (auto-generated if None)

        Returns:
            Path to saved file
        """
        if not self.current_state:
            raise ValueError("No current state to save")

        if filename is None:
            safe_title = re.sub(r'[^\w\-]', '_', self.current_state.title[:30])
            filename = f"{safe_title}_framework_output.json"

        output_path = self.output_dir / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.current_state.to_framework_output(), f, indent=2, ensure_ascii=False)

        self.logger.info(f"Saved framework output to {output_path}")
        return output_path


def main():
    """Test the Ingestion State manager."""
    import sys
    sys.path.insert(0, '/home/clawd/projects/g-manga/src/stage1_input')
    
    from text_parser import TextParser
    from metadata_extractor import MetadataExtractor
    from chapter_segmenter import ChapterSegmenter

    # Load cached Dorian Gray text
    with open('/home/clawd/projects/g-manga/cache/downloads/abac0c091ac9399b223221e1ba974664.txt', 'r', encoding='utf-8') as f:
        text = f.read()

    # Process the text
    parser = TextParser()
    cleaned_text, _ = parser.parse(text)

    extractor = MetadataExtractor()
    metadata = extractor.extract(cleaned_text, source_url="https://www.gutenberg.org/files/174/174-0.txt")

    segmenter = ChapterSegmenter()
    result = segmenter.segment(cleaned_text)

    # Create and populate ingestion state
    manager = IngestionStateManager(output_dir="/home/clawd/projects/g-manga/output")
    manager.create_state(metadata.title, metadata.author, metadata.source_url)
    manager.set_metadata(metadata.language, metadata.year, metadata.gutenberg_id)
    
    # Add chapters
    for chapter in result.chapters:
        manager.add_chapter(
            number=chapter.number,
            title=chapter.title,
            word_count=chapter.word_count,
            content_type=chapter.content_type.value,
            is_optional=chapter.is_optional
        )

    # Set statistics
    manager.set_statistics(
        total_words=result.total_words,
        total_characters=len(cleaned_text)
    )

    # Finalize and save
    state = manager.finalize()
    
    # Print summary
    print("=== Ingestion State Summary ===")
    print(f"Title: {state.title}")
    print(f"Author: {state.author}")
    print(f"Year: {state.year}")
    print(f"Language: {state.language}")
    print(f"Gutenberg ID: {state.gutenberg_id}")
    print(f"Chapters: {len(state.chapters)}")
    print(f"Total Words: {state.statistics.total_words}")
    print(f"Validation Passed: {state.validation_passed}")
    if state.validation_issues:
        print(f"Validation Issues: {state.validation_issues}")
    print()
    
    # Show framework output
    print("=== Framework Output ===")
    framework = state.to_framework_output()
    print(json.dumps(framework, indent=2))


if __name__ == "__main__":
    import re  # Import for the main function
    main()
