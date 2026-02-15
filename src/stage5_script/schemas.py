"""Module 5: Script Generation - Data Schemas"""

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
from enum import Enum


class PanelSize(Enum):
    """Panel size classifications."""
    FULL_WIDTH = "full_width"
    HALF_WIDTH = "half_width"
    THREE_QUARTER = "three_quarter"
    QUARTER = "quarter"
    SPLASH = "splash"


class CameraAngle(Enum):
    """Camera angles for manga panels."""
    WIDE = "wide"
    MEDIUM = "medium"
    MEDIUM_CLOSE = "medium_close"
    CLOSE_UP = "close_up"
    EXTREME_CLOSE_UP = "extreme_close_up"
    LOW_ANGLE = "low_angle"
    HIGH_ANGLE = "high_angle"
    BIRD_EYE = "bird_eye"
    WORM_EYE = "worm_eye"
    OVER_SHOULDER = "over_shoulder"
    POINT_OF_VIEW = "point_of_view"


class PanelTransition(Enum):
    """Transition to next panel/page."""
    CUT = "cut"
    FADE = "fade"
    DISSOLVE = "dissolve"
    PAGE_TURN = "page_turn"


@dataclass
class DialogueLine:
    """Single line of dialogue."""
    speaker: str
    text: str
    tone: str = "neutral"
    bubble_type: str = "speech"  # speech, thought, whisper, shout
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Caption:
    """Narrative caption."""
    text: str
    position: str = "bottom"  # top, bottom, overlay
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SoundEffect:
    """Sound effect description."""
    text: str
    position: Dict[str, int]  # x, y, width, height
    style: str = "comic"  # comic, manga, minimal
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PanelSpec:
    """Individual panel specification."""
    panel_number: int
    page_number: int
    size: str = "three_quarter"
    visual_description: str = ""
    dialogue: List[Dict] = field(default_factory=list)
    captions: List[Dict] = field(default_factory=list)
    sfx: List[Dict] = field(default_factory=list)
    camera: str = "medium"
    camera_description: Optional[str] = None
    characters: List[str] = field(default_factory=list)
    location: Optional[str] = None
    time_period: Optional[str] = None
    composition_notes: Optional[str] = None
    lighting_notes: str = "Natural lighting"
    mood_notes: str = ""
    page_turn: bool = False
    transition: Optional[str] = None
    action_beat: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'panel_number': self.panel_number,
            'page_number': self.page_number,
            'size': self.size,
            'visual': self.visual_description,
            'camera': self.camera,
            'dialogue': self.dialogue,
            'captions': self.captions,
            'sfx': self.sfx,
            'characters': self.characters,
            'location': self.location,
            'time_period': self.time_period,
            'composition_notes': self.composition_notes,
            'lighting_notes': self.lighting_notes,
            'mood_notes': self.mood_notes,
            'page_turn': self.page_turn,
            'transition': self.transition,
            'action_beat': self.action_beat
        }


@dataclass
class PageScript:
    """Single page of the manga."""
    page_number: int
    chapter_number: int
    panels: List[PanelSpec] = field(default_factory=list)
    layout_template: str = "6_panel_grid"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'page_number': self.page_number,
            'chapter_number': self.chapter_number,
            'layout_template': self.layout_template,
            'panels': [p.to_dict() for p in self.panels]
        }


@dataclass
class Script:
    """Complete manga script."""
    title: str = ""
    author: str = ""
    pages: List[PageScript] = field(default_factory=list)
    total_pages: int = 0
    total_panels: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'title': self.title,
            'author': self.author,
            'total_pages': self.total_pages,
            'total_panels': self.total_panels,
            'pages': [p.to_dict() for p in self.pages]
        }
    
    def save(self, path: str):
        """Save script to JSON file."""
        import json
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
