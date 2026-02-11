"""
Storyboard Storage - Stage 3.1.6
Handles saving, loading, and managing storyboards.
"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class StoryboardPanel:
    """A single panel in a storyboard."""
    panel_id: str
    page_number: int
    panel_number: int
    description: str
    camera: str
    mood: str
    lighting: Optional[str] = None
    composition: Optional[str] = None
    action: Optional[str] = None
    dialogue: Optional[str] = None
    thumbnail_prompt: Optional[str] = None
    thumbnail_path: Optional[str] = None
    status: str = "pending"  # pending, approved, rejected


@dataclass
class Storyboard:
    """Complete storyboard for a project."""
    storyboard_id: str
    project_id: str
    scene_id: Optional[str] = None
    chapter_number: Optional[int] = None
    panels: List[StoryboardPanel] = None
    created_at: str = None
    updated_at: str = None
    status: str = "draft"  # draft, approved, rejected

    def __post_init__(self):
        if self.panels is None:
            self.panels = []
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if not self.updated_at:
            self.updated_at = datetime.now(timezone.utc).isoformat()


class StoryboardStorage:
    """Manages storyboard storage and retrieval."""

    def __init__(self, project_dir: str):
        """
        Initialize storyboard storage.

        Args:
            project_dir: Path to the project directory
        """
        self.project_dir = Path(project_dir)
        self.storyboard_dir = self.project_dir / "storyboard"
        self._ensure_directories()

    def _ensure_directories(self):
        """Create storyboard directory if it doesn't exist."""
        self.storyboard_dir.mkdir(parents=True, exist_ok=True)

    def save_storyboard(self, storyboard: Storyboard) -> str:
        """
        Save a storyboard to disk.

        Args:
            storyboard: Storyboard object to save

        Returns:
            Path to saved file
        """
        # Generate filename
        filename = f"{storyboard.storyboard_id}.json"
        filepath = self.storyboard_dir / filename

        # Convert to dict
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
                    "action": panel.action,
                    "dialogue": panel.dialogue,
                    "thumbnail_prompt": panel.thumbnail_prompt,
                    "thumbnail_path": panel.thumbnail_path,
                    "status": panel.status
                }
                for panel in storyboard.panels
            ],
            "created_at": storyboard.created_at,
            "updated_at": storyboard.updated_at,
            "status": storyboard.status
        }

        # Save to file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return str(filepath)

    def load_storyboard(self, storyboard_id: str) -> Optional[Storyboard]:
        """
        Load a storyboard from disk.

        Args:
            storyboard_id: ID of the storyboard to load

        Returns:
            Storyboard object or None if not found
        """
        filepath = self.storyboard_dir / f"{storyboard_id}.json"

        if not filepath.exists():
            return None

        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Reconstruct storyboard
        panels = [
            StoryboardPanel(
                panel_id=panel["panel_id"],
                page_number=panel["page_number"],
                panel_number=panel["panel_number"],
                description=panel["description"],
                camera=panel["camera"],
                mood=panel["mood"],
                lighting=panel.get("lighting"),
                composition=panel.get("composition"),
                action=panel.get("action"),
                dialogue=panel.get("dialogue"),
                thumbnail_prompt=panel.get("thumbnail_prompt"),
                thumbnail_path=panel.get("thumbnail_path"),
                status=panel.get("status", "pending")
            )
            for panel in data["panels"]
        ]

        return Storyboard(
            storyboard_id=data["storyboard_id"],
            project_id=data["project_id"],
            scene_id=data.get("scene_id"),
            chapter_number=data.get("chapter_number"),
            panels=panels,
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            status=data.get("status", "draft")
        )

    def list_storyboards(self, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all storyboards in the project.

        Args:
            project_id: Optional project ID to filter by

        Returns:
            List of storyboard summaries
        """
        storyboards = []

        if not self.storyboard_dir.exists():
            return []

        for filepath in self.storyboard_dir.glob("*.json"):
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Filter by project if specified
            if project_id and data.get("project_id") != project_id:
                continue

            storyboards.append({
                "storyboard_id": data["storyboard_id"],
                "project_id": data["project_id"],
                "scene_id": data.get("scene_id"),
                "chapter_number": data.get("chapter_number"),
                "panel_count": len(data.get("panels", [])),
                "status": data.get("status", "draft"),
                "created_at": data.get("created_at"),
                "updated_at": data.get("updated_at")
            })

        return sorted(storyboards, key=lambda x: x.get("created_at", ""))

    def delete_storyboard(self, storyboard_id: str) -> bool:
        """
        Delete a storyboard.

        Args:
            storyboard_id: ID of the storyboard to delete

        Returns:
            True if deleted, False if not found
        """
        filepath = self.storyboard_dir / f"{storyboard_id}.json"

        if filepath.exists():
            filepath.unlink()
            return True

        return False

    def update_panel(self, storyboard_id: str, panel_id: str, updates: Dict[str, Any]) -> Optional[Storyboard]:
        """
        Update a specific panel in a storyboard.

        Args:
            storyboard_id: ID of the storyboard
            panel_id: ID of the panel to update
            updates: Dictionary of field updates

        Returns:
            Updated storyboard or None if not found
        """
        storyboard = self.load_storyboard(storyboard_id)

        if not storyboard:
            return None

        # Find and update panel
        for panel in storyboard.panels:
            if panel.panel_id == panel_id:
                for key, value in updates.items():
                    if hasattr(panel, key):
                        setattr(panel, key, value)
                break

        # Update timestamp
        storyboard.updated_at = datetime.now(timezone.utc).isoformat()

        # Save updated storyboard
        self.save_storyboard(storyboard)

        return storyboard

    def reorder_panels(self, storyboard_id: str, panel_ids: List[str]) -> Optional[Storyboard]:
        """
        Reorder panels in a storyboard.

        Args:
            storyboard_id: ID of the storyboard
            panel_ids: List of panel IDs in desired order

        Returns:
            Updated storyboard or None if not found
        """
        storyboard = self.load_storyboard(storyboard_id)

        if not storyboard:
            return None

        # Create panel lookup
        panel_lookup = {panel.panel_id: panel for panel in storyboard.panels}

        # Reorder panels
        new_order = []
        for i, panel_id in enumerate(panel_ids):
            if panel_id in panel_lookup:
                panel = panel_lookup[panel_id]
                panel.panel_number = i + 1
                new_order.append(panel)

        storyboard.panels = new_order
        storyboard.updated_at = datetime.now(timezone.utc).isoformat()

        # Save updated storyboard
        self.save_storyboard(storyboard)

        return storyboard

    def add_panel(self, storyboard_id: str, panel: StoryboardPanel, insert_after: Optional[str] = None) -> Optional[Storyboard]:
        """
        Add a new panel to a storyboard.

        Args:
            storyboard_id: ID of the storyboard
            panel: Panel to add
            insert_after: Optional panel ID to insert after

        Returns:
            Updated storyboard or None if not found
        """
        storyboard = self.load_storyboard(storyboard_id)

        if not storyboard:
            return None

        # Set panel number
        if insert_after:
            insert_idx = None
            for i, p in enumerate(storyboard.panels):
                if p.panel_id == insert_after:
                    insert_idx = i + 1
                    break

            if insert_idx is not None:
                storyboard.panels.insert(insert_idx, panel)
            else:
                storyboard.panels.append(panel)
        else:
            storyboard.panels.append(panel)

        # Renumber panels
        for i, p in enumerate(storyboard.panels):
            p.panel_number = i + 1

        # Update timestamp
        storyboard.updated_at = datetime.now(timezone.utc).isoformat()

        # Save updated storyboard
        self.save_storyboard(storyboard)

        return storyboard

    def remove_panel(self, storyboard_id: str, panel_id: str) -> Optional[Storyboard]:
        """
        Remove a panel from a storyboard.

        Args:
            storyboard_id: ID of the storyboard
            panel_id: ID of the panel to remove

        Returns:
            Updated storyboard or None if not found
        """
        storyboard = self.load_storyboard(storyboard_id)

        if not storyboard:
            return None

        # Remove panel
        storyboard.panels = [p for p in storyboard.panels if p.panel_id != panel_id]

        # Renumber panels
        for i, p in enumerate(storyboard.panels):
            p.panel_number = i + 1

        # Update timestamp
        storyboard.updated_at = datetime.now(timezone.utc).isoformat()

        # Save updated storyboard
        self.save_storyboard(storyboard)

        return storyboard


def create_storyboard(
    project_id: str,
    scene_id: Optional[str] = None,
    chapter_number: Optional[int] = None,
    panels: Optional[List[StoryboardPanel]] = None
) -> Storyboard:
    """
    Create a new storyboard.

    Args:
        project_id: Project ID
        scene_id: Optional scene ID
        chapter_number: Optional chapter number
        panels: Optional list of panels

    Returns:
        New Storyboard object
    """
    storyboard_id = f"sb-{uuid.uuid4().hex[:8]}"

    return Storyboard(
        storyboard_id=storyboard_id,
        project_id=project_id,
        scene_id=scene_id,
        chapter_number=chapter_number,
        panels=panels or []
    )
