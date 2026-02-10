"""
SDXL Provider - Stage 6.1.3
Stability AI SDXL image generation implementation.
"""

import time
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import json
import base64

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


class SDXLProvider(ImageProvider):
    """SDXL (Stability AI) image generation provider."""

    def __init__(self, config: ProviderConfig):
        """
        Initialize SDXL Provider.

        Args:
            config: Provider configuration
        """
        super().__init__(config)
        self.base_url = config.base_url or "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
        self.model = "sd-1024"

        # SDXL costs (as of 2024)
        # SDXL Turbo: $0.004/image
        # SDXL: $0.04/image
        self.cost_per_image = {
            "standard": 0.04,
            "turbo": 0.004
        }

        # SDXL default parameters
        self.default_steps = 30
        self.default_cfg_scale = 7.5

        # Rate limiting
        self.request_times = []
        self.rate_limit = config.rate_limit

    def generate(
        self,
        prompt: str,
        size: Optional[ImageSize] = None,
        quality: Optional[ImageQuality] = None,
        steps: int = 30,
        cfg_scale: float = 7.5,
        negative_prompt: str = "",
        style_preset: Optional[str] = None,
        **kwargs
    ) -> GenerationResult:
        """
        Generate a single image with SDXL.

        Args:
            prompt: Image generation prompt
            size: Image size (default: config.default_size)
            quality: Image quality (default: config.quality)
            steps: Number of diffusion steps (default: 30)
            cfg_scale: CFG scale (default: 7.5)
            negative_prompt: Negative prompt (default: "")
            style_preset: Style preset (e.g., "3d-model", "analog-film", "anime")
            **kwargs: Additional parameters

        Returns:
            GenerationResult with image bytes or error
        """
        # Use defaults from config
        if size is None:
            size = self.config.default_size
        if quality is None:
            quality = self.config.quality

        # Check rate limit
        self._check_rate_limit()

        # Prepare request
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        # SDXL uses width/height
        width, height = size.value

        payload = {
            "text_prompts": [
                {
                    "text": prompt,
                    "weight": 1.0
                }
            ],
            "cfg_scale": cfg_scale,
            "height": height,
            "width": width,
            "steps": steps,
            "samples": 1,
            "seed": 0  # Random seed
        }

        # Add negative prompt if provided
        if negative_prompt:
            payload["text_prompts"].append({
                "text": negative_prompt,
                "weight": -1.0
            })

        # Add style preset if provided
        if style_preset:
            payload["style_preset"] = style_preset

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
                    return self._handle_success(response, prompt, size, quality, steps)
                elif response.status_code == 401:
                    raise AuthenticationError("Invalid API key")
                elif response.status_code == 429:
                    raise RateLimitError("Rate limit exceeded")
                else:
                    error_data = response.json()
                    error_msg = error_data.get("message", error_data.get("errors", "Unknown error"))
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
        steps: int = 30,
        cfg_scale: float = 7.5,
        negative_prompt: str = "",
        **kwargs
    ) -> BatchGenerationResult:
        """
        Generate multiple images in batch.

        Args:
            prompts: List of image prompts
            size: Image size
            quality: Image quality
            max_concurrent: Max concurrent requests
            steps: Number of diffusion steps
            cfg_scale: CFG scale
            negative_prompt: Negative prompt
            **kwargs: Additional parameters

        Returns:
            BatchGenerationResult with all results
        """
        results = []
        total_cost = 0.0

        # Generate images sequentially
        for i, prompt in enumerate(prompts):
            print(f"Generating image {i+1}/{len(prompts)}...")

            result = self.generate(
                prompt=prompt,
                size=size,
                quality=quality,
                steps=steps,
                cfg_scale=cfg_scale,
                negative_prompt=negative_prompt
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
        Validate an SDXL generated image.

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
        Estimate cost for SDXL generation.

        Args:
            num_images: Number of images
            size: Image size
            quality: Image quality

        Returns:
            Estimated cost in USD
        """
        # SDXL cost per image
        quality_key = quality.value if quality else "standard"
        cost_per_image = self.cost_per_image.get(quality_key, self.config.cost_per_image)

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
        quality: ImageQuality,
        steps: int
    ) -> GenerationResult:
        """
        Handle successful API response.

        Args:
            response: API response
            prompt: Original prompt
            size: Image size
            quality: Image quality
            steps: Number of steps

        Returns:
            GenerationResult
        """
        data = response.json()

        # Extract image data (base64)
        if not data.get("artifacts") or len(data["artifacts"]) == 0:
            return self._create_error_result(
                prompt=prompt,
                error="No image data in response",
                cost=self.estimate_cost(1, size, quality)
            )

        image_data = data["artifacts"][0]["base64"]
        image_bytes = base64.b64decode(image_data)

        # Determine image format
        image_format = "png"  # SDXL returns PNG

        # Build metadata
        metadata = {
            "model": self.model,
            "size": str(size),
            "quality": quality.value,
            "steps": steps,
            "finish_reasons": data["artifacts"][0].get("finishReasons", []),
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


def create_sdxl_provider(
    api_key: str,
    **kwargs
) -> SDXLProvider:
    """
    Create an SDXL provider instance.

    Args:
        api_key: Stability AI API key
        **kwargs: Additional configuration options

    Returns:
        SDXLProvider instance
    """
    config = ProviderConfig(
        provider_type=ProviderType.SDXL,
        api_key=api_key,
        default_size=ImageSize.SQUARE_1024,
        quality=ImageQuality.STANDARD,
        rate_limit=20,  # 20 requests per minute
        cost_per_image=0.04,
        **kwargs
    )

    return SDXLProvider(config)


def main():
    """Test SDXL Provider."""
    print("=" * 70)
    print("SDXL Provider Test")
    print("=" * 70)

    # Create provider (with test API key)
    print("\n[Test] Creating SDXL provider...")
    try:
        provider = create_sdxl_provider(
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

    print("\n" + "=" * 70)
    print("SDXL Provider - PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()
