"""Stage 3: Adaptation Planning - Data Schemas"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum


class ArcRole(Enum):
    """Role of an act in the narrative structure."""
    SETUP = "setup"
    RISING_ACTION = "rising_action"
    CLIMAX = "climax"
    FALLING_ACTION = "falling_action"
    RESOLUTION = "resolution"


class ChapterRole(Enum):
    """Role of a chapter in the narrative."""
    SETUP = "setup"
    INCITING_INCIDENT = "inciting_incident"
    DEVELOPMENT = "development"
    TURNING_POINT = "turning_point"
    CLIMAX = "climax"
    RESOLUTION = "resolution"
    BRIDGE = "bridge"


class PageType(Enum):
    """Type of page in the manga."""
    SPLASH = "splash"           # Full-page impact shot
    STANDARD = "standard"       # Normal panel page
    SPREAD = "spread"           # Double-page spread
    TRANSITION = "transition"   # Chapter transition
    TITLE = "title"             # Chapter title page


@dataclass
class NarrativeArc:
    """Represents a narrative act/arc."""
    act_number: int
    chapters: List[int]  # Chapter numbers in this act
    theme: str
    arc_role: ArcRole
    key_events: List[str] = field(default_factory=list)
    emotional_tone: str = ""
    
    @property
    def chapter_count(self) -> int:
        return len(self.chapters)


@dataclass
class EmotionalPeak:
    """Represents an emotional peak in the story."""
    chapter: int
    description: str
    intensity: float  # 1.0 to 10.0
    peak_type: str  # "climax", "tragedy", "revelation", "tension"
    key_moment: str = ""


@dataclass
class CharacterArc:
    """Represents a character's arc across the story."""
    character_name: str
    role: str  # "protagonist", "antagonist", "supporting"
    arc_beats: List[Dict] = field(default_factory=list)  # {"chapter": int, "description": str, "change": str}
    transformation_summary: str = ""
    starting_state: str = ""
    ending_state: str = ""


@dataclass
class PacingStructure:
    """Represents the overall pacing structure."""
    setup_chapters: List[int]
    rising_action_chapters: List[int]
    climax_chapters: List[int]
    falling_action_chapters: List[int]
    resolution_chapters: List[int]
    
    # Pacing ratios (should sum to ~1.0)
    setup_ratio: float = 0.15
    rising_ratio: float = 0.40
    climax_ratio: float = 0.20
    falling_ratio: float = 0.15
    resolution_ratio: float = 0.10


@dataclass
class NovelLevelAnalysis:
    """Complete novel-level analysis for adaptation planning."""
    title: str
    author: str
    total_chapters: int
    
    # Narrative structure
    narrative_arcs: List[NarrativeArc] = field(default_factory=list)
    pacing_structure: Optional[PacingStructure] = None
    
    # Thematic analysis
    major_themes: List[str] = field(default_factory=list)
    mood_tone: str = ""
    
    # Character arcs
    character_arcs: List[CharacterArc] = field(default_factory=list)
    
    # Emotional peaks (ordered by occurrence)
    emotional_peaks: List[EmotionalPeak] = field(default_factory=list)
    
    # Overall arc assessment
    protagonist: str = ""
    central_conflict: str = ""
    thematic_statements: List[str] = field(default_factory=list)
    
    # Story rhythm
    story_rhythm: str = ""  # "fast", "slow", "varied", "deliberate"
    key_symbols: List[str] = field(default_factory=list)
    
    @property
    def act_count(self) -> int:
        return len(self.narrative_arcs)
    
    @property
    def peak_count(self) -> int:
        return len(self.emotional_peaks)


@dataclass
class ChapterLevelAnalysis:
    """Analysis of a single chapter's role in the adaptation."""
    chapter_number: int
    chapter_title: str
    word_count: int
    
    # Arc role
    arc_role: ChapterRole
    act_number: int
    
    # How this chapter serves the overall story
    narrative_function: str
    emotional_trajectory: str
    
    # Scene information
    key_scenes: List[str] = field(default_factory=list)
    location_changes: List[str] = field(default_factory=list)
    character_focus: List[str] = field(default_factory=list)
    
    # Adaptation considerations
    is_splash_page_candidate: bool = False
    splash_page_reason: str = ""
    is_visual_heavy: bool = False
    dialogue_density: str = "medium"  # "low", "medium", "high"
    action_density: str = "medium"  # "low", "medium", "high"
    
    # Connection to larger arc
    setup_for: List[int] = field(default_factory=list)  # Chapter numbers this sets up
    payoff_from: List[int] = field(default_factory=list)  # Chapter numbers this pays off


@dataclass
class SplashPage:
    """Represents a splash page decision."""
    chapter: int
    page_number: int  # Approximate page in chapter
    splash_id: str
    description: str
    reason: str  # Why this is a splash page
    scene_type: str  # "action", "revelation", "emotional", "atmospheric"
    visual_elements: List[str] = field(default_factory=list)
    
    @property
    def is_novel_opening(self) -> bool:
        return self.chapter == 1 and self.page_number == 1


@dataclass
class PageAllocation:
    """Page allocation for a chapter."""
    chapter_number: int
    total_pages: int
    splash_pages: int = 0
    standard_pages: int = 0
    spreads: int = 0
    transitions: int = 0
    
    # Detailed breakdown
    panels_per_page: int = 6  # Average panels per page
    estimated_dialogue_pages: int = 0
    estimated_action_pages: int = 0
    estimated_transition_pages: int = 0
    
    # Reasoning
    allocation_reasoning: str = ""
    based_on_novel_context: bool = False


@dataclass
class AdaptationPlan:
    """Complete adaptation plan combining novel and chapter-level analysis."""
    # Novel context (computed once)
    novel_level_analysis: NovelLevelAnalysis
    
    # Chapter allocations
    page_allocation: List[PageAllocation]
    
    # Splash page decisions
    splash_pages: List[SplashPage]
    
    # Summary statistics
    total_target_pages: int
    pages_per_chapter_avg: float
    
    # Metadata
    created_with: str = "AdaptationPlanner"
    target_format: str = "manga"
    
    # Validation
    is_valid: bool = True
    validation_notes: List[str] = field(default_factory=list)
    
    @property
    def chapter_count(self) -> int:
        return len(self.page_allocation)
    
    @property
    def splash_page_count(self) -> int:
        return len(self.splash_pages)
