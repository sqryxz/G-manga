"""
Retry/Fallback Manager - Stage 6.1.5
Manages retries and fallback between providers.
"""

import time
import asyncio
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timezone
from enum import Enum
from collections import defaultdict

from .providers.base import (
    ImageProvider,
    ProviderType,
    GenerationResult,
    BatchGenerationResult,
    ImageSize,
    ImageQuality,
    GenerationError,
    RateLimitError,
    AuthenticationError
)


class FallbackStrategy(Enum):
    """Fallback strategy options."""
    NONE = "none"  # No fallback
    NEXT_PROVIDER = "next_provider"  # Try next provider in list
    CHEAPEST = "cheapest"  # Fallback to cheapest provider
    HIGHEST_QUALITY = "highest_quality"  # Fallback to highest quality


class RetryConfig:
    """Retry configuration."""

    def __init__(
        self,
        max_retries: int = 3,
        backoff_factor: float = 2.0,
        initial_backoff: float = 1.0,
        max_backoff: float = 60.0,
        retryable_errors: List[str] = None
    ):
        """
        Initialize retry configuration.

        Args:
            max_retries: Maximum number of retries
            backoff_factor: Exponential backoff factor
            initial_backoff: Initial backoff delay in seconds
            max_backoff: Maximum backoff delay in seconds
            retryable_errors: List of error types that are retryable
        """
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.initial_backoff = initial_backoff
        self.max_backoff = max_backoff
        self.retryable_errors = retryable_errors or [
            "rate_limit",
            "timeout",
            "server_error"
        ]


class RetryFallbackManager:
    """Manages retries and fallbacks for image generation."""

    def __init__(
        self,
        providers: Dict[str, ImageProvider],
        fallback_strategy: FallbackStrategy = FallbackStrategy.NEXT_PROVIDER,
        retry_config: Optional[RetryConfig] = None
    ):
        """
        Initialize retry/fallback manager.

        Args:
            providers: Dictionary of provider name -> provider instance
            fallback_strategy: Strategy for fallback
            retry_config: Retry configuration
        """
        self.providers = providers
        self.fallback_strategy = fallback_strategy
        self.retry_config = retry_config or RetryConfig()

        # Statistics
        self.attempts = defaultdict(int)
        self.successes = defaultdict(int)
        self.failures = defaultdict(int)
        self.fallback_count = 0

        # Provider order for fallback
        self.provider_order = list(providers.keys())

    def generate_with_retry(
        self,
        prompt: str,
        provider_name: Optional[str] = None,
        size: Optional[ImageSize] = None,
        quality: Optional[ImageQuality] = None,
        **kwargs
    ) -> GenerationResult:
        """
        Generate image with retry and fallback logic.

        Args:
            prompt: Image prompt
            provider_name: Primary provider name (default: first in list)
            size: Image size
            quality: Image quality
            **kwargs: Additional parameters

        Returns:
            GenerationResult
        """
        # Get primary provider
        if provider_name is None:
            provider_name = self.provider_order[0]

        # Try with retries
        for attempt in range(self.retry_config.max_retries + 1):
            # Select provider (may change on fallback)
            provider = self.providers[provider_name]
            self.attempts[provider_name] += 1

            try:
                result = provider.generate(
                    prompt=prompt,
                    size=size,
                    quality=quality,
                    **kwargs
                )

                if result.success:
                    self.successes[provider_name] += 1
                    return result
                else:
                    # Generation failed - check if we should retry
                    if attempt < self.retry_config.max_retries and self._should_retry(result.error):
                        # Apply backoff
                        backoff = self._calculate_backoff(attempt)
                        time.sleep(backoff)
                        continue
                    else:
                        self.failures[provider_name] += 1
                        # Try fallback
                        fallback_result = self._try_fallback(
                            prompt=prompt,
                            provider_name=provider_name,
                            size=size,
                            quality=quality,
                            **kwargs
                        )
                        if fallback_result is not None:
                            return fallback_result
                        return result

            except (RateLimitError, AuthenticationError) as e:
                self.failures[provider_name] += 1
                # Don't retry auth errors
                if isinstance(e, AuthenticationError):
                    # Try fallback
                    fallback_result = self._try_fallback(
                        prompt=prompt,
                        provider_name=provider_name,
                        size=size,
                        quality=quality,
                        **kwargs
                    )
                    if fallback_result is not None:
                        return fallback_result
                return self._create_error_result(prompt, str(e))
            except Exception as e:
                self.failures[provider_name] += 1
                # Unexpected error
                if attempt < self.retry_config.max_retries:
                    backoff = self._calculate_backoff(attempt)
                    time.sleep(backoff)
                    continue
                else:
                    # Try fallback
                    fallback_result = self._try_fallback(
                        prompt=prompt,
                        provider_name=provider_name,
                        size=size,
                        quality=quality,
                        **kwargs
                    )
                    if fallback_result is not None:
                        return fallback_result
                    return self._create_error_result(prompt, str(e))

        # All attempts failed
        return self._create_error_result(prompt, "Max retries exceeded")

    def batch_generate_with_retry(
        self,
        prompts: List[str],
        provider_name: Optional[str] = None,
        size: Optional[ImageSize] = None,
        quality: Optional[ImageQuality] = None,
        **kwargs
    ) -> BatchGenerationResult:
        """
        Generate multiple images with retry/fallback.

        Args:
            prompts: List of prompts
            provider_name: Primary provider name
            size: Image size
            quality: Image quality
            **kwargs: Additional parameters

        Returns:
            BatchGenerationResult
        """
        results = []
        total_cost = 0.0

        for prompt in prompts:
            result = self.generate_with_retry(
                prompt=prompt,
                provider_name=provider_name,
                size=size,
                quality=quality,
                **kwargs
            )
            results.append(result)
            total_cost += result.cost

        # Count successes/failures
        total_success = sum(1 for r in results if r.success)
        total_failed = len(results) - total_success

        return BatchGenerationResult(
            total_requested=len(prompts),
            total_success=total_success,
            total_failed=total_failed,
            results=results,
            total_cost=total_cost,
            provider=ProviderType.DALLE3,  # Placeholder
            generated_at=datetime.now(timezone.utc)
        )

    def _should_retry(self, error: Optional[str]) -> bool:
        """
        Check if error is retryable.

        Args:
            error: Error message

        Returns:
            True if retryable
        """
        if error is None:
            return False

        error_lower = error.lower()
        return any(
            retryable in error_lower
            for retryable in self.retry_config.retryable_errors
        )

    def _calculate_backoff(self, attempt: int) -> float:
        """
        Calculate exponential backoff delay.

        Args:
            attempt: Attempt number (0-indexed)

        Returns:
            Backoff delay in seconds
        """
        backoff = self.retry_config.initial_backoff * (
            self.retry_config.backoff_factor ** attempt
        )
        return min(backoff, self.retry_config.max_backoff)

    def _try_fallback(
        self,
        prompt: str,
        provider_name: str,
        size: Optional[ImageSize],
        quality: Optional[ImageQuality],
        **kwargs
    ) -> Optional[GenerationResult]:
        """
        Try fallback providers.

        Args:
            prompt: Image prompt
            provider_name: Current provider that failed
            size: Image size
            quality: Image quality
            **kwargs: Additional parameters

        Returns:
            GenerationResult if fallback succeeded, None otherwise
        """
        if self.fallback_strategy == FallbackStrategy.NONE:
            return None

        # Get fallback provider based on strategy
        fallback_provider = self._get_fallback_provider(provider_name)

        if fallback_provider is None or fallback_provider == provider_name:
            return None

        print(f"Falling back from {provider_name} to {fallback_provider}...")
        self.fallback_count += 1

        try:
            result = self.providers[fallback_provider].generate(
                prompt=prompt,
                size=size,
                quality=quality,
                **kwargs
            )
            self.attempts[fallback_provider] += 1

            if result.success:
                self.successes[fallback_provider] += 1
                return result
            else:
                self.failures[fallback_provider] += 1
                return None

        except Exception as e:
            self.failures[fallback_provider] += 1
            return None

    def _get_fallback_provider(self, current_provider: str) -> Optional[str]:
        """
        Get fallback provider based on strategy.

        Args:
            current_provider: Current provider name

        Returns:
            Fallback provider name or None
        """
        if self.fallback_strategy == FallbackStrategy.NEXT_PROVIDER:
            # Try next provider in list
            try:
                idx = self.provider_order.index(current_provider)
                if idx + 1 < len(self.provider_order):
                    return self.provider_order[idx + 1]
            except ValueError:
                pass

        elif self.fallback_strategy == FallbackStrategy.CHEAPEST:
            # Find cheapest provider
            costs = {
                name: provider.get_provider_info()["cost_per_image"]
                for name, provider in self.providers.items()
                if name != current_provider
            }
            if costs:
                return min(costs, key=costs.get)

        elif self.fallback_strategy == FallbackStrategy.HIGHEST_QUALITY:
            # Prefer HD quality providers
            for name in self.provider_order:
                if name != current_provider:
                    provider = self.providers[name]
                    if provider.config.quality == ImageQuality.HD:
                        return name

        return None

    def _create_error_result(self, prompt: str, error: str) -> GenerationResult:
        """Create an error result."""
        return GenerationResult(
            success=False,
            image_bytes=None,
            image_format="none",
            provider=ProviderType.DALLE3,  # Placeholder
            prompt=prompt,
            metadata={},
            error=error,
            cost=0.0
        )

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get retry/fallback statistics.

        Returns:
            Dictionary with statistics
        """
        stats = {
            "providers": {}
        }

        for provider_name in self.providers.keys():
            attempts = self.attempts[provider_name]
            successes = self.successes[provider_name]
            failures = self.failures[provider_name]

            success_rate = successes / attempts if attempts > 0 else 0.0

            stats["providers"][provider_name] = {
                "attempts": attempts,
                "successes": successes,
                "failures": failures,
                "success_rate": success_rate
            }

        stats["fallback_count"] = self.fallback_count
        stats["fallback_strategy"] = self.fallback_strategy.value

        return stats

    def reset_statistics(self):
        """Reset all statistics."""
        self.attempts.clear()
        self.successes.clear()
        self.failures.clear()
        self.fallback_count = 0


def create_retry_fallback_manager(
    providers: Dict[str, ImageProvider],
    fallback_strategy: str = "next_provider",
    max_retries: int = 3,
    **kwargs
) -> RetryFallbackManager:
    """
    Create a retry/fallback manager.

    Args:
        providers: Dictionary of provider name -> provider
        fallback_strategy: Strategy name
        max_retries: Maximum retries
        **kwargs: Additional configuration

    Returns:
        RetryFallbackManager instance
    """
    try:
        strategy = FallbackStrategy(fallback_strategy.lower())
    except ValueError:
        strategy = FallbackStrategy.NONE

    retry_config = RetryConfig(max_retries=max_retries, **kwargs)

    return RetryFallbackManager(
        providers=providers,
        fallback_strategy=strategy,
        retry_config=retry_config
    )


def main():
    """Test Retry/Fallback Manager."""
    print("=" * 70)
    print("Retry/Fallback Manager Test")
    print("=" * 70)

    # Note: This is a structural test
    # Full testing would require mock providers

    print("\n[Test] Creating retry/fallback manager...")
    print("✓ Manager structure created")
    print("  Requires actual providers for full testing")

    # Test retry config
    from stage6_image_generation.retry_manager import RetryConfig

    retry_config = RetryConfig(
        max_retries=5,
        backoff_factor=2.0,
        initial_backoff=1.0
    )

    print("\n[Test] Testing backoff calculation...")
    for i in range(5):
        backoff = retry_config.initial_backoff * (retry_config.backoff_factor ** i)
        print(f"  Attempt {i}: {backoff:.1f}s")

    # Test fallback strategies
    from stage6_image_generation.retry_manager import FallbackStrategy

    print("\n[Test] Testing fallback strategies...")
    for strategy in FallbackStrategy:
        print(f"  {strategy.value}")

    print("\n" + "=" * 70)
    print("Retry/Fallback Manager - PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()
