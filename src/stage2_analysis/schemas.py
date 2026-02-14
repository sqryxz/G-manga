"""Module 2: Analysis Engine - Data Schemas"""

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
from enum import Enum


class ContentType(Enum):
    """Type of content."""
    CHAPTER = "chapter"
    PREFACE = "preface"
    APPENDIX = "appendix"
    UNKNOWN = "unknown"


@dataclass
class Character:
    """Extracted character data."""
    name: str
    aliases: List[str] = field(default_factory=list)
    first_appearance: str = ""
    role: str = "minor"  # protagonist, antagonist, supporting, minor
    physical_descriptions: List[str] = field(default_factory=list)
    relationships: Dict[str, str] = field(default_factory=dict)
    chapter_first_appeared: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Location:
    """Extracted location data."""
    name: str
    location_type: str = "interior"  # interior, exterior
    privacy: str = "private"  # public, private
    descriptions: List[str] = field(default_factory=list)
    chapters_appeared: List[int] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PlotBeat:
    """Extracted plot beat."""
    beat_number: int
    chapter: int
    description: str
    is_major: bool = False
    beat_type: str = "action"  # action, revelation, decision, emotional
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Dialogue:
    """Extracted dialogue."""
    speaker: str
    quote: str
    context: str
    tone: str = "neutral"  # neutral, angry, happy, sad, etc.
    chapter: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class KeyQuote:
    """Key quote from the text."""
    quote: str
    context: str
    speaker: str = ""
    significance: str = ""
    chapter: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AnalysisResult:
    """Complete analysis result."""
    characters: List[Character] = field(default_factory=list)
    locations: List[Location] = field(default_factory=list)
    plot_beats: List[PlotBeat] = field(default_factory=list)
    dialogue: List[Dialogue] = field(default_factory=list)
    key_quotes: List[KeyQuote] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'characters': [c.to_dict() for c in self.characters],
            'locations': [l.to_dict() for l in self.locations],
            'plot_beats': [b.to_dict() for b in self.plot_beats],
            'dialogue': [d.to_dict() for d in self.dialogue],
            'key_quotes': [q.to_dict() for q in self.key_quotes]
        }
