#!/usr/bin/env python3
"""
Stage 3.1.2 - Chapter-3-Scene-3 Panel Generator (OpenRouter aurora-alpha)
Generates detailed storyboard panels for chapter-3-scene-3 only.

Usage:
    python3 run_chapter3_scene3_aurora.py
"""

import sys
import json
import os
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# Add src to path
PROJECT_DIR = Path("/home/clawd/projects/g-manga")
sys.path.insert(0, str(PROJECT_DIR / 'src'))

from common.openrouter import OpenRouterClient
from stage3_story_planning.detailed_storyboard import DetailedStoryboardGenerator

# Configuration
OUTPUT_DIR = PROJECT_DIR / "output/projects/picture-of-dorian-gray-20260212-20260212"
INTERMEDIATE_DIR = OUTPUT_DIR / "intermediate"
VISUAL_BEATS_FILE = INTERMEDIATE_DIR / "visual_beats.json"
SCENES_FILE = INTERMEDIATE_DIR / "scenes.json"
STORYBOARD_FILE = INTERMEDIATE_DIR / "storyboard.json"

# Target scene
TARGET_SCENE_ID = "chapter-3-scene-3"
TARGET_PANELS = 6


def load_json(file_path: Path) -> Dict:
    """Load JSON from file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(data: Any, file_path: Path):
    """Save data to JSON file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved: {file_path}")


def get_scene_context(scene: Dict, scene_beats: List[Dict]) -> str:
    """Get context text for the scene."""
    summary = scene.get('summary', '')
    location = scene.get('location', '')
    characters = scene.get('characters', [])
    
    context = f"SCENE SUMMARY: {summary}\n"
    context += f"LOCATION: {location}\n"
    context += f"CHARACTERS: {', '.join(characters) if characters else 'None specified'}\n\n"
    
    # Add visual beat descriptions
    context += "VISUAL BEATS:\n"
    for i, beat in enumerate(scene_beats, 1):
        desc = beat.get('description', beat.get('visual_description', ''))
        focus = beat.get('visual_focus', '')
        priority = beat.get('priority', '')
        context += f"  Beat {i}: [{focus}] {desc} (priority: {priority})\n"
    
    return context


def process_panel_specs(beat: Dict) -> List[Dict]:
    """Extract panel specs from a visual beat."""
    panels = beat.get('panels', [])
    specs = []
    
    for panel in panels:
        panel_num = panel.get('panel_number', '1')
        # Extract numeric part
        if '.' in str(panel_num):
            num = int(panel_num.split('.')[-1])
        else:
            num = int(panel_num) if str(panel_num).isdigit() else 1
        
        specs.append({
            "number": num,
            "shot_type": panel.get('shot_type', 'medium').lower(),
            "angle": panel.get('angle', 'eye-level').lower().replace('-', ' '),
            "focus": panel.get('focus', 'character')
        })
    
    return specs


def create_openrouter_aurora_client():
    """Create OpenRouter client with aurora-alpha model."""
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    
    if not api_key:
        print("⚠️  WARNING: OPENROUTER_API_KEY not set!")
        print("   Falling back to mock generation")
        from stage3_story_planning.detailed_storyboard import MockLLMClient
        return MockLLMClient(), "mock"
    
    try:
        client = OpenRouterClient(api_key=api_key)
        print(f"✓ OpenRouter client initialized")
        print(f"  - Using model: openrouter/aurora-alpha")
        
        # Test connection
        test_result = client.generate("Hello", model="openrouter/aurora-alpha")
        if test_result.success:
            print(f"✓ OpenRouter aurora-alpha connection verified")
            return client, "openrouter/aurora-alpha"
        else:
            print(f"⚠️  OpenRouter test failed: {test_result.error}")
            print("   Falling back to mock generation")
            from stage3_story_planning.detailed_storyboard import MockLLMClient
            return MockLLMClient(), "mock"
    except Exception as e:
        print(f"⚠️  OpenRouter initialization failed: {e}")
        print("   Falling back to mock generation")
        from stage3_story_planning.detailed_storyboard import MockLLMClient
        return MockLLMClient(), "mock"


class AuroraAlphaAdapter:
    """Adapter to use OpenRouter client with DetailedStoryboardGenerator."""
    
    def __init__(self, client: Any, model: str):
        self.client = client
        self.model = model
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text and return raw string."""
        result = self.client.generate(prompt, model=self.model)
        if result.success:
            return result.text
        else:
            raise Exception(f"OpenRouter generation failed: {result.error}")


def main():
    print("=" * 80)
    print("STAGE 3.1.2 - Chapter-3-Scene-3 Panel Generator (OpenRouter aurora-alpha)")
    print("=" * 80)
    print()
    
    # Check input files
    if not VISUAL_BEATS_FILE.exists():
        print(f"✗ Error: Visual beats file not found: {VISUAL_BEATS_FILE}")
        sys.exit(1)
    
    if not SCENES_FILE.exists():
        print(f"✗ Error: Scenes file not found: {SCENES_FILE}")
        sys.exit(1)
    
    print(f"Loading input files...")
    print(f"  - Visual beats: {VISUAL_BEATS_FILE}")
    print(f"  - Scenes: {SCENES_FILE}")
    print()
    
    # Load data
    visual_beats = load_json(VISUAL_BEATS_FILE)
    scenes_data = load_json(SCENES_FILE)
    scenes = scenes_data.get('scenes', scenes_data)
    
    print(f"✓ Loaded {len(visual_beats)} visual beats")
    print(f"✓ Loaded {len(scenes)} scenes")
    
    # Find target scene beats
    target_beats = [b for b in visual_beats if b.get('scene_id') == TARGET_SCENE_ID]
    
    if not target_beats:
        print(f"✗ Error: No visual beats found for scene {TARGET_SCENE_ID}")
        sys.exit(1)
    
    print(f"✓ Found {len(target_beats)} visual beats for {TARGET_SCENE_ID}")
    
    # Find scene data
    scene_lookup = {s.get('id', ''): s for s in scenes}
    target_scene = scene_lookup.get(TARGET_SCENE_ID, {})
    
    scene_summary = target_scene.get('summary', 'No summary available')
    scene_location = target_scene.get('location', 'Unknown location')
    scene_characters = target_scene.get('characters', [])
    
    print()
    print(f"Scene: {TARGET_SCENE_ID}")
    print(f"  Summary: {scene_summary}")
    print(f"  Location: {scene_location}")
    print(f"  Characters: {', '.join(scene_characters)}")
    print()
    
    # Create OpenRouter client
    llm_client, generation_mode = create_openrouter_aurora_client()
    
    # Create adapter if not mock
    if hasattr(llm_client, 'generate'):
        llm_client = AuroraAlphaAdapter(llm_client, "openrouter/aurora-alpha")
    
    # Initialize storyboard generator
    generator = DetailedStoryboardGenerator(llm_client=llm_client)
    
    print()
    print("-" * 80)
    print(f"Generating {TARGET_PANELS} detailed panels for {TARGET_SCENE_ID}...")
    print("-" * 80)
    
    # Process panel specs from beats
    all_panel_specs = []
    for beat in target_beats:
        specs = process_panel_specs(beat)
        all_panel_specs.extend(specs)
    
    print(f"  Panel specs to generate: {len(all_panel_specs)}")
    
    # Get context
    scene_context = get_scene_context(target_scene, target_beats)
    
    # Generate panels using LLM
    try:
        panels = generator.generate(
            scene_text=scene_context,
            visual_beats=target_beats,
            panel_specs=all_panel_specs
        )
        
        panel_dicts = []
        for panel in panels:
            if hasattr(panel, 'to_dict'):
                panel_dict = panel.to_dict()
            elif hasattr(panel, '__dict__'):
                panel_dict = panel.__dict__
            else:
                panel_dict = panel
            
            panel_dict['scene_id'] = TARGET_SCENE_ID
            panel_dict['scene_number'] = 3
            panel_dicts.append(panel_dict)
        
        print(f"✓ Generated {len(panel_dicts)} panels")
        
    except Exception as e:
        print(f"✗ Error generating panels: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Load existing storyboard
    existing_panels = []
    if STORYBOARD_FILE.exists():
        existing_storyboard = load_json(STORYBOARD_FILE)
        existing_panels = existing_storyboard.get('panels', [])
        print(f"✓ Loaded existing storyboard with {len(existing_panels)} panels")
    
    # Remove any existing panels for chapter-3-scene-3
    filtered_panels = [p for p in existing_panels if p.get('scene_id') != TARGET_SCENE_ID]
    
    # Add new panels
    final_panels = filtered_panels + panel_dicts
    
    # Sort panels by scene_id and panel_number
    def panel_sort_key(p):
        scene = p.get('scene_id', '')
        num = p.get('panel_number', 0)
        # Extract chapter and scene numbers
        parts = scene.replace('chapter-', '').replace('scene-', '').split('-')
        if len(parts) >= 2:
            chapter = int(parts[0]) if parts[0].isdigit() else 0
            scene_num = int(parts[1]) if parts[1].isdigit() else 0
            return (chapter, scene_num, num)
        return (0, 0, num)
    
    final_panels.sort(key=panel_sort_key)
    
    # Create final storyboard
    storyboard = {
        "storyboard_id": f"sb-{OUTPUT_DIR.name}",
        "project_id": OUTPUT_DIR.name,
        "generation_mode": generation_mode,
        "provider": "openrouter",
        "model": "openrouter/aurora-alpha",
        "total_scenes_processed": len(set(p.get('scene_id') for p in final_panels)),
        "total_panels": len(final_panels),
        "panels": final_panels,
        "generated_at": datetime.utcnow().isoformat() + "Z"
    }
    
    # Save storyboard
    print()
    print(f"Saving storyboard to {STORYBOARD_FILE}...")
    save_json(storyboard, STORYBOARD_FILE)
    
    # Summary
    chapter3_scene3_panels = [p for p in final_panels if p.get('scene_id') == TARGET_SCENE_ID]
    
    print()
    print("=" * 80)
    print("STAGE 3.1.2 COMPLETE - Chapter-3-Scene-3")
    print("=" * 80)
    print()
    print(f"Summary:")
    print(f"  - Scene: {TARGET_SCENE_ID}")
    print(f"  - Panels generated: {len(panel_dicts)}")
    print(f"  - Total panels in storyboard: {len(final_panels)}")
    print(f"  - Generation mode: {generation_mode}")
    print(f"  - Model: openrouter/aurora-alpha")
    print(f"  - Output file: {STORYBOARD_FILE}")
    print()
    
    print(f"Chapter-3-Scene-3 Panels:")
    for i, panel in enumerate(chapter3_scene3_panels, 1):
        print(f"  {i}. Panel {panel.get('panel_number', i)}: {panel.get('shot_type', 'unknown')} - {panel.get('mood', 'no mood')}")
    
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
