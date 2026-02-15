"""Module 5: Script Orchestrator - Entry point"""

import json
from typing import Optional

from .schemas import Script, PageScript, PanelSpec
from .script_generator import ScriptGenerator


class ScriptOrchestrator:
    """
    Orchestrates script generation from analysis to final script.
    """
    
    def __init__(self, llm_client=None, model: str = "aurora-alpha"):
        """
        Initialize orchestrator.
        
        Args:
            llm_client: LLM client for rich generation
            model: Model to use for generation
        """
        self.generator = ScriptGenerator(llm_client=llm_client, model=model)
    
    def generate(
        self,
        analysis_result,
        adaptation_plan,
        target_pages: int = 100
    ) -> Script:
        """
        Generate complete manga script.
        
        Args:
            analysis_result: From Module 2 AnalysisEngine
            adaptation_plan: From Module 3 AdaptationPlanner
            target_pages: Target total pages
            
        Returns:
            Complete Script object
        """
        print(f"Generating manga script ({target_pages} pages)...")
        
        script = self.generator.generate(
            analysis_result=analysis_result,
            adaptation_plan=adaptation_plan,
            target_pages=target_pages
        )
        
        print(f"Generated {script.total_pages} pages with {script.total_panels} panels")
        
        return script
    
    def save_script(self, script: Script, path: str):
        """Save script to JSON file."""
        script.save(path)
        print(f"Script saved to {path}")
    
    def load_script(self, path: str) -> Script:
        """Load script from JSON file."""
        with open(path, 'r') as f:
            data = json.load(f)
        
        script = Script(
            title=data.get('title', ''),
            author=data.get('author', ''),
            total_pages=data.get('total_pages', 0),
            total_panels=data.get('total_panels', 0)
        )
        
        for page_data in data.get('pages', []):
            page = PageScript(
                page_number=page_data.get('page_number', 0),
                chapter_number=page_data.get('chapter_number', 0),
                layout_template=page_data.get('layout_template', '6_panel_grid')
            )
            
            for panel_data in page_data.get('panels', []):
                panel = PanelSpec(
                    panel_number=panel_data.get('panel_number', 0),
                    page_number=panel_data.get('page_number', 0),
                    size=panel_data.get('size', 'three_quarter'),
                    visual_description=panel_data.get('visual', ''),
                    dialogue=panel_data.get('dialogue', []),
                    captions=panel_data.get('captions', []),
                    sfx=panel_data.get('sfx', []),
                    camera=panel_data.get('camera', 'medium'),
                    characters=panel_data.get('characters', []),
                    location=panel_data.get('location'),
                    lighting_notes=panel_data.get('lighting_notes', 'Natural lighting'),
                    mood_notes=panel_data.get('mood_notes', '')
                )
                page.panels.append(panel)
            
            script.pages.append(page)
        
        return script
    
    def print_summary(self, script: Script):
        """Print script summary."""
        print(f"\n{'='*50}")
        print(f"SCRIPT SUMMARY: {script.title}")
        print(f"{'='*50}")
        print(f"Total Pages: {script.total_pages}")
        print(f"Total Panels: {script.total_panels}")
        print(f"Avg Panels/Page: {script.total_panels / max(1, script.total_pages):.1f}")
        print()
        
        # Panel size distribution
        size_counts = {}
        for page in script.pages:
            for panel in page.panels:
                size = panel.size
                size_counts[size] = size_counts.get(size, 0) + 1
        
        print("Panel Size Distribution:")
        for size, count in sorted(size_counts.items()):
            print(f"  {size}: {count}")
        
        print()
        
        # Camera angle distribution
        camera_counts = {}
        for page in script.pages:
            for panel in page.panels:
                camera = panel.camera
                camera_counts[camera] = camera_counts.get(camera, 0) + 1
        
        print("Camera Angle Distribution:")
        for camera, count in sorted(camera_counts.items(), key=lambda x: -x[1]):
            print(f"  {camera}: {count}")
        
        print(f"{'='*50}")
