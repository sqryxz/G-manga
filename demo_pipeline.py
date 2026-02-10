"""
Demo Script - G-Manga Pipeline Stages 1 & 2
Demonstrates all completed functionality.
"""

import sys
from pathlib import Path

# Use proper package imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from stage1_input.url_fetcher import URLFetcher
from stage1_input.text_parser import TextParser
from stage1_input.metadata_extractor import MetadataExtractor
from stage1_input.project import ProjectInitializer
from models.project import Metadata, Chapter, Scene, TextRange
from stage2_preprocessing.text_cleaner import TextCleaner
from stage2_preprocessing.chapter_segmenter import ChapterSegmenter
from stage2_preprocessing.scene_breakdown import SceneBreakdown
from stage2_preprocessing.state import StatePersistence
from common.mocking import MockLLMClient


def demo_pipeline():
    """Run complete pipeline demo."""
    print("=" * 70)
    print("G-Manga Pipeline Demo - Stages 1 & 2")
    print("=" * 70)

    # Step 1: Fetch from Gutenberg
    print("\n" + "=" * 70)
    print("STAGE 1.1.1: URL Fetcher")
    print("=" * 70)

    test_url = "https://www.gutenberg.org/files/174/174-0.txt"

    fetcher = URLFetcher(cache_dir="/home/clawd/projects/g-manga/tests/cache")
    print(f"Fetching: {test_url}")

    raw_content = fetcher.fetch(test_url)
    print(f"✓ Fetched {len(raw_content):,} characters")

    # Show first 100 chars
    print(f"Preview: {raw_content[:100]}...")

    # Step 2: Parse and remove boilerplate
    print("\n" + "=" * 70)
    print("STAGE 1.1.2: Text Parser")
    print("=" * 70)

    parser = TextParser()
    cleaned_text, content_type = parser.parse(raw_content)

    print(f"✓ Content type: {content_type}")
    print(f"✓ Removed {len(raw_content) - len(cleaned_text):,} characters of boilerplate")
    print(f"✓ Cleaned text length: {len(cleaned_text):,} characters")

    # Step 3: Extract metadata
    print("\n" + "=" * 70)
    print("STAGE 1.1.3: Metadata Extractor")
    print("=" * 70)

    extractor = MetadataExtractor()
    metadata_data = extractor.extract(cleaned_text, source_url=test_url)

    metadata = Metadata(**metadata_data.model_dump() if hasattr(metadata_data, 'model_dump') else metadata_data.__dict__)

    print(f"✓ Title: {metadata.title}")
    print(f"✓ Author: {metadata.author}")
    print(f"✓ Year: {metadata.year}")
    print(f"✓ Language: {metadata.language}")
    print(f"✓ Gutenberg ID: {metadata.gutenberg_id}")

    # Step 4: Initialize project
    print("\n" + "=" * 70)
    print("STAGE 1.1.5: Project Initializer")
    print("=" * 70)

    initializer = ProjectInitializer(base_dir="/home/clawd/projects/g-manga/projects")
    project = initializer.create_project("Demo Dorian Gray", metadata)

    print(f"✓ Project ID: {project.id}")
    print(f"✓ Project name: {project.name}")
    print(f"✓ Created at: {project.created_at}")

    # Step 5: Text cleaning (Stage 2.1.1)
    print("\n" + "=" * 70)
    print("STAGE 2.1.1: Text Cleaner")
    print("=" * 70)

    cleaner = TextCleaner()
    super_clean = cleaner.clean(cleaned_text)

    print(f"✓ Cleaned text length: {len(super_clean):,} characters")
    print(f"✓ Removed {len(cleaned_text) - len(super_clean):,} more characters")

    # Step 6: Chapter segmentation (Stage 2.1.2)
    print("\n" + "=" * 70)
    print("STAGE 2.1.2: Chapter Segmenter")
    print("=" * 70)

    segmenter = ChapterSegmenter()
    chapters_data = segmenter.segment(super_clean)

    print(f"✓ Found {len(chapters_data)} chapters")

    # Show first 3 chapters
    print("\nFirst 3 chapters:")
    for i, chapter in enumerate(chapters_data[:3]):
        print(f"  Chapter {chapter.chapter_number}: '{chapter.title or '(Untitled)'}'")
        print(f"    Lines: {chapter.start_line} - {chapter.end_line}")
        print(f"    Length: {chapter.end_line - chapter.start_line:,} lines")

    # Step 7: Scene breakdown (Stage 2.1.3)
    print("\n" + "=" * 70)
    print("STAGE 2.1.3: Scene Breakdown (with mock LLM)")
    print("=" * 70)

    breakdown = SceneBreakdown(llm_client=MockLLMClient())

    # Get first chapter text
    lines = super_clean.split("\n")
    first_chapter = chapters_data[0]
    chapter_text = "\n".join(lines[first_chapter.start_line:first_chapter.end_line])

    scenes = breakdown.breakdown_chapter(
        chapter_text,
        f"chapter-{first_chapter.chapter_number}",
        first_chapter.chapter_number
    )

    print(f"✓ Found {len(scenes)} scenes in Chapter 1")

    # Show scenes
    for scene in scenes:
        print(f"\n  Scene {scene.number}:")
        print(f"    ID: {scene.id}")
        print(f"    Summary: {scene.summary}")
        print(f"    Location: {scene.location}")
        print(f"    Characters: {', '.join(scene.characters)}")
        print(f"    Lines: {scene.text_range.start} - {scene.text_range.end}")

        # Show first 100 chars of scene text
        if scene.text:
            preview = scene.text[:100].replace('\n', ' ')
            print(f"    Preview: {preview}...")

    # Step 8: State persistence (Stage 2.1.5)
    print("\n" + "=" * 70)
    print("STAGE 2.1.5: State Persistence")
    print("=" * 70)

    persistence = StatePersistence(f"/home/clawd/projects/g-manga/projects/{project.id}")

    # Convert to Pydantic models
    chapters = []
    for chapter_data in chapters_data[:3]:  # Only save first 3 for demo
        chapter = Chapter(
            id=f"chapter-{chapter_data.chapter_number}",
            number=chapter_data.chapter_number,
            title=chapter_data.title,
            text_range=TextRange(start=chapter_data.start_line, end=chapter_data.end_line)
        )
        chapters.append(chapter)

    persistence.save_chapters(chapters)
    persistence.save_scenes(scenes)

    # Update state
    state = persistence.load_state()
    current_stages = state.get("stages_completed", [])
    if "input" not in current_stages:
        current_stages.append("input")
    current_stages.append("preprocessing")

    persistence.save_state("preprocessing", current_stages)

    print("✓ Chapters saved to checkpoint")
    print("✓ Scenes saved to checkpoint")
    print("✓ Project state updated")

    # Summary
    print("\n" + "=" * 70)
    print("PIPELINE SUMMARY")
    print("=" * 70)

    print(f"""
✅ Stage 1: Input (Gutenberg Fetching)
   - URL Fetcher: {len(raw_content):,} characters fetched
   - Text Parser: Boilerplate removed
   - Metadata Extractor: {metadata.title} by {metadata.author}
   - Project Initializer: {project.id} created

✅ Stage 2: Preprocessing (Text Cleaning & Segmentation)
   - Text Cleaner: {len(super_clean):,} characters cleaned
   - Chapter Segmenter: {len(chapters_data)} chapters found
   - Scene Breakdown: {len(scenes)} scenes in Chapter 1
   - State Persistence: Checkpoints saved

📊 Statistics:
   - Original text: {len(raw_content):,} characters
   - After cleaning: {len(super_clean):,} characters
   - Chapters: {len(chapters_data)}
   - First chapter scenes: {len(scenes)}
   - Project ID: {project.id}

📂 Files Created:
   - {project.id}/config.json
   - {project.id}/state.json
   - {project.id}/intermediate/chapters.json
   - {project.id}/intermediate/scenes.json
    """)

    print("=" * 70)
    print("✅ Pipeline Demo Complete!")
    print("=" * 70)


if __name__ == "__main__":
    try:
        demo_pipeline()
    except Exception as e:
        print(f"\n❌ Demo ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
