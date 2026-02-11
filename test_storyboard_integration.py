"""
Test Storyboard Integration
"""

import sys
import tempfile
import json
from pathlib import Path

sys.path.insert(0, '/home/clawd/projects/g-manga/src/stage3_story_planning')
sys.path.insert(0, '/home/clawd/projects/g-manga/src')

from stage3_story_planning.storyboard_storage import (
    StoryboardStorage, Storyboard, StoryboardPanel
)


def test_storyboard_storage():
    """Test storyboard storage functionality."""
    print("=" * 60)
    print("Testing Storyboard Storage")
    print("=" * 60)

    # Create temporary project directory
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        print(f"\nProject directory: {project_dir}")

        # Initialize storage
        storage = StoryboardStorage(str(project_dir))

        # Create a storyboard
        panels = [
            StoryboardPanel(
                panel_id="p1",
                page_number=1,
                panel_number=1,
                description="Wide shot of art studio with natural light",
                camera="wide",
                mood="peaceful",
                lighting="natural sunlight",
                composition="centered",
                thumbnail_prompt="Quick sketch, studio, wide shot"
            ),
            StoryboardPanel(
                panel_id="p2",
                page_number=1,
                panel_number=2,
                description="Basil at his easel with brush in hand",
                camera="medium",
                mood="contemplative",
                lighting="warm golden hour",
                composition="character-focused",
                thumbnail_prompt="Character sketch, artist at work"
            ),
            StoryboardPanel(
                panel_id="p3",
                page_number=1,
                panel_number=3,
                description="Lord Henry enters, examining the painting",
                camera="eye-level",
                mood="curious",
                lighting="natural",
                composition="two-shot",
                thumbnail_prompt="Two characters, conversation"
            )
        ]

        storyboard = Storyboard(
            storyboard_id="sb-001",
            project_id="test-project",
            scene_id="scene-1",
            chapter_number=1,
            panels=panels
        )

        print(f"\nCreated storyboard: {storyboard.storyboard_id}")
        print(f"  Panels: {len(storyboard.panels)}")

        # Save storyboard
        filepath = storage.save_storyboard(storyboard)
        filepath = Path(filepath)
        print(f"  Saved to: {filepath}")

        # Verify file exists
        assert filepath.exists(), "Storyboard file should exist"
        print("  ✓ File saved successfully")

        # Load storyboard
        loaded = storage.load_storyboard("sb-001")
        assert loaded is not None, "Should load storyboard"
        assert len(loaded.panels) == 3, "Should have 3 panels"
        print("  ✓ Storyboard loaded successfully")

        # List storyboards
        storyboards = storage.list_storyboards()
        assert len(storyboards) == 1, "Should have 1 storyboard"
        print(f"  ✓ Listed {len(storyboards)} storyboard(s)")

        # Test update panel
        updated = storage.update_panel("sb-001", "p2", {
            "description": "Updated description for panel 2",
            "mood": "serious"
        })
        assert updated.panels[1].description == "Updated description for panel 2"
        assert updated.panels[1].mood == "serious"
        print("  ✓ Panel updated successfully")

        # Test reorder panels
        reordered = storage.reorder_panels("sb-001", ["p3", "p1", "p2"])
        assert reordered.panels[0].panel_id == "p3"
        assert reordered.panels[1].panel_id == "p1"
        assert reordered.panels[2].panel_id == "p2"
        print("  ✓ Panels reordered successfully")

        # Test add panel
        new_panel = StoryboardPanel(
            panel_id="p4",
            page_number=1,
            panel_number=4,
            description="New panel added",
            camera="close-up",
            mood="neutral"
        )
        added = storage.add_panel("sb-001", new_panel, insert_after="p2")
        assert len(added.panels) == 4, "Should have 4 panels now"
        print("  ✓ Panel added successfully")

        # Test remove panel
        removed = storage.remove_panel("sb-001", "p4")
        assert len(removed.panels) == 3, "Should have 3 panels after removal"
        print("  ✓ Panel removed successfully")

        # Test delete storyboard
        deleted = storage.delete_storyboard("sb-001")
        assert deleted, "Should delete successfully"
        assert storage.load_storyboard("sb-001") is None, "Should not exist after deletion"
        print("  ✓ Storyboard deleted successfully")

    print("\n" + "=" * 60)
    print("✅ All Storyboard Storage Tests Passed!")
    print("=" * 60)


def test_storyboard_format():
    """Test storyboard JSON format."""
    print("\n" + "=" * 60)
    print("Testing Storyboard JSON Format")
    print("=" * 60)

    # Create example storyboard
    panels = [
        StoryboardPanel(
            panel_id="p1",
            page_number=1,
            panel_number=1,
            description="Wide shot of art studio",
            camera="wide",
            mood="peaceful",
            lighting="natural sunlight",
            composition="centered",
            thumbnail_prompt="Quick sketch, studio, wide shot"
        )
    ]

    storyboard = Storyboard(
        storyboard_id="sb-001",
        project_id="dorian-gray-ch1",
        scene_id="scene-1",
        chapter_number=1,
        panels=panels
    )

    # Convert to dict (as would be saved)
    data = {
        "storyboard_id": storyboard.storyboard_id,
        "project_id": storyboard.project_id,
        "scene_id": storyboard.scene_id,
        "chapter_number": storyboard.chapter_number,
        "panels": [
            {
                "panel_id": panel.panel_id,
                "page_number": panel.page_number,
                "panel_number": panel.panel_number,
                "description": panel.description,
                "camera": panel.camera,
                "mood": panel.mood,
                "lighting": panel.lighting,
                "composition": panel.composition,
                "thumbnail_prompt": panel.thumbnail_prompt,
                "status": panel.status
            }
            for panel in storyboard.panels
        ],
        "created_at": storyboard.created_at,
        "updated_at": storyboard.updated_at,
        "status": storyboard.status
    }

    # Pretty print
    json_str = json.dumps(data, indent=2, ensure_ascii=False)
    print("\nExample Storyboard JSON:")
    print(json_str)

    print("\n" + "=" * 60)
    print("✅ Storyboard Format Test Complete!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_storyboard_storage()
        test_storyboard_format()

        print("\n" + "=" * 60)
        print("🎉 All Tests Passed Successfully!")
        print("=" * 60)

        print("\n📋 Summary of New CLI Commands:")
        print("-" * 60)
        print("g-manga storyboard <project-id>")
        print("    Generate storyboard for a project")
        print()
        print("g-manga storyboard list <project-id>")
        print("    List all storyboards in a project")
        print()
        print("g-manga storyboard view <project-id> <storyboard-id>")
        print("    View a storyboard with all panels")
        print()
        print("g-manga storyboard edit <project-id> <storyboard-id> <panel-id>")
        print("    Edit a panel in a storyboard")
        print()
        print("g-manga storyboard reorder <project-id> <storyboard-id> <panel-ids>")
        print("    Reorder panels in a storyboard")
        print()
        print("g-manga storyboard add <project-id> <storyboard-id>")
        print("    Add a new panel to a storyboard")
        print()
        print("g-manga storyboard remove <project-id> <storyboard-id> <panel-id>")
        print("    Remove a panel from a storyboard")
        print()
        print("g-manga storyboard approve <project-id> <storyboard-id>")
        print("    Approve a storyboard or specific panel")
        print()
        print("g-manga storyboard reject <project-id> <storyboard-id>")
        print("    Reject a storyboard or specific panel")
        print()
        print("g-manga storyboard export <project-id> <storyboard-id>")
        print("    Export a storyboard to file")
        print()
        print("g-manga storyboard interactive <project-id> <storyboard-id>")
        print("    Interactive storyboard review session")
        print("-" * 60)

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
