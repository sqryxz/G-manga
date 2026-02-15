"""
Z.AI LLM Client - Integration with Z.AI API (https://z.ai)
Supports GLM-4.7 and other Z.AI models via OpenAI-compatible API

⚠️ SECURITY: API keys are loaded from environment variable ZAI_API_KEY
   Never hardcode keys in this file.
"""

import json
import logging
import time
import os
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime
from abc import ABC, abstractmethod

import requests
from typing import overload, Literal

from common.logging import get_logger


@dataclass
class ZAIGenerationResult:
    """Result from Z.AI LLM generation."""
    success: bool
    text: str
    model: str
    tokens_used: int = 0
    cost_usd: float = 0.0
    error: Optional[str] = None
    latency_ms: int = 0
    timestamp: Optional[datetime] = None


class BaseZAIClient(ABC):
    """Abstract base class for Z.AI clients."""
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> ZAIGenerationResult:
        """Generate text from prompt."""
        pass
    
    @abstractmethod
    def generate_batch(self, prompts: List[str], **kwargs) -> List[ZAIGenerationResult]:
        """Generate text from multiple prompts."""
        pass


class ZAIClient(BaseZAIClient):
    """
    Client for Z.AI API (https://z.ai).
    
    Z.AI provides GLM-4.7 and other models via OpenAI-compatible API.
    API Documentation: https://docs.z.ai/guides/overview/quick-start
    
    Supports both:
    - International endpoint: https://api.z.ai/api/paas/v4/
    - Chinese endpoint: https://open.bigmodel.cn/api/paas/v4/
    """

    # Available Z.AI models
    AVAILABLE_MODELS = {
        "glm-4.7": {
            "description": "GLM-4.7 - Latest general-purpose model",
            "max_tokens": 8192,
            "input_cost_per_1m": 0.50,
            "output_cost_per_1m": 0.50,
        },
        "glm-4.5": {
            "description": "GLM-4.5 - Previous generation",
            "max_tokens": 8192,
            "input_cost_per_1m": 0.30,
            "output_cost_per_1m": 0.30,
        },
        "glm-4.5-flash": {
            "description": "GLM-4.5 Flash - Fast, cost-effective",
            "max_tokens": 8192,
            "input_cost_per_1m": 0.10,
            "output_cost_per_1m": 0.10,
        },
        "glm-4.7-coding": {
            "description": "GLM-4.7 Coding - Optimized for code",
            "max_tokens": 8192,
            "input_cost_per_1m": 0.50,
            "output_cost_per_1m": 0.50,
        },
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.z.ai/api/paas/v4/",
        timeout: int = 60,
        max_retries: int = 3,
        default_model: str = "glm-4.7"
    ):
        """
        Initialize Z.AI client.

        Args:
            api_key: Z.AI API key (optional, loads from ZAI_API_KEY env var)
            base_url: API base URL (default: international endpoint)
            timeout: Request timeout in seconds
            max_retries: Max retry attempts for failed requests
            default_model: Default model to use
        """
        self.logger = get_logger(__name__)
        
        self.api_key = api_key or os.getenv("ZAI_API_KEY", "")
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        self.default_model = default_model
        
        if not self.api_key:
            self.logger.warning("No Z.AI API key configured. Set ZAI_API_KEY environment variable.")
            raise ValueError(
                "Z.AI API key not configured. "
                "Set ZAI_API_KEY env var or pass api_key parameter."
            )
        
        self.logger.info(f"Z.AI client initialized (endpoint: {self.base_url})")

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API request."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _make_request(
        self,
        prompt: str,
        model: str,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs
    ) -> ZAIGenerationResult:
        """
        Make a single API request to Z.AI.

        Args:
            prompt: Input prompt
            model: Model ID (e.g., "glm-4.7")
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation
            **kwargs: Additional parameters

        Returns:
            ZAIGenerationResult with response or error
        """
        start_time = time.time()

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
            **kwargs
        }

        try:
            response = requests.post(
                url=f"{self.base_url}/chat/completions",
                headers=self._get_headers(),
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()

            data = response.json()

            # Extract response
            text = data["choices"][0]["message"]["content"]

            # Calculate metrics
            latency_ms = int((time.time() - start_time) * 1000)
            tokens = data.get("usage", {}).get("total_tokens", 0)
            
            # Estimate cost
            cost = self._estimate_cost(model, tokens)

            return ZAIGenerationResult(
                success=True,
                text=text,
                model=model,
                tokens_used=tokens,
                cost_usd=cost,
                latency_ms=latency_ms,
                timestamp=datetime.utcnow()
            )

        except requests.exceptions.Timeout:
            return ZAIGenerationResult(
                success=False,
                text="",
                model=model,
                error="Request timeout",
                latency_ms=self.timeout * 1000,
                timestamp=datetime.utcnow()
            )
        except requests.exceptions.RequestException as e:
            return ZAIGenerationResult(
                success=False,
                text="",
                model=model,
                error=str(e),
                latency_ms=int((time.time() - start_time) * 1000),
                timestamp=datetime.utcnow()
            )
        except (KeyError, IndexError) as e:
            return ZAIGenerationResult(
                success=False,
                text="",
                model=model,
                error=f"Invalid response format: {str(e)}",
                latency_ms=int((time.time() - start_time) * 1000),
                timestamp=datetime.utcnow()
            )

    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        **kwargs
    ) -> ZAIGenerationResult:
        """
        Generate text using Z.AI.

        Args:
            prompt: Input prompt
            model: Specific model to use (defaults to self.default_model)
            **kwargs: Additional generation parameters

        Returns:
            ZAIGenerationResult with response
        """
        model_to_use = model or self.default_model
        
        # Retry logic
        last_error = None
        for attempt in range(self.max_retries):
            result = self._make_request(prompt, model_to_use, **kwargs)
            
            if result.success:
                return result
            
            last_error = result.error
            self.logger.warning(f"Attempt {attempt + 1}/{self.max_retries} failed: {last_error}")
            
            if attempt < self.max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
        
        # All retries failed
        return ZAIGenerationResult(
            success=False,
            text="",
            model=model_to_use,
            error=f"All retries failed: {last_error}" if last_error else "Generation failed",
            timestamp=datetime.utcnow()
        )

    def generate_batch(
        self,
        prompts: List[str],
        model: Optional[str] = None,
        **kwargs
    ) -> List[ZAIGenerationResult]:
        """
        Generate text for multiple prompts.

        Args:
            prompts: List of input prompts
            model: Model to use (optional)
            **kwargs: Additional generation parameters

        Returns:
            List of ZAIGenerationResults
        """
        return [self.generate(p, model, **kwargs) for p in prompts]

    def _estimate_cost(self, model: str, tokens: int) -> float:
        """
        Estimate cost for a generation.

        Args:
            model: Model ID
            tokens: Total tokens used

        Returns:
            Estimated cost in USD
        """
        model_info = self.AVAILABLE_MODELS.get(model, self.AVAILABLE_MODELS["glm-4.7"])
        cost_per_1m = model_info["input_cost_per_1m"]
        return (tokens / 1_000_000) * cost_per_1m

    def get_available_models(self) -> List[Dict[str, Any]]:
        """
        Get list of available Z.AI models.

        Returns:
            List of model information dictionaries
        """
        return [
            {
                "id": model_id,
                "description": info["description"],
                "max_tokens": info["max_tokens"],
                "cost_per_1m_tokens": info["input_cost_per_1m"],
            }
            for model_id, info in self.AVAILABLE_MODELS.items()
        ]

    def get_model_info(self, model: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific model.

        Args:
            model: Model ID

        Returns:
            Model information or None
        """
        return self.AVAILABLE_MODELS.get(model)


class ZAIClientAdapter:
    """
    Adapter to make ZAIClient compatible with BaseLLMClient interface.
    This allows Z.AI to be used interchangeably with other LLM clients.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.z.ai/api/paas/v4/",
        default_model: str = "glm-4.7",
        **kwargs
    ):
        """
        Initialize Z.AI adapter.

        Args:
            api_key: Z.AI API key
            base_url: API endpoint URL
            default_model: Default model for generation
            **kwargs: Additional client parameters
        """
        self.client = ZAIClient(
            api_key=api_key,
            base_url=base_url,
            default_model=default_model,
            **kwargs
        )
        self.default_model = default_model

    def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate text and return raw string (compatible with BaseLLMClient).

        Args:
            prompt: Input prompt
            **kwargs: Additional parameters (model, temperature, etc.)

        Returns:
            Generated text string
        """
        result = self.client.generate(prompt, **kwargs)
        
        if result.success:
            return result.text
        else:
            raise Exception(f"Z.AI generation failed: {result.error}")

    def generate_batch(self, prompts: List[str], **kwargs) -> List[str]:
        """
        Generate text for multiple prompts.

        Args:
            prompts: List of input prompts
            **kwargs: Additional parameters

        Returns:
            List of generated text strings
        """
        results = self.client.generate_batch(prompts, **kwargs)
        
        texts = []
        for result in results:
            if result.success:
                texts.append(result.text)
            else:
                texts.append(f"[Error: {result.error}]")
        
        return texts

    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available models (proxy to client)."""
        return self.client.get_available_models()

    def get_model_info(self, model: str) -> Optional[Dict[str, Any]]:
        """Get model info (proxy to client)."""
        return self.client.get_model_info(model)

    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics (for compatibility)."""
        return {
            "client_type": "zai",
            "default_model": self.default_model,
            "endpoint": self.client.base_url,
        }


@overload
def create_zai_client(
    *,
    use_adapter: Literal[True] = True,
    **kwargs
) -> ZAIClientAdapter: ...


@overload
def create_zai_client(
    *,
    use_adapter: Literal[False],
    **kwargs
) -> ZAIClient: ...


def create_zai_client(
    api_key: Optional[str] = None,
    base_url: str = "https://api.z.ai/api/paas/v4/",
    default_model: str = "glm-4.7",
    use_adapter: bool = True,
    **kwargs
) -> Union[ZAIClient, ZAIClientAdapter]:
    """
    Factory function to create Z.AI client.

    Args:
        api_key: Z.AI API key (or set ZAI_API_KEY env var)
        base_url: API endpoint
        default_model: Default model to use
        use_adapter: If True, returns adapter compatible with BaseLLMClient
        **kwargs: Additional client parameters

    Returns:
        ZAIClient or ZAIClientAdapter instance
    """
    if use_adapter:
        return ZAIClientAdapter(
            api_key=api_key,
            base_url=base_url,
            default_model=default_model,
            **kwargs
        )
    else:
        return ZAIClient(
            api_key=api_key,
            base_url=base_url,
            default_model=default_model,
            **kwargs
        )


# Convenience function for direct generation
def generate_with_zai(
    prompt: str,
    api_key: Optional[str] = None,
    model: str = "glm-4.7",
    **kwargs
) -> str:
    """
    Convenience function for single generation with Z.AI.

    Args:
        prompt: Input prompt
        api_key: Z.AI API key (or set ZAI_API_KEY env var)
        model: Model to use
        **kwargs: Additional parameters

    Returns:
        Generated text
    """
    client = create_zai_client(api_key=api_key, default_model=model, use_adapter=True)
    return client.generate(prompt, **kwargs)


if __name__ == "__main__":
    # Test the client
    logger = logging.getLogger("g_manga")
    logger.info("Z.AI Client Test")

    try:
        # Create client
        client = create_zai_client(use_adapter=False)
        
        # List available models
        logger.info("Available Z.AI models:")
        for model in client.get_available_models():
            logger.info(f"  - {model['id']}: {model['description']}")
        
        # Test generation
        logger.info("\nTesting generation...")
        result = client.generate(
            prompt="Generate a brief scene description for a manga panel showing an artist in a studio.",
            model="glm-4.7"
        )
        
        if result.success:
            logger.info(f"Response: {result.text}")
            logger.info(f"Model: {result.model}")
            logger.info(f"Tokens: {result.tokens_used}")
            logger.info(f"Cost: ${result.cost_usd:.6f}")
            logger.info(f"Latency: {result.latency_ms}ms")
        else:
            logger.error(f"Generation failed: {result.error}")
            
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        logger.info("To configure, set your API key:")
        logger.info("  export ZAI_API_KEY='your-api-key'")
    except Exception as e:
        logger.error(f"Error: {e}")
