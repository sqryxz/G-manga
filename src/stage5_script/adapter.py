"""Stage 5 Adapter - Bridges old panel generation with new script generation.

This module provides adapters to convert between:
- Old format: Storyboards → PanelBuilder → PanelOptimizer → Panel Prompts
- New format: AnalysisResult + AdaptationPlan → ScriptOrchestrator → Script

Usage:
    from stage5_script.adapter import Stage5Adapter
    
    adapter = Stage5Adapter(llm_client=client)
    script = adapter.run_script_generation(analysis_result, adaptation_plan, target_pages=100)
"""

from typing import List, Dict, Any, Optional
from dataclasses import asdict

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from stage5_script.schemas import Script, PageScript, PanelSpec
from stage5_script.script_orchestrator import ScriptOrchestrator


class Stage5Adapter:
    """
    Adapter that runs new Script Generation alongside old panel generation.
    
    Produces:
    - script: Complete manga script (new format)
    - panels: Panel prompts (old format for compatibility)
    """
    
    def __init__(self, llm_client=None, model: str = "openai/gpt-4o-mini"):
        self.llm_client = llm_client
        self.model = model
        
        # New processor
        self.orchestrator = ScriptOrchestrator(llm_client=llm_client, model=model)
    
    def run_script_generation(
        self,
        analysis_result,
        adaptation_plan,
        target_pages: int = 100,
        title: str = "",
        author: str = ""
    ) -> Dict[str, Any]:
        """
        Run complete Stage 5 script generation.
        
        Args:
            analysis_result: From Stage 2 (AnalysisEngine)
            adaptation_plan: From Stage 3 (AdaptationPlanner)
            target_pages: Target total pages for manga
            title: Book title
            author: Book author
            
        Returns:
            Dict with:
            - script: Script object (new format)
            - panels: List of panel specs
            - summary: Script statistics
        """
        result = {
            "script": None,
            "panels": [],
            "summary": {}
        }
        
        # Run ScriptOrchestrator
        if self.llm_client:
            # Set title/author in generator
            self.orchestrator.generator.title = title or "Unknown"
            self.orchestrator.generator.author = author or "Unknown"
            
            script = self.orchestrator.generate(
                analysis_result=analysis_result,
                adaptation_plan=adaptation_plan,
                target_pages=target_pages
            )
            
            result["script"] = script
            
            # Convert to panel format for compatibility
            panels = self._script_to_panels(script)
            result["panels"] = panels
            
            # Create summary
            result["summary"] = {
                "total_pages": script.total_pages,
                "total_panels": script.total_panels,
                "avg_panels_per_page": script.total_panels / max(1, script.total_pages),
                "title": script.title,
                "author": script.author
            }
        
        return result
    
    def _script_to_panels(self, script: Script) -> List[Dict[str, Any]]:
        """Convert Script to panel format for Stage 6 compatibility."""
        panels = []
        
        for page in script.pages:
            for panel in page.panels:
                panel_dict = {
                    "panel_id": f"p{page.page_number}-{panel.panel_number}",
                    "scene_id": f"chapter-{page.chapter_number}",
                    "page_number": page.page_number,
                    "panel_number": panel.panel_number,
                    "type": panel.size,
                    "description": panel.visual_description,
                    "camera": panel.camera,
                    "dialogue": panel.dialogue,
                    "captions": panel.captions,
                    "sfx": panel.sfx,
                    "characters": panel.characters,
                    "location": panel.location,
                    "lighting_notes": panel.lighting_notes,
                    "mood_notes": panel.mood_notes
                }
                panels.append(panel_dict)
        
        return panels
    
    def script_to_stage6_format(self, script: Script) -> Dict[str, Any]:
        """
        Convert Script to format usable by Stage 6.
        
        This creates a unified data structure that Stage 6 can use.
        """
        return {
            "script": {
                "title": script.title,
                "author": script.author,
                "total_pages": script.total_pages,
                "total_panels": script.total_panels
            },
            "pages": [
                {
                    "page_number": page.page_number,
                    "chapter_number": page.chapter_number,
                    "layout_template": page.layout_template,
                    "panels": [
                        {
                            "panel_number": panel.panel_number,
                            "size": panel.size,
                            "visual_description": panel.visual_description,
                            "camera": panel.camera,
                            "dialogue": panel.dialogue,
                            "captions": panel.captions,
                            "sfx": panel.sfx,
                            "characters": panel.characters,
                            "location": panel.location,
                            "time_period": panel.time_period,
                            "composition_notes": panel.composition_notes,
                            "lighting_notes": panel.lighting_notes,
                            "mood_notes": panel.mood_notes,
                            "page_turn": panel.page_turn,
                            "transition": panel.transition,
                            "action_beat": panel.action_beat
                        }
                        for panel in page.panels
                    ]
                }
                for page in script.pages
            ],
            "statistics": {
                "total_pages": script.total_pages,
                "total_panels": script.total_panels,
                "avg_panels_per_page": script.total_panels / max(1, script.total_pages)
            }
        }
    
    def save_script(self, script: Script, output_path: str):
        """Save script to JSON file."""
        from pathlib import Path
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.orchestrator.save_script(script, str(output_file))
    
    def load_script(self, input_path: str) -> Script:
        """Load script from JSON file."""
        return self.orchestrator.load_script(input_path)
