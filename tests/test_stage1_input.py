"""
Integration Test: Stage 1 - Input
Tests the complete Input stage from URL fetch to project initialization.
"""

import sys
sys.path.insert(0, '/home/clawd/projects/g-manga/src')
sys.path.insert(0, '/home/clawd/projects/g-manga/src/stage1_input')

from url_fetcher import URLFetcher
from text_parser import TextParser
from metadata_extractor import MetadataExtractor
from project import ProjectInitializer
from models.project import Metadata


def test_input_stage():
    """Test complete Input stage pipeline."""
    print("=" * 60)
    print("Stage 1 Integration Test: Input (Gutenberg Fetching)")
    print("=" * 60)

    # Step 1: URL Fetcher
    print("\n[1/4] Testing URL Fetcher...")
    test_url = "https://www.gutenberg.org/files/174/174-0.txt"

    fetcher = URLFetcher(cache_dir="/home/clawd/projects/g-manga/tests/cache")
    raw_content = fetcher.fetch(test_url)

    assert len(raw_content) > 400000, "Content too short"
    assert "Oscar Wilde" in raw_content or "Dorian Gray" in raw_content, "Wrong content"
    print(f"✓ Fetched {len(raw_content):,} characters")

    # Step 2: Text Parser
    print("\n[2/4] Testing Text Parser...")
    parser = TextParser()
    cleaned_text, content_type = parser.parse(raw_content)

    assert len(cleaned_text) > 400000, "Cleaned text too short"
    assert content_type == "txt", f"Expected txt, got {content_type}"
    assert "*** START OF" not in cleaned_text, "Boilerplate not removed"
    assert "*** END OF" not in cleaned_text, "Boilerplate not removed"

    removed = len(raw_content) - len(cleaned_text)
    print(f"✓ Removed {removed:,} characters of boilerplate")
    print(f"✓ Content type: {content_type}")

    # Step 3: Metadata Extractor
    print("\n[3/4] Testing Metadata Extractor...")
    extractor = MetadataExtractor()
    metadata_data = extractor.extract(cleaned_text, source_url=test_url)

    assert metadata_data.title, "Title not extracted"
    assert metadata_data.author, "Author not extracted"
    assert metadata_data.gutenberg_id == 174, "Wrong Gutenberg ID"
    assert metadata_data.language == "en", "Wrong language"

    print(f"✓ Title: {metadata_data.title}")
    print(f"✓ Author: {metadata_data.author}")
    print(f"✓ Year: {metadata_data.year}")
    print(f"✓ Language: {metadata_data.language}")
    print(f"✓ Gutenberg ID: {metadata_data.gutenberg_id}")

    # Step 4: Project Initializer
    print("\n[4/4] Testing Project Initializer...")
    metadata = Metadata(**metadata_data.model_dump() if hasattr(metadata_data, 'model_dump') else metadata_data.__dict__)

    initializer = ProjectInitializer(base_dir="/home/clawd/projects/g-manga/projects")
    project = initializer.create_project("Test Dorian Gray", metadata)

    assert project.id, "Project ID not generated"
    assert project.metadata.title == metadata_data.title, "Title mismatch"
    assert len(project.chapters) == 0, "Chapters should be empty"

    print(f"✓ Project ID: {project.id}")
    print(f"✓ Project name: {project.name}")

    # Verify project files
    print("\n" + "=" * 60)
    print("Verifying Project Files...")
    print("=" * 60)

    from pathlib import Path
    project_dir = Path("/home/clawd/projects/g-manga/projects") / project.id

    config_path = project_dir / "config.json"
    state_path = project_dir / "state.json"

    assert config_path.exists(), "config.json not created"
    assert state_path.exists(), "state.json not created"

    for subdir in ["cache", "intermediate", "output", "output/panels", "output/pages", "output/thumbnails", "src"]:
        path = project_dir / subdir
        assert path.exists(), f"{subdir} not created"

    print("✓ config.json created")
    print("✓ state.json created")
    print("✓ All subdirectories created")

    # Expected Outputs Documentation
    print("\n" + "=" * 60)
    print("Expected Outputs (Stage 1)")
    print("=" * 60)
    print("""
Stage 1 produces the following outputs:

1. Raw Content
   - Fetched from Project Gutenberg URL
   - Stored in cache (by URL hash)
   - Approx. 430KB for Dorian Gray

2. Cleaned Text
   - Gutenberg boilerplate removed
   - Chapter markers preserved
   - Text formatting normalized
   - Approx. 429KB for Dorian Gray

3. Metadata
   - Title: "Picture of Dorian Gray"
   - Author: "Oscar Wilde"
   - Year: 1820-1890 (detected from content)
   - Language: "en"
   - Gutenberg ID: 174

4. Project Structure
   - config.json: Project configuration
   - state.json: Current stage and checksum
   - cache/: Downloaded content cache
   - intermediate/: Stage outputs
   - output/: Final generated content
   - output/panels/: Individual panel images
   - output/pages/: Composed page images
   - output/thumbnails/: Preview thumbnails
   - src/: Source files for the project

5. State Information
   - current_stage: "input"
   - stages_completed: []
   - checksum: MD5 hash of project data
    """)

    print("\n" + "=" * 60)
    print("✅ Stage 1 Integration Test: PASSED")
    print("=" * 60)

    return True


if __name__ == "__main__":
    try:
        test_input_stage()
    except AssertionError as e:
        print(f"\n❌ Test FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
