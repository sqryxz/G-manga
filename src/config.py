"""
Settings Management - Centralized configuration for G-Manga
"""

import os
from pathlib import Path
from typing import Optional, List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMSettings(BaseSettings):
    """LLM-related settings."""
    model_config = SettingsConfigDict(env_prefix="LLM_")
    
    # Provider selection
    provider: str = Field(
        default="openrouter",
        description="LLM provider: openai or openrouter"
    )
    
    # OpenRouter/OpenAI API key
    api_key: str = Field(
        default="",
        description="API key (set via OPENROUTER_API_KEY or OPENAI_API_KEY env var)"
    )
    
    # Optional attribution for OpenRouter
    http_referer: str = Field(
        default="",
        description="Website URL for OpenRouter rankings"
    )
    x_title: str = Field(
        default="G-Manga",
        description="Application name for OpenRouter"
    )
    
    # API settings
    api_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        description="Base URL for LLM API"
    )
    api_timeout: int = Field(
        default=60,
        description="Timeout for LLM API calls in seconds"
    )
    max_retries: int = Field(
        default=3,
        description="Maximum retries for failed API calls"
    )
    
    # Stage-specific model configurations
    scene_breakdown_model: str = Field(
        default="openai/gpt-4o",
        description="Model for scene breakdown and summarization"
    )
    character_extraction_model: str = Field(
        default="openai/gpt-4o",
        description="Model for character extraction and descriptions"
    )
    visual_adaptation_model: str = Field(
        default="anthropic/claude-sonnet-4-20250514",
        description="Model for prose-to-visual adaptation"
    )
    panel_breakdown_model: str = Field(
        default="openai/gpt-4o-mini",
        description="Model for panel breakdown and pacing"
    )
    storyboard_generation_model: str = Field(
        default="openai/gpt-4o",
        description="Model for detailed storyboard generation"
    )
    
    # Fallback models (tried in order if primary fails)
    fallback_models: List[str] = Field(
        default_factory=lambda: [
            "openai/gpt-4o",
            "anthropic/claude-sonnet-4-20250514",
            "google/gemini-2.5-pro"
        ],
        description="Fallback model chain for reliability"
    )
    
    def get_api_key(self) -> str:
        """
        Get API key from config or environment.

        Returns:
            API key string

        Raises:
            ValueError: If no API key is configured
        """
        import warnings

        if self.api_key:
            return self.api_key

        # Check environment variables
        if self.provider == "openrouter":
            key = os.getenv("OPENROUTER_API_KEY", "")
        else:
            key = os.getenv("OPENAI_API_KEY", "")

        if not key:
            warnings.warn(
                f"No API key configured for {self.provider}. "
                "Set OPENROUTER_API_KEY or OPENAI_API_KEY environment variable, "
                "or configure in config.yaml",
                UserWarning
            )
            return ""

        return key

    def validate_api_key(self) -> bool:
        """
        Validate that an API key is configured.

        Returns:
            True if API key is available, False otherwise
        """
        return bool(self.get_api_key())


class DALLESettings(BaseSettings):
    """DALL-E 3 specific settings."""
    model_config = SettingsConfigDict(env_prefix="IMAGE_DALLE_")
    
    enabled: bool = Field(
        default=True,
        description="Enable DALL-E 3 provider"
    )
    model: str = Field(
        default="dall-e-3",
        description="DALL-E model version"
    )
    size: str = Field(
        default="1024x1024",
        description="DALL-E image size"
    )
    quality: str = Field(
        default="hd",
        description="DALL-E image quality (standard or hd)"
    )
    style: str = Field(
        default="vivid",
        description="Image style (vivid or natural)"
    )
    api_key_env: str = Field(
        default="OPENAI_API_KEY",
        description="Environment variable for API key"
    )
    cost_per_image: float = Field(
        default=0.04,
        description="Cost per image in USD"
    )
    rate_limit: int = Field(
        default=10,
        description="Rate limit (requests per minute)"
    )
    timeout: int = Field(
        default=60,
        description="Timeout in seconds"
    )
    max_retries: int = Field(
        default=3,
        description="Maximum retry attempts"
    )


class SDXLSettings(BaseSettings):
    """Stability AI SDXL specific settings."""
    model_config = SettingsConfigDict(env_prefix="IMAGE_SDXL_")
    
    enabled: bool = Field(
        default=True,
        description="Enable SDXL provider"
    )
    model: str = Field(
        default="stable-diffusion-xl-1024-v1-0",
        description="SDXL model identifier"
    )
    size: str = Field(
        default="1024x1024",
        description="Default image size"
    )
    steps: int = Field(
        default=30,
        description="Number of diffusion steps"
    )
    cfg_scale: float = Field(
        default=7.5,
        description="Classifier-free guidance scale"
    )
    api_key_env: str = Field(
        default="STABILITY_API_KEY",
        description="Environment variable for API key"
    )
    cost_per_image: float = Field(
        default=0.04,
        description="Cost per image in USD"
    )
    rate_limit: int = Field(
        default=20,
        description="Rate limit (requests per minute)"
    )
    timeout: int = Field(
        default=60,
        description="Timeout in seconds"
    )
    max_retries: int = Field(
        default=3,
        description="Maximum retry attempts"
    )


class OpenRouterSettings(BaseSettings):
    """OpenRouter image generation settings."""
    model_config = SettingsConfigDict(env_prefix="IMAGE_OPENROUTER_")
    
    enabled: bool = Field(
        default=True,
        description="Enable OpenRouter provider"
    )
    default_model: str = Field(
        default="stabilityai/stable-diffusion-xl-base-1.0",
        description="Default model identifier"
    )
    available_models: list = Field(
        default_factory=lambda: [
            "stabilityai/stable-diffusion-xl-base-1.0",
            "stabilityai/stable-diffusion-xl-refiner-1.0",
            "runwayml/stable-diffusion-v1-5",
        ],
        description="Available models"
    )
    size: str = Field(
        default="1024x1024",
        description="Default image size"
    )
    api_key_env: str = Field(
        default="OPENROUTER_API_KEY",
        description="Environment variable for API key"
    )
    attribution_http_referer: str = Field(
        default="",
        description="Website URL for OpenRouter rankings"
    )
    attribution_x_title: str = Field(
        default="G-Manga",
        description="Application name for OpenRouter"
    )
    cost_per_image: float = Field(
        default=0.01,
        description="Cost per image in USD (varies by model)"
    )
    rate_limit: int = Field(
        default=20,
        description="Rate limit (requests per minute)"
    )
    timeout: int = Field(
        default=60,
        description="Timeout in seconds"
    )
    max_retries: int = Field(
        default=3,
        description="Maximum retry attempts"
    )


class MidjourneySettings(BaseSettings):
    """Midjourney specific settings."""
    model_config = SettingsConfigDict(env_prefix="IMAGE_MIDJOURNEY_")
    
    enabled: bool = Field(
        default=False,
        description="Enable Midjourney provider (requires additional setup)"
    )
    api_key_env: str = Field(
        default="MIDJOURNEY_API_KEY",
        description="Environment variable for API key"
    )
    cost_per_image: float = Field(
        default=0.10,
        description="Cost per image in USD (approximate)"
    )


class ImageGenerationSettings(BaseSettings):
    """Image generation settings."""
    model_config = SettingsConfigDict(env_prefix="IMAGE_")
    
    # Default provider
    default_provider: str = Field(
        default="dalle3",
        description="Default image generation provider"
    )
    
    # Provider-specific settings
    dalle: DALLESettings = Field(
        default_factory=DALLESettings,
        description="DALL-E 3 configuration"
    )
    
    sdxl: SDXLSettings = Field(
        default_factory=SDXLSettings,
        description="SDXL configuration"
    )
    
    openrouter: OpenRouterSettings = Field(
        default_factory=OpenRouterSettings,
        description="OpenRouter configuration"
    )
    
    midjourney: MidjourneySettings = Field(
        default_factory=MidjourneySettings,
        description="Midjourney configuration"
    )


class MangaSettings(BaseSettings):
    """Manga-specific styling settings."""
    model_config = SettingsConfigDict(env_prefix="MANGA_")
    
    reading_direction: str = Field(
        default="left_to_right",
        description="Reading direction (left_to_right or right_to_left)"
    )
    line_weight: str = Field(
        default="medium",
        description="Line weight (thin, medium, bold)"
    )
    shading_style: str = Field(
        default="screen_tones",
        description="Shading style (hatching, screen_tones, solid)"
    )
    color_mode: str = Field(
        default="black_and_white",
        description="Color mode (black_and_white, grayscale, color)"
    )
    panel_style: str = Field(
        default="traditional_borders",
        description="Panel border style"
    )
    default_page_size: str = Field(
        default="A4",
        description="Default page size for export"
    )


class StorageSettings(BaseSettings):
    """Storage and caching settings."""
    model_config = SettingsConfigDict(env_prefix="STORAGE_")
    
    cache_dir: str = Field(
        default="./cache",
        description="Directory for caching"
    )
    output_dir: str = Field(
        default="./output",
        description="Directory for output files"
    )
    projects_dir: str = Field(
        default="./projects",
        description="Directory for project files"
    )
    keep_intermediates: bool = Field(
        default=False,
        description="Keep intermediate files after completion"
    )


class Settings(BaseSettings):
    """Main settings class combining all configuration sections."""
    
    # LLM Configuration
    llm: LLMSettings = Field(default_factory=LLMSettings)
    
    # Image Generation Configuration
    image: ImageGenerationSettings = Field(default_factory=ImageGenerationSettings)
    
    # Manga Styling Configuration
    manga: MangaSettings = Field(default_factory=MangaSettings)
    
    # Storage Configuration
    storage: StorageSettings = Field(default_factory=StorageSettings)
    
    # Global settings
    debug_mode: bool = Field(
        default=False,
        description="Enable debug mode for additional logging"
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR)"
    )
    
    @classmethod
    def from_yaml(cls, config_path: str) -> "Settings":
        """
        Load settings from YAML file.
        
        Args:
            config_path: Path to YAML configuration file
            
        Returns:
            Settings instance
        """
        import yaml
        
        config_file = Path(config_path)
        if not config_file.exists():
            return cls()
        
        with open(config_file, 'r') as f:
            config_data = yaml.safe_load(f) or {}
        
        return cls(**config_data)
    
    def save_yaml(self, config_path: str) -> None:
        """
        Save settings to YAML file.
        
        Args:
            config_path: Path to YAML configuration file
        """
        import yaml
        
        config_data = self.model_dump(exclude_none=True)
        
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f, default_flow_style=False, indent=2)
    
    def get_llm_model(self, stage: str) -> str:
        """
        Get the configured LLM model for a specific stage.
        
        Args:
            stage: Stage name (scene_breakdown, character_extraction, etc.)
            
        Returns:
            Model name for the specified stage
        """
        stage_mapping = {
            "scene_breakdown": self.llm.scene_breakdown_model,
            "character_extraction": self.llm.character_extraction_model,
            "visual_adaptation": self.llm.visual_adaptation_model,
            "panel_breakdown": self.llm.panel_breakdown_model,
            "storyboard_generation": self.llm.storyboard_generation_model,
        }
        
        return stage_mapping.get(stage, self.llm.scene_breakdown_model)
    
    def get_image_provider(self) -> str:
        """
        Get the configured default image provider.
        
        Returns:
            Provider name
        """
        return self.image.default_provider


# Global settings instance (lazy loaded)
_settings: Optional[Settings] = None


def get_settings(config_path: Optional[str] = None) -> Settings:
    """
    Get global settings instance.
    
    Args:
        config_path: Optional path to config.yaml file
        
    Returns:
        Settings instance
    """
    global _settings
    
    if _settings is None:
        if config_path and Path(config_path).exists():
            _settings = Settings.from_yaml(config_path)
        else:
            _settings = Settings()
    
    return _settings


def reset_settings() -> None:
    """Reset global settings (useful for testing)."""
    global _settings
    _settings = None
