#!/usr/bin/env python3
"""
Stage 6: Image Generation using OpenRouter - Batch Mode
Generates manga panel images in batches to handle rate limits.
"""

import sys
import json
import os
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from stage6_image_generation.providers.openrouter import OpenRouterImageProvider
from stage6_image_generation.providers.base import ProviderConfig, ProviderType, ImageSize, ImageQuality

# Load environment variables
load_dotenv()

def load_panel_prompts(prompts_path: str) -> list:
    """Load panel prompts from JSON file."""
    with open(prompts_path, 'r') as f:
        return json.load(f)

def generate_images_batch(
    panels: list,
    output_dir: str,
    provider: OpenRouterImageProvider,
    start_index: int = 0,
    batch_size: int = 5
) -> tuple:
    """
    Generate images for a batch of panels.

    Returns:
        Tuple of (successful_count, failed_count, last_index)
    """
    successful = 0
    failed = 0
    last_index = start_index

    for i, panel in enumerate(panels[start_index:], start=start_index):
        panel_id = panel['panel_id']
        scene_id = panel['scene_id']
        prompt = panel['prompt']

        # Check if already generated
        filename = f"{scene_id}_{panel_id}.png"
        filepath = os.path.join(output_dir, filename)
        if os.path.exists(filepath):
            print(f"[{i+1}/{len(panels)}] Skipping (exists): {scene_id} - {panel_id}")
            successful += 1
            last_index = i + 1
            continue

        print(f"[{i+1}/{len(panels)}] Generating: {scene_id} - {panel_id}")

        try:
            result = provider.generate(
                prompt=prompt,
                size=ImageSize.SQUARE_1024,
                quality=ImageQuality.STANDARD,
                timeout=120
            )

            if result.success and result.image_bytes:
                with open(filepath, 'wb') as f:
                    f.write(result.image_bytes)
                print(f"  ✓ Saved: {filename} ({len(result.image_bytes)} bytes)")
                successful += 1
            else:
                error = getattr(result, 'error', 'Unknown error')
                print(f"  ✗ Failed: {error}")
                failed += 1

        except Exception as e:
            print(f"  ✗ Error: {str(e)}")
            failed += 1

        last_index = i + 1

        # Rate limiting between requests
        if i < len(panels) - 1:
            time.sleep(3)

    return successful, failed, last_index

def main():
    """Main entry point."""
    # Paths
    project_id = "picture-of-dorian-gray-20260212-20260212"
    project_dir = f"output/projects/{project_id}"
    prompts_path = f"{project_dir}/intermediate/panel_prompts.json"
    output_dir = f"{project_dir}/output/panels"

    # Get API key
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        print("ERROR: OPENROUTER_API_KEY not found!")
        sys.exit(1)

    print(f"API Key: {api_key[:10]}...{api_key[-5:]}")

    # Load prompts
    print(f"\nLoading prompts from: {prompts_path}")
    all_panels = load_panel_prompts(prompts_path)
    print(f"Total panels: {len(all_panels)}")

    # Get unique panels
    unique_panels = []
    seen = set()
    for panel in all_panels:
        key = f"{panel['scene_id']}_{panel['panel_id']}"
        if key not in seen:
            unique_panels.append(panel)
            seen.add(key)

    print(f"Unique panels: {len(unique_panels)}")

    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Count existing images
    existing_images = [f for f in os.listdir(output_dir) if f.endswith('.png')]
    print(f"Existing images: {len(existing_images)}")

    # Create provider
    config = ProviderConfig(
        provider_type=ProviderType.SDXL,
        api_key=api_key,
        default_size=ImageSize.SQUARE_1024,
        quality=ImageQuality.STANDARD,
        rate_limit=10,
        cost_per_image=0.02,
        max_retries=2,
        timeout=120
    )

    provider = OpenRouterImageProvider(config, model="google/gemini-2.5-flash-image")

    # Find starting index (first missing image)
    start_index = 0
    for i, panel in enumerate(unique_panels):
        filename = f"{panel['scene_id']}_{panel['panel_id']}.png"
        if not os.path.exists(os.path.join(output_dir, filename)):
            start_index = i
            break

    print(f"\nStarting from index: {start_index}")

    # Generate remaining images
    print("\n" + "=" * 80)
    print("GENERATING IMAGES")
    print("=" * 80)

    total_successful = 0
    total_failed = 0

    # Process in batches with pauses
    batch_size = 3
    while start_index < len(unique_panels):
        end_index = min(start_index + batch_size, len(unique_panels))

        print(f"\n--- Batch {start_index//batch_size + 1}: panels {start_index+1} to {end_index} ---")

        successful, failed, last_index = generate_images_batch(
            panels=unique_panels,
            output_dir=output_dir,
            provider=provider,
            start_index=start_index,
            batch_size=batch_size
        )

        total_successful += successful
        total_failed += failed
        start_index = last_index

        # Pause between batches
        if start_index < len(unique_panels):
            print("\nPausing 30 seconds before next batch...")
            time.sleep(30)

    # Final count
    final_count = len([f for f in os.listdir(output_dir) if f.endswith('.png')])

    print("\n" + "=" * 80)
    print("GENERATION COMPLETE")
    print("=" * 80)
    print(f"Total panels: {len(unique_panels)}")
    print(f"Generated: {final_count}")
    print(f"Output: {output_dir}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
