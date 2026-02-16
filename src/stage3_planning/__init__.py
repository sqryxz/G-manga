"""
Stage 3: Adaptation Planning Module
Analyzes novel structure and creates page allocation plans for manga adaptation.
"""

from .schemas import (
    NovelLevelAnalysis,
    NarrativeArc,
    EmotionalPeak,
    CharacterArc,
    PacingStructure,
    ChapterLevelAnalysis,
    SplashPage,
    PageAllocation,
    AdaptationPlan,
    ArcRole,
    ChapterRole,
    PageType
)

from .adaptation_planner import AdaptationPlanner, NovelLevelAnalyzer, ChapterLevelPlanner
from .adapter import Stage3Adapter

__all__ = [
    'NovelLevelAnalysis',
    'NarrativeArc',
    'EmotionalPeak', 
    'CharacterArc',
    'PacingStructure',
    'ChapterLevelAnalysis',
    'SplashPage',
    'PageAllocation',
    'AdaptationPlan',
    'ArcRole',
    'ChapterRole',
    'PageType',
    'AdaptationPlanner',
    'NovelLevelAnalyzer',
    'ChapterLevelPlanner',
    'Stage3Adapter'
]
