"""Module 5: Script Generator - Core generation logic"""

import json
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from .schemas import (
    Script, PageScript, PanelSpec,
    PanelSize, CameraAngle
)


class ScriptGenerator:
    """
    Generates panel-by-panel manga scripts from analysis.
    """
    
    def __init__(self, llm_client=None, model: str = "aurora-alpha"):
        self.llm_client = llm_client
        self.model = model
        self.panel_sizes = list(PanelSize.__members__.keys())
        self.camera_angles = list(CameraAngle.__members__.keys())
    
    def generate(
        self,
        analysis_result,
        adaptation_plan,
        target_pages: int = 100
    ) -> Script:
        """
        Generate full manga script.
        
        Args:
            analysis_result: From Module 2 (characters, locations, beats, dialogue)
            adaptation_plan: From Module 3 (page allocation, splash pages)
            target_pages: Target total pages
            
        Returns:
            Complete Script object
        """
        script = Script(
            title="The Picture of Dorian Gray",
            author="Oscar Wilde",
            pages=[],
            total_pages=target_pages
        )
        
        # Get page allocation
        page_alloc = adaptation_plan.page_allocation if hasattr(adaptation_plan, 'page_allocation') else []
        if not page_alloc:
            # Fallback: equal distribution (handle None analysis_result)
            total_chapters = 20  # Default for Dorian Gray
            pages_per_chapter = max(1, target_pages // total_chapters)
            remaining = target_pages - (pages_per_chapter * total_chapters)
            page_alloc = []
            for i in range(total_chapters):
                pages = pages_per_chapter + (1 if i < remaining else 0)
                page_alloc.append({'chapter': i+1, 'pages': pages})
        
        # Generate pages for each chapter
        current_page = 1
        for alloc in page_alloc:
            chapter_num = alloc.get('chapter', 1)
            num_pages = alloc.get('pages', 5)
            
            for p in range(num_pages):
                page_script = self._generate_page(
                    chapter_num=chapter_num,
                    page_number=current_page,
                    analysis_result=analysis_result,
                    adaptation_plan=adaptation_plan
                )
                script.pages.append(page_script)
                current_page += 1
        
        script.total_pages = len(script.pages)
        script.total_panels = sum(len(p.panels) for p in script.pages)
        
        return script
    
    def _generate_page(
        self,
        chapter_num: int,
        page_number: int,
        analysis_result,
        adaptation_plan
    ) -> PageScript:
        """Generate a single page."""
        
        page = PageScript(
            page_number=page_number,
            chapter_number=chapter_num,
            panels=[]
        )
        
        # Determine panel count based on chapter type
        chapter_level = self._get_chapter_level(chapter_num, adaptation_plan)
        
        if chapter_level == 'climax':
            panel_count = 4  # More detailed for climaxes
        elif chapter_level == 'setup':
            panel_count = 6  # Faster pacing for setup
        else:
            panel_count = 5  # Standard
        
        # Generate panels
        for p in range(panel_count):
            panel = self._generate_panel(
                panel_number=p + 1,
                page_number=page_number,
                chapter_num=chapter_num,
                panel_index=p,
                total_panels=panel_count,
                analysis_result=analysis_result
            )
            page.panels.append(panel)
        
        return page
    
    def _generate_panel(
        self,
        panel_number: int,
        page_number: int,
        chapter_num: int,
        panel_index: int,
        total_panels: int,
        analysis_result
    ) -> PanelSpec:
        """Generate a single panel."""
        
        # Determine panel size based on position
        if panel_index == 0 and total_panels <= 4:
            size = "splash"
        elif panel_index == 0:
            size = "full_width"
        elif panel_index == total_panels - 1:
            size = "half_width"
        elif panel_index % 3 == 0:
            size = "three_quarter"
        else:
            size = "quarter"
        
        # Determine camera angle
        camera = self._select_camera(panel_index, total_panels)
        
        # Generate visual description
        visual_desc = self._generate_visual_description(
            chapter_num, panel_number, analysis_result
        )
        
        # Extract dialogue for this panel
        dialogue = self._extract_dialogue_for_panel(
            chapter_num, panel_number, analysis_result
        )
        
        # Generate captions
        captions = []
        if panel_number == 1:
            captions = [{'text': f'Chapter {chapter_num}', 'position': 'top'}]
        
        panel = PanelSpec(
            panel_number=panel_number,
            page_number=page_number,
            size=size,
            visual_description=visual_desc,
            dialogue=dialogue,
            captions=captions,
            camera=camera,
            characters=[],
            lighting_notes="Natural lighting",
            mood_notes=self._get_mood_for_panel(chapter_num, panel_number)
        )
        
        return panel
    
    def _get_chapter_level(self, chapter_num: int, adaptation_plan) -> str:
        """Determine if chapter is setup, normal, or climax."""
        
        splash_pages = getattr(adaptation_plan, 'splash_pages', []) or []
        
        for splash in splash_pages:
            if splash.get('chapter') == chapter_num:
                return 'climax'
        
        if chapter_num <= 5:
            return 'setup'
        elif chapter_num >= 15:
            return 'climax'
        else:
            return 'normal'
    
    def _select_camera(self, panel_index: int, total_panels: int) -> str:
        """Select appropriate camera angle."""
        
        if panel_index == 0:
            return "wide"
        elif panel_index == total_panels - 1:
            return "medium_close"
        else:
            cameras = ["medium", "medium", "medium_close", "low_angle", "over_shoulder"]
            return cameras[panel_index % len(cameras)]
    
    def _generate_visual_description(
        self,
        chapter_num: int,
        panel_num: int,
        analysis_result
    ) -> str:
        """Generate visual description for panel."""
        
        # Try to use LLM for rich descriptions
        if self.llm_client:
            prompt = f"""Generate a manga panel visual description.

Chapter: {chapter_num}
Panel: {panel_num}

Describe what happens visually. Include:
- Setting/background
- Character positions and actions
- Mood and atmosphere
- Key visual elements

Return ONLY a brief description (1-2 sentences)."""
            
            try:
                response = self.llm_client.generate(prompt, model=self.model)
                if hasattr(response, 'text'):
                    return response.text.strip()
            except:
                pass
        
        # Fallback template descriptions
        templates = [
            "Character in thoughtful pose against Victorian interior.",
            "Close-up showing emotional reaction.",
            "Wide shot establishing the setting.",
            "Two characters in conversation, medium shot.",
            "Action moment captured in dynamic pose.",
            "Atmospheric scene with mood lighting.",
            "Character expression conveys inner turmoil.",
            "Setting detail emphasizes the era.",
        ]
        
        return templates[panel_num % len(templates)]
    
    def _extract_dialogue_for_panel(
        self,
        chapter_num: int,
        panel_num: int,
        analysis_result
    ) -> List[Dict]:
        """Extract relevant dialogue for this panel."""
        
        dialogue = getattr(analysis_result, 'dialogue', []) or []
        
        # Simple distribution: each panel gets some dialogue
        dialogue_per_panel = len(dialogue) // max(1, len(dialogue) // 3) if dialogue else 0
        
        panel_dialogue = []
        for d in dialogue[:dialogue_per_panel]:
            if hasattr(d, 'chapter') and d.chapter == chapter_num:
                panel_dialogue.append({
                    'speaker': d.speaker if hasattr(d, 'speaker') else 'Unknown',
                    'text': d.quote if hasattr(d, 'quote') else '',
                    'tone': d.tone if hasattr(d, 'tone') else 'neutral'
                })
        
        return panel_dialogue
    
    def _get_mood_for_panel(self, chapter: int, panel: int) -> str:
        """Get mood description for panel."""
        
        moods = [
            "Contemplative and atmospheric",
            "Tense with underlying danger",
            "Elegant and refined",
            "Melancholic with hint of corruption",
            "Dramatic with emotional intensity",
            "Quiet moment of reflection",
            "Tense confrontation",
            "Supernatural and unsettling",
        ]
        
        return moods[(chapter + panel) % len(moods)]
