"""
Tests for Project Schema
"""

import sys
sys.path.insert(0, '/home/clawd/projects/g-manga/src')

from models.project import (
    Metadata, TextRange, Chapter, Scene, VisualBeat,
    Panel, Page, Storyboard, Character, Project, generate_project_id
)
from pydantic import ValidationError


def test_metadata_creation():
    """Test creating valid Metadata."""
    metadata = Metadata(
        title="Test Book",
        author="Test Author",
        year=2020,
        language="en",
        gutenberg_id=12345
    )
    assert metadata.title == "Test Book"
    assert metadata.author == "Test Author"
    assert metadata.year == 2020
    assert metadata.language == "en"


def test_metadata_validation():
    """Test Metadata validation."""
    # Invalid year
    try:
        Metadata(title="Test", author="Test", year=2050)
        assert False, "Should have raised validation error"
    except ValidationError:
        pass

    # Invalid language
    try:
        Metadata(title="Test", author="Test", language="x")
        assert False, "Should have raised validation error"
    except ValidationError:
        pass


def test_text_range():
    """Test TextRange creation."""
    range_obj = TextRange(start=0, end=100)
    assert range_obj.start == 0
    assert range_obj.end == 100

    # Invalid range
    try:
        TextRange(start=100, end=50)
        assert False, "Should have raised validation error"
    except ValidationError:
        pass


def test_chapter():
    """Test Chapter creation."""
    chapter = Chapter(
        id="chapter-1",
        number=1,
        title="First Chapter",
        text_range=TextRange(start=0, end=100)
    )
    assert chapter.id == "chapter-1"
    assert chapter.number == 1
    assert chapter.title == "First Chapter"


def test_scene():
    """Test Scene creation."""
    scene = Scene(
        id="scene-1-1",
        chapter_id="chapter-1",
        number=1,
        summary="Introduction scene",
        location="Kitchen",
        characters=["John", "Mary"],
        text_range=TextRange(start=0, end=50)
    )
    assert scene.id == "scene-1-1"
    assert len(scene.characters) == 2
    assert scene.location == "Kitchen"


def test_panel():
    """Test Panel creation."""
    panel = Panel(
        id="p1-1",
        page_number=1,
        panel_number=1,
        type="medium",
        description="A person standing",
        camera="eye-level",
        mood="calm",
        dialogue=[{"speaker": "John", "text": "Hello"}]
    )
    assert panel.id == "p1-1"
    assert panel.type == "medium"
    assert len(panel.dialogue) == 1


def test_character():
    """Test Character creation."""
    character = Character(
        id="char-john",
        name="John Doe",
        aliases=["Johnny", "J"],
        appearance={"age": 30, "hair": "brown"},
        frequency=5
    )
    assert character.id == "char-john"
    assert len(character.aliases) == 2
    assert character.frequency == 5


def test_project():
    """Test Project creation."""
    metadata = Metadata(title="Test", author="Author")
    project = Project(
        id="test-project-20240202",
        name="Test Project",
        metadata=metadata
    )
    assert project.id == "test-project-20240202"
    assert len(project.chapters) == 0
    assert len(project.scenes) == 0

    # Test adding chapter
    chapter = Chapter(
        id="chapter-1",
        number=1,
        title="First Chapter",
        text_range=TextRange(start=0, end=100)
    )
    project.add_chapter(chapter)
    assert len(project.chapters) == 1

    # Test adding scene
    scene = Scene(
        id="scene-1-1",
        chapter_id="chapter-1",
        number=1,
        summary="Test scene",
        location="Test",
        characters=[],
        text_range=TextRange(start=0, end=50)
    )
    project.add_scene(scene)
    assert len(project.scenes) == 1


def test_generate_project_id():
    """Test project ID generation."""
    id1 = generate_project_id("My Awesome Project")
    id2 = generate_project_id("My Awesome Project")
    assert id1.startswith("my-awesome-project-")
    assert id2.startswith("my-awesome-project-")
    # Timestamps should be same within second, so IDs should be similar


def test_json_serialization():
    """Test JSON serialization/deserialization."""
    metadata = Metadata(title="Test", author="Author", year=2020)
    json_str = metadata.model_dump_json()
    assert "title" in json_str

    # Deserialize
    metadata2 = Metadata.model_validate_json(json_str)
    assert metadata2.title == "Test"
    assert metadata2.year == 2020


if __name__ == "__main__":
    # Run all tests
    print("Running project model tests...")

    test_metadata_creation()
    print("✓ test_metadata_creation")

    test_metadata_validation()
    print("✓ test_metadata_validation")

    test_text_range()
    print("✓ test_text_range")

    test_chapter()
    print("✓ test_chapter")

    test_scene()
    print("✓ test_scene")

    test_panel()
    print("✓ test_panel")

    test_character()
    print("✓ test_character")

    test_project()
    print("✓ test_project")

    test_generate_project_id()
    print("✓ test_generate_project_id")

    test_json_serialization()
    print("✓ test_json_serialization")

    print("\n✅ All tests passed!")
