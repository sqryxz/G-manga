#!/usr/bin/env python3
"""
Test Image Generation Setup - Stage 6.1.6
Verify that all image generation providers are properly configured.
"""

import sys
import os

# Add src to path
sys.path.insert(0, '/home/clawd/projects/g-manga/src')

from stage6_image_generation.providers import (
    ImageProviderFactory,
    ProviderRegistry,
    create_image_provider,
    DALLE3Provider,
    SDXLProvider,
    OpenRouterImageProvider,
    ImageSize,
    ImageQuality
)

from src.config import Settings


def test_provider_registry():
    """Test that all providers are registered."""
    print("=" * 70)
    print("Testing Provider Registry")
    print("=" * 70)
    
    print("\n[Test] Registered providers...")
    providers = ProviderRegistry.list_providers()
    print(f"✓ Registered: {providers}")
    
    expected = ["dalle3", "sdxl", "openrouter"]
    for provider in expected:
        if provider in providers:
            print(f"✓ {provider} is registered")
        else:
            print(f"✗ {provider} is NOT registered")
            return False
    
    return True


def test_provider_creation():
    """Test creating providers with fake API keys."""
    print("\n" + "=" * 70)
    print("Testing Provider Creation")
    print("=" * 70)
    
    # Test DALL-E 3
    print("\n[Test] Creating DALL-E 3 provider...")
    try:
        dalle = create_image_provider(
            provider_type="dalle3",
            api_key="fake-key-for-testing"
        )
        print("✓ DALL-E 3 provider created")
        info = dalle.get_provider_info()
        print(f"  Type: {info['provider_type']}")
        print(f"  Quality: {info['quality']}")
        print(f"  Default size: {info['default_size']}")
        print(f"  Cost: ${info['cost_per_image']:.2f}/image")
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False
    
    # Test SDXL
    print("\n[Test] Creating SDXL provider...")
    try:
        sdxl = create_image_provider(
            provider_type="sdxl",
            api_key="fake-key-for-testing"
        )
        print("✓ SDXL provider created")
        info = sdxl.get_provider_info()
        print(f"  Type: {info['provider_type']}")
        print(f"  Model: {sdxl.model}")
        print(f"  Cost: ${info['cost_per_image']:.2f}/image")
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False
    
    # Test OpenRouter
    print("\n[Test] Creating OpenRouter provider...")
    try:
        orouter = create_image_provider(
            provider_type="openrouter",
            api_key="fake-key-for-testing"
        )
        print("✓ OpenRouter provider created")
        info = orouter.get_provider_info()
        print(f"  Type: {info['provider_type']}")
        print(f"  Cost: ${info['cost_per_image']:.2f}/image")
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False
    
    return True


def test_configuration():
    """Test loading configuration."""
    print("\n" + "=" * 70)
    print("Testing Configuration")
    print("=" * 70)
    
    print("\n[Test] Loading settings from config.yaml...")
    try:
        settings = Settings.from_yaml("/home/clawd/projects/g-manga/config.yaml")
        print("✓ Settings loaded successfully")
        
        # Check image settings
        print(f"\n  Default provider: {settings.image.default_provider}")
        print(f"  DALL-E enabled: {settings.image.dalle.enabled}")
        print(f"  DALL-E model: {settings.image.dalle.model}")
        print(f"  DALL-E quality: {settings.image.dalle.quality}")
        print(f"  SDXL enabled: {settings.image.sdxl.enabled}")
        print(f"  SDXL model: {settings.image.sdxl.model}")
        print(f"  OpenRouter enabled: {settings.image.openrouter.enabled}")
        print(f"  OpenRouter default model: {settings.image.openrouter.default_model}")
        
        return True
    except Exception as e:
        print(f"✗ Failed to load configuration: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_key_validation():
    """Test API key validation."""
    print("\n" + "=" * 70)
    print("Testing API Key Validation")
    print("=" * 70)
    
    print("\n[Test] Checking environment variables for API keys...")
    validation = ImageProviderFactory.validate_api_keys()
    
    print("\n  Provider availability:")
    for provider, has_key in validation.items():
        status = "✓ Has key" if has_key else "✗ Missing key"
        env_var = ImageProviderFactory._get_env_var(provider)
        print(f"    {provider}: {status} (env: {env_var})")
    
    # Count how many we have
    available = sum(1 for v in validation.values() if v)
    print(f"\n  {available}/{len(validation)} providers have API keys configured")
    
    return True


def test_image_generation_capabilities():
    """Test that providers have correct capabilities."""
    print("\n" + "=" * 70)
    print("Testing Image Generation Capabilities")
    print("=" * 70)
    
    print("\n[Test] Checking provider capabilities...")
    
    # Test DALL-E 3
    try:
        dalle = create_image_provider(
            provider_type="dalle3",
            api_key="fake-key"
        )
        
        print("\n  DALL-E 3 capabilities:")
        print(f"    Sizes: {[str(s) for s in dalle.allowed_sizes]}")
        
        # Test cost estimation
        cost = dalle.estimate_cost(
            num_images=4,
            size=ImageSize.SQUARE_1024,
            quality=ImageQuality.HD
        )
        print(f"    Cost for 4 HD images: ${cost:.2f}")
        
        # Test validation
        valid_png = b'\x89PNG\r\n\x1a\n' + b'x' * 5000
        result = dalle.validate(valid_png, "test")
        print(f"    Validation score: {result.score:.2f}")
        
    except Exception as e:
        print(f"✗ DALL-E 3 test failed: {e}")
    
    # Test SDXL
    try:
        sdxl = create_image_provider(
            provider_type="sdxl",
            api_key="fake-key"
        )
        
        print("\n  SDXL capabilities:")
        print(f"    Default steps: {sdxl.default_steps}")
        print(f"    Default CFG scale: {sdxl.default_cfg_scale}")
        
        # Test cost estimation
        cost = sdxl.estimate_cost(
            num_images=4,
            size=ImageSize.SQUARE_1024,
            quality=ImageQuality.STANDARD
        )
        print(f"    Cost for 4 images: ${cost:.2f}")
        
    except Exception as e:
        print(f"✗ SDXL test failed: {e}")
    
    return True


def test_provider_factory():
    """Test the provider factory functions."""
    print("\n" + "=" * 70)
    print("Testing Provider Factory")
    print("=" * 70)
    
    print("\n[Test] Testing create_image_provider...")
    
    # Test creating provider with just type
    provider = create_image_provider(
        provider_type="dalle3",
        api_key="test-key"
    )
    print(f"✓ Created provider: {type(provider).__name__}")
    
    # Test creating from config
    from stage6_image_generation.providers.base import create_provider_config
    
    config = create_provider_config(
        provider_type="sdxl",
        api_key="test-key",
        max_retries=5
    )
    
    from stage6_image_generation.providers import ImageProviderFactory
    provider = ImageProviderFactory.create_from_config(config)
    print(f"✓ Created from config: {type(provider).__name__}")
    print(f"  Max retries: {provider.config.max_retries}")
    
    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("G-Manga Image Generation Setup Test")
    print("=" * 70)
    
    tests = [
        ("Provider Registry", test_provider_registry),
        ("Provider Creation", test_provider_creation),
        ("Configuration", test_configuration),
        ("API Key Validation", test_api_key_validation),
        ("Image Generation Capabilities", test_image_generation_capabilities),
        ("Provider Factory", test_provider_factory),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n✗ {name} failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    passed = 0
    failed = 0
    
    for name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"  {status}: {name}")
        if success:
            passed += 1
        else:
            failed += 1
    
    print(f"\n  Total: {passed + failed} tests")
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")
    
    if failed == 0:
        print("\n" + "=" * 70)
        print("All tests passed! ✓")
        print("=" * 70)
        print("\nTo use real image generation:")
        print("1. Set environment variables for API keys:")
        print("   - export OPENAI_API_KEY=your-key  # For DALL-E 3")
        print("   - export STABILITY_API_KEY=your-key  # For SDXL")
        print("   - export OPENROUTER_API_KEY=your-key  # For OpenRouter")
        print("2. Run: python -m stage6_image_generation.providers.factory")
        print("=" * 70)
        return 0
    else:
        print("\n" + "=" * 70)
        print("Some tests failed. Please check the output above.")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
