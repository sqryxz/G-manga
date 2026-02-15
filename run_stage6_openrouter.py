#!/usr/bin/env python3
"""
Stage 6: Image Generation using OpenRouter
Generates manga panel images for "The Picture of Dorian Gray" project.
"""

import sys
import json
import os
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from stage6_image_generation.providers.openrouter import OpenRouterImageProvider, create_openrouter_provider
from stage6_image_generation.providers.base import ProviderConfig, ProviderType, ImageSize, ImageQuality

# Load environment variables
load_dotenv()

def load_panel_prompts(prompts_path: str) -> list:
    """Load panel prompts from JSON file."""
    with open(prompts_path, 'r') as f:
        return json.load(f)

def generate_images_for_project(
    project_dir: str,
    prompts_path: str,
    output_dir: str,
    api_key: str,
    model: str = "google/gemini-2.5-flash-image"
) -> dict:
    """
    Generate images for all panels in the project.

    Args:
        project_dir: Project directory path
        prompts_path: Path to panel prompts JSON
        output_dir: Output directory for images
        api_key: OpenRouter API key
        model: Model to use for generation

    Returns:
        Dict with generation statistics
    """
    print("=" * 80)
    print("STAGE 6: IMAGE GENERATION (OpenRouter)")
    print("=" * 80)

    # Load prompts
    print(f"\n[1/4] Loading panel prompts from: {prompts_path}")
    panels = load_panel_prompts(prompts_path)
    print(f"      Found {len(panels)} panels to generate")

    # Group panels by unique prompts (avoid duplicates)
    unique_prompts = {}
    for panel in panels:
        panel_id = panel['panel_id']
        scene_id = panel['scene_id']
        key = f"{scene_id}_{panel_id}"
        if key not in unique_prompts:
            unique_prompts[key] = panel

    print(f"      Unique panels: {len(unique_prompts)}")

    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    print(f"\n[2/4] Output directory: {output_dir}")

    # Create OpenRouter provider
    print(f"\n[3/4] Initializing OpenRouter provider...")
    print(f"      Model: {model}")

    config = ProviderConfig(
        provider_type=ProviderType.SDXL,
        api_key=api_key,
        default_size=ImageSize.SQUARE_1024,
        quality=ImageQuality.STANDARD,
        rate_limit=10,  # requests per minute
        cost_per_image=0.02,
        max_retries=3,
        timeout=60
    )

    provider = OpenRouterImageProvider(config, model=model)

    # Generate images
    print(f"\n[4/4] Generating images...")
    print("-" * 80)

    results = {
        "successful": 0,
        "failed": 0,
        "images": []
    }

    for i, (key, panel) in enumerate(unique_prompts.items(), 1):
        panel_id = panel['panel_id']
        scene_id = panel['scene_id']
        prompt = panel['prompt']
        original_desc = panel.get('original_description', '')

        print(f"\n[{i}/{len(unique_prompts)}] Generating: {scene_id} - {panel_id}")

        try:
            # Generate image
            result = provider.generate(
                prompt=prompt,
                size=ImageSize.SQUARE_1024,
                quality=ImageQuality.STANDARD
            )

            if result.success and result.image_bytes:
                # Save image
                filename = f"{scene_id}_{panel_id}.png"
                filepath = os.path.join(output_dir, filename)

                with open(filepath, 'wb') as f:
                    f.write(result.image_bytes)

                print(f"  ✓ Saved: {filename} ({len(result.image_bytes)} bytes)")
                results["successful"] += 1
                results["images"].append({
                    "panel_id": panel_id,
                    "scene_id": scene_id,
                    "filename": filename,
                    "success": True
                })
            else:
                print(f"  ✗ Failed: {result.error if hasattr(result, 'error') else 'Unknown error'}")
                results["failed"] += 1
                results["images"].append({
                    "panel_id": panel_id,
                    "scene_id": scene_id,
                    "success": False,
                    "error": getattr(result, 'error', 'Unknown error')
                })

        except Exception as e:
            print(f"  ✗ Error: {str(e)}")
            results["failed"] += 1
            results["images"].append({
                "panel_id": panel_id,
                "scene_id": scene_id,
                "success": False,
                "error": str(e)
            })

        # Rate limiting - small delay between requests
        if i < len(unique_prompts):
            import time
            time.sleep(2)

    # Summary
    print("\n" + "=" * 80)
    print("GENERATION COMPLETE")
    print("=" * 80)
    print(f"Successful: {results['successful']}")
    print(f"Failed: {results['failed']}")
    print(f"Total: {len(unique_prompts)}")
    print(f"Output directory: {output_dir}")

    return results

def main():
    """Main entry point."""
    # Paths
    project_id = "picture-of-dorian-gray-20260212-20260212"
    project_dir = f"output/projects/{project_id}"
    prompts_path = f"{project_dir}/intermediate/panel_prompts.json"
    output_dir = f"{project_dir}/output/panels"

    # Load prompts to count
    panels = load_panel_prompts(prompts_path)
    unique_prompts = {}
    for panel in panels:
        key = f"{panel['scene_id']}_{panel['panel_id']}"
        if key not in unique_prompts:
            unique_prompts[key] = panel

    # Get API key
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        print("ERROR: OPENROUTER_API_KEY not found in environment!")
        print("Please set it in .env file or export it:")
        print("  export OPENROUTER_API_KEY=your-api-key")
        sys.exit(1)

    print(f"\nUsing API key: {api_key[:10]}...{api_key[-5:]}")

    # Run generation
    results = generate_images_for_project(
        project_dir=project_dir,
        prompts_path=prompts_path,
        output_dir=output_dir,
        api_key=api_key,
        model="google/gemini-2.5-flash-image"
    )

    # Save results summary
    results_path = f"{project_dir}/output/stage6_results.json"
    with open(results_path, 'w') as f:
        json.dump({
            "project_id": project_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_panels": len(unique_prompts) if 'unique_prompts' in dir() else 0,
            "successful": results["successful"],
            "failed": results["failed"],
            "images": results["images"]
        }, f, indent=2)

    print(f"\nResults saved to: {results_path}")

    return 0 if results["failed"] == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
