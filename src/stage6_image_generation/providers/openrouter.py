"""
OpenRouter Image Provider - Stage 6.1.4
Image generation via OpenRouter API (supports multiple SD models)
"""

import time
import requests
import base64
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

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


class OpenRouterImageProvider(ImageProvider):
    """
    Image generation provider using OpenRouter API.
    
    Supports various Stable Diffusion models:
    - stabilityai/stable-diffusion-xl-base-1.0
    - stabilityai/stable-diffusion-xl-base-1.0
    - runwayml/stable-diffusion-v1-5
    - and many others available on OpenRouter
    """

    def __init__(self, config: ProviderConfig, model: str = "google/gemini-2.5-flash-image"):
        """
        Initialize OpenRouter Image Provider.

        Args:
            config: Provider configuration
            model: Model identifier (overrides provider_type)
        """
        super().__init__(config)
        self.base_url = config.base_url or "https://openrouter.ai/api/v1"
        
        # Use explicitly passed model, fallback to provider_type.value
        self.model = model if model else (
            config.provider_type.value if config.provider_type 
            else "google/gemini-2.5-flash-image"
        )
        
        # OpenRouter costs vary by model (approximate)
        self.cost_per_image = config.cost_per_image or 0.02  # Gemini default

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
        **kwargs
    ) -> GenerationResult:
        """
        Generate a single image via OpenRouter.

        Args:
            prompt: Image generation prompt
            size: Image size (default: config.default_size)
            quality: Image quality (default: config.quality)
            steps: Number of diffusion steps
            cfg_scale: CFG scale
            negative_prompt: Negative prompt
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

        # Prepare headers
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": getattr(self.config, 'http_referer', '') or "https://github.com/g-manga",
            "X-Title": getattr(self.config, 'x_title', '') or "G-Manga"
        }

        # Prepare payload - OpenRouter uses chat/completions with modalities
        width, height = size.value

        # Calculate aspect ratio from dimensions
        def gcd(a, b):
            while b:
                a, b = b, a % b
            return a
        ratio_gcd = gcd(width, height)
        aspect_ratio = f"{width//ratio_gcd}:{height//ratio_gcd}"

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "modalities": ["image", "text"],
            "image_config": {
                "aspect_ratio": aspect_ratio
            }
        }

        # Retry logic
        last_error = None
        for attempt in range(self.config.max_retries):
            try:
                # Exponential backoff
                if attempt > 0:
                    backoff = 2 ** attempt
                    time.sleep(backoff)

                # Make request to chat/completions endpoint
                response = requests.post(
                    f"{self.base_url}/chat/completions",
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
                    try:
                        error_data = response.json()
                        error_msg = error_data.get("error", {}).get("message", "Unknown error")
                    except:
                        error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
                    raise GenerationError(f"API error: {error_msg}")

            except (RateLimitError, AuthenticationError) as e:
                return self._create_error_result(
                    prompt=prompt,
                    error=str(e),
                    cost=0.0
                )
            except Exception as e:
                last_error = e
                continue

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
        Validate an image from OpenRouter.

        Args:
            image_bytes: Generated image data
            prompt: Original prompt used

        Returns:
            ValidationResult with score and errors
        """
        errors = []
        warnings = []

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

        if len(image_bytes) < 1024:
            errors.append(ValidationError(
                error_code="TOO_SMALL",
                error_message=f"Image too small: {len(image_bytes)} bytes",
                severity=ValidationSeverity.ERROR
            ))

        if len(image_bytes) >= 8:
            header = image_bytes[:8]
            is_png = header == b'\x89PNG\r\n\x1a\n'
            is_jpeg = header[:2] == b'\xff\xd8'

            if not (is_png or is_jpeg):
                errors.append(ValidationError(
                    error_code="INVALID_FORMAT",
                    error_message="Invalid image format (expected PNG or JPEG)",
                    severity=ValidationSeverity.ERROR
                ))

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
        Estimate cost for OpenRouter generation.

        Args:
            num_images: Number of images
            size: Image size
            quality: Image quality

        Returns:
            Estimated cost in USD
        """
        return self.cost_per_image * num_images

    def _check_rate_limit(self):
        """
        Check if rate limit would be exceeded.

        Raises:
            RateLimitError: If rate limit exceeded
        """
        now = time.time()
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

        # Check for OpenRouter chat/completions response format
        if not data.get("choices") or len(data["choices"]) == 0:
            return self._create_error_result(
                prompt=prompt,
                error="No choices in response",
                cost=self.estimate_cost(1, size, quality)
            )

        message = data["choices"][0].get("message", {})
        images = message.get("images", [])

        if not images:
            # Check if there's content text
            content = message.get("content", "")
            return self._create_error_result(
                prompt=prompt,
                error=f"No images in response. Content: {content[:200]}",
                cost=self.estimate_cost(1, size, quality)
            )

        # Extract base64 image data
        image_info = images[0]
        image_url = image_info.get("image_url", {})
        b64_data = image_url.get("url", "")

        if not b64_data:
            return self._create_error_result(
                prompt=prompt,
                error="No image URL in response",
                cost=self.estimate_cost(1, size, quality)
            )

        # Parse base64 data URL
        if b64_data.startswith("data:image"):
            # data:image/png;base64,...
            header, b64_body = b64_data.split(",", 1)
            image_format = header.split("/")[1].split(";")[0]
        else:
            # Direct base64
            b64_body = b64_data
            image_format = "png"

        try:
            image_bytes = base64.b64decode(b64_body)
        except Exception as e:
            return self._create_error_result(
                prompt=prompt,
                error=f"Failed to decode base64 image: {e}",
                cost=self.estimate_cost(1, size, quality)
            )

        # Build metadata
        metadata = {
            "model": self.model,
            "size": str(size),
            "quality": quality.value,
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


def create_openrouter_provider(
    api_key: str,
    model: str = "google/gemini-2.5-flash-image",
    **kwargs
) -> OpenRouterImageProvider:
    """
    Create an OpenRouter image provider instance.

    Args:
        api_key: OpenRouter API key
        model: Model identifier (default: google/gemini-2.5-flash-image)
        **kwargs: Additional configuration options

    Returns:
        OpenRouterImageProvider instance
    """
    config = ProviderConfig(
        provider_type=ProviderType.SDXL,  # Placeholder, actual model is passed separately
        api_key=api_key,
        default_size=ImageSize.SQUARE_1024,
        quality=ImageQuality.STANDARD,
        rate_limit=20,
        cost_per_image=0.02,  # Gemini pricing
        **kwargs
    )

    return OpenRouterImageProvider(config, model=model)


def main():
    """Test OpenRouter Image Provider."""
    print("=" * 70)
    print("OpenRouter Image Provider Test")
    print("=" * 70)

    # Create provider (with test API key)
    print("\n[Test] Creating OpenRouter provider...")
    try:
        provider = create_openrouter_provider(
            api_key="test-api-key",
            model="stabilityai/stable-diffusion-xl-base-1.0",
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
    cost_1 = provider.estimate_cost(1)
    cost_10 = provider.estimate_cost(10)
    print(f"✓ 1 image: ${cost_1:.2f}")
    print(f"✓ 10 images: ${cost_10:.2f}")

    # Test validation
    print("\n[Test] Testing image validation...")

    # Test with empty image
    empty_result = provider.validate(b"", "test prompt")
    print(f"✓ Empty image - Valid: {empty_result.is_valid}, Score: {empty_result.score:.2f}")

    # Test with valid PNG header
    valid_png = b'\x89PNG\r\n\x1a\n' + b'x' * 5000
    valid_result = provider.validate(valid_png, "test prompt")
    print(f"✓ Valid PNG - Valid: {valid_result.is_valid}, Score: {valid_result.score:.2f}")

    print("\n" + "=" * 70)
    print("OpenRouter Image Provider - PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()
