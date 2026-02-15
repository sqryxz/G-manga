#!/usr/bin/env python3
"""
Stage 3.1.2 Detailed Storyboard Generator
Generates detailed storyboard panels from visual beats.

Usage:
    # Use default provider (Z.AI or env var)
    python3 run_stage_3_1_2.py
    
    # Use OpenRouter with GPT-4o-mini
    python3 run_stage_3_1_2.py --provider openrouter --model openai/gpt-4o-mini
    
    # Use mock (testing)
    python3 run_stage_3_1_2.py --mock
    
    # Use Z.AI with specific model
    python3 run_stage_3_1_2.py --provider zai --model glm-4.7
"""

import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))
sys.path.insert(0, str(Path(__file__).parent / 'src' / 'stage3_story_planning'))

from common.logging import setup_logger
from common.llm_factory import create_llm_client
from stage3_story_planning.detailed_storyboard import DetailedStoryboardGenerator


def load_json(file_path: Path) -> Any:
    """Load JSON from file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(data: Any, file_path: Path) -> None:
    """Save data to JSON file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved: {file_path}")


def get_project_paths(project_id: str = None) -> Dict[str, Path]:
    """Get paths for a project."""
    if project_id is None:
        project_id = "picture-of-dorian-gray-20260212-20260212"
    
    project_dir = Path(f"output/projects/{project_id}")
    intermediate_dir = project_dir / "intermediate"
    
    return {
        "project_dir": project_dir,
        "intermediate": intermediate_dir,
        "visual_beats": intermediate_dir / "visual_beats.json",
        "scenes": intermediate_dir / "scenes.json",
        "storyboard": intermediate_dir / "storyboard.json"
    }


def convert_visual_beats(beats_data: List[Dict]) -> List[Dict]:
    """Convert visual beats to format expected by DetailedStoryboardGenerator."""
    converted = []
    for beat in beats_data:
        converted.append({
            "number": beat.get('beat_number', beat.get('number', 1)),
            "description": beat.get('description', beat.get('visual_description', ''))
        })
    return converted


def convert_panel_specs(panels_data: List[Dict]) -> List[Dict]:
    """Convert panel specs to format expected by DetailedStoryboardGenerator."""
    converted = []
    for panel in panels_data:
        panel_num = panel.get('panel_number', 1)
        if '.' in str(panel_num):
            panel_num = int(panel_num.split('.')[-1])
        else:
            panel_num = int(panel_num) if str(panel_num).isdigit() else 1
        
        converted.append({
            "number": panel_num,
            "shot_type": panel.get('shot_type', 'medium'),
            "angle": panel.get('angle', 'eye-level'),
            "focus": panel.get('focus', 'character')
        })
    return converted


def main():
    parser = argparse.ArgumentParser(
        description="Stage 3.1.2: Generate detailed storyboard from visual beats",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use default provider (from LLM_PROVIDER env var)
  python3 run_stage_3_1_2.py
  
  # Use OpenRouter with GPT-4o-mini
  python3 run_stage_3_1_2.py --provider openrouter --model openai/gpt-4o-mini
  
  # Use Z.AI with GLM-4.7
  python3 run_stage_3_1_2.py --provider zai --model glm-4.7
  
  # Use mock for testing
  python3 run_stage_3_1_2.py --mock
  
  # Debug mode - show what would happen
  python3 run_stage_3_1_2.py --dry-run
        """
    )
    
    parser.add_argument("--project", "-p", type=str, default=None,
                        help="Project ID (default: picture-of-dorian-gray-20260212-20260212)")
    parser.add_argument("--provider", type=str, choices=["zai", "openrouter", "auto"], default="auto",
                        help="LLM provider (default: auto from LLM_PROVIDER env var)")
    parser.add_argument("--model", "-m", type=str, default=None,
                        help="Specific model to use (provider-dependent)")
    parser.add_argument("--mock", action="store_true",
                        help="Use mock LLM client for testing")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show configuration without generating")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Verbose logging")
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = "DEBUG" if args.verbose else "INFO"
    logger = setup_logger("g_manga.stage_3_1_2", level=log_level)
    
    # Get paths
    paths = get_project_paths(args.project)
    
    print("=" * 80)
    print("STAGE 3.1.2 - Detailed Storyboard Generator")
    print("=" * 80)
    print()
    
    # Display configuration
    print("Configuration:")
    print(f"  Provider: {args.provider}")
    if args.model:
        print(f"  Model: {args.model}")
    print(f"  Mock: {args.mock}")
    print(f"  Project: {args.project or 'picture-of-dorian-gray-20260212-20260212'}")
    print(f"  Paths:")
    for key, path in paths.items():
        print(f"    - {key}: {path}")
    print()
    
    if args.dry_run:
        print("⚠️  Dry run - no changes will be made")
        return 0
    
    # Check input files
    if not paths["visual_beats"].exists():
        print(f"✗ Error: Visual beats file not found: {paths['visual_beats']}")
        sys.exit(1)
    
    if not paths["scenes"].exists():
        print(f"✗ Error: Scenes file not found: {paths['scenes']}")
        sys.exit(1)
    
    print("Loading input files...")
    print(f"  - Visual beats: {paths['visual_beats']}")
    print(f"  - Scenes: {paths['scenes']}")
    
    visual_beats_data = load_json(paths["visual_beats"])
    scenes_data = load_json(paths["scenes"])
    
    # Handle scenes format
    if isinstance(scenes_data, dict) and 'scenes' in scenes_data:
        scenes_list = scenes_data['scenes']
    else:
        scenes_list = scenes_data
    
    print(f"  Loaded {len(visual_beats_data)} visual beats")
    print(f"  Loaded {len(scenes_list)} scenes")
    print()
    
    # Create LLM client
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
            print(f"  ✓ Client created: {stats.get('client_type', 'unknown')}")
            if stats.get('default_model'):
                print(f"    Model: {stats['default_model']}")
        else:
            print(f"  ✓ Client created (mock)")
    except Exception as e:
        print(f"✗ Error creating client: {e}")
        print("Falling back to mock client...")
        llm_client = create_llm_client(use_mock=True)
    
    print()
    
    # Create storyboard generator
    generator = DetailedStoryboardGenerator(llm_client=llm_client)
    
    # Process each scene
    print("Processing scenes...")
    print("-" * 80)
    
    all_panels = []
    total_panels = 0
    scenes_processed = 0
    
    # Group visual beats by scene
    beats_by_scene = {}
    for beat in visual_beats_data:
        scene_id = beat.get('scene_id', 'unknown')
        if scene_id not in beats_by_scene:
            beats_by_scene[scene_id] = []
        beats_by_scene[scene_id].append(beat)
    
    # Create scene lookup
    scene_lookup = {s.get('id', s.get('scene_id', '')): s for s in scenes_list}
    
    for scene_id, scene_beats in beats_by_scene.items():
        # Find scene data
        scene = scene_lookup.get(scene_id, {})
        scene_text = scene.get('text', scene.get('description', ''))
        
        # Get scene number
        scene_num = scene.get('scene_number', scene.get('number', 0))
        
        # Convert visual beats
        converted_beats = convert_visual_beats(scene_beats)
        
        # Extract all panels from beats
        all_scene_panels = []
        for beat in scene_beats:
            panels = beat.get('panels', [])
            all_scene_panels.extend(panels)
        
        if not all_scene_panels:
            print(f"  ⊘ {scene_id}: No panels found, skipping")
            continue
        
        # Convert panel specs
        panel_specs = convert_panel_specs(all_scene_panels)
        
        # Generate detailed panels
        print(f"  → {scene_id}: Processing {len(panel_specs)} panels...")
        
        try:
            detailed_panels = generator.generate(
                scene_text=scene_text,
                visual_beats=converted_beats,
                panel_specs=panel_specs
            )
            
            # Convert to dicts
            for panel in detailed_panels:
                if hasattr(panel, 'to_dict'):
                    panel_dict = panel.to_dict()
                elif hasattr(panel, '__dict__'):
                    panel_dict = panel.__dict__
                else:
                    panel_dict = panel
                
                panel_dict['scene_id'] = scene_id
                panel_dict['scene_number'] = scene_num
                all_panels.append(panel_dict)
            
            total_panels += len(detailed_panels)
            scenes_processed += 1
            print(f"    ✓ Generated {len(detailed_panels)} detailed panels")
            
        except Exception as e:
            print(f"    ✗ Error: {e}")
            continue
    
    print("-" * 80)
    print()
    
    # Create output
    storyboard_output = {
        "storyboard_id": f"sb-{args.project or 'picture-of-dorian-gray-20260212-20260212'}",
        "project_id": args.project or "picture-of-dorian-gray-20260212-20260212",
        "generation_mode": "real_llm" if not args.mock else "mock",
        "provider": args.provider if args.provider != "auto" else "from_env",
        "model": args.model,
        "total_scenes_processed": scenes_processed,
        "total_panels": total_panels,
        "panels": all_panels,
        "generated_at": str(Path(__file__).resolve())
    }
    
    # Save storyboard
    print(f"Saving storyboard to {paths['storyboard']}...")
    save_json(storyboard_output, paths["storyboard"])
    
    print()
    print("=" * 80)
    print("STAGE 3.1.2 COMPLETE")
    print("=" * 80)
    print()
    print(f"Summary:")
    print(f"  - Scenes processed: {scenes_processed}")
    print(f"  - Total panels generated: {total_panels}")
    print(f"  - Output: {paths['storyboard']}")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
