#!/usr/bin/env python3
"""
Quick Integration Test - Image Generation
Tests basic image generation functionality.
"""

import sys
import os

sys.path.insert(0, '/home/clawd/projects/g-manga/src')

from stage6_image_generation.providers import create_image_provider
from stage6_image_generation.providers.base import ImageSize, ImageQuality


def test_provider_creation(provider_type):
    """Test creating a provider."""
    print(f"\n{'='*60}")
    print(f"Testing {provider_type.upper()} Provider")
    print(f"{'='*60}")
    
    # Create provider with fake key for testing
    try:
        provider = create_image_provider(
            provider_type,
            api_key="fake-key-for-testing"
        )
        print(f"✓ Provider created: {type(provider).__name__}")
    except Exception as e:
        print(f"✗ Failed to create provider: {e}")
        return None
    
    return provider


def test_cost_estimation(provider):
    """Test cost estimation."""
    print(f"\n[Test] Cost estimation...")
    
    cost = provider.estimate_cost(
        num_images=4,
        size=ImageSize.SQUARE_1024,
        quality=ImageQuality.HD
    )
    
    print(f"  4 HD images at {provider.provider_type.value}: ${cost:.2f}")
    return cost


def test_validation(provider):
    """Test image validation."""
    print(f"\n[Test] Image validation...")
    
    # Test with valid PNG
    valid_png = b'\x89PNG\r\n\x1a\n' + b'x' * 5000
    result = provider.validate(valid_png, "test prompt")
    print(f"  Valid PNG - Valid: {result.is_valid}, Score: {result.score:.2f}")
    
    # Test with invalid image
    invalid = b"not an image"
    result = provider.validate(invalid, "test prompt")
    print(f"  Invalid image - Valid: {result.is_valid}, Score: {result.score:.2f}")
    
    return result


def test_mock_generation(provider):
    """Test mock generation (won't actually call API without real key)."""
    print(f"\n[Test] Mock generation test...")
    
    # This will fail without real API key, but tests the flow
    result = provider.generate(
        prompt="A manga panel with a heroic character",
        size=ImageSize.SQUARE_1024,
        quality=ImageQuality.HD
    )
    
    if result.success:
        print(f"  ✓ Generation successful!")
        print(f"  Image size: {len(result.image_bytes)} bytes")
        print(f"  Format: {result.image_format}")
        print(f"  Cost: ${result.cost:.2f}")
    else:
        print(f"  ✗ Generation failed (expected without real API key)")
        print(f"  Error: {result.error}")
        print(f"  (This is expected - set API key to test real generation)")
    
    return result


def main():
    """Run integration tests."""
    print("\n" + "="*60)
    print("G-Manga Image Generation - Integration Test")
    print("="*60)
    
    providers_to_test = ["dalle3", "sdxl", "openrouter"]
    
    for provider_type in providers_to_test:
        provider = test_provider_creation(provider_type)
        
        if provider:
            test_cost_estimation(provider)
            test_validation(provider)
            test_mock_generation(provider)
    
    print("\n" + "="*60)
    print("Integration Test Complete")
    print("="*60)
    print("\nTo test real image generation:")
    print("1. Set API key: export OPENAI_API_KEY=your-key")
    print("2. Run: python3 -c 'from providers import create_image_provider; p = create_image_provider(\"dalle3\"); r = p.generate(\"test\"); print(r.success)'")
    print("\n" + "="*60)


if __name__ == "__main__":
    main()
