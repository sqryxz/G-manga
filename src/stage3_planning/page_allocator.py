"""Stage 3: Page Allocation Module

Allocates pages to chapters based on novel-level context.
Uses the overall narrative arc to make better page distribution decisions.
"""

from typing import List, Dict, Optional
from dataclasses import dataclass

from .schemas import (
    PageAllocation, ChapterLevelAnalysis, NovelLevelAnalysis,
    ChapterRole, ArcRole, PageType
)


@dataclass
class PageAllocationConfig:
    """Configuration for page allocation."""
    # Base page counts
    base_pages_per_chapter: int = 5
    min_pages_per_chapter: int = 3
    max_pages_per_chapter: int = 15
    
    # Multipliers by chapter role
    role_multipliers: Dict[ChapterRole, float] = None
    
    # Multipliers by arc role
    arc_multipliers: Dict[ArcRole, float] = None
    
    # Emotional peak bonus
    peak_multiplier: float = 1.3
    
    # Splash page impact
    splash_page_deduction: float = 0.5  # Pages saved by splash page
    
    def __post_init__(self):
        if self.role_multipliers is None:
            self.role_multipliers = {
                ChapterRole.SETUP: 0.7,
                ChapterRole.INCITING_INCIDENT: 1.2,
                ChapterRole.DEVELOPMENT: 1.0,
                ChapterRole.TURNING_POINT: 1.3,
                ChapterRole.CLIMAX: 1.5,
                ChapterRole.RESOLUTION: 0.8,
                ChapterRole.BRIDGE: 0.6,
            }
        
        if self.arc_multipliers is None:
            self.arc_multipliers = {
                ArcRole.SETUP: 0.8,
                ArcRole.RISING_ACTION: 1.0,
                ArcRole.CLIMAX: 1.4,
                ArcRole.FALLING_ACTION: 0.9,
                ArcRole.RESOLUTION: 0.7,
            }


class PageAllocator:
    """Allocates pages to chapters based on novel context."""
    
    def __init__(self, config: Optional[PageAllocationConfig] = None):
        self.config = config or PageAllocationConfig()
    
    def allocate_pages(
        self,
        chapter: ChapterLevelAnalysis,
        novel_context: NovelLevelAnalysis,
        target_pages: int
    ) -> PageAllocation:
        """
        Allocate pages for a chapter using novel context.
        
        Args:
            chapter: Chapter-level analysis
            novel_context: Novel-level analysis for context
            target_pages: Total target pages for adaptation
        
        Returns:
            PageAllocation with page counts
        """
        # Calculate base pages using novel context
        base_pages = self._calculate_base_pages(novel_context, target_pages)
        
        # Apply chapter-specific adjustments
        adjusted_pages = self._apply_chapter_adjustments(
            chapter, base_pages, novel_context
        )
        
        # Ensure within bounds
        final_pages = self._constrain_pages(adjusted_pages)
        
        # Calculate page type breakdown
        page_breakdown = self._calculate_page_breakdown(chapter, final_pages)
        
        return PageAllocation(
            chapter_number=chapter.chapter_number,
            total_pages=final_pages,
            splash_pages=page_breakdown['splash_pages'],
            standard_pages=page_breakdown['standard_pages'],
            spreads=page_breakdown['spreads'],
            transitions=page_breakdown['transitions'],
            panels_per_page=self._estimate_panels(chapter),
            estimated_dialogue_pages=page_breakdown['dialogue_pages'],
            estimated_action_pages=page_breakdown['action_pages'],
            estimated_transition_pages=page_breakdown['transition_pages'],
            allocation_reasoning=self._generate_reasoning(chapter, final_pages, base_pages),
            based_on_novel_context=True
        )
    
    def _calculate_base_pages(
        self,
        novel_context: NovelLevelAnalysis,
        target_pages: int
    ) -> float:
        """Calculate base pages using novel structure."""
        total_chapters = novel_context.total_chapters
        
        if total_chapters == 0:
            return self.config.base_pages_per_chapter
        
        # Equal distribution as starting point
        equal_share = target_pages / total_chapters
        
        # Adjust based on pacing structure
        if novel_context.pacing_structure:
            pacing = novel_context.pacing_structure
            
            # Use ratios for base distribution
            total_ratio = (
                pacing.setup_ratio + 
                pacing.rising_ratio + 
                pacing.climax_ratio + 
                pacing.falling_ratio + 
                pacing.resolution_ratio
            )
            
            if total_ratio > 0:
                # Weight by section importance
                weighted_share = (
                    (pacing.setup_ratio * 0.8 + pacing.rising_ratio * 1.0 + 
                     pacing.climax_ratio * 1.4 + pacing.falling_ratio * 0.9 + 
                     pacing.resolution_ratio * 0.7) * target_pages / total_chapters
                )
                return weighted_share
        
        return equal_share
    
    def _apply_chapter_adjustments(
        self,
        chapter: ChapterLevelAnalysis,
        base_pages: float,
        novel_context: NovelLevelAnalysis
    ) -> float:
        """Apply chapter-specific adjustments."""
        adjusted = base_pages
        
        # Apply chapter role multiplier
        role_mult = self.config.role_multipliers.get(chapter.arc_role, 1.0)
        adjusted *= role_mult
        
        # Get arc information for this chapter
        arc_role = self._get_arc_role(chapter, novel_context)
        if arc_role:
            arc_mult = self.config.arc_multipliers.get(arc_role, 1.0)
            adjusted *= arc_mult
        
        # Check if this is an emotional peak chapter
        is_peak = self._is_emotional_peak(chapter, novel_context)
        if is_peak:
            adjusted *= self.config.peak_multiplier
        
        # Check for splash page candidate (reduces page need)
        if chapter.is_splash_page_candidate:
            adjusted -= self.config.splash_page_deduction
        
        # Adjust for density
        if chapter.dialogue_density == "high":
            adjusted *= 1.1  # More dialogue = more pages needed
        elif chapter.dialogue_density == "low":
            adjusted *= 0.9
        
        if chapter.action_density == "high":
            adjusted *= 1.15  # More action = more pages needed
        elif chapter.action_density == "low":
            adjusted *= 0.85
        
        # Adjust for visual heaviness
        if chapter.is_visual_heavy:
            adjusted *= 1.1
        
        return adjusted
    
    def _constrain_pages(self, pages: float) -> int:
        """Constrain pages to min/max bounds."""
        return int(max(
            self.config.min_pages_per_chapter,
            min(self.config.max_pages_per_chapter, pages)
        ))
    
    def _calculate_page_breakdown(
        self,
        chapter: ChapterLevelAnalysis,
        total_pages: int
    ) -> Dict:
        """Calculate page type breakdown."""
        breakdown = {
            'splash_pages': 0,
            'standard_pages': 0,
            'spreads': 0,
            'transitions': 0,
            'dialogue_pages': 0,
            'action_pages': 0,
            'transition_pages': 0
        }
        
        # Splash page for chapter opening if candidate
        if chapter.is_splash_page_candidate:
            breakdown['splash_pages'] = 1
        
        # Spreads for climactic moments
        if chapter.arc_role in [ChapterRole.CLIMAX, ChapterRole.TURNING_POINT]:
            breakdown['spreads'] = 1
        
        # Transitions
        breakdown['transitions'] = 1
        breakdown['transition_pages'] = 1
        
        # Remaining pages are standard
        remaining = total_pages - breakdown['splash_pages'] - breakdown['spreads']
        breakdown['standard_pages'] = max(0, remaining)
        
        # Estimate dialogue vs action pages
        if chapter.dialogue_density == "high":
            breakdown['dialogue_pages'] = int(remaining * 0.7)
            breakdown['action_pages'] = remaining - breakdown['dialogue_pages']
        elif chapter.action_density == "high":
            breakdown['action_pages'] = int(remaining * 0.6)
            breakdown['dialogue_pages'] = remaining - breakdown['action_pages']
        else:
            breakdown['dialogue_pages'] = int(remaining * 0.5)
            breakdown['action_pages'] = remaining - breakdown['dialogue_pages']
        
        return breakdown
    
    def _estimate_panels(self, chapter: ChapterLevelAnalysis) -> int:
        """Estimate average panels per page."""
        if chapter.is_visual_heavy:
            return 5  # Fewer panels, more detail
        return 6  # Standard manga pace
    
    def _get_arc_role(
        self,
        chapter: ChapterLevelAnalysis,
        novel_context: NovelLevelAnalysis
    ) -> Optional[ArcRole]:
        """Get the arc role for a chapter."""
        for arc in novel_context.narrative_arcs:
            if chapter.chapter_number in arc.chapters:
                return arc.arc_role
        return None
    
    def _is_emotional_peak(
        self,
        chapter: ChapterLevelAnalysis,
        novel_context: NovelLevelAnalysis
    ) -> bool:
        """Check if chapter contains an emotional peak."""
        for peak in novel_context.emotional_peaks:
            if peak.chapter == chapter.chapter_number:
                return True
        return False
    
    def _generate_reasoning(
        self,
        chapter: ChapterLevelAnalysis,
        final_pages: int,
        base_pages: float
    ) -> str:
        """Generate reasoning for the page allocation."""
        reasons = []
        
        # Base allocation
        reasons.append(f"Base: {base_pages:.1f} pages (novel context)")
        
        # Chapter role
        role = chapter.arc_role.value
        reasons.append(f"Chapter role: {role}")
        
        # Adjustments
        if chapter.is_splash_page_candidate:
            reasons.append("Splash page candidate (+visual impact)")
        
        if chapter.is_emotional_peak if hasattr(chapter, 'is_emotional_peak') else False:
            reasons.append("Emotional peak (+expansion)")
        
        if chapter.is_visual_heavy:
            reasons.append("Visual-heavy content (+expansion)")
        
        if chapter.dialogue_density == "high":
            reasons.append("High dialogue density (+expansion)")
        
        if chapter.action_density == "high":
            reasons.append("High action density (+expansion)")
        
        return "; ".join(reasons)
    
    def allocate_all_chapters(
        self,
        chapter_analyses: List[ChapterLevelAnalysis],
        novel_context: NovelLevelAnalysis,
        target_pages: int
    ) -> List[PageAllocation]:
        """
        Allocate pages for all chapters.
        
        Args:
            chapter_analyses: List of chapter analyses
            novel_context: Novel-level analysis
            target_pages: Total target pages
        
        Returns:
            List of PageAllocation objects
        """
        allocations = []
        
        for chapter in chapter_analyses:
            allocation = self.allocate_pages(chapter, novel_context, target_pages)
            allocations.append(allocation)
        
        # Normalize to match target_pages exactly
        allocations = self._normalize_allocations(allocations, target_pages)
        
        return allocations
    
    def _normalize_allocations(
        self,
        allocations: List[PageAllocation],
        target_pages: int
    ) -> List[PageAllocation]:
        """Normalize allocations to match target_pages exactly."""
        current_total = sum(a.total_pages for a in allocations)
        
        if current_total == target_pages:
            return allocations
        
        # Calculate adjustment per chapter
        diff = target_pages - current_total
        chapters = len(allocations)
        
        if diff > 0:
            # Need to add pages - distribute to important chapters
            for i, alloc in enumerate(allocations):
                if alloc.total_pages < self.config.max_pages_per_chapter:
                    add = min(2, diff)  # Max 2 pages per chapter
                    alloc.total_pages += add
                    alloc.standard_pages += add
                    diff -= add
                    if diff <= 0:
                        break
        else:
            # Need to remove pages - reduce from less critical chapters
            for i, alloc in enumerate(allocations):
                if alloc.total_pages > self.config.min_pages_per_chapter:
                    remove = min(2, abs(diff))
                    alloc.total_pages -= remove
                    alloc.standard_pages -= remove
                    diff += remove
                    if diff >= 0:
                        break
        
        return allocations
