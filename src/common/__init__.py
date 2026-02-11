"""Common utilities for G-Manga"""

from .mocking import MockLLMClient, BaseLLMClient
from .openrouter import (
    OpenRouterClient,
    create_openrouter_client,
    generate_with_openrouter,
    GenerationResult,
    cost_tracker
)
from .zai_client import (
    ZAIClient,
    ZAIClientAdapter,
    ZAIGenerationResult,
    create_zai_client,
    generate_with_zai
)
from .logging import (
    setup_logger,
    get_logger,
    get_default_logger,
    ProgressLogger,
    LogContext,
    configure_from_settings
)

__all__ = [
    # Mocking
    "MockLLMClient",
    "BaseLLMClient",
    # OpenRouter
    "OpenRouterClient",
    "create_openrouter_client",
    "generate_with_openrouter",
    "GenerationResult",
    "cost_tracker",
    # Z.AI
    "ZAIClient",
    "ZAIClientAdapter",
    "ZAIGenerationResult",
    "create_zai_client",
    "generate_with_zai",
    # Logging
    "setup_logger",
    "get_logger",
    "get_default_logger",
    "ProgressLogger",
    "LogContext",
    "configure_from_settings",
]
