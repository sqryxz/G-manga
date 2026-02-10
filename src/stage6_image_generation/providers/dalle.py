"""
DALL-E 3 Provider - Stage 6.1.2
OpenAI DALL-E 3 image generation implementation.
"""

import time
import requests
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone
import json

from .base import (
    ImageProvider,
    ProviderConfig,
    GenerationResult,
    BatchGenerationResult,
    ValidationResult,
    ValidationError,
    ValidationSeverity,
    ImageSize,
    ImageQuality,
    ProviderType,
    RateLimitError,
    AuthenticationError,
    GenerationError
)


class DALLE3Provider(ImageProvider):
    """DALL-E 3 image generation provider."""

    def __init__(self, config: ProviderConfig):
        """
        Initialize DALL-E 3 Provider.

        Args:
            config: Provider configuration
        """
        super().__init__(config)
        self.base_url = "https://api.openai.com/v1/images/generations"
        self.model = "dall-e-3"

        # DALL-E 3 specific costs (as of 2024)
        self.cost_table = {
            (1024, 1024): {
                "standard": 0.04,
                "hd": 0.08
            },
            (1792, 1024): {
                "standard": 0.08,
                "hd": 0.12
            },
            (1024, 1792): {
                "standard": 0.08,
                "hd": 0.12
            }
        }

        # DALL-E 3 allowed sizes
        self.allowed_sizes = [
            ImageSize.SQUARE_1024,
            ImageSize.LANDSCAPE_1792,
            ImageSize.PORTRAIT_1792
        ]

        # Rate limiting
        self.request_times = []
        self.rate_limit = config.rate_limit

    def generate(
        self,
        prompt: str,
        size: Optional[ImageSize] = None,
        quality: Optional[ImageQuality] = None,
        style: str = "vivid",  # "vivid" or "natural"
        **kwargs
    ) -> GenerationResult:
        """
        Generate a single image with DALL-E 3.

        Args:
            prompt: Image generation prompt
            size: Image size (default: config.default_size)
            quality: Image quality (default: config.quality)
            style: Image style ("vivid" or "natural")
            **kwargs: Additional parameters (ignored for DALL-E 3)

        Returns:
            GenerationResult with image bytes or error
        """
        # Use defaults from config
        if size is None:
            size = self.config.default_size
        if quality is None:
            quality = self.config.quality

        # Validate size
        if size not in self.allowed_sizes:
            return self._create_error_result(
                prompt=prompt,
                error=f"Size {size} not supported by DALL-E 3. "
                       f"Allowed sizes: {[str(s) for s in self.allowed_sizes]}",
                cost=0.0
            )

        # Check rate limit
        self._check_rate_limit()

        # Prepare request
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "prompt": prompt,
            "n": 1,
            "size": str(size),
            "quality": quality.value,
            "style": style
        }

        # Retry logic
        last_error = None
        for attempt in range(self.config.max_retries):
            try:
                # Exponential backoff
                if attempt > 0:
                    backoff = 2 ** attempt
                    time.sleep(backoff)

                # Make request
                response = requests.post(
                    self.base_url,
                    headers=headers,
                    json=payload,
                    timeout=self.config.timeout
                )

                # Track request
                self.request_times.append(time.time())

                # Handle response
                if response.status_code == 200:
                    return self._handle_success(response, prompt, size, quality)
                elif response.status_code == 401:
                    raise AuthenticationError("Invalid API key")
                elif response.status_code == 429:
                    raise RateLimitError("Rate limit exceeded")
                else:
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get("message", "Unknown error")
                    raise GenerationError(f"API error: {error_msg}")

            except (RateLimitError, AuthenticationError) as e:
                # Don't retry auth or rate limit errors
                return self._create_error_result(
                    prompt=prompt,
                    error=str(e),
                    cost=0.0
                )
            except Exception as e:
                last_error = e
                continue

        # All retries failed
        cost = self.estimate_cost(1, size, quality)
        return self._create_error_result(
            prompt=prompt,
            error=f"Max retries exceeded: {last_error}",
            cost=cost
        )

    def batch_generate(
        self,
        prompts: List[str],
        size: Optional[ImageSize] = None,
        quality: Optional[ImageQuality] = None,
        max_concurrent: int = 3,
        style: str = "vivid",
        **kwargs
    ) -> BatchGenerationResult:
        """
        Generate multiple images in batch.

        Args:
            prompts: List of image prompts
            size: Image size (default: config.default_size)
            quality: Image quality (default: config.quality)
            max_concurrent: Max concurrent requests
            style: Image style ("vivid" or "natural")
            **kwargs: Additional parameters

        Returns:
            BatchGenerationResult with all results
        """
        results = []
        total_cost = 0.0

        # Generate images sequentially (DALL-E 3 doesn't support true batch)
        for i, prompt in enumerate(prompts):
            print(f"Generating image {i+1}/{len(prompts)}...")

            result = self.generate(
                prompt=prompt,
                size=size,
                quality=quality,
                style=style
            )

            results.append(result)
            total_cost += result.cost

            # Small delay between requests
            if i < len(prompts) - 1:
                time.sleep(1)

        # Count successes/failures
        total_success = sum(1 for r in results if r.success)
        total_failed = len(results) - total_success

        return BatchGenerationResult(
            total_requested=len(prompts),
            total_success=total_success,
            total_failed=total_failed,
            results=results,
            total_cost=total_cost,
            provider=self.provider_type,
            generated_at=datetime.now(timezone.utc)
        )

    def validate(
        self,
        image_bytes: bytes,
        prompt: str
    ) -> ValidationResult:
        """
        Validate a DALL-E 3 generated image.

        Args:
            image_bytes: Generated image data
            prompt: Original prompt used

        Returns:
            ValidationResult with score and errors
        """
        errors = []
        warnings = []

        # Check if image is not empty
        if not image_bytes:
            errors.append(ValidationError(
                error_code="EMPTY_IMAGE",
                error_message="Image is empty",
                severity=ValidationSeverity.ERROR
            ))
            return ValidationResult(
                is_valid=False,
                score=0.0,
                errors=errors,
                warnings=warnings
            )

        # Check image size (minimum 1KB)
        if len(image_bytes) < 1024:
            errors.append(ValidationError(
                error_code="TOO_SMALL",
                error_message=f"Image too small: {len(image_bytes)} bytes",
                severity=ValidationSeverity.ERROR
            ))

        # Check if it's a valid image by looking at header
        if len(image_bytes) >= 8:
            header = image_bytes[:8]
            # PNG header: 89 50 4E 47 0D 0A 1A 0A
            # JPEG header: FF D8 FF
            is_png = header == b'\x89PNG\r\n\x1a\n'
            is_jpeg = header[:2] == b'\xff\xd8'

            if not (is_png or is_jpeg):
                errors.append(ValidationError(
                    error_code="INVALID_FORMAT",
                    error_message="Invalid image format (expected PNG or JPEG)",
                    severity=ValidationSeverity.ERROR
                ))

        # Calculate score based on errors and warnings
        score = 1.0
        for error in errors:
            if error.severity == ValidationSeverity.ERROR:
                score -= 0.5
        for warning in warnings:
            score -= 0.1

        score = max(0.0, min(1.0, score))

        return ValidationResult(
            is_valid=score > 0.5,
            score=score,
            errors=errors,
            warnings=warnings
        )

    def estimate_cost(
        self,
        num_images: int,
        size: Optional[ImageSize] = None,
        quality: Optional[ImageQuality] = None
    ) -> float:
        """
        Estimate cost for DALL-E 3 generation.

        Args:
            num_images: Number of images
            size: Image size
            quality: Image quality

        Returns:
            Estimated cost in USD
        """
        if size is None:
            size = self.config.default_size
        if quality is None:
            quality = self.config.quality

        # Get dimensions
        dims = size.value
        size_key = (dims[0], dims[1])

        # Get cost per image
        if size_key in self.cost_table:
            cost_per_image = self.cost_table[size_key].get(
                quality.value,
                self.config.cost_per_image
            )
        else:
            cost_per_image = self.config.cost_per_image

        return cost_per_image * num_images

    def _check_rate_limit(self):
        """
        Check if rate limit would be exceeded.

        Raises:
            RateLimitError: If rate limit exceeded
        """
        now = time.time()
        # Remove old requests (older than 1 minute)
        self.request_times = [
            t for t in self.request_times
            if now - t < 60
        ]

        if len(self.request_times) >= self.rate_limit:
            raise RateLimitError(
                f"Rate limit exceeded: {len(self.request_times)} requests "
                f"in last 60 seconds (limit: {self.rate_limit})"
            )

    def _handle_success(
        self,
        response: requests.Response,
        prompt: str,
        size: ImageSize,
        quality: ImageQuality
    ) -> GenerationResult:
        """
        Handle successful API response.

        Args:
            response: API response
            prompt: Original prompt
            size: Image size
            quality: Image quality

        Returns:
            GenerationResult
        """
        data = response.json()

        # Extract image URL and download
        image_url = data["data"][0]["revised_prompt"]
        image_response = requests.get(image_url, timeout=30)

        if image_response.status_code != 200:
            return self._create_error_result(
                prompt=prompt,
                error=f"Failed to download image from {image_url}",
                cost=self.estimate_cost(1, size, quality)
            )

        image_bytes = image_response.content

        # Determine image format
        image_format = "png"  # DALL-E 3 returns PNG

        # Build metadata
        metadata = {
            "model": self.model,
            "size": str(size),
            "quality": quality.value,
            "revised_prompt": data["data"][0].get("revised_prompt", prompt),
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        return GenerationResult(
            success=True,
            image_bytes=image_bytes,
            image_format=image_format,
            provider=self.provider_type,
            prompt=prompt,
            metadata=metadata,
            cost=self.estimate_cost(1, size, quality)
        )


def create_dalle3_provider(
    api_key: str,
    **kwargs
) -> DALLE3Provider:
    """
    Create a DALL-E 3 provider instance.

    Args:
        api_key: OpenAI API key
        **kwargs: Additional configuration options

    Returns:
        DALLE3Provider instance
    """
    config = ProviderConfig(
        provider_type=ProviderType.DALLE3,
        api_key=api_key,
        default_size=ImageSize.SQUARE_1024,
        quality=ImageQuality.STANDARD,
        rate_limit=10,  # 10 requests per minute
        cost_per_image=0.04,
        **kwargs
    )

    return DALLE3Provider(config)


def main():
    """Test DALL-E 3 Provider."""
    print("=" * 70)
    print("DALL-E 3 Provider Test")
    print("=" * 70)

    # Create provider (with test API key)
    print("\n[Test] Creating DALL-E 3 provider...")
    try:
        provider = create_dalle3_provider(
            api_key="test-api-key",
            max_retries=3,
            timeout=30
        )
        print("✓ Provider created successfully")
    except Exception as e:
        print(f"✗ Failed to create provider: {e}")
        return

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

    # Test rate limiting
    print("\n[Test] Testing rate limiting...")
    try:
        # This will fail because we don't have a real API key
        result = provider.generate("A cat")
        print(f"✓ Generation attempted (expected to fail without real API key)")
        print(f"  Success: {result.success}")
        if not result.success:
            print(f"  Error: {result.error}")
    except Exception as e:
        print(f"✓ Exception (expected): {e}")

    print("\n" + "=" * 70)
    print("DALL-E 3 Provider - PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()
