"""
OpenRouter LLM Client - Unified API for 100+ AI models
"""

import json
import logging
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

import requests

from config import get_settings
from common.logging import get_logger


@dataclass
class GenerationResult:
    """Result from LLM generation."""
    success: bool
    text: str
    model: str
    tokens_used: int = 0
    cost_usd: float = 0.0
    error: Optional[str] = None
    latency_ms: int = 0
    timestamp: Optional[datetime] = None


class OpenRouterClient:
    """Client for OpenRouter API with fallback support."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenRouter client.

        Args:
            api_key: OpenRouter API key (optional, loads from config/env)
        """
        self.logger = get_logger(__name__)
        settings = get_settings()
        llm = settings.llm

        self.api_key = api_key or llm.get_api_key()
        self.base_url = llm.api_base_url.rstrip('/')
        self.http_referer = llm.http_referer
        self.x_title = llm.x_title
        self.timeout = llm.api_timeout
        self.max_retries = llm.max_retries
        self.fallback_models = llm.fallback_models

        if not self.api_key:
            self.logger.warning("No API key configured. Set OPENROUTER_API_KEY or configure in config.yaml")
            raise ValueError(
                "OpenRouter API key not configured. "
                "Set OPENROUTER_API_KEY env var or configure in config.yaml"
            )

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API request."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.http_referer,
            "X-Title": self.x_title,
        }
        # Remove empty headers
        return {k: v for k, v in headers.items() if v}

    def _make_request(
        self,
        prompt: str,
        model: str,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs
    ) -> GenerationResult:
        """
        Make a single API request to OpenRouter.

        Args:
            prompt: Input prompt
            model: Model ID (e.g., "openai/gpt-4o")
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation
            **kwargs: Additional parameters

        Returns:
            GenerationResult with response or error
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

            # Estimate cost (OpenRouter provides this in response)
            # Note: Actual costs may vary
            tokens = data.get("usage", {}).get("total_tokens", 0)
            cost = data.get("usage", {}).get("completion_tokens", 0) * 0.00006  # Rough estimate

            return GenerationResult(
                success=True,
                text=text,
                model=model,
                tokens_used=tokens,
                cost_usd=cost,
                latency_ms=latency_ms,
                timestamp=datetime.utcnow()
            )

        except requests.exceptions.Timeout:
            return GenerationResult(
                success=False,
                text="",
                model=model,
                error="Request timeout",
                latency_ms=self.timeout * 1000,
                timestamp=datetime.utcnow()
            )
        except requests.exceptions.RequestException as e:
            return GenerationResult(
                success=False,
                text="",
                model=model,
                error=str(e),
                latency_ms=int((time.time() - start_time) * 1000),
                timestamp=datetime.utcnow()
            )

    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        use_fallback: bool = True,
        **kwargs
    ) -> GenerationResult:
        """
        Generate text using OpenRouter.

        Args:
            prompt: Input prompt
            model: Specific model to use (optional)
            use_fallback: Try fallback models if primary fails
            **kwargs: Additional generation parameters

        Returns:
            GenerationResult with response
        """
        if model:
            models_to_try = [model] + self.fallback_models if use_fallback else [model]
        else:
            models_to_try = self.fallback_models

        last_error = None
        for model in models_to_try:
            result = self._make_request(prompt, model, **kwargs)

            if result.success:
                return result

            last_error = result.error
            continue

        # All models failed
        return GenerationResult(
            success=False,
            text="",
            model=models_to_try[0] if models_to_try else "unknown",
            error=f"All models failed: {last_error}" if last_error else "No models available",
            timestamp=datetime.utcnow()
        )

    def generate_batch(
        self,
        prompts: List[str],
        model: Optional[str] = None,
        **kwargs
    ) -> List[GenerationResult]:
        """
        Generate text for multiple prompts.

        Args:
            prompts: List of input prompts
            model: Model to use (optional)
            **kwargs: Additional generation parameters

        Returns:
            List of GenerationResults
        """
        return [self.generate(p, model, **kwargs) for p in prompts]

    def get_available_models(self) -> List[Dict[str, str]]:
        """
        Get list of available models from OpenRouter.

        Returns:
            List of model information dictionaries
        """
        try:
            response = requests.get(
                url=f"{self.base_url}/models",
                headers=self._get_headers(),
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            return [
                {
                    "id": m.get("id", ""),
                    "name": m.get("name", ""),
                    "provider": m.get("id", "").split("/")[0] if "/" in m.get("id", "") else "unknown"
                }
                for m in data.get("data", [])
            ]
        except Exception as e:
            self.logger.error(f"Failed to fetch models: {e}")
            return []

    def estimate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """
        Estimate cost for a generation.

        Note: This is a rough estimate. Actual costs vary by model.
        See https://openrouter.ai/docs for current pricing.

        Args:
            model: Model ID
            prompt_tokens: Number of input tokens
            completion_tokens: Number of output tokens

        Returns:
            Estimated cost in USD
        """
        # Rough pricing per 1M tokens (USD)
        pricing = {
            "openai/gpt-4o": {"input": 5.00, "output": 15.00},
            "openai/gpt-4o-mini": {"input": 0.15, "output": 0.60},
            "anthropic/claude-sonnet-4-20250514": {"input": 3.00, "output": 15.00},
            "anthropic/claude-haiku-3-5-20250514": {"input": 0.25, "output": 1.25},
            "google/gemini-2.5-pro": {"input": 1.25, "output": 5.00},
            "deepseek/deepseek-chat": {"input": 0.14, "output": 0.28},
        }

        # Default pricing (very rough)
        default = {"input": 2.00, "output": 10.00}

        rates = pricing.get(model, default)

        return (prompt_tokens / 1_000_000) * rates["input"] + \
               (completion_tokens / 1_000_000) * rates["output"]


class CostTracker:
    """Track API usage and costs."""

    def __init__(self):
        self.total_requests: int = 0
        self.total_tokens: int = 0
        self.total_cost: float = 0.0
        self.results: List[GenerationResult] = []

    def add_result(self, result: GenerationResult) -> None:
        """Add a generation result to tracking."""
        self.total_requests += 1
        self.total_tokens += result.tokens_used
        self.total_cost += result.cost_usd
        self.results.append(result)

    def get_summary(self) -> Dict[str, Any]:
        """Get usage summary."""
        success_count = sum(1 for r in self.results if r.success)
        return {
            "total_requests": self.total_requests,
            "successful_requests": success_count,
            "failed_requests": self.total_requests - success_count,
            "total_tokens": self.total_tokens,
            "total_cost_usd": round(self.total_cost, 4),
            "avg_latency_ms": sum(r.latency_ms for r in self.results) / max(1, len(self.results))
        }

    def reset(self) -> None:
        """Reset tracking."""
        self.total_requests = 0
        self.total_tokens = 0
        self.total_cost = 0.0
        self.results = []


# Global cost tracker
cost_tracker = CostTracker()


def create_openrouter_client(api_key: Optional[str] = None) -> OpenRouterClient:
    """
    Create an OpenRouter client.

    Args:
        api_key: Optional API key

    Returns:
        OpenRouterClient instance
    """
    return OpenRouterClient(api_key)


def generate_with_openrouter(
    prompt: str,
    model: Optional[str] = None,
    use_fallback: bool = True,
    track_cost: bool = True,
    **kwargs
) -> GenerationResult:
    """
    Convenience function for single generation.

    Args:
        prompt: Input prompt
        model: Model to use (optional)
        use_fallback: Try fallback models
        track_cost: Track usage and costs
        **kwargs: Additional parameters

    Returns:
        GenerationResult
    """
    client = create_openrouter_client()
    result = client.generate(prompt, model, use_fallback, **kwargs)

    if track_cost:
        cost_tracker.add_result(result)

    return result


if __name__ == "__main__":
    # Test the client
    logger = logging.getLogger("g_manga")
    logger.info("OpenRouter Client Test")

    try:
        client = create_openrouter_client()

        # List available models
        logger.info("Fetching available models...")
        models = client.get_available_models()
        logger.info(f"Found {len(models)} models")

        # Show models by provider
        providers = {}
        for m in models:
            p = m["provider"]
            if p not in providers:
                providers[p] = []
            providers[p].append(m)

        for provider, model_list in providers.items():
            logger.info(f"{provider}: {len(model_list)} models")

        # Test generation
        logger.info("Testing generation...")
        result = client.generate(
            prompt="Say hello in exactly 3 words.",
            model="openai/gpt-4o-mini"
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
        logger.info("  export OPENROUTER_API_KEY='sk-or-v1-...'")
