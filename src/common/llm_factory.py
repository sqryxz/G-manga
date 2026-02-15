"""
LLM Client Factory - Switch between Z.AI and OpenRouter providers.

Usage:
    from common.llm_factory import create_llm_client
    
    # Default (Z.AI)
    client = create_llm_client()
    
    # Explicit provider
    client = create_llm_client(provider="zai")
    client = create_llm_client(provider="openrouter")
    
    # With options
    client = create_llm_client(provider="openrouter", model="openai/gpt-4o-mini")
"""

import os
from typing import Optional, Union, Dict, Any

from common.logging import get_logger


# Provider constants
PROVIDER_ZAI = "zai"
PROVIDER_OPENROUTER = "openrouter"
PROVIDER_MOCK = "mock"

# Default settings
DEFAULT_PROVIDER = os.getenv("LLM_PROVIDER", PROVIDER_ZAI)
DEFAULT_OPENROUTER_MODEL = os.getenv("OPENROUTER_DEFAULT_MODEL", "openai/gpt-4o-mini")
DEFAULT_ZAI_MODEL = os.getenv("ZAI_DEFAULT_MODEL", "glm-4.7")


class LLMClientError(Exception):
    """Exception raised when LLM client creation fails."""
    pass


def create_llm_client(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    use_mock: bool = False,
    **kwargs
) -> Any:
    """
    Factory function to create LLM client for storyboard generation.
    
    Args:
        provider: LLM provider ("zai", "openrouter", or "mock"). 
                  Default: reads from LLM_PROVIDER env var, fallback to "zai"
        model: Specific model to use (provider-dependent)
        use_mock: If True, return mock client (overrides provider)
        **kwargs: Additional provider-specific options
        
    Returns:
        LLM client instance with `.generate(prompt, **kwargs)` method
        
    Raises:
        LLMClientError: If client creation fails
        
    Examples:
        # Use default provider
        client = create_llm_client()
        
        # Use OpenRouter with specific model
        client = create_llm_client(provider="openrouter", model="anthropic/claude-sonnet-4-20250514")
        
        # Use mock for testing
        client = create_llm_client(use_mock=True)
    """
    logger = get_logger(__name__)
    
    # Handle mock mode
    if use_mock:
        from common.mocking import MockLLMClient
        logger.info("🧪 Mock LLM client initialized")
        return MockLLMClient()
    
    # Determine provider
    if provider is None:
        provider = DEFAULT_PROVIDER
    
    provider = provider.lower()
    
    if provider == PROVIDER_ZAI:
        return _create_zai_client(model, logger, **kwargs)
    elif provider == PROVIDER_OPENROUTER:
        return _create_openrouter_client(model, logger, **kwargs)
    elif provider == PROVIDER_MOCK:
        from common.mocking import MockLLMClient
        logger.info("🧪 Mock LLM client initialized")
        return MockLLMClient()
    else:
        raise LLMClientError(f"Unknown LLM provider: {provider}. Supported: zai, openrouter, mock")


def _create_zai_client(model: Optional[str], logger, **kwargs) -> Any:
    """Create Z.AI client."""
    try:
        from common.zai_client import create_zai_client as zai_factory
        
        client = zai_factory(
            api_key=kwargs.get("api_key"),
            base_url=kwargs.get("base_url", "https://api.z.ai/api/paas/v4/"),
            default_model=model or DEFAULT_ZAI_MODEL,
            use_adapter=True,
            **kwargs
        )
        logger.info(f"🔧 Z.AI LLM client initialized (model: {model or DEFAULT_ZAI_MODEL})")
        return client
    except ValueError as e:
        raise LLMClientError(f"Z.AI configuration error: {e}")
    except Exception as e:
        raise LLMClientError(f"Failed to create Z.AI client: {e}")


def _create_openrouter_client(model: Optional[str], logger, **kwargs) -> Any:
    """Create OpenRouter client."""
    try:
        from common.openrouter import OpenRouterClient
        
        client = OpenRouterClient(api_key=kwargs.get("api_key"))
        
        # Get model from args or env
        model_to_use = model or kwargs.get("default_model") or DEFAULT_OPENROUTER_MODEL
        
        logger.info(f"🔧 OpenRouter LLM client initialized (model: {model_to_use})")
        
        # Return adapter for consistent interface
        return _OpenRouterAdapter(client, model_to_use)
    except ValueError as e:
        raise LLMClientError(f"OpenRouter configuration error: {e}")
    except Exception as e:
        raise LLMClientError(f"Failed to create OpenRouter client: {e}")


class _OpenRouterAdapter:
    """
    Adapter to make OpenRouterClient compatible with storyboard generators.
    
    Provides a simple `.generate(prompt, **kwargs)` interface.
    """
    
    def __init__(self, client: Any, default_model: str):
        self.client = client
        self.default_model = default_model
    
    def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate text and return raw string.
        
        Args:
            prompt: Input prompt
            **kwargs: Additional parameters (model, temperature, etc.)
            
        Returns:
            Generated text string
        """
        model = kwargs.pop("model", None) or self.default_model
        result = self.client.generate(prompt, model=model, **kwargs)
        
        if result.success:
            return result.text
        else:
            raise Exception(f"OpenRouter generation failed: {result.error}")
    
    def generate_batch(self, prompts: list, **kwargs) -> list:
        """Generate text for multiple prompts."""
        return [self.generate(p, **kwargs) for p in prompts]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics."""
        return {
            "client_type": "openrouter",
            "default_model": self.default_model
        }


def get_provider_info(provider: str) -> Dict[str, Any]:
    """
    Get information about a specific provider.
    
    Args:
        provider: Provider name ("zai", "openrouter")
        
    Returns:
        Dictionary with provider information
    """
    if provider == PROVIDER_ZAI:
        return {
            "name": "Z.AI",
            "models": ["glm-4.7", "glm-4.5", "glm-4.5-flash", "glm-4.7-coding"],
            "env_var": "ZAI_API_KEY",
            "default_model": DEFAULT_ZAI_MODEL,
            "description": "GLM models from Z.AI (OpenAI-compatible API)"
        }
    elif provider == PROVIDER_OPENROUTER:
        return {
            "name": "OpenRouter",
            "models": ["openai/gpt-4o-mini", "openai/gpt-4o", "anthropic/claude-sonnet-4-20250514", "google/gemini-2.5-pro"],
            "env_var": "OPENROUTER_API_KEY",
            "default_model": DEFAULT_OPENROUTER_MODEL,
            "description": "Unified API for 100+ models from OpenAI, Anthropic, Google, etc."
        }
    else:
        return {"error": f"Unknown provider: {provider}"}


def list_providers() -> Dict[str, Dict[str, Any]]:
    """List all available providers with their information."""
    return {
        PROVIDER_ZAI: get_provider_info(PROVIDER_ZAI),
        PROVIDER_OPENROUTER: get_provider_info(PROVIDER_OPENROUTER),
        PROVIDER_MOCK: {
            "name": "Mock",
            "models": ["mock"],
            "env_var": None,
            "default_model": "mock",
            "description": "Template-based mock generation for testing"
        }
    }


if __name__ == "__main__":
    import sys
    
    print("=" * 60)
    print("LLM Client Factory - Provider Information")
    print("=" * 60)
    print()
    
    # Show current default
    print(f"Current default provider: {DEFAULT_PROVIDER}")
    print(f"OpenRouter default model: {DEFAULT_OPENROUTER_MODEL}")
    print(f"Z.AI default model: {DEFAULT_ZAI_MODEL}")
    print()
    
    # List providers
    print("Available Providers:")
    print("-" * 60)
    
    providers = list_providers()
    for key, info in providers.items():
        if "error" not in info:
            print(f"\n[{key.upper()}] {info['name']}")
            print(f"  Description: {info['description']}")
            print(f"  Env Var: {info['env_var'] or 'N/A'}")
            print(f"  Default Model: {info['default_model']}")
            print(f"  Models: {', '.join(info['models'][:4])}")
    
    print()
    print("-" * 60)
    print("Usage in environment:")
    print("  export LLM_PROVIDER=openrouter     # Set default provider")
    print("  export OPENROUTER_API_KEY=sk-...   # Set OpenRouter key")
    print("  export ZAI_API_KEY=...            # Set Z.AI key")
    print()
    
    # Test client creation
    print("-" * 60)
    print("Testing client creation:")
    print()
    
    for provider in [PROVIDER_ZAI, PROVIDER_OPENROUTER, PROVIDER_MOCK]:
        try:
            client = create_llm_client(provider=provider, use_mock=(provider == PROVIDER_MOCK))
            print(f"✓ {provider.upper()}: Client created successfully")
        except Exception as e:
            print(f"✗ {provider.upper()}: {e}")
    
    print()
    print("Note: Real API calls require valid API keys in environment variables.")
