"""Stage 3 Adapter - Bridges old story planning with new adaptation planner.

This module provides adapters to convert between:
- Old format: Scenes → Visual Adaptation → Panel Breakdown → Storyboard
- New format: AnalysisResult → AdaptationPlanner → AdaptationPlan

Usage:
    from stage3_planning.adapter import Stage3Adapter
    
    adapter = Stage3Adapter(llm_client=client)
    plan = adapter.run_adaptation_planning(analysis_result, target_pages=100)
"""

from typing import List, Dict, Any, Optional
from dataclasses import asdict

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from stage3_planning.schemas import AdaptationPlan, NovelLevelAnalysis, PageAllocation, SplashPage
from stage3_planning.adaptation_planner import AdaptationPlanner


class Stage3Adapter:
    """
    Adapter that runs new Adaptation Planning alongside old story planning.
    
    Produces:
    - adaptation_plan: New format (page allocation, splash pages, narrative arcs)
    - storyboard: Old format (for backward compatibility with Stage 5)
    """
    
    def __init__(self, llm_client=None, model: str = "openai/gpt-4o-mini"):
        self.llm_client = llm_client
        self.model = model
        
        # New processor
        self.planner = AdaptationPlanner(llm_client=llm_client, model=model)
    
    def run_adaptation_planning(
        self,
        analysis_result,
        target_pages: int = 100,
        title: str = "",
        author: str = ""
    ) -> Dict[str, Any]:
        """
        Run complete Stage 3 adaptation planning.
        
        Args:
            analysis_result: From Stage 2 (AnalysisEngine)
            target_pages: Target total pages for manga adaptation
            title: Book title
            author: Book author
            
        Returns:
            Dict with:
            - adaptation_plan: AdaptationPlan (new format)
            - novel_analysis: NovelLevelAnalysis
            - page_allocations: List[PageAllocation]
            - splash_pages: List[SplashPage]
        """
        result = {
            "adaptation_plan": None,
            "novel_analysis": None,
            "page_allocations": [],
            "splash_pages": [],
            "summary": {}
        }
        
        # Run AdaptationPlanner
        if self.llm_client:
            adaptation_plan = self.planner.plan(
                analysis_result=analysis_result,
                target_pages=target_pages,
                title=title,
                author=author
            )
            
            result["adaptation_plan"] = adaptation_plan
            result["novel_analysis"] = adaptation_plan.novel_level_analysis
            result["page_allocations"] = adaptation_plan.page_allocation
            result["splash_pages"] = adaptation_plan.splash_pages
            
            # Create summary
            result["summary"] = {
                "target_pages": target_pages,
                "total_chapters": adaptation_plan.novel_level_analysis.total_chapters,
                "narrative_arcs": len(adaptation_plan.novel_level_analysis.narrative_arcs),
                "emotional_peaks": len(adaptation_plan.novel_level_analysis.emotional_peaks),
                "character_arcs": len(adaptation_plan.novel_level_analysis.character_arcs),
                "splash_pages": len(adaptation_plan.splash_pages),
                "pages_per_chapter_avg": adaptation_plan.pages_per_chapter_avg,
                "major_themes": adaptation_plan.novel_level_analysis.major_themes,
                "mood_tone": adaptation_plan.novel_level_analysis.mood_tone,
                "story_rhythm": adaptation_plan.novel_level_analysis.story_rhythm,
                "protagonist": adaptation_plan.novel_level_analysis.protagonist,
                "central_conflict": adaptation_plan.novel_level_analysis.central_conflict
            }
        
        return result
    
    def adaptation_plan_to_stage4_format(self, adaptation_plan: AdaptationPlan) -> Dict[str, Any]:
        """
        Convert AdaptationPlan to format usable by Stage 4.
        
        This creates a unified data structure that Stage 4 can use.
        """
        novel = adaptation_plan.novel_level_analysis
        
        return {
            "novel_analysis": {
                "title": novel.title,
                "author": novel.author,
                "total_chapters": novel.total_chapters,
                "narrative_arcs": [self._arc_to_dict(arc) for arc in novel.narrative_arcs],
                "pacing_structure": self._pacing_to_dict(novel.pacing_structure) if novel.pacing_structure else None,
                "major_themes": novel.major_themes,
                "mood_tone": novel.mood_tone,
                "character_arcs": [self._char_arc_to_dict(arc) for arc in novel.character_arcs],
                "emotional_peaks": [self._peak_to_dict(peak) for peak in novel.emotional_peaks],
                "protagonist": novel.protagonist,
                "central_conflict": novel.central_conflict,
                "story_rhythm": novel.story_rhythm,
                "key_symbols": novel.key_symbols
            },
            "page_allocations": [self._page_alloc_to_dict(alloc) for alloc in adaptation_plan.page_allocation],
            "splash_pages": [self._splash_to_dict(splash) for splash in adaptation_plan.splash_pages],
            "summary": {
                "total_target_pages": adaptation_plan.total_target_pages,
                "pages_per_chapter_avg": adaptation_plan.pages_per_chapter_avg,
                "splash_page_count": adaptation_plan.splash_page_count
            }
        }
    
    def _arc_to_dict(self, arc) -> Dict[str, Any]:
        return {
            "act_number": arc.act_number,
            "chapters": arc.chapters,
            "theme": arc.theme,
            "arc_role": arc.arc_role.value if hasattr(arc.arc_role, 'value') else str(arc.arc_role),
            "key_events": arc.key_events,
            "emotional_tone": arc.emotional_tone
        }
    
    def _pacing_to_dict(self, pacing) -> Dict[str, Any]:
        return {
            "setup_chapters": pacing.setup_chapters,
            "rising_action_chapters": pacing.rising_action_chapters,
            "climax_chapters": pacing.climax_chapters,
            "falling_action_chapters": pacing.falling_action_chapters,
            "resolution_chapters": pacing.resolution_chapters,
            "setup_ratio": pacing.setup_ratio,
            "rising_ratio": pacing.rising_ratio,
            "climax_ratio": pacing.climax_ratio,
            "falling_ratio": pacing.falling_ratio,
            "resolution_ratio": pacing.resolution_ratio
        }
    
    def _char_arc_to_dict(self, arc) -> Dict[str, Any]:
        return {
            "character_name": arc.character_name,
            "role": arc.role,
            "arc_beats": arc.arc_beats,
            "transformation_summary": arc.transformation_summary,
            "starting_state": arc.starting_state,
            "ending_state": arc.ending_state
        }
    
    def _peak_to_dict(self, peak) -> Dict[str, Any]:
        return {
            "chapter": peak.chapter,
            "description": peak.description,
            "intensity": peak.intensity,
            "peak_type": peak.peak_type,
            "key_moment": peak.key_moment
        }
    
    def _page_alloc_to_dict(self, alloc) -> Dict[str, Any]:
        return {
            "chapter_number": alloc.chapter_number,
            "total_pages": alloc.total_pages,
            "splash_pages": alloc.splash_pages,
            "standard_pages": alloc.standard_pages,
            "panels_per_page": alloc.panels_per_page,
            "allocation_reasoning": alloc.allocation_reasoning
        }
    
    def _splash_to_dict(self, splash) -> Dict[str, Any]:
        return {
            "chapter": splash.chapter,
            "page_number": splash.page_number,
            "splash_id": splash.splash_id,
            "description": splash.description,
            "reason": splash.reason,
            "scene_type": splash.scene_type,
            "visual_elements": splash.visual_elements
        }
    
    def save_adaptation_plan(self, adaptation_plan: AdaptationPlan, output_path: str):
        """Save adaptation plan to JSON file."""
        import json
        from pathlib import Path
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        plan_dict = self.adaptation_plan_to_stage4_format(adaptation_plan)
        
        with open(output_file, 'w') as f:
            json.dump(plan_dict, f, indent=2)
    
    def load_adaptation_plan(self, input_path: str) -> Dict[str, Any]:
        """Load adaptation plan from JSON file."""
        import json
        
        with open(input_path, 'r') as f:
            return json.load(f)
