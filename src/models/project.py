"""
Project Schema - Stage 1.1.4
Pydantic models for G-Manga project data structures.
"""

from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class Metadata(BaseModel):
    """Metadata for a Project Gutenberg text."""
    title: str = Field(..., min_length=1, max_length=500)
    author: str = Field(..., min_length=1, max_length=200)
    year: Optional[int] = Field(None, ge=1400, le=2030)
    language: str = Field(default="en", min_length=2, max_length=10)
    gutenberg_id: Optional[int] = Field(None, gt=0)
    source_url: Optional[str] = Field(None, max_length=1000)

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        """Validate language code."""
        v = v.lower().strip()
        if len(v) < 2:
            raise ValueError("Language code must be at least 2 characters")
        return v


class TextRange(BaseModel):
    """A range of text (for chapters, scenes, etc.)."""
    start: int = Field(..., ge=0, description="Starting line number (0-indexed)")
    end: int = Field(..., ge=0, description="Ending line number (0-indexed)")

    @field_validator("end")
    @classmethod
    def validate_range(cls, v: int, info) -> int:
        """Ensure end > start."""
        if "start" in info.data and v <= info.data["start"]:
            raise ValueError("End must be greater than start")
        return v


class Chapter(BaseModel):
    """A chapter from the source text."""
    id: str = Field(..., pattern=r"^[a-z0-9-]+$")
    number: int = Field(..., gt=0)
    title: Optional[str] = Field(None, max_length=500)
    text_range: TextRange
    content: Optional[str] = None  # Full chapter text

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        """Validate ID format."""
        return v.lower().strip()


class Scene(BaseModel):
    """A scene within a chapter."""
    id: str = Field(..., pattern=r"^[a-z0-9-]+$")
    chapter_id: str = Field(..., pattern=r"^[a-z0-9-]+$")
    number: int = Field(..., gt=0)
    summary: str = Field(..., min_length=1, max_length=2000)
    location: str = Field(..., min_length=1, max_length=200)
    characters: List[str] = Field(default_factory=list)
    text_range: TextRange
    text: Optional[str] = None  # Add text field for scene content

    @field_validator("id", "chapter_id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        """Validate ID format."""
        return v.lower().strip()

    @field_validator("characters")
    @classmethod
    def validate_characters(cls, v: List[str]) -> List[str]:
        """Validate character list."""
        return [c.strip() for c in v if c.strip()]


class VisualBeat(BaseModel):
    """A visual beat in the story planning stage."""
    id: str = Field(..., pattern=r"^[a-z0-9-]+$")
    scene_id: str = Field(..., pattern=r"^[a-z0-9-]+$")
    description: str = Field(..., min_length=1, max_length=1000)
    show_vs_tell: str = Field(..., pattern=r"^(show|tell|both)$")
    priority: int = Field(default=1, ge=1, le=5)


class Panel(BaseModel):
    """A panel in the storyboard."""
    id: str = Field(..., pattern=r"^[a-z0-9-]+$")
    page_number: int = Field(..., gt=0)
    panel_number: int = Field(..., gt=0)
    type: str = Field(..., pattern=r"^(establishing|wide|medium|close-up|extreme-close-up|action|dialogue|splash)$")
    description: str = Field(..., min_length=1, max_length=2000)
    camera: str = Field(default="eye-level", max_length=200)
    mood: str = Field(default="neutral", max_length=200)
    dialogue: List[Dict[str, str]] = Field(default_factory=list)  # [{"speaker": "X", "text": "..."}]
    narration: str = Field(default="", max_length=1000)

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        """Validate ID format."""
        return v.lower().strip()


class PanelDescription(BaseModel):
    """Detailed description for a single panel in storyboard generation."""
    id: str = Field(..., pattern=r"^[a-z0-9-]+$")
    page_number: int = Field(..., gt=0)
    panel_number: int = Field(..., gt=0)
    type: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=2000)
    camera: str = Field(default="eye-level", max_length=200)
    mood: str = Field(default="neutral", max_length=200)
    lighting: str = Field(default="natural", max_length=200)
    composition: str = Field(default="centered", max_length=200)
    dialogue: List[Dict[str, str]] = Field(default_factory=list)
    narration: str = Field(default="", max_length=1000)
    characters: List[str] = Field(default_factory=list)
    props: List[str] = Field(default_factory=list)

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        """Validate ID format."""
        return v.lower().strip()


class Page(BaseModel):
    """A page in the comic."""
    page_number: int = Field(..., gt=0)
    panels: List[Panel] = Field(default_factory=list)
    layout: str = Field(default="4-panel", max_length=100)


class Storyboard(BaseModel):
    """Complete storyboard for a project."""
    pages: List[Page] = Field(default_factory=list)
    total_panels: int = Field(default=0)

    @field_validator("total_panels")
    @classmethod
    def calculate_total(cls, v: int, info) -> int:
        """Calculate total panels from pages."""
        if "pages" in info.data:
            return sum(len(page.panels) for page in info.data["pages"])
        return v


class Character(BaseModel):
    """A character in the story."""
    id: str = Field(..., pattern=r"^[a-z0-9-]+$")
    name: str = Field(..., min_length=1, max_length=200)
    aliases: List[str] = Field(default_factory=list)
    appearance: Dict[str, Any] = Field(default_factory=dict)
    reference_prompt: Optional[str] = Field(None, max_length=2000)
    frequency: int = Field(default=0, ge=0)

    @field_validator("id", "name")
    @classmethod
    def validate_id_name(cls, v: str) -> str:
        """Validate ID and name."""
        return v.strip()


class Project(BaseModel):
    """A G-Manga project."""
    id: str = Field(..., pattern=r"^[a-z0-9-]+$")
    name: str = Field(..., min_length=1, max_length=200)
    metadata: Metadata
    chapters: List[Chapter] = Field(default_factory=list)
    scenes: List[Scene] = Field(default_factory=list)
    storyboard: Optional[Storyboard] = None
    characters: Dict[str, Character] = Field(default_factory=dict)
    raw_text: Optional[str] = None
    cleaned_text: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("id", "name")
    @classmethod
    def validate_id_name(cls, v: str) -> str:
        """Validate ID and name."""
        return v.strip()

    def add_chapter(self, chapter: Chapter) -> None:
        """Add a chapter to the project."""
        self.chapters.append(chapter)
        self.updated_at = datetime.now(timezone.utc)

    def add_scene(self, scene: Scene) -> None:
        """Add a scene to the project."""
        self.scenes.append(scene)
        self.updated_at = datetime.now(timezone.utc)

    def add_character(self, character: Character) -> None:
        """Add a character to the project."""
        self.characters[character.id] = character
        self.updated_at = datetime.now(timezone.utc)


def generate_project_id(name: str) -> str:
    """Generate a unique project ID from name."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    # Convert name to slug format
    slug = name.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return f"{slug}-{timestamp}"


# Import re at module level for generate_project_id
import re
