"""
Integration Test: Stage 2 - Preprocessing
Tests complete Preprocessing stage from text cleaning to scene breakdown.
"""

import sys
import json
from pathlib import Path
sys.path.insert(0, '/home/clawd/projects/g-manga/src')
sys.path.insert(0, '/home/clawd/projects/g-manga/src/stage1_input')
sys.path.insert(0, '/home/clawd/projects/g-manga/src/stage2_preprocessing')

from url_fetcher import URLFetcher
from text_parser import TextParser
from metadata_extractor import MetadataExtractor
from project import ProjectInitializer
from models.project import Project, Metadata, Chapter, TextRange

# Stage 2 imports
from text_cleaner import TextCleaner
from chapter_segmenter import ChapterSegmenter
from scene_breakdown import SceneBreakdown, MockLLMClient
from state import StatePersistence


def test_preprocessing_stage():
    """Test complete Preprocessing stage pipeline."""
    print("=" * 60)
    print("Stage 2 Integration Test: Preprocessing")
    print("=" * 60)

    # Use the test project from Stage 1
    initializer = ProjectInitializer(base_dir="/home/clawd/projects/g-manga/projects")
    project = initializer.load_project("test-dorian-gray-20260202")

    if not project:
        # Create project for testing
        test_url = "https://www.gutenberg.org/files/174/174-0.txt"

        fetcher = URLFetcher()
        raw = fetcher.fetch(test_url)

        parser = TextParser()
        cleaned, _ = parser.parse(raw)

        extractor = MetadataExtractor()
        metadata_data = extractor.extract(cleaned, source_url=test_url)
        metadata = Metadata(**metadata_data.model_dump() if hasattr(metadata_data, 'model_dump') else metadata_data.__dict__)

        project = initializer.create_project("Test Dorian Gray", metadata)

        # Save cleaned text to project
        with open(f"/home/clawd/projects/g-manga/projects/{project.id}/cache/text.txt", 'w', encoding='utf-8') as f:
            f.write(cleaned)

        print(f"\n✓ Project: {project.id}")
        print(f"✓ Text length: {len(cleaned):,} characters")
    else:
        print(f"\n✓ Loaded existing project: {project.id}")

    # Step 1: Text Cleaner
    print("\n[1/4] Testing Text Cleaner...")
    cleaner = TextCleaner()

    # Get text from project (either file or recreate)
    text_file = f"/home/clawd/projects/g-manga/projects/{project.id}/cache/text.txt"
    if Path(text_file).exists():
        with open(text_file, 'r', encoding='utf-8') as f:
            text = f.read()
    else:
        # Fetch again for testing
        test_url = "https://www.gutenberg.org/files/174/174-0.txt"
        fetcher = URLFetcher()
        raw = fetcher.fetch(test_url)
        parser = TextParser()
        text, _ = parser.parse(raw)

    super_clean = cleaner.clean(text)

    assert len(super_clean) > 400000, "Text too short after cleaning"
    print(f"✓ Cleaned text: {len(super_clean):,} characters")
    print(f"  Difference: {len(text) - len(super_clean):,} characters")

    # Step 2: Chapter Segmenter
    print("\n[2/4] Testing Chapter Segmenter...")
    segmenter = ChapterSegmenter()
    chapters_data = segmenter.segment(super_clean)

    assert len(chapters_data) > 10, "Too few chapters found"
    assert len(chapters_data) < 50, "Too many chapters found (over-segmented)"

    # Convert to Chapter objects
    for chapter_data in chapters_data:
        chapter = Chapter(
            id=f"chapter-{chapter_data.chapter_number}",
            number=chapter_data.chapter_number,
            title=chapter_data.title,
            text_range=TextRange(start=chapter_data.start_line, end=chapter_data.end_line)
        )
        project.add_chapter(chapter)

    print(f"✓ Found {len(project.chapters)} chapters")
    print(f"  First chapter: '{project.chapters[0].title or '(Untitled)'}'")

    # Save chapters to persistence
    persistence = StatePersistence(f"/home/clawd/projects/g-manga/projects/{project.id}")
    persistence.save_chapters(project.chapters)

    # Verify checkpoint
    assert persistence.has_checkpoint("chapters"), "Chapters checkpoint not created"
    print("✓ Chapters saved to checkpoint")

    # Step 3: Scene Breakdown (first chapter only, with mock LLM)
    print("\n[3/4] Testing Scene Breakdown (with mock LLM)...")
    breakdown = SceneBreakdown(llm_client=MockLLMClient())

    # Break down first chapter
    first_chapter_data = chapters_data[0] if chapters_data else None
    if first_chapter_data:
        chapter_id = f"chapter-{first_chapter_data.chapter_number}"

        # Get text for this chapter
        lines = super_clean.split("\n")
        chapter_text = "\n".join(lines[first_chapter_data.start_line:first_chapter_data.end_line])

        scenes = breakdown.breakdown_chapter(chapter_text, chapter_id, first_chapter_data.chapter_number)

        assert len(scenes) > 0, "No scenes found"
        assert len(scenes[0].location) > 0, "Scene location missing"

        # Add to project
        for scene in scenes:
            project.add_scene(scene)

        print(f"✓ Found {len(scenes)} scenes in Chapter 1")
        for i, scene in enumerate(scenes[:3]):
            print(f"  Scene {i+1}: {scene.summary}")
            print(f"    Location: {scene.location}")

    # Save scenes to persistence
    if project.scenes:  # Check if scenes is a dict or list
        scenes_to_save = list(project.scenes.values()) if hasattr(project.scenes, 'values') else project.scenes
    else:
        scenes_to_save = []

    persistence.save_scenes(scenes_to_save)

    # Verify checkpoint
    assert persistence.has_checkpoint("scenes"), "Scenes checkpoint not created"
    print("✓ Scenes saved to checkpoint")

    # Step 4: State Persistence
    print("\n[4/4] Testing State Persistence...")
    updated_state = persistence.load_state()

    assert "current_stage" in updated_state, "State not saved"
    assert "stages_completed" in updated_state, "Stages completed not saved"

    # Update state
    current_stages = updated_state.get("stages_completed", [])
    if "input" not in current_stages:
        current_stages.append("input")

    persistence.save_state("preprocessing", current_stages)

    updated_state = persistence.load_state()
    assert updated_state["current_stage"] == "preprocessing", "State not updated correctly"

    print("✓ State saved and loaded correctly")

    # Expected Outputs Documentation
    print("\n" + "=" * 60)
    print("Expected Outputs (Stage 2)")
    print("=" * 60)
    print("""
Stage 2 produces the following outputs:

1. Cleaned Text
   - Unicode normalized (NFC)
   - Extra whitespace removed
   - Broken paragraphs fixed
   - Chapter markers preserved
   - Approx. 429KB for Dorian Gray

2. Chapter Segmentation
   - 20 chapters for Dorian Gray
   - Each chapter with:
     * Chapter number
     * Title (if available)
     * Text range (start/end lines)
     * Chapter content
   - Saved to: intermediate/chapters.json

3. Scene Breakdown
   - Scenes within chapters (5-50 scenes per chapter)
   - Each scene with:
     * Scene ID
     * Chapter ID
     * Summary (1-2 sentences)
     * Location
     * Characters present
     * Text range
   - LLM-generated (batch 2-3 chapters per call)
   - Saved to: intermediate/scenes.json

4. Project State
   - current_stage: "preprocessing"
   - stages_completed: ["input", "preprocessing"]
   - updated_at: Timestamp
   - checksum: Project data hash
   - Saved to: state.json

5. Intermediate Files
   - intermediate/chapters.json: Chapter data
   - intermediate/scenes.json: Scene data
   - Used for resume capability
    """)

    print("\n" + "=" * 60)
    print("✅ Stage 2 Integration Test: PASSED")
    print("=" * 60)

    return True


if __name__ == "__main__":
    try:
        test_preprocessing_stage()
    except AssertionError as e:
        print(f"\n❌ Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
