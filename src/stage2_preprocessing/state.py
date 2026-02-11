"""
State Persistence - Stage 2.1.5
Saves and loads chapter segmentation and scene breakdown state.
"""

import json
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timezone

import sys
sys.path.insert(0, '/home/clawd/projects/g-manga/src')
from models.project import Chapter, Scene, TextRange


class StatePersistence:
    """Manages persistence for preprocessing stage."""

    def __init__(self, project_dir: str):
        """
        Initialize State Persistence.

        Args:
            project_dir: Path to project directory
        """
        self.project_dir = Path(project_dir)
        self.intermediate_dir = self.project_dir / "intermediate"
        self.intermediate_dir.mkdir(parents=True, exist_ok=True)

    def save_chapters(self, chapters: List[Chapter]) -> None:
        """
        Save chapter segmentation to JSON.

        Args:
            chapters: List of Chapter objects
        """
        # Convert to dict using model_dump for Pydantic
        chapters_data = []
        for chapter in chapters:
            chapter_dict = chapter.model_dump()
            # Add extra fields
            chapter_dict['length'] = len(chapter.content) if chapter.content else 0
            chapter_dict['start'] = chapter.text_range.start
            chapter_dict['end'] = chapter.text_range.end
            # Remove nested text_range from dict
            if 'text_range' in chapter_dict:
                del chapter_dict['text_range']
            # Remove content field (too large)
            if 'content' in chapter_dict:
                del chapter_dict['content']
            chapters_data.append(chapter_dict)

        # Save to file
        chapters_path = self.intermediate_dir / "chapters.json"
        with open(chapters_path, 'w', encoding='utf-8') as f:
            json.dump({
                "chapters": chapters_data,
                "total_chapters": len(chapters),
                "saved_at": datetime.now(timezone.utc).isoformat()
            }, f, indent=2, ensure_ascii=False)

        print(f"✓ Saved {len(chapters)} chapters to {chapters_path}")

    def load_chapters(self) -> List[Chapter]:
        """
        Load chapter segmentation from JSON.

        Returns:
            List of Chapter objects
        """
        chapters_path = self.intermediate_dir / "chapters.json"

        if not chapters_path.exists():
            return []

        with open(chapters_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Convert to Chapter objects
        chapters = []
        for chapter_data in data.get("chapters", []):
            chapter = Chapter(
                id=chapter_data["id"],
                number=chapter_data["number"],
                title=chapter_data.get("title"),
                text_range=TextRange(
                    start=chapter_data["start"],
                    end=chapter_data["end"]
                ),
                content=None  # Content loaded separately
            )
            chapters.append(chapter)

        print(f"✓ Loaded {len(chapters)} chapters from checkpoint")
        return chapters

    def save_scenes(self, scenes: List[Scene]) -> None:
        """
        Save scene breakdown to JSON.

        Args:
            scenes: List of Scene objects
        """
        # Convert to dict using model_dump for Pydantic
        scenes_data = []
        for scene in scenes:
            scene_dict = scene.model_dump()
            # Add extra fields
            scene_dict['length'] = len(scene.text) if scene.text else 0
            scene_dict['start'] = scene.text_range.start
            scene_dict['end'] = scene.text_range.end
            # Remove nested text_range from dict
            if 'text_range' in scene_dict:
                del scene_dict['text_range']
            scenes_data.append(scene_dict)

        # Save to file
        scenes_path = self.intermediate_dir / "scenes.json"
        with open(scenes_path, 'w', encoding='utf-8') as f:
            json.dump({
                "scenes": scenes_data,
                "total_scenes": len(scenes),
                "saved_at": datetime.now(timezone.utc).isoformat()
            }, f, indent=2, ensure_ascii=False)

        print(f"✓ Saved {len(scenes)} scenes to {scenes_path}")

    def load_scenes(self) -> List[Scene]:
        """
        Load scene breakdown from JSON.

        Returns:
            List of Scene objects
        """
        scenes_path = self.intermediate_dir / "scenes.json"

        if not scenes_path.exists():
            return []

        with open(scenes_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Convert to Scene objects
        scenes = []
        for scene_data in data.get("scenes", []):
            scene = Scene(
                id=scene_data["id"],
                chapter_id=scene_data["chapter_id"],
                number=scene_data["number"],
                summary=scene_data["summary"],
                location=scene_data["location"],
                characters=scene_data["characters"],
                text_range=TextRange(
                    start=scene_data["start"],
                    end=scene_data["end"]
                ),
                text=None  # Text loaded separately
            )
            scenes.append(scene)

        print(f"✓ Loaded {len(scenes)} scenes from checkpoint")
        return scenes

    def save_state(self, stage: str, stages_completed: List[str]) -> None:
        """
        Save project state.

        Args:
            stage: Current stage name
            stages_completed: List of completed stages
        """
        state_path = self.project_dir / "state.json"

        # Load existing state
        if state_path.exists():
            with open(state_path, 'r', encoding='utf-8') as f:
                state = json.load(f)
        else:
            state = {}

        # Update
        state["current_stage"] = stage
        state["stages_completed"] = stages_completed
        state["updated_at"] = datetime.utcnow().isoformat()

        # Save
        with open(state_path, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)

        print(f"✓ State saved: current_stage={stage}")

    def load_state(self) -> dict:
        """
        Load project state.

        Returns:
            State dictionary or empty dict if not found
        """
        state_path = self.project_dir / "state.json"

        if not state_path.exists():
            return {}

        with open(state_path, 'r', encoding='utf-8') as f:
            state = json.load(f)

        return state

    def has_checkpoint(self, checkpoint_type: str) -> bool:
        """
        Check if a checkpoint exists.

        Args:
            checkpoint_type: "chapters" or "scenes"

        Returns:
            True if checkpoint exists
        """
        if checkpoint_type == "chapters":
            return (self.intermediate_dir / "chapters.json").exists()
        elif checkpoint_type == "scenes":
            return (self.intermediate_dir / "scenes.json").exists()
        return False

    def clear_checkpoint(self, checkpoint_type: str) -> None:
        """
        Clear a checkpoint.

        Args:
            checkpoint_type: "chapters" or "scenes"
        """
        if checkpoint_type == "chapters":
            path = self.intermediate_dir / "chapters.json"
        elif checkpoint_type == "scenes":
            path = self.intermediate_dir / "scenes.json"
        else:
            return

        if path.exists():
            path.unlink()
            print(f"✓ Cleared checkpoint: {checkpoint_type}")

    def save_storyboard(self, storyboard: dict) -> None:
        """
        Save storyboard to JSON.

        Args:
            storyboard: Storyboard dictionary
        """
        storyboard_path = self.intermediate_dir / "storyboard.json"

        # Add metadata
        storyboard_data = {
            **storyboard,
            "saved_at": datetime.now(timezone.utc).isoformat()
        }

        with open(storyboard_path, 'w', encoding='utf-8') as f:
            json.dump(storyboard_data, f, indent=2, ensure_ascii=False)

        print(f"✓ Saved storyboard to {storyboard_path}")

    def load_storyboard(self) -> dict:
        """
        Load storyboard from JSON.

        Returns:
            Storyboard dictionary or empty dict if not found
        """
        storyboard_path = self.intermediate_dir / "storyboard.json"

        if not storyboard_path.exists():
            return {}

        with open(storyboard_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return data


def main():
    """Test State Persistence."""
    import sys
    sys.path.insert(0, '/home/clawd/projects/g-manga/src/stage2_preprocessing')

    # Create a test project directory
    from chapter_segmenter import ChapterSegmenter
    from scene_breakdown import SceneBreakdown, MockLLMClient

    # Use test project
    test_project_dir = "/home/clawd/projects/g-manga/projects/test-stage2-20260202"
    persistence = StatePersistence(test_project_dir)

    # Create test data
    test_chapters = [
        Chapter(
            id="chapter-1",
            number=1,
            title="Test Chapter",
            text_range=TextRange(start=0, end=100)
        )
    ]

    # Save chapters
    persistence.save_chapters(test_chapters)

    # Load chapters
    loaded_chapters = persistence.load_chapters()
    assert len(loaded_chapters) == 1
    assert loaded_chapters[0].id == "chapter-1"
    print("✓ Chapter save/load test passed")

    # Check checkpoint
    assert persistence.has_checkpoint("chapters")
    print("✓ Checkpoint detection test passed")

    print("\nState Persistence module working correctly!")


if __name__ == "__main__":
    main()
