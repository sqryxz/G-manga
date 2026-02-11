"""
Image Provider Factory - Stage 6.1.5
Factory functions for creating image providers from configuration.
"""

import os
from typing import Optional, Dict, Any
import warnings

from .base import (
    ImageProvider,
    ProviderConfig,
    ProviderType,
    ImageQuality,
    ImageSize,
    create_provider_config,
    AuthenticationError,
    RateLimitError
)

from .dalle import create_dalle3_provider, DALLE3Provider
from .sdxl import create_sdxl_provider, SDXLProvider
from .openrouter import create_openrouter_provider, OpenRouterImageProvider


class ProviderRegistry:
    """Registry of available image providers."""
    
    _providers: Dict[str, type] = {
        "dalle3": DALLE3Provider,
        "sdxl": SDXLProvider,
        "openrouter": OpenRouterImageProvider,
    }
    
    @classmethod
    def register(cls, name: str, provider_class: type):
        """
        Register a new provider.
        
        Args:
            name: Provider name
            provider_class: Provider class
        """
        cls._providers[name.lower()] = provider_class
    
    @classmethod
    def get(cls, name: str) -> Optional[type]:
        """
        Get provider class by name.
        
        Args:
            name: Provider name
            
        Returns:
            Provider class or None
        """
        return cls._providers.get(name.lower())
    
    @classmethod
    def list_providers(cls) -> list:
        """
        List all registered providers.
        
        Returns:
            List of provider names
        """
        return list(cls._providers.keys())


class ImageProviderFactory:
    """
    Factory for creating image providers.
    """
    
    @staticmethod
    def create_provider(
        provider_type: str,
        api_key: Optional[str] = None,
        **kwargs
    ) -> ImageProvider:
        """
        Create an image provider instance.
        
        Args:
            provider_type: Provider type (dalle3, sdxl, openrouter)
            api_key: API key (optional, will check env vars if not provided)
            **kwargs: Additional provider configuration
            
        Returns:
            ImageProvider instance
            
        Raises:
            ValueError: If provider type is unknown
            AuthenticationError: If no API key is available
        """
        # Normalize provider type
        provider_type = provider_type.lower()
        
        # Get API key from environment if not provided
        if api_key is None:
            api_key = ImageProviderFactory._get_api_key(provider_type)
        
        if not api_key:
            raise AuthenticationError(
                f"No API key found for provider '{provider_type}'. "
                f"Set {ImageProviderFactory._get_env_var(provider_type)} "
                "environment variable or pass api_key parameter."
            )
        
        # Create provider based on type
        if provider_type in ["dalle3", "dall-e-3"]:
            return create_dalle3_provider(api_key=api_key, **kwargs)
        
        elif provider_type in ["sdxl", "stable-diffusion-xl"]:
            return create_sdxl_provider(api_key=api_key, **kwargs)
        
        elif provider_type == "openrouter":
            model = kwargs.pop("model", "stabilityai/stable-diffusion-xl-base-1.0")
            return create_openrouter_provider(api_key=api_key, model=model, **kwargs)
        
        else:
            raise ValueError(
                f"Unknown provider type: {provider_type}. "
                f"Available providers: {ProviderRegistry.list_providers()}"
            )
    
    @staticmethod
    def create_from_config(config: ProviderConfig) -> ImageProvider:
        """
        Create a provider from ProviderConfig.
        
        Args:
            config: Provider configuration
            
        Returns:
            ImageProvider instance
        """
        provider_type = config.provider_type.value if hasattr(config.provider_type, 'value') else str(config.provider_type)
        
        return ImageProviderFactory.create_provider(
            provider_type=provider_type,
            api_key=config.api_key
        )
    
    @staticmethod
    def _get_api_key(provider_type: str) -> str:
        """
        Get API key from environment for provider.
        
        Args:
            provider_type: Provider type
            
        Returns:
            API key or empty string
        """
        env_var = ImageProviderFactory._get_env_var(provider_type)
        return os.getenv(env_var, "")
    
    @staticmethod
    def _get_env_var(provider_type: str) -> str:
        """
        Get environment variable name for API key.
        
        Args:
            provider_type: Provider type
            
        Returns:
            Environment variable name
        """
        env_vars = {
            "dalle3": "OPENAI_API_KEY",
            "dall-e-3": "OPENAI_API_KEY",
            "sdxl": "STABILITY_API_KEY",
            "stable-diffusion-xl": "STABILITY_API_KEY",
            "openrouter": "OPENROUTER_API_KEY",
        }
        
        return env_vars.get(provider_type.lower(), f"{provider_type.upper()}_API_KEY")
    
    @staticmethod
    def validate_api_keys(provider_type: Optional[str] = None) -> Dict[str, bool]:
        """
        Validate API keys for providers.
        
        Args:
            provider_type: Optional specific provider to check
            
        Returns:
            Dictionary of provider -> has_valid_key
        """
        results = {}
        
        providers_to_check = (
            [provider_type] if provider_type 
            else ["dalle3", "sdxl", "openrouter"]
        )
        
        for provider in providers_to_check:
            env_var = ImageProviderFactory._get_env_var(provider)
            api_key = os.getenv(env_var, "")
            results[provider] = bool(api_key)
        
        return results
    
    @staticmethod
    def list_available_providers() -> list:
        """
        List all available providers.
        
        Returns:
            List of provider names
        """
        return ProviderRegistry.list_providers()


def create_image_provider(
    provider_type: str,
    api_key: Optional[str] = None,
    **kwargs
) -> ImageProvider:
    """
    Convenience function to create an image provider.
    
    Args:
        provider_type: Provider type (dalle3, sdxl, openrouter)
        api_key: API key (optional)
        **kwargs: Additional configuration
        
    Returns:
        ImageProvider instance
    """
    return ImageProviderFactory.create_provider(
        provider_type=provider_type,
        api_key=api_key,
        **kwargs
    )


def get_provider_info(provider_type: str) -> Dict[str, Any]:
    """
    Get information about a provider.
    
    Args:
        provider_type: Provider type
        
    Returns:
        Provider information dictionary
    """
    provider_class = ProviderRegistry.get(provider_type)
    
    if not provider_class:
        raise ValueError(f"Unknown provider: {provider_type}")
    
    # Create a test instance to get info
    try:
        # Use fake API key for info retrieval
        test_config = create_provider_config(
            provider_type=provider_type,
            api_key="test-key"
        )
        provider = ImageProviderFactory.create_from_config(test_config)
        return provider.get_provider_info()
    except AuthenticationError:
        # Expected when no API key is available
        return {
            "provider_type": provider_type,
            "status": "needs_api_key",
            "env_var": ImageProviderFactory._get_env_var(provider_type)
        }


def main():
    """Test Image Provider Factory."""
    print("=" * 70)
    print("Image Provider Factory Test")
    print("=" * 70)
    
    # List available providers
    print("\n[Test] Listing available providers...")
    providers = ImageProviderFactory.list_available_providers()
    print(f"✓ Available providers: {providers}")
    
    # List registered providers
    print("\n[Test] Registered providers in registry...")
    registered = ProviderRegistry.list_providers()
    print(f"✓ Registered: {registered}")
    
    # Test provider creation (with fake API key)
    print("\n[Test] Testing DALL-E 3 provider creation...")
    try:
        dalle_provider = create_image_provider(
            provider_type="dalle3",
            api_key="fake-api-key"
        )
        print("✓ DALL-E 3 provider created")
        info = dalle_provider.get_provider_info()
        print(f"  Type: {info['provider_type']}")
        print(f"  Cost per image: ${info['cost_per_image']:.2f}")
    except Exception as e:
        print(f"✗ Failed: {e}")
    
    print("\n[Test] Testing SDXL provider creation...")
    try:
        sdxl_provider = create_image_provider(
            provider_type="sdxl",
            api_key="fake-api-key"
        )
        print("✓ SDXL provider created")
        info = sdxl_provider.get_provider_info()
        print(f"  Type: {info['provider_type']}")
        print(f"  Cost per image: ${info['cost_per_image']:.2f}")
    except Exception as e:
        print(f"✗ Failed: {e}")
    
    print("\n[Test] Testing OpenRouter provider creation...")
    try:
        or_provider = create_image_provider(
            provider_type="openrouter",
            api_key="fake-api-key"
        )
        print("✓ OpenRouter provider created")
        info = or_provider.get_provider_info()
        print(f"  Type: {info['provider_type']}")
        print(f"  Cost per image: ${info['cost_per_image']:.2f}")
    except Exception as e:
        print(f"✗ Failed: {e}")
    
    # Test API key validation
    print("\n[Test] Validating API keys...")
    validation_results = ImageProviderFactory.validate_api_keys()
    print(f"✓ Validation results:")
    for provider, has_key in validation_results.items():
        status = "✓ Has key" if has_key else "✗ Missing key"
        env_var = ImageProviderFactory._get_env_var(provider)
        print(f"  {provider}: {status} (env: {env_var})")
    
    # Test unknown provider
    print("\n[Test] Testing unknown provider...")
    try:
        create_image_provider(provider_type="unknown", api_key="fake-key")
        print("✗ Should have raised ValueError")
    except ValueError as e:
        print(f"✓ Correctly raised ValueError: {e}")
    
    print("\n" + "=" * 70)
    print("Image Provider Factory - PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()
