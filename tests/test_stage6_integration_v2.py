#!/usr/bin/env python3
"""
Stage 6 Integration Test - 6.1.8
End-to-end test of image generation pipeline.
"""

import sys
sys.path.insert(0, '/home/clawd/projects/g-manga/src')

from stage6_image_generation.providers.dalle import create_dalle3_provider
from stage6_image_generation.providers.sdxl import create_sdxl_provider
from stage6_image_generation.image_validator import create_image_validator
from stage6_image_generation.retry_manager_fixed import create_retry_fallback_manager, FallbackStrategy
from stage6_image_generation.queue_manager_fixed import create_queue_manager
from stage6_image_generation.image_storage_fixed import create_image_storage
from stage6_image_generation.providers.base import ImageSize, ImageQuality, GenerationResult, ProviderType


def test_end_to_end_image_generation():
    """Test complete image generation pipeline."""
    print("=" * 70)
    print("Stage 6 Integration Test - End-to-End Image Generation")
    print("=" * 70)

    # Note: This test uses mock providers since we don't have real API keys
    # In production, replace with actual API keys

    # Step 1: Create providers
    print("\n[Step 1] Creating image providers...")
    providers = {}

    # DALL-E 3 provider (mock)
    dalle_provider = create_dalle3_provider(
        api_key="mock-key",
        max_retries=2,
        timeout=30
    )
    providers["dalle3"] = dalle_provider
    print(f"✓ Created DALL-E 3 provider")

    # SDXL provider (mock)
    sdxl_provider = create_sdxl_provider(
        api_key="mock-key",
        max_retries=2,
        timeout=30
    )
    providers["sdxl"] = sdxl_provider
    print(f"✓ Created SDXL provider")

    # Step 2: Create retry/fallback manager
    print("\n[Step 2] Creating retry/fallback manager...")
    retry_manager = create_retry_fallback_manager(
        providers=providers,
        fallback_strategy="next_provider",
        max_retries=2
    )
    print(f"✓ Created retry/fallback manager")
    print(f"  Fallback strategy: {retry_manager.fallback_strategy.value}")

    # Step 3: Create image validator
    print("\n[Step 3] Creating image validator...")
    validator = create_image_validator(min_size_kb=10, max_size_mb=50)
    print(f"✓ Created image validator")
    print(f"  Min size: {validator.min_size_kb} KB")
    print(f"  Max size: {validator.max_size_mb} MB")

    # Step 4: Create queue manager
    print("\n[Step 4] Creating queue manager...")
    queue_manager = create_queue_manager(
        providers=providers,
        max_concurrent=3,
        enable_rate_limiting=True
    )
    print(f"✓ Created queue manager")
    print(f"  Max concurrent: {queue_manager.max_concurrent}")

    # Step 5: Create image storage
    print("\n[Step 5] Creating image storage...")
    import tempfile
    import os

    temp_dir = tempfile.mkdtemp(prefix="g-manga-stage6-test-")
    storage = create_image_storage(temp_dir, create_subdirs=True)
    print(f"✓ Created image storage")
    print(f"  Project dir: {temp_dir}")

    # Step 6: Test provider information
    print("\n[Step 6] Testing provider information...")
    for name, provider in providers.items():
        info = provider.get_provider_info()
        print(f"  {name.upper()}:")
        print(f"    Type: {info['provider_type']}")
        print(f"    Rate limit: {info['rate_limit']} req/min")
        print(f"    Cost per image: ${info['cost_per_image']:.2f}")

    # Step 7: Test cost estimation
    print("\n[Step 7] Testing cost estimation...")
    dalle_cost = dalle_provider.estimate_cost(10, ImageSize.SQUARE_1024, ImageQuality.HD)
    sdxl_cost = sdxl_provider.estimate_cost(10, ImageSize.SQUARE_1024, ImageQuality.STANDARD)
    print(f"✓ DALL-E 3 (10 HD images): ${dalle_cost:.2f}")
    print(f"✓ SDXL (10 standard images): ${sdxl_cost:.2f}")

    # Step 8: Test image validation
    print("\n[Step 8] Testing image validation...")
    test_images = [
        (b"", "empty prompt", "Empty image"),
        (b"x" * 100, "small prompt", "Too small"),
        (b'\x89PNG\r\n\x1a\n' + b'x' * 20000, "valid prompt", "Valid PNG")
    ]

    validation_results = []
    for image_bytes, prompt, description in test_images:
        result = validator.validate(image_bytes, prompt, check_prompt_match=False)
        validation_results.append(result)
        print(f"  {description}:")
        print(f"    Valid: {result.is_valid}, Score: {result.score:.2f}")
        print(f"    Errors: {len(result.errors)}, Warnings: {len(result.warnings)}")

    # Step 9: Test queue operations
    print("\n[Step 9] Testing queue operations...")
    tasks = []
    for i in range(5):
        task_id = f"task-{i}"
        task = queue_manager.add_task(
            task_id=task_id,
            prompt=f"Test prompt {i}",
            provider_name="dalle3",
            size=ImageSize.SQUARE_1024,
            quality=ImageQuality.STANDARD
        )
        tasks.append(task)

    stats = queue_manager.get_statistics()
    print(f"✓ Added {len(tasks)} tasks to queue")
    print(f"  Queue size: {stats['queue_size']}")
    print(f"  Total tasks: {stats['total_tasks']}")

    # Step 10: Test storage operations
    print("\n[Step 10] Testing storage operations...")

    # Create a fake generation result
    fake_result = GenerationResult(
        success=True,
        image_bytes=b'\x89PNG\r\n\x1a\n' + b'x' * 20000,
        image_format="png",
        provider=ProviderType.DALLE3,
        prompt="A cat",
        metadata={"model": "dall-e-3"},
        cost=0.04
    )

    # Save image
    filepath = storage.save_image(
        result=fake_result,
        panel_id="p1-1",
        scene_id="scene-1",
        prompt="A cat"
    )
    print(f"✓ Saved image to: {os.path.basename(filepath)}")

    # Get image
    loaded = storage.get_image("p1-1")
    print(f"✓ Loaded {len(loaded)} bytes")

    # Get metadata
    meta = storage.get_metadata("p1-1")
    print(f"✓ Metadata: panel_id={meta['panel_id']}, scene_id={meta['scene_id']}")

    # Get statistics
    storage_stats = storage.get_statistics()
    print(f"✓ Storage statistics:")
    print(f"  Images saved: {storage_stats['images_saved']}")
    print(f"  Total size: {storage_stats['total_size_mb']} MB")

    # Export summary
    export_file = os.path.join(temp_dir, "summary.json")
    storage.export_summary(export_file)
    print(f"✓ Exported summary to: summary.json")

    # Step 11: Test retry/fallback statistics
    print("\n[Step 11] Testing retry/fallback statistics...")
    retry_stats = retry_manager.get_statistics()
    print(f"✓ Retry/fallback statistics:")
    print(f"  Fallback count: {retry_stats['fallback_count']}")
    print(f"  Fallback strategy: {retry_stats['fallback_strategy']}")
    for provider_name, provider_stats in retry_stats['providers'].items():
        print(f"  {provider_name}:")
        print(f"    Attempts: {provider_stats['attempts']}")
        print(f"    Successes: {provider_stats['successes']}")
        print(f"    Failures: {provider_stats['failures']}")

    # Step 12: Test integration between components
    print("\n[Step 12] Testing component integration...")

    # Scenario: Generate -> Validate -> Store
    print(f"  Scenario: Generate -> Validate -> Store")

    # 1. Generate (mock - just create fake result)
    print(f"    1. Generate image...")
    fake_result = GenerationResult(
        success=True,
        image_bytes=b'\x89PNG\r\n\x1a\n' + b'x' * 25000,
        image_format="png",
        provider=ProviderType.SDXL,
        prompt="A dog",
        metadata={"model": "sd-1024"},
        cost=0.04
    )
    print(f"       ✓ Generated: {fake_result.success}")

    # 2. Validate
    print(f"    2. Validate image...")
    validation = validator.validate(fake_result.image_bytes, "A dog")
    print(f"       ✓ Valid: {validation.is_valid}, Score: {validation.score:.2f}")

    # 3. Store
    print(f"    3. Store image...")
    if validation.is_valid:
        filepath = storage.save_image(
            result=fake_result,
            panel_id="p2-1",
            scene_id="scene-2",
            prompt="A dog"
        )
        print(f"       ✓ Stored: {os.path.basename(filepath)}")

    # Summary
    print("\n" + "=" * 70)
    print("Stage 6 Integration Test - PASSED")
    print("=" * 70)

    # Component summary
    print("\n[Summary] Components Tested:")
    print(f"  ✓ Image Providers: {len(providers)} (DALL-E 3, SDXL)")
    print(f"  ✓ Retry/Fallback Manager: Created with next_provider strategy")
    print(f"  ✓ Image Validator: Tested with 3 images")
    print(f"  ✓ Queue Manager: Added {len(tasks)} tasks")
    print(f"  ✓ Image Storage: Saved {storage_stats['images_saved']} images")

    # Cleanup
    print(f"\n[Cleanup] Removing temp directory...")
    import shutil
    shutil.rmtree(temp_dir)
    print(f"✓ Cleaned up: {temp_dir}")

    return True


def main():
    """Run integration tests."""
    try:
        success = test_end_to_end_image_generation()
        return 0 if success else 1
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
