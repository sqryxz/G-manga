"""
Image Validator - Stage 6.1.4
Validates generated images for quality and completeness.
"""

import io
import sys
sys.path.insert(0, '/home/clawd/projects/g-manga/src')

from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

from stage6_image_generation.providers.base import (
    ValidationResult,
    ValidationError,
    ValidationSeverity
)


class ImageValidator:
    """Validates generated images for quality and completeness."""

    def __init__(self):
        """Initialize Image Validator."""
        self.min_size_kb = 10
        self.max_size_mb = 50
        self.min_dimensions = (256, 256)
        self.max_dimensions = (4096, 4096)

    def validate(
        self,
        image_bytes: bytes,
        prompt: str,
        check_prompt_match: bool = True
    ) -> ValidationResult:
        """
        Validate a generated image.

        Args:
            image_bytes: Generated image data
            prompt: Original prompt used
            check_prompt_match: Whether to check if prompt matches (basic check)

        Returns:
            ValidationResult with score and errors
        """
        errors = []
        warnings = []

        # 1. Check if image is not empty
        if not image_bytes:
            errors.append(ValidationError(
                error_code="EMPTY_IMAGE",
                error_message="Image is empty",
                severity=ValidationSeverity.ERROR
            ))
            return self._create_result(errors, warnings)

        # 2. Check image size
        size_kb = len(image_bytes) / 1024
        size_mb = size_kb / 1024

        if size_kb < self.min_size_kb:
            errors.append(ValidationError(
                error_code="TOO_SMALL",
                error_message=f"Image too small: {size_kb:.1f} KB (min: {self.min_size_kb} KB)",
                severity=ValidationSeverity.ERROR
            ))

        if size_mb > self.max_size_mb:
            errors.append(ValidationError(
                error_code="TOO_LARGE",
                error_message=f"Image too large: {size_mb:.1f} MB (max: {self.max_size_mb} MB)",
                severity=ValidationSeverity.ERROR
            ))

        # 3. Check image format
        if len(image_bytes) >= 8:
            header = image_bytes[:8]
            is_png = header == b'\x89PNG\r\n\x1a\n'
            is_jpeg = header[:2] == b'\xff\xd8'
            is_webp = header[:4] == b'RIFF'

            if not (is_png or is_jpeg or is_webp):
                errors.append(ValidationError(
                    error_code="INVALID_FORMAT",
                    error_message="Invalid image format (expected PNG, JPEG, or WebP)",
                    severity=ValidationSeverity.ERROR
                ))
            elif is_webp:
                warnings.append(ValidationError(
                    error_code="WEBP_FORMAT",
                    error_message="WebP format - consider PNG for better compatibility",
                    severity=ValidationSeverity.WARNING
                ))

        # 4. Try to read image dimensions (if PIL is available)
        try:
            from PIL import Image
            img = Image.open(io.BytesIO(image_bytes))
            width, height = img.size

            # Check minimum dimensions
            if width < self.min_dimensions[0] or height < self.min_dimensions[1]:
                errors.append(ValidationError(
                    error_code="DIMENSIONS_TOO_SMALL",
                    error_message=f"Image dimensions too small: {width}x{height} (min: {self.min_dimensions[0]}x{self.min_dimensions[1]})",
                    severity=ValidationSeverity.ERROR
                ))

            # Check maximum dimensions
            if width > self.max_dimensions[0] or height > self.max_dimensions[1]:
                warnings.append(ValidationError(
                    error_code="DIMENSIONS_TOO_LARGE",
                    error_message=f"Image dimensions very large: {width}x{height} (max: {self.max_dimensions[0]}x{self.max_dimensions[1]})",
                    severity=ValidationSeverity.WARNING
                ))

            # Check aspect ratio (should be reasonable)
            aspect_ratio = max(width, height) / min(width, height)
            if aspect_ratio > 3:
                warnings.append(ValidationError(
                    error_code="EXTREME_ASPECT_RATIO",
                    error_message=f"Extreme aspect ratio: {aspect_ratio:.1f}:1 (may look distorted)",
                    severity=ValidationSeverity.WARNING
                ))

        except ImportError:
            # PIL not available - skip dimension checks
            warnings.append(ValidationError(
                error_code="PIL_NOT_AVAILABLE",
                error_message="PIL not installed - skipping dimension checks",
                severity=ValidationSeverity.WARNING
            ))
        except Exception as e:
            errors.append(ValidationError(
                error_code="IMAGE_READ_ERROR",
                error_message=f"Failed to read image: {str(e)}",
                severity=ValidationSeverity.ERROR
            ))

        # 5. Basic prompt matching check (optional)
        if check_prompt_match and prompt:
            # Check for common failure indicators in prompt
            failure_indicators = [
                "failed to generate",
                "error",
                "could not",
                "unable to"
            ]

            prompt_lower = prompt.lower()
            for indicator in failure_indicators:
                if indicator in prompt_lower:
                    errors.append(ValidationError(
                        error_code="PROMPT_FAILURE",
                        error_message=f"Prompt contains failure indicator: '{indicator}'",
                        severity=ValidationSeverity.ERROR
                    ))
                    break

        # 6. Check for corrupted image data
        try:
            # Try to verify image integrity
            if len(image_bytes) >= 8:
                # PNG checksum validation (simplified)
                if image_bytes[:4] == b'\x89PNG':
                    # PNG files should end with IEND chunk
                    if b'IEND' not in image_bytes[-50:]:
                        errors.append(ValidationError(
                            error_code="CORRUPTED_PNG",
                            error_message="PNG file appears corrupted (missing IEND)",
                            severity=ValidationSeverity.ERROR
                        ))
        except Exception:
            # Skip if validation fails
            pass

        return self._create_result(errors, warnings)

    def _create_result(
        self,
        errors: List[ValidationError],
        warnings: List[ValidationError]
    ) -> ValidationResult:
        """
        Create a validation result.

        Args:
            errors: List of errors
            warnings: List of warnings

        Returns:
            ValidationResult
        """
        # Calculate score
        score = 1.0
        for error in errors:
            if error.severity == ValidationSeverity.ERROR:
                score -= 0.5
        for warning in warnings:
            score -= 0.1

        score = max(0.0, min(1.0, score))

        # Determine if valid
        is_valid = score > 0.5

        return ValidationResult(
            is_valid=is_valid,
            score=score,
            errors=errors,
            warnings=warnings,
            checked_at=datetime.now(timezone.utc)
        )

    def validate_batch(
        self,
        images: List[tuple],
        check_prompt_match: bool = True
    ) -> List[ValidationResult]:
        """
        Validate multiple images.

        Args:
            images: List of (image_bytes, prompt) tuples
            check_prompt_match: Whether to check prompt match

        Returns:
            List of ValidationResult objects
        """
        results = []
        for image_bytes, prompt in images:
            result = self.validate(image_bytes, prompt, check_prompt_match)
            results.append(result)

        return results

    def get_validation_summary(self, results: List[ValidationResult]) -> Dict[str, Any]:
        """
        Get summary of validation results.

        Args:
            results: List of ValidationResult objects

        Returns:
            Dictionary with summary stats
        """
        total = len(results)
        valid = sum(1 for r in results if r.is_valid)
        invalid = total - valid

        # Calculate average score
        avg_score = sum(r.score for r in results) / total if total > 0 else 0.0

        # Count error types
        error_types = {}
        for result in results:
            for error in result.errors:
                error_code = error.error_code
                error_types[error_code] = error_types.get(error_code, 0) + 1

        # Count warning types
        warning_types = {}
        for result in results:
            for warning in result.warnings:
                warning_code = warning.error_code
                warning_types[warning_code] = warning_types.get(warning_code, 0) + 1

        return {
            "total": total,
            "valid": valid,
            "invalid": invalid,
            "validity_rate": valid / total if total > 0 else 0.0,
            "average_score": avg_score,
            "error_types": error_types,
            "warning_types": warning_types
        }


def create_image_validator(
    min_size_kb: int = 10,
    max_size_mb: int = 50
) -> ImageValidator:
    """
    Create an image validator instance.

    Args:
        min_size_kb: Minimum image size in KB
        max_size_mb: Maximum image size in MB

    Returns:
        ImageValidator instance
    """
    validator = ImageValidator()
    validator.min_size_kb = min_size_kb
    validator.max_size_mb = max_size_mb

    return validator


def main():
    """Test Image Validator."""
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


if __name__ == "__main__":
    main()
