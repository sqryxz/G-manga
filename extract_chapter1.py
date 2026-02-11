#!/usr/bin/env python3
"""
Extract Chapter 1 of Dorian Gray and generate FLUX images.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from stage2_preprocessing.chapter_segmenter import ChapterSegmenter
from stage1_input.text_parser import TextParser

def extract_chapter_1():
    """Extract Chapter 1 from the cached text."""
    # Read cached text
    cache_path = Path("/home/clawd/projects/g-manga/cache/downloads/abac0c091ac9399b223221e1ba974664.txt")
    
    with open(cache_path, 'r', encoding='utf-8') as f:
        raw_text = f.read()
    
    # Parse text
    parser = TextParser()
    cleaned_text, metadata = parser.parse(raw_text)
    
    # Find chapters
    segmenter = ChapterSegmenter()
    segments = segmenter.segment(cleaned_text)
    
    # Extract text for Chapter 1
    lines = cleaned_text.split('\n')
    
    # The first real chapter (after preface) should be Chapter I
    chapter_1 = None
    for seg in segments:
        if seg.chapter_number == 1:
            chapter_1_text = '\n'.join(lines[seg.start_line:seg.end_line])
            chapter_1 = {
                'id': f"chapter-{seg.chapter_number}",
                'number': seg.chapter_number,
                'title': seg.title,
                'start_line': seg.start_line,
                'end_line': seg.end_line,
                'text': chapter_1_text
            }
            break
    
    return chapter_1, cleaned_text

if __name__ == "__main__":
    chapter_1, full_text = extract_chapter_1()
    
    if chapter_1:
        print(f"Chapter 1: {chapter_1['title']}")
        print(f"Lines: {chapter_1['start_line']} - {chapter_1['end_line']}")
        print(f"Characters: {len(chapter_1['text']):,}")
        print(f"\nFirst 500 characters:")
        print(chapter_1['text'][:500])
    else:
        print("Could not find Chapter 1")
