#!/usr/bin/env python3
"""
Stage 3.1.2 - Detailed Storyboard Generator
Generates detailed manga panel descriptions using LLM.

Usage:
    python3 run_stage_3_1_2_real.py --provider openrouter --model openrouter/aurora-alpha
    python3 run_stage_3_1_2_real.py --provider zai --model glm-4.7
    python3 run_stage_3_1_2_real.py --mock
"""

import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# Add src to path
PROJECT_DIR = Path("/home/clawd/projects/g-manga")
sys.path.insert(0, str(PROJECT_DIR / 'src'))

from common.llm_factory import create_llm_client
from stage3_story_planning.detailed_storyboard import (
    DetailedStoryboardGenerator,
    DetailedPanel
)

# Configuration
OUTPUT_DIR = PROJECT_DIR / "output/projects/picture-of-dorian-gray-20260212-20260212"
INTERMEDIATE_DIR = OUTPUT_DIR / "intermediate"
VISUAL_BEATS_FILE = INTERMEDIATE_DIR / "visual_beats.json"
SCENES_FILE = INTERMEDIATE_DIR / "scenes.json"
STORYBOARD_FILE = INTERMEDIATE_DIR / "storyboard.json"


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


def get_scene_text(scene: Dict, scene_beats: List[Dict]) -> str:
    """Get or generate scene text for context."""
    scene_text = scene.get('text', '').strip()
    
    # If empty, build from scene summary and descriptions
    if not scene_text:
        summary = scene.get('summary', '')
        descriptions = [beat.get('description', '') for beat in scene_beats]
        scene_text = f"{summary}\n\nVisual beats:\n" + "\n".join(f"- {d}" for d in descriptions if d)
    
    return scene_text[:3000]  # Limit to avoid token overflow


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


def group_beats_by_scene(visual_beats: List[Dict]) -> Dict[str, List[Dict]]:
    """Group visual beats by scene_id."""
    grouped = {}
    for beat in visual_beats:
        scene_id = beat.get('scene_id', 'unknown')
        if scene_id not in grouped:
            grouped[scene_id] = []
        grouped[scene_id].append(beat)
    return grouped


def extract_characters(scene: Dict, beats: List[Dict]) -> List[str]:
    """Extract unique characters from scene and beats."""
    characters = set(scene.get('characters', []))
    
    for beat in beats:
        # Check for character references in description
        desc = beat.get('description', '')
        if 'Basil' in desc:
            characters.add('Basil Hallward')
        if 'Dorian' in desc:
            characters.add('Dorian Gray')
        if 'Lord Henry' in desc or 'Henry' in desc:
            characters.add('Lord Henry Wotton')
        if 'Harry' in desc:
            characters.add('Lord Henry Wotton')
    
    return sorted(list(characters))


import argparse


def main():
    parser = argparse.ArgumentParser(
        description="Stage 3.1.2: Generate detailed storyboard from visual beats",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use OpenRouter with aurora-alpha
  python3 run_stage_3_1_2_real.py --provider openrouter --model openrouter/aurora-alpha
  
  # Use Z.AI
  python3 run_stage_3_1_2_real.py --provider zai --model glm-4.7
  
  # Use mock for testing
  python3 run_stage_3_1_2_real.py --mock
        """
    )
    
    parser.add_argument("--provider", type=str, choices=["zai", "openrouter", "auto"], default="auto",
                        help="LLM provider (default: auto from LLM_PROVIDER env var)")
    parser.add_argument("--model", "-m", type=str, default=None,
                        help="Specific model to use")
    parser.add_argument("--mock", action="store_true",
                        help="Use mock LLM client")
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("STAGE 3.1.2 - Detailed Storyboard Generator")
    print("=" * 80)
    print()
    
    # Initialize LLM client using factory
    print("Initializing LLM client...")
    try:
        llm_client = create_llm_client(
            provider=None if args.provider == "auto" else args.provider,
            model=args.model,
            use_mock=args.mock
        )
        
        # Get provider info
        if hasattr(llm_client, 'get_stats'):
            stats = llm_client.get_stats()
            provider_type = stats.get('client_type', 'unknown')
            model = args.model or stats.get('default_model', '')
            print(f"✓ {provider_type.upper()} client initialized")
            print(f"  - Model: {model}")
        else:
            print(f"✓ Mock client initialized")
            provider_type = "mock"
            model = "mock"
            
    except Exception as e:
        print(f"✗ Error initializing LLM client: {e}")
        print("Falling back to mock client...")
        from stage3_story_planning.detailed_storyboard import MockLLMClient
        llm_client = MockLLMClient()
        provider_type = "mock"
        model = "mock"
        print(f"✓ Mock client initialized")
    
    # Check input files
    if not VISUAL_BEATS_FILE.exists():
        print(f"✗ Error: Visual beats file not found: {VISUAL_BEATS_FILE}")
        sys.exit(1)
    
    if not SCENES_FILE.exists():
        print(f"✗ Error: Scenes file not found: {SCENES_FILE}")
        sys.exit(1)
    
    print(f"\nLoading input files...")
    print(f"  - Visual beats: {VISUAL_BEATS_FILE}")
    print(f"  - Scenes: {SCENES_FILE}")
    
    # Load data
    visual_beats = load_json(VISUAL_BEATS_FILE)
    scenes_data = load_json(SCENES_FILE)
    scenes = scenes_data.get('scenes', scenes_data)
    
    print(f"\n✓ Loaded {len(visual_beats)} visual beats")
    print(f"✓ Loaded {len(scenes)} scenes")
    
    # Group beats by scene
    beats_by_scene = group_beats_by_scene(visual_beats)
    print(f"✓ Grouped into {len(beats_by_scene)} unique scenes")
    
    # Create scene lookup
    scene_lookup = {scene.get('id', ''): scene for scene in scenes}
    
    # Initialize storyboard generator
    generator = DetailedStoryboardGenerator(llm_client=llm_client)
    
    print()
    print("-" * 80)
    print("Generating detailed storyboard panels...")
    print("-" * 80)
    
    all_panels = []
    panels_by_scene = {}
    total_panels = 0
    scenes_processed = 0
    errors = []
    
    scene_ids = sorted(beats_by_scene.keys())
    
    for i, scene_id in enumerate(scene_ids):
        scene_beats = beats_by_scene[scene_id]
        scene = scene_lookup.get(scene_id, {})
        
        print(f"\n[{i+1}/{len(scene_ids)}] Processing: {scene_id}")
        
        # Get scene text for context
        scene_text = get_scene_text(scene, scene_beats)
        
        # Process panel specs from beats
        all_panel_specs = []
        for beat in scene_beats:
            specs = process_panel_specs(beat)
            all_panel_specs.extend(specs)
        
        if not all_panel_specs:
            print(f"  → No panels to generate for this scene")
            continue
        
        print(f"  → Generating {len(all_panel_specs)} panels...")
        
        # Generate panels using LLM
        try:
            panels = generator.generate(
                scene_text=scene_text,
                visual_beats=scene_beats,
                panel_specs=all_panel_specs
            )
            
            # Store panels
            panels_by_scene[scene_id] = [p.to_dict() for p in panels]
            all_panels.extend(panels)
            total_panels += len(panels)
            scenes_processed += 1
            
            print(f"  ✓ Generated {len(panels)} panels")
            
        except Exception as e:
            error_msg = f"Error in {scene_id}: {str(e)}"
            errors.append(error_msg)
            print(f"  ✗ Error: {e}")
            
            # Continue with empty panels for this scene
            panels_by_scene[scene_id] = []
    
    print()
    print("-" * 80)
    
    # Generation mode string
    generation_mode = f"{provider_type}/{model}" if provider_type != "mock" else "mock"
    
    # Create final storyboard output
    storyboard = {
        "storyboard_id": f"sb-{OUTPUT_DIR.name}",
        "project_id": OUTPUT_DIR.name,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "generation_mode": generation_mode,
        "generation_note": (
            "Storyboard generated using visual beats as input. "
            "Each panel includes detailed descriptions, mood, lighting, composition, "
            "and character/prop information for manga illustration."
        ),
        "input_stats": {
            "visual_beats_used": len(visual_beats),
            "scenes_processed": scenes_processed,
            "total_scenes_in_project": len(scenes)
        },
        "output_stats": {
            "total_panels": total_panels,
            "panels_by_scene": {k: len(v) for k, v in panels_by_scene.items()}
        },
        "panels": [p.to_dict() if hasattr(p, 'to_dict') else p for p in all_panels],
        "panels_by_scene": panels_by_scene,
        "errors": errors if errors else None
    }
    
    # Remove None values
    storyboard = {k: v for k, v in storyboard.items() if v is not None}
    
    # Save storyboard
    print(f"\nSaving storyboard to {STORYBOARD_FILE}...")
    save_json(storyboard, STORYBOARD_FILE)
    
    print()
    print("=" * 80)
    print("STAGE 3.1.2 COMPLETE")
    print("=" * 80)
    print()
    print(f"Summary:")
    print(f"  - Scenes processed: {scenes_processed}")
    print(f"  - Total panels generated: {total_panels}")
    print(f"  - Generation mode: {generation_mode}")
    print(f"  - Output file: {STORYBOARD_FILE}")
    
    if errors:
        print(f"\n  ⚠️  {len(errors)} errors occurred (see output)")
        for error in errors[:3]:
            print(f"    - {error}")
    
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
