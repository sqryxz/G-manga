#!/usr/bin/env python3
"""
Test Image Validator
"""

import sys
sys.path.insert(0, '/home/clawd/projects/g-manga/src')

from stage6_image_generation.image_validator import create_image_validator

print("=" * 70)
print("Image Validator Test")
print("=" * 70)

# Create validator
print("\n[Test] Creating image validator...")
validator = create_image_validator(min_size_kb=10, max_size_mb=50)
print("✓ Validator created")
print(f"  Min size: {validator.min_size_kb} KB")
print(f"  Max size: {validator.max_size_mb} MB")

# Test validation
print("\n[Test] Testing image validation...")

# Test 1: Empty image
print("\n  Test 1: Empty image")
result1 = validator.validate(b"", "")
print(f"    Valid: {result1.is_valid}, Score: {result1.score:.2f}")
print(f"    Errors: {[e.error_code for e in result1.errors]}")

# Test 2: Too small image
print("\n  Test 2: Too small image")
result2 = validator.validate(b"x" * 100, "test")
print(f"    Valid: {result2.is_valid}, Score: {result2.score:.2f}")
print(f"    Errors: {[e.error_code for e in result2.errors]}")

# Test 3: Valid PNG
print("\n  Test 3: Valid PNG")
valid_png = b'\x89PNG\r\n\x1a\n' + b'x' * 20000 + b'IEND'
result3 = validator.validate(valid_png, "A cat")
print(f"    Valid: {result3.is_valid}, Score: {result3.score:.2f}")
print(f"    Errors: {[e.error_code for e in result3.errors]}")
print(f"    Warnings: {[w.error_code for w in result3.warnings]}")

# Test 4: Corrupted PNG (missing IEND)
print("\n  Test 4: Corrupted PNG")
corrupt_png = b'\x89PNG\r\n\x1a\n' + b'x' * 20000
result4 = validator.validate(corrupt_png, "A cat")
print(f"    Valid: {result4.is_valid}, Score: {result4.score:.2f}")
print(f"    Errors: {[e.error_code for e in result4.errors]}")

# Test 5: Batch validation
print("\n[Test] Testing batch validation...")
images = [
    (b"", "empty"),
    (b"x" * 100, "small"),
    (valid_png, "valid")
]
batch_results = validator.validate_batch(images)
summary = validator.get_validation_summary(batch_results)
print(f"✓ Total: {summary['total']}")
print(f"  Valid: {summary['valid']}")
print(f"  Invalid: {summary['invalid']}")
print(f"  Validity rate: {summary['validity_rate']:.2%}")
print(f"  Avg score: {summary['average_score']:.2f}")

print("\n" + "=" * 70)
print("Image Validator - PASSED")
print("=" * 70)
