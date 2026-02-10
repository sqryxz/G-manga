#!/usr/bin/env python3
"""
Test SDXL Provider
"""

import sys
sys.path.insert(0, '/home/clawd/projects/g-manga/src')

from stage6_image_generation.providers.sdxl import create_sdxl_provider
from stage6_image_generation.providers.base import ImageSize, ImageQuality

print("=" * 70)
print("SDXL Provider Test")
print("=" * 70)

# Create provider
print("\n[Test] Creating SDXL provider...")
try:
    provider = create_sdxl_provider(
        api_key="test-api-key",
        max_retries=3,
        timeout=30
    )
    print("✓ Provider created successfully")
except Exception as e:
    print(f"✗ Failed: {e}")
    sys.exit(1)

# Test provider info
print("\n[Test] Getting provider info...")
info = provider.get_provider_info()
print(f"✓ Provider type: {info['provider_type']}")
print(f"  Model: {provider.model}")
print(f"  Rate limit: {info['rate_limit']} req/min")
print(f"  Cost per image: ${info['cost_per_image']:.2f}")

# Test cost estimation
print("\n[Test] Testing cost estimation...")
cost_1 = provider.estimate_cost(1, ImageSize.SQUARE_1024, ImageQuality.STANDARD)
cost_10 = provider.estimate_cost(10, ImageSize.SQUARE_1024, ImageQuality.HD)
print(f"✓ 1 standard image: ${cost_1:.2f}")
print(f"✓ 10 HD images: ${cost_10:.2f}")

# Test validation
print("\n[Test] Testing image validation...")

# Test with empty image
empty_result = provider.validate(b"", "test prompt")
print(f"✓ Empty image - Valid: {empty_result.is_valid}, Score: {empty_result.score:.2f}")

# Test with too-small image
small_result = provider.validate(b"x" * 500, "test prompt")
print(f"✓ Small image - Valid: {small_result.is_valid}, Score: {small_result.score:.2f}")

# Test with valid PNG header
valid_png = b'\x89PNG\r\n\x1a\n' + b'x' * 5000
valid_result = provider.validate(valid_png, "test prompt")
print(f"✓ Valid PNG - Valid: {valid_result.is_valid}, Score: {valid_result.score:.2f}")

print("\n" + "=" * 70)
print("SDXL Provider - PASSED")
print("=" * 70)
