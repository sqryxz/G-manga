"""
Image Provider Interface - Stage 6.1.1
Defines abstract base class for all image generation providers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import io
from datetime import datetime


class ProviderType(Enum):
    """Supported image provider types."""
    DALLE3 = "dalle3"
    SDXL = "sdxl"
    MIDJOURNEY = "midjourney"


class ImageQuality(Enum):
    """Image quality levels."""
    STANDARD = "standard"
    HD = "hd"
    ULTRA = "ultra"


class ImageSize(Enum):
    """Standard image sizes."""
    SQUARE_256 = (256, 256)
    SQUARE_512 = (512, 512)
    SQUARE_1024 = (1024, 1024)
    LANDSCAPE_1024 = (1024, 768)
    PORTRAIT_1024 = (768, 1024)
    LANDSCAPE_1792 = (1792, 1024)
    PORTRAIT_1792 = (1024, 1792)

    def __str__(self):
        return f"{self.value[0]}x{self.value[1]}"


@dataclass
class ProviderConfig:
    """Configuration for an image provider."""
    provider_type: ProviderType
    api_key: str
    base_url: Optional[str] = None
    max_retries: int = 3
    timeout: int = 60
    rate_limit: int = 10  # requests per minute
    quality: ImageQuality = ImageQuality.STANDARD
    default_size: ImageSize = ImageSize.SQUARE_1024
    enable_fallback: bool = True
    cost_per_image: float = 0.04  # USD


@dataclass
class GenerationResult:
    """Result of image generation."""
    success: bool
    image_bytes: Optional[bytes]
    image_format: str  # png, jpg, webp
    provider: ProviderType
    prompt: str
    metadata: Dict[str, Any]
    error: Optional[str] = None
    cost: float = 0.0
    generated_at: Optional[datetime] = None

    def __post_init__(self):
        if self.generated_at is None:
            self.generated_at = datetime.utcnow()


@dataclass
class BatchGenerationResult:
    """Result of batch image generation."""
    total_requested: int
    total_success: int
    total_failed: int
    results: List[GenerationResult]
    total_cost: float
    provider: ProviderType
    generated_at: datetime

    def __post_init__(self):
        if self.generated_at is None:
            self.generated_at = datetime.utcnow()


@dataclass
class ValidationError:
    """Image validation error."""
    error_code: str
    error_message: str
    severity: "ValidationSeverity"
    suggestions: Optional[List[str]] = None


class ValidationSeverity(Enum):
    """Validation error severity."""
    WARNING = "warning"  # Image is acceptable but has issues
    ERROR = "error"  # Image should be regenerated


@dataclass
class ValidationResult:
    """Result of image validation."""
    is_valid: bool
    score: float  # 0.0 to 1.0
    errors: List[ValidationError]
    warnings: List[ValidationError]
    checked_at: Optional[datetime] = None

    def __post_init__(self):
        if self.checked_at is None:
            self.checked_at = datetime.utcnow()


class ImageProvider(ABC):
    """
    Abstract base class for image generation providers.

    All providers must implement these methods:
    - generate(): Generate a single image
    - batch_generate(): Generate multiple images
    - validate(): Validate a generated image
    """

    def __init__(self, config: ProviderConfig):
        """
        Initialize image provider.

        Args:
            config: Provider configuration
        """
        self.config = config
        self.provider_type = config.provider_type

    @abstractmethod
    def generate(
        self,
        prompt: str,
        size: Optional[ImageSize] = None,
        quality: Optional[ImageQuality] = None,
        **kwargs
    ) -> GenerationResult:
        """
        Generate a single image from prompt.

        Args:
            prompt: Image generation prompt
            size: Image size (default: config.default_size)
            quality: Image quality (default: config.quality)
            **kwargs: Provider-specific parameters

        Returns:
            GenerationResult with image bytes or error
        """
        pass

    @abstractmethod
    def batch_generate(
        self,
        prompts: List[str],
        size: Optional[ImageSize] = None,
        quality: Optional[ImageQuality] = None,
        max_concurrent: int = 3,
        **kwargs
    ) -> BatchGenerationResult:
        """
        Generate multiple images in batch.

        Args:
            prompts: List of image prompts
            size: Image size (default: config.default_size)
            quality: Image quality (default: config.quality)
            max_concurrent: Max concurrent requests
            **kwargs: Provider-specific parameters

        Returns:
            BatchGenerationResult with all results
        """
        pass

    @abstractmethod
    def validate(
        self,
        image_bytes: bytes,
        prompt: str
    ) -> ValidationResult:
        """
        Validate a generated image.

        Args:
            image_bytes: Generated image data
            prompt: Original prompt used

        Returns:
            ValidationResult with score and errors
        """
        pass

    @abstractmethod
    def estimate_cost(
        self,
        num_images: int,
        size: Optional[ImageSize] = None,
        quality: Optional[ImageQuality] = None
    ) -> float:
        """
        Estimate cost for image generation.

        Args:
            num_images: Number of images to generate
            size: Image size
            quality: Image quality

        Returns:
            Estimated cost in USD
        """
        pass

    def get_provider_info(self) -> Dict[str, Any]:
        """
        Get provider information.

        Returns:
            Dictionary with provider details
        """
        return {
            "provider_type": self.provider_type.value,
            "quality": self.config.quality.value,
            "default_size": str(self.config.default_size),
            "max_retries": self.config.max_retries,
            "timeout": self.config.timeout,
            "rate_limit": self.config.rate_limit,
            "cost_per_image": self.config.cost_per_image,
            "enable_fallback": self.config.enable_fallback
        }

    def _create_error_result(
        self,
        prompt: str,
        error: str,
        cost: float = 0.0
    ) -> GenerationResult:
        """
        Create an error result.

        Args:
            prompt: Original prompt
            error: Error message
            cost: Cost incurred

        Returns:
            GenerationResult with error
        """
        return GenerationResult(
            success=False,
            image_bytes=None,
            image_format="none",
            provider=self.provider_type,
            prompt=prompt,
            metadata={},
            error=error,
            cost=cost
        )


class ProviderException(Exception):
    """Base exception for provider errors."""
    pass


class RateLimitError(ProviderException):
    """Raised when rate limit is exceeded."""
    pass


class AuthenticationError(ProviderException):
    """Raised when authentication fails."""
    pass


class GenerationError(ProviderException):
    """Raised when image generation fails."""
    pass


def create_provider_config(
    provider_type: str,
    api_key: str,
    **kwargs
) -> ProviderConfig:
    """
    Create a provider configuration.

    Args:
        provider_type: Provider type (dalle3, sdxl, midjourney)
        api_key: API key for the provider
        **kwargs: Additional configuration options

    Returns:
        ProviderConfig object

    Raises:
        ValueError: If provider_type is invalid
    """
    try:
        provider_enum = ProviderType(provider_type.lower())
    except ValueError:
        raise ValueError(
            f"Invalid provider type: {provider_type}. "
            f"Valid types: {[p.value for p in ProviderType]}"
        )

    # Convert quality string to enum if needed
    if 'quality' in kwargs and isinstance(kwargs['quality'], str):
        try:
            kwargs['quality'] = ImageQuality(kwargs['quality'].lower())
        except ValueError:
            raise ValueError(
                f"Invalid quality: {kwargs['quality']}. "
                f"Valid types: {[q.value for q in ImageQuality]}"
            )

    return ProviderConfig(
        provider_type=provider_enum,
        api_key=api_key,
        **kwargs
    )


def main():
    """Test Image Provider Interface."""
    print("=" * 70)
    print("Image Provider Interface Test")
    print("=" * 70)

    # Test creating provider config
    print("\n[Test] Creating provider configuration...")
    config = create_provider_config(
        provider_type="dalle3",
        api_key="test-key",
        max_retries=5,
        timeout=90,
        quality="hd"
    )
    print(f"✓ Provider type: {config.provider_type.value}")
    print(f"  Max retries: {config.max_retries}")
    print(f"  Timeout: {config.timeout}")
    print(f"  Quality: {config.quality.value}")

    # Test enums
    print("\n[Test] Testing enums...")
    print(f"✓ Provider types: {[p.value for p in ProviderType]}")
    print(f"✓ Image qualities: {[q.value for q in ImageQuality]}")
    print(f"✓ Image sizes: {[str(s) for s in ImageSize]}")

    # Test dataclasses
    print("\n[Test] Testing dataclasses...")
    result = GenerationResult(
        success=True,
        image_bytes=b"fake_image_data",
        image_format="png",
        provider=ProviderType.DALLE3,
        prompt="A cat",
        metadata={"model": "dall-e-3"},
        cost=0.04
    )
    print(f"✓ Generation result: {result.success}")
    print(f"  Provider: {result.provider.value}")
    print(f"  Cost: ${result.cost:.2f}")

    # Test validation result
    print("\n[Test] Testing validation result...")
    validation = ValidationResult(
        is_valid=True,
        score=0.95,
        errors=[],
        warnings=[]
    )
    print(f"✓ Validation result: {validation.is_valid}")
    print(f"  Score: {validation.score:.2f}")

    # Test exceptions
    print("\n[Test] Testing exceptions...")
    try:
        raise RateLimitError("Rate limit exceeded")
    except ProviderException as e:
        print(f"✓ Caught rate limit error: {e}")

    try:
        raise AuthenticationError("Invalid API key")
    except ProviderException as e:
        print(f"✓ Caught authentication error: {e}")

    try:
        raise GenerationError("Generation failed")
    except ProviderException as e:
        print(f"✓ Caught generation error: {e}")

    # Test invalid provider type
    print("\n[Test] Testing invalid provider type...")
    try:
        create_provider_config("invalid", "test-key")
    except ValueError as e:
        print(f"✓ Caught expected error: {e}")

    print("\n" + "=" * 70)
    print("Image Provider Interface - PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()
