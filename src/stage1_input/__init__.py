"""
Stage 1 Input Module - G-Manga
Handles text ingestion from Project Gutenberg and other sources.
"""

from .url_fetcher import URLFetcher
from .text_parser import TextParser
from .metadata_extractor import MetadataExtractor, Metadata
from .chapter_segmenter import ChapterSegmenter, Chapter, SegmentationResult, ContentType
from .ingestion_state import IngestionState, IngestionStateManager, ChapterState, IngestionStatus

__all__ = [
    # URL Fetcher
    "URLFetcher",
    
    # Text Parser
    "TextParser",
    
    # Metadata Extractor
    "MetadataExtractor",
    "Metadata",
    
    # Chapter Segmenter
    "ChapterSegmenter",
    "Chapter",
    "SegmentationResult",
    "ContentType",
    
    # Ingestion State
    "IngestionState",
    "IngestionStateManager",
    "ChapterState",
    "IngestionStatus",
]
