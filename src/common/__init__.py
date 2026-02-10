"""Common utilities for G-Manga"""

from .mocking import MockLLMClient, BaseLLMClient
from .openrouter import (
    OpenRouterClient,
    create_openrouter_client,
    generate_with_openrouter,
    GenerationResult,
    cost_tracker
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
    # Logging
    "setup_logger",
    "get_logger",
    "get_default_logger",
    "ProgressLogger",
    "LogContext",
    "configure_from_settings",
]
