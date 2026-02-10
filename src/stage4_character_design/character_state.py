"""
Character State Persistence - Stage 4.1.5
Saves and loads character design state.
"""

import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

import sys
sys.path.insert(0, '/home/clawd/projects/g-manga/src')
from models.project import Character


class CharacterStatePersistence:
    """Manages persistence for character design stage."""

    def __init__(self, project_dir: str):
        """
        Initialize Character State Persistence.

        Args:
            project_dir: Path to project directory
        """
        self.project_dir = Path(project_dir)
        self.intermediate_dir = self.project_dir / "intermediate"
        self.intermediate_dir.mkdir(parents=True, exist_ok=True)

    def save_characters(self, characters: List[Character], project_id: str) -> None:
        """
        Save character data to JSON.

        Args:
            characters: List of Character objects
            project_id: Project ID
        """
        # Convert to dict
        chars_data = []
        for char in characters:
            char_dict = char.model_dump()
            chars_data.append(char_dict)

        # Save to file
        chars_path = self.intermediate_dir / "characters.json"
        with open(chars_path, 'w', encoding='utf-8') as f:
            json.dump({
                "project_id": project_id,
                "total_characters": len(characters),
                "characters": chars_data,
                "saved_at": datetime.now(timezone.utc).isoformat()
            }, f, indent=2, ensure_ascii=False)

        print(f"Saved {len(characters)} characters to {chars_path}")

    def load_characters(self) -> Optional[List[Dict[str, Any]]]:
        """
        Load character data from JSON.

        Returns:
            List of character dictionaries or None
        """
        chars_path = self.intermediate_dir / "characters.json"

        if not chars_path.exists():
            return None

        with open(chars_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        print(f"Loaded {len(data.get('characters', []))} characters from {chars_path}")
        return data.get("characters", [])

    def save_character_embeddings(self, embeddings: Dict[str, Dict[str, Any]], project_id: str) -> None:
        """
        Save character embeddings to JSON.

        Args:
            embeddings: Dict of character_id -> embedding data
            project_id: Project ID
        """
        embeddings_path = self.intermediate_dir / "character_embeddings.json"

        with open(embeddings_path, 'w', encoding='utf-8') as f:
            json.dump({
                "project_id": project_id,
                "embeddings": embeddings,
                "saved_at": datetime.now(timezone.utc).isoformat()
            }, f, indent=2, ensure_ascii=False)

        print(f"Saved character embeddings to {embeddings_path}")

    def load_character_embeddings(self) -> Optional[Dict[str, Any]]:
        """
        Load character embeddings from JSON.

        Returns:
            Embeddings dictionary or None
        """
        embeddings_path = self.intermediate_dir / "character_embeddings.json"

        if not embeddings_path.exists():
            return None

        with open(embeddings_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        print(f"Loaded character embeddings from {embeddings_path}")
        return data.get("embeddings", {})

    def save_ref_sheets(self, ref_sheets: List[Dict[str, Any]], project_id: str) -> None:
        """
        Save reference sheet prompts to JSON.

        Args:
            ref_sheets: List of reference sheet dictionaries
            project_id: Project ID
        """
        ref_sheets_path = self.intermediate_dir / "reference_sheets.json"

        with open(ref_sheets_path, 'w', encoding='utf-8') as f:
            json.dump({
                "project_id": project_id,
                "total_ref_sheets": len(ref_sheets),
                "ref_sheets": ref_sheets,
                "saved_at": datetime.now(timezone.utc).isoformat()
            }, f, indent=2, ensure_ascii=False)

        print(f"Saved {len(ref_sheets)} reference sheets to {ref_sheets_path}")

    def load_ref_sheets(self) -> Optional[List[Dict[str, Any]]]:
        """
        Load reference sheet prompts from JSON.

        Returns:
            List of reference sheet dictionaries or None
        """
        ref_sheets_path = self.intermediate_dir / "reference_sheets.json"

        if not ref_sheets_path.exists():
            return None

        with open(ref_sheets_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        print(f"Loaded {len(data.get('ref_sheets', []))} reference sheets from {ref_sheets_path}")
        return data.get("ref_sheets", [])

    def save_state(self, project_id: str, current_stage: str, stages_completed: List[str]) -> None:
        """
        Update project state with character design stage.

        Args:
            project_id: Project ID
            current_stage: Current stage name
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
        state["current_stage"] = current_stage
        if "character_design" not in stages_completed:
            stages_completed.append("character_design")

        # Update
        state["updated_at"] = datetime.now(timezone.utc).isoformat()

        with open(state_path, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)

        print(f"Updated state to: {current_stage}")


def main():
    """Test Character State Persistence."""
    import sys
    sys.path.insert(0, '/home/clawd/projects/g-manga/src')

    from models.project import Character

    # Test with project directory
    test_project_dir = "/home/clawd/projects/g-manga/projects/test-stage4-20260203"

    persistence = CharacterStatePersistence(test_project_dir)

    # Create test characters
    test_characters = [
        Character(
            id="char-basil",
            name="Basil Hallward",
            aliases=["Basil"],
            appearance={
                "age": "late 20s",
                "gender": "male",
                "height": "average",
                "build": "lean, artistic"
            },
            reference_prompt=None
        ),
        Character(
            id="char-henry",
            name="Lord Henry Wotton",
            aliases=["Lord Henry"],
            appearance={
                "age": "late 20s",
                "gender": "male",
                "height": "tall",
                "build": "lean, aristocratic"
            },
            reference_prompt=None
        )
    ]

    # Test save
    print("Testing save_characters...")
    persistence.save_characters(test_characters, "test-project")
    print()

    # Test load
    print("Testing load_characters...")
    loaded = persistence.load_characters()
    assert loaded is not None, "Failed to load characters"
    assert len(loaded) == 2, f"Expected 2 characters, got {len(loaded)}"
    print(f"Loaded {len(loaded)} characters")
    print()

    # Test embeddings
    print("Testing save_character_embeddings...")
    test_embeddings = {
        "char-basil": {
            "embedding": [0.1] * 384,
            "mentions": [(1, None), (1, None)]
        },
        "char-henry": {
            "embedding": [0.2] * 384,
            "mentions": [(1, None)]
        }
    }
    persistence.save_character_embeddings(test_embeddings, "test-project")
    print()

    # Test ref sheets
    print("Testing save_ref_sheets...")
    test_ref_sheets = [
        {
            "character_id": "char-basil",
            "description": "Reference sheet for Basil",
            "style_tags": ["detailed", "realistic", "emotional"]
        },
        {
            "character_id": "char-henry",
            "description": "Reference sheet for Lord Henry",
            "style_tags": ["stylish", "elegant", "sophisticated"]
        }
    ]
    persistence.save_ref_sheets(test_ref_sheets, "test-project")
    print()

    # Test state update
    print("Testing save_state...")
    persistence.save_state(
        "test-project",
        "character_design",
        ["input", "preprocessing", "story_planning", "character_design"]
    )
    print()

    print("=" * 70)
    print("Character State Persistence Test - PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()
