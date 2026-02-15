#!/usr/bin/env python3
"""
Character Consistency Helper Functions for G-Manga Pipeline

This module provides helper functions for:
- Reading character profiles
- Generating reference sheets (placeholder for image generation)
- Updating panel prompts with character references
"""

import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional
from character_consistency import CharacterConsistencySystem


def load_character_profiles(profiles_path: str = None) -> Dict:
    """
    Load character profiles from JSON file.
    
    Args:
        profiles_path: Path to character profiles JSON (default: character_mapping.json)
    
    Returns:
        Dictionary of character profiles
    """
    if profiles_path is None:
        # Try to find the latest character mapping
        base_path = Path("/home/clawd/projects/g-manga/output/projects")
        for project_dir in sorted(base_path.iterdir(), reverse=True):
            mapping_path = project_dir / "intermediate" / "character_mapping.json"
            if mapping_path.exists():
                profiles_path = str(mapping_path)
                break
    
    with open(profiles_path, 'r') as f:
        return json.load(f)


def generate_reference_sheet_prompt(character_data: Dict) -> str:
    """
    Generate a prompt for creating a character reference sheet.
    
    Args:
        character_data: Character information from mapping
    
    Returns:
        Prompt string for image generation
    """
    features = character_data.get("key_features", [])
    clothing = character_data.get("clothing", [])
    palette = character_data.get("color_palette", {})
    
    prompt = f"""Character Reference Sheet for {character_data.get('name', 'Unknown')}

Physical Description:
- Height: {character_data.get('height', 'average')}
- Build: {character_data.get('build', 'average')}
- Age: {character_data.get('age', 'adult')}

Key Features:
{chr(10).join(f'- {f}' for f in features)}

Color Palette:
{chr(10).join(f'- {k}: {v}' for k, v in palette.items())}

Clothing:
{chr(10).join(f'- {c}' for c in clothing)}

Personality Traits:
{chr(10).join(f'- {t}' for t in character_data.get('personality_traits', []))}

Style: Victorian era manga, detailed linework, consistent character sheet format
"""
    return prompt


def update_panel_prompts_with_character_refs(
    project_path: str,
    character_mapping_path: str = None,
    panel_prompts_path: str = None,
    output_path: str = None
) -> Dict:
    """
    Main helper function to update panel prompts with character references.
    
    This is the primary entry point for the character consistency system.
    
    Args:
        project_path: Path to project directory
        character_mapping_path: Path to character mapping JSON (optional)
        panel_prompts_path: Path to input panel prompts JSON (optional)
        output_path: Path for output JSON (optional)
    
    Returns:
        Dictionary with processed panels and metadata
    """
    system = CharacterConsistencySystem(project_path)
    
    # Determine paths
    if character_mapping_path is None:
        char_mapping_path = f"{project_path}/intermediate/character_mapping.json"
    else:
        char_mapping_path = character_mapping_path
    
    if panel_prompts_path is None:
        # Try to find panel prompts in parent directory
        panel_prompts_path = f"../picture-of-dorian-gray-20260212-20260212/intermediate/panel_prompts.json"
    
    # Load character mapping
    system.load_character_mapping(char_mapping_path)
    
    # Process panel prompts
    result = system.process_panel_prompts(panel_prompts_path, output_path)
    
    return result


def generate_all_reference_sheets(
    project_path: str,
    output_dir: str = None,
    output_format: str = "prompts"
) -> Dict:
    """
    Generate reference sheet prompts for all characters.
    
    Args:
        project_path: Path to project directory
        output_dir: Directory to save prompts (optional)
        output_format: 'prompts' for text, 'json' for JSON, 'images' for image generation
    
    Returns:
        Dictionary with all reference prompts
    """
    char_mapping = load_character_profiles(f"{project_path}/intermediate/character_mapping.json")
    characters = char_mapping.get("characters", {})
    
    all_prompts = {}
    for char_name, char_data in characters.items():
        all_prompts[char_name] = {
            "reference_sheet": char_data.get("reference_sheet", ""),
            "prompt": generate_reference_sheet_prompt(char_data),
            "metadata": {
                "height": char_data.get("height"),
                "build": char_data.get("build"),
                "key_features": char_data.get("key_features", [])[:3]
            }
        }
    
    if output_dir:
        output_path = Path(output_dir) / "reference_sheet_prompts.json"
        with open(output_path, 'w') as f:
            json.dump(all_prompts, f, indent=2)
    
    return all_prompts


def run_full_pipeline(project_path: str) -> Dict:
    """
    Run the complete character consistency pipeline.
    
    This function:
    1. Loads character profiles
    2. Processes panel prompts
    3. Updates prompts with character references
    4. Generates reference sheet prompts
    5. Creates a summary report
    
    Args:
        project_path: Path to project directory
    
    Returns:
        Dictionary with all results and reports
    """
    results = {}
    
    # Step 1: Load character mapping
    char_mapping_path = f"{project_path}/intermediate/character_mapping.json"
    with open(char_mapping_path, 'r') as f:
        character_mapping = json.load(f)
    results["character_mapping"] = character_mapping
    results["total_characters"] = len(character_mapping.get("characters", {}))
    
    # Step 2: Process panel prompts
    panel_results = update_panel_prompts_with_character_refs(
        project_path=project_path,
        character_mapping_path=char_mapping_path,
        panel_prompts_path=f"../picture-of-dorian-gray-20260212-20260212/intermediate/panel_prompts.json",
        output_path=f"{project_path}/intermediate/panel_prompts.json"
    )
    results["panel_processing"] = panel_results
    
    # Step 3: Generate reference sheet prompts
    ref_prompts = generate_all_reference_sheets(
        project_path=project_path,
        output_dir=f"{project_path}/intermediate",
        output_format="json"
    )
    results["reference_sheet_prompts"] = ref_prompts
    
    # Step 4: Generate summary report
    report = {
        "project": project_path,
        "total_characters": results["total_characters"],
        "total_panels_processed": panel_results["metadata"]["total_panels"],
        "panels_with_characters": panel_results["metadata"]["panels_with_characters"],
        "reference_sheets_generated": len(ref_prompts),
        "character_names": list(ref_prompts.keys()),
        "output_files": [
            f"{project_path}/intermediate/character_mapping.json",
            f"{project_path}/intermediate/panel_prompts.json",
            f"{project_path}/intermediate/reference_sheet_prompts.json"
        ]
    }
    results["summary_report"] = report
    
    return results


def main():
    """CLI entry point for the helper functions."""
    parser = argparse.ArgumentParser(
        description="Character Consistency Helper Functions for G-Manga Pipeline"
    )
    parser.add_argument(
        "--project-path",
        default="/home/clawd/projects/g-manga/output/projects/picture-of-dorian-gray-20260213-20260213",
        help="Path to project directory"
    )
    parser.add_argument(
        "--action",
        choices=["process", "generate-refs", "full-pipeline", "report"],
        default="process",
        help="Action to perform"
    )
    
    args = parser.parse_args()
    
    if args.action == "process":
        result = update_panel_prompts_with_character_refs(args.project_path)
        print(f"Processed {result['metadata']['total_panels']} panels")
        print(f"Panels with character references: {result['metadata']['panels_with_characters']}")
    
    elif args.action == "generate-refs":
        prompts = generate_all_reference_sheets(args.project_path)
        print(f"Generated prompts for {len(prompts)} characters")
        for name in prompts:
            print(f"  - {name}")
    
    elif args.action == "full-pipeline":
        results = run_full_pipeline(args.project_path)
        report = results["summary_report"]
        print("=" * 50)
        print("Character Consistency Pipeline Complete")
        print("=" * 50)
        print(f"Total Characters: {report['total_characters']}")
        print(f"Total Panels Processed: {report['total_panels_processed']}")
        print(f"Panels with Characters: {report['panels_with_characters']}")
        print(f"\nOutput Files:")
        for f in report["output_files"]:
            print(f"  - {f}")
    
    elif args.action == "report":
        system = CharacterConsistencySystem(args.project_path)
        system.load_character_mapping(f"{args.project_path}/intermediate/character_mapping.json")
        report = system.generate_character_report()
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
