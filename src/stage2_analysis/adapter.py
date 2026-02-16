"""Stage 2 Adapter - Bridges old preprocessing with new analysis engine.

This module provides adapters to convert between:
- Old format: ChapterSegmenter → SceneBreakdown → Scenes
- New format: ChapterSegmenter → AnalysisEngine → AnalysisResult

Usage:
    from stage2_analysis.adapter import Stage2Adapter
    
    adapter = Stage2Adapter(llm_client=client)
    result = adapter.run_full_analysis(chapters, cleaned_text)
"""

from typing import List, Dict, Any, Optional
from dataclasses import asdict

# Import from same package
from .schemas import AnalysisResult, Character, Location, PlotBeat, Dialogue, KeyQuote
from .analysis_engine import AnalysisEngine

# Import from old preprocessing - use absolute imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from stage2_preprocessing.chapter_segmenter import ChapterSegmenter
from stage2_preprocessing.scene_breakdown import SceneBreakdown


class Stage2Adapter:
    """
    Adapter that runs both old and new Stage 2 processing.
    
    Produces:
    - scenes: Old format (for backward compatibility with Stage 3)
    - analysis: New format (characters, locations, plot_beats, dialogue)
    """
    
    def __init__(self, llm_client=None, model: str = "openai/gpt-4o-mini"):
        self.llm_client = llm_client
        self.model = model
        
        # Old processors
        self.chapter_segmenter = ChapterSegmenter()
        self.scene_breakdown = SceneBreakdown(llm_client=llm_client)
        
        # New processor
        self.analysis_engine = AnalysisEngine(llm_client=llm_client, model=model)
    
    def run_full_analysis(
        self,
        cleaned_text: str,
        chapters_data: List[Any] = None,
        run_analysis: bool = True,
        run_scene_breakdown: bool = True
    ) -> Dict[str, Any]:
        """
        Run complete Stage 2 analysis.
        
        Args:
            cleaned_text: Pre-cleaned text
            chapters_data: Pre-segmented chapters (optional)
            run_analysis: Run new AnalysisEngine (characters, locations, etc.)
            run_scene_breakdown: Run old SceneBreakdown for scenes
            
        Returns:
            Dict with:
            - chapters: Chapter data
            - scenes: Scene data (old format)
            - analysis: AnalysisResult (new format)
            - character_count: Number of characters found
            - location_count: Number of locations found
        """
        result = {
            "chapters": [],
            "scenes": [],
            "analysis": None,
            "character_count": 0,
            "location_count": 0,
            "plot_beat_count": 0,
            "dialogue_count": 0
        }
        
        # 1. Segment chapters (if not provided)
        if chapters_data is None:
            chapters_data = self.chapter_segmenter.segment(cleaned_text)
        
        result["chapters"] = chapters_data
        
        # 2. Run Scene Breakdown (old format)
        if run_scene_breakdown:
            scenes = self._run_scene_breakdown(cleaned_text, chapters_data)
            result["scenes"] = scenes
        
        # 3. Run Analysis Engine (new format)
        if run_analysis and self.llm_client:
            analysis = self.analysis_engine.analyze(chapters_data)
            result["analysis"] = analysis
            result["character_count"] = len(analysis.characters)
            result["location_count"] = len(analysis.locations)
            result["plot_beat_count"] = len(analysis.plot_beats)
            result["dialogue_count"] = len(analysis.dialogue)
        elif run_analysis:
            # No LLM - create empty analysis
            result["analysis"] = AnalysisResult()
        
        return result
    
    def _run_scene_breakdown(self, cleaned_text: str, chapters_data: List[Any]) -> List[Any]:
        """Run old scene breakdown."""
        all_scenes = []
        
        for chapter_data in chapters_data:
            lines = cleaned_text.split("\n")
            chapter_text = "\n".join(lines[chapter_data.start_line:chapter_data.end_line])
            
            scenes = self.scene_breakdown.breakdown_chapter(
                chapter_text,
                f"chapter-{chapter_data.chapter_number}",
                chapter_data.chapter_number
            )
            all_scenes.extend(scenes)
        
        return all_scenes
    
    def analysis_to_stage3_format(self, analysis: AnalysisResult) -> Dict[str, Any]:
        """
        Convert AnalysisResult to format usable by Stage 3.
        
        This creates a unified data structure that Stage 3 can use.
        """
        return {
            "characters": [self._character_to_dict(c) for c in analysis.characters],
            "locations": [self._location_to_dict(l) for l in analysis.locations],
            "plot_beats": [self._plotbeat_to_dict(b) for b in analysis.plot_beats],
            "dialogue": [self._dialogue_to_dict(d) for d in analysis.dialogue],
            "key_quotes": [self._quote_to_dict(q) for q in analysis.key_quotes],
            "summary": {
                "total_characters": len(analysis.characters),
                "total_locations": len(analysis.locations),
                "total_plot_beats": len(analysis.plot_beats),
                "total_dialogue": len(analysis.dialogue),
                "total_quotes": len(analysis.key_quotes)
            }
        }
    
    def _character_to_dict(self, char: Character) -> Dict[str, Any]:
        return {
            "name": char.name,
            "aliases": char.aliases,
            "first_appearance": char.first_appearance,
            "role": char.role,
            "physical_descriptions": char.physical_descriptions,
            "relationships": char.relationships,
            "chapter_first_appeared": char.chapter_first_appeared
        }
    
    def _location_to_dict(self, loc: Location) -> Dict[str, Any]:
        return {
            "name": loc.name,
            "location_type": loc.location_type,
            "privacy": loc.privacy,
            "descriptions": loc.descriptions,
            "chapters_appeared": loc.chapters_appeared
        }
    
    def _plotbeat_to_dict(self, beat: PlotBeat) -> Dict[str, Any]:
        return {
            "beat_number": beat.beat_number,
            "chapter": beat.chapter,
            "description": beat.description,
            "is_major": beat.is_major,
            "beat_type": beat.beat_type
        }
    
    def _dialogue_to_dict(self, dial: Dialogue) -> Dict[str, Any]:
        return {
            "speaker": dial.speaker,
            "quote": dial.quote,
            "context": dial.context,
            "tone": dial.tone,
            "chapter": dial.chapter
        }
    
    def _quote_to_dict(self, quote: KeyQuote) -> Dict[str, Any]:
        return {
            "quote": quote.quote,
            "context": quote.context,
            "speaker": quote.speaker,
            "significance": quote.significance,
            "chapter": quote.chapter
        }
    
    def save_analysis(self, analysis: AnalysisResult, output_path: str):
        """Save analysis result to JSON file."""
        import json
        from pathlib import Path
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(analysis.to_dict(), f, indent=2)
    
    def load_analysis(self, input_path: str) -> AnalysisResult:
        """Load analysis result from JSON file."""
        import json
        
        with open(input_path, 'r') as f:
            data = json.load(f)
        
        return AnalysisResult(
            characters=[Character(**c) for c in data.get('characters', [])],
            locations=[Location(**l) for l in data.get('locations', [])],
            plot_beats=[PlotBeat(**b) for b in data.get('plot_beats', [])],
            dialogue=[Dialogue(**d) for d in data.get('dialogue', [])],
            key_quotes=[KeyQuote(**q) for q in data.get('key_quotes', [])]
        )
