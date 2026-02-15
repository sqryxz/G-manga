"""Stage 3: Compression Decider Module

Determines how to handle scenes: expand, compress, or omit.
Uses novel-level context to make better decisions.
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from .schemas import (
    ChapterLevelAnalysis, NovelLevelAnalysis, PageAllocation,
    ChapterRole, ArcRole, EmotionalPeak, CharacterArc
)


class CompressionDecision(Enum):
    """Decision on how to handle content."""
    EXPAND = "expand"      # Give more space than proportional
    KEEP = "keep"          # Keep proportional representation
    COMPRESS = "compress"  # Reduce but keep essential
    OMIT = "omit"          # Remove entirely (only for truly optional)


@dataclass
class SceneDecision:
    """Decision for a specific scene or content block."""
    scene_id: str
    original_description: str
    decision: CompressionDecision
    reasoning: str
    page_impact: float  # Multiplier for page allocation
    visual_potential: str  # "high", "medium", "low"
    key_elements_to_preserve: List[str] = None
    notes: str = ""
    
    def __post_init__(self):
        if self.key_elements_to_preserve is None:
            self.key_elements_to_preserve = []


@dataclass
class SceneGroupDecision:
    """Decisions for a group of scenes."""
    group_id: str
    scenes: List[SceneDecision]
    overall_decision: CompressionDecision
    group_reasoning: str
    total_page_multiplier: float = 1.0


class CompressionDecider:
    """Decides how to handle scenes based on novel context."""
    
    def __init__(
        self,
        expansion_ratio: float = 1.0,
        compression_ratio: float = 0.7,
        omit_threshold: float = 0.3
    ):
        """
        Initialize the compression decider.
        
        Args:
            expansion_ratio: Multiplier for expanded content
            compression_ratio: Multiplier for compressed content
            omit_threshold: Importance below which content is omitted
        """
        self.expansion_ratio = expansion_ratio
        self.compression_ratio = compression_ratio
        self.omit_threshold = omit_threshold
        
        # Thresholds for decisions
        self.expansion_threshold = 0.8  # High importance = expand
        self.keep_threshold = 0.4       # Medium importance = keep
        self.compression_threshold = 0.25  # Low importance = compress
    
    def decide_chapter_scenes(
        self,
        chapter: ChapterLevelAnalysis,
        scenes: List[Dict],
        novel_context: NovelLevelAnalysis
    ) -> List[SceneDecision]:
        """
        Make compression decisions for scenes in a chapter.
        
        Args:
            chapter: Chapter-level analysis
            scenes: List of scene dictionaries with 'id', 'description', 'importance'
            novel_context: Novel-level analysis
        
        Returns:
            List of SceneDecision objects
        """
        decisions = []
        
        # Get chapter context
        arc_role = self._get_arc_role(chapter, novel_context)
        is_peak = self._is_emotional_peak(chapter, novel_context)
        character_focus = set(chapter.character_focus)
        
        for scene in scenes:
            decision = self._decide_single_scene(
                scene, chapter, arc_role, is_peak, character_focus, novel_context
            )
            decisions.append(decision)
        
        return decisions
    
    def _decide_single_scene(
        self,
        scene: Dict,
        chapter: ChapterLevelAnalysis,
        arc_role: Optional[ArcRole],
        is_peak: bool,
        character_focus: set,
        novel_context: NovelLevelAnalysis
    ) -> SceneDecision:
        """Make decision for a single scene."""
        scene_id = scene.get('id', 'unknown')
        description = scene.get('description', '')
        base_importance = scene.get('importance', 0.5)
        has_dialogue = scene.get('has_dialogue', False)
        has_action = scene.get('has_action', False)
        is_memorable = scene.get('is_memorable', False)
        thematic_relevance = scene.get('thematic_relevance', 0.5)
        
        # Calculate adjusted importance
        importance = self._calculate_importance(
            base_importance,
            chapter.arc_role,
            arc_role,
            is_peak,
            has_dialogue,
            has_action,
            is_memorable,
            thematic_relevance,
            character_focus,
            scene,
            novel_context
        )
        
        # Make decision based on importance and context
        decision, reasoning, page_impact = self._make_decision(
            importance,
            chapter.arc_role,
            arc_role,
            is_peak,
            scene
        )
        
        # Assess visual potential
        visual_potential = self._assess_visual_potential(
            scene, chapter, is_peak, arc_role
        )
        
        return SceneDecision(
            scene_id=scene_id,
            original_description=description,
            decision=decision,
            reasoning=reasoning,
            page_impact=page_impact,
            visual_potential=visual_potential,
            key_elements_to_preserve=scene.get('key_elements', []),
            notes=self._generate_notes(scene, decision, importance)
        )
    
    def _calculate_importance(
        self,
        base_importance: float,
        chapter_role: ChapterRole,
        arc_role: Optional[ArcRole],
        is_peak: bool,
        has_dialogue: bool,
        has_action: bool,
        is_memorable: bool,
        thematic_relevance: float,
        character_focus: set,
        scene: Dict,
        novel_context: NovelLevelAnalysis
    ) -> float:
        """Calculate adjusted importance score."""
        importance = base_importance
        
        # Chapter role adjustments
        if chapter_role == ChapterRole.CLIMAX:
            importance *= 1.5
        elif chapter_role == ChapterRole.TURNING_POINT:
            importance *= 1.3
        elif chapter_role == ChapterRole.INCITING_INCIDENT:
            importance *= 1.2
        elif chapter_role == ChapterRole.SETUP:
            importance *= 0.8
        
        # Arc role adjustments
        if arc_role == ArcRole.CLIMAX:
            importance *= 1.4
        elif arc_role == ArcRole.RISING_ACTION:
            importance *= 1.1
        elif arc_role == ArcRole.SETUP:
            importance *= 0.9
        
        # Emotional peak bonus
        if is_peak:
            importance *= 1.3
        
        # Content type adjustments
        if is_memorable:
            importance *= 1.2
        if has_action:
            importance *= 1.1
        if has_dialogue:
            importance *= 1.05
        
        # Thematic relevance
        importance *= (0.8 + 0.4 * thematic_relevance)
        
        # Character focus
        scene_characters = set(scene.get('characters', []))
        if scene_characters & character_focus:
            importance *= 1.15
        
        # Check if scene is in key emotional peaks
        for peak in novel_context.emotional_peaks:
            if scene.get('chapter') == peak.chapter and is_memorable:
                importance *= 1.1
        
        return min(1.0, importance)  # Cap at 1.0
    
    def _make_decision(
        self,
        importance: float,
        chapter_role: ChapterRole,
        arc_role: Optional[ArcRole],
        is_peak: bool,
        scene: Dict
    ) -> Tuple[CompressionDecision, str, float]:
        """Make compression decision based on importance."""
        
        # Very high importance = expand
        if importance >= self.expansion_threshold:
            if is_peak or chapter_role == ChapterRole.CLIMAX:
                decision = CompressionDecision.EXPAND
                reasoning = f"Critical scene (importance: {importance:.2f}) - expand for emotional impact"
                page_impact = self.expansion_ratio * 1.2
            else:
                decision = CompressionDecision.KEEP
                reasoning = f"Important scene (importance: {importance:.2f}) - keep proportionally"
                page_impact = 1.0
        
        # Medium importance = keep
        elif importance >= self.keep_threshold:
            decision = CompressionDecision.KEEP
            reasoning = f"Standard scene (importance: {importance:.2f}) - maintain narrative flow"
            page_impact = 1.0
        
        # Low-medium importance = compress
        elif importance >= self.compression_threshold:
            decision = CompressionDecision.COMPRESS
            reasoning = f"Secondary scene (importance: {importance:.2f}) - compress while preserving key beats"
            page_impact = self.compression_ratio
        
        # Very low importance = omit
        else:
            decision = CompressionDecision.OMIT
            if scene.get('essential', False):
                decision = CompressionDecision.COMPRESS
                reasoning = f"Marked essential (importance: {importance:.2f}) - compress rather than omit"
                page_impact = self.compression_ratio * 0.8
            else:
                reasoning = f"Low importance scene (importance: {importance:.2f}) - omit for pacing"
                page_impact = 0.0
        
        return decision, reasoning, page_impact
    
    def _assess_visual_potential(
        self,
        scene: Dict,
        chapter: ChapterLevelAnalysis,
        is_peak: bool,
        arc_role: Optional[ArcRole]
    ) -> str:
        """Assess visual potential of a scene."""
        visual_score = 0
        
        # Has action
        if scene.get('has_action', False):
            visual_score += 2
        
        # Has vivid descriptions
        if scene.get('has_vivid_description', False):
            visual_score += 2
        
        # Emotional peak
        if is_peak:
            visual_score += 3
        
        # Climax chapter
        if chapter.arc_role == ChapterRole.CLIMAX:
            visual_score += 2
        
        # Arc climax
        if arc_role == ArcRole.CLIMAX:
            visual_score += 2
        
        # Has symbolic content
        if scene.get('has_symbolic_content', False):
            visual_score += 1
        
        # Setting description
        if scene.get('has_setting_description', False):
            visual_score += 1
        
        if visual_score >= 7:
            return "high"
        elif visual_score >= 4:
            return "medium"
        else:
            return "low"
    
    def _get_arc_role(
        self,
        chapter: ChapterLevelAnalysis,
        novel_context: NovelLevelAnalysis
    ) -> Optional[ArcRole]:
        """Get arc role for chapter."""
        for arc in novel_context.narrative_arcs:
            if chapter.chapter_number in arc.chapters:
                return arc.arc_role
        return None
    
    def _is_emotional_peak(
        self,
        chapter: ChapterLevelAnalysis,
        novel_context: NovelLevelAnalysis
    ) -> bool:
        """Check if chapter is an emotional peak."""
        for peak in novel_context.emotional_peaks:
            if peak.chapter == chapter.chapter_number:
                return True
        return False
    
    def _generate_notes(
        self,
        scene: Dict,
        decision: CompressionDecision,
        importance: float
    ) -> str:
        """Generate notes for the decision."""
        notes = []
        
        if decision == CompressionDecision.EXPAND:
            notes.append("Consider splash page or spread for key moment")
        
        if scene.get('has_key_quote', False):
            notes.append("Preserve key quote in dialogue")
        
        if scene.get('character_introduction', False):
            notes.append("Ensure character introduction is clear")
        
        if importance > 0.7:
            notes.append("High priority for visual detail")
        
        return "; ".join(notes) if notes else ""
    
    def prioritize_scenes(
        self,
        decisions: List[SceneDecision]
    ) -> List[SceneDecision]:
        """Prioritize scenes by their allocation impact."""
        # Sort by page_impact descending
        return sorted(decisions, key=lambda d: d.page_impact, reverse=True)
    
    def generate_scene_summary(
        self,
        decisions: List[SceneDecision]
    ) -> Dict:
        """Generate summary of scene decisions."""
        summary = {
            'expand': [],
            'keep': [],
            'compress': [],
            'omit': []
        }
        
        for decision in decisions:
            if decision.decision == CompressionDecision.EXPAND:
                summary['expand'].append(decision.scene_id)
            elif decision.decision == CompressionDecision.KEEP:
                summary['keep'].append(decision.scene_id)
            elif decision.decision == CompressionDecision.COMPRESS:
                summary['compress'].append(decision.scene_id)
            elif decision.decision == CompressionDecision.OMIT:
                summary['omit'].append(decision.scene_id)
        
        summary['total_scenes'] = len(decisions)
        summary['total_page_impact'] = sum(d.page_impact for d in decisions)
        
        return summary
