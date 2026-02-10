"""
Settings Management - Centralized configuration for G-Manga
"""

from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMSettings(BaseSettings):
    """LLM-related settings."""
    model_config = SettingsConfigDict(env_prefix="LLM_")
    
    # Stage-specific model configurations
    scene_breakdown_model: str = Field(
        default="gpt-4o",
        description="Model for scene breakdown and summarization"
    )
    character_extraction_model: str = Field(
        default="gpt-4o",
        description="Model for character extraction and descriptions"
    )
    visual_adaptation_model: str = Field(
        default="gpt-4o",
        description="Model for prose-to-visual adaptation"
    )
    panel_breakdown_model: str = Field(
        default="gpt-4o-mini",
        description="Model for panel breakdown and pacing"
    )
    storyboard_generation_model: str = Field(
        default="gpt-4o",
        description="Model for detailed storyboard generation"
    )
    
    # API settings
    api_base_url: str = Field(
        default="https://api.openai.com/v1",
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


class ImageGenerationSettings(BaseSettings):
    """Image generation settings."""
    model_config = SettingsConfigDict(env_prefix="IMAGE_")
    
    # Default provider
    default_provider: str = Field(
        default="dalle3",
        description="Default image generation provider"
    )
    
    # DALL-E 3 settings
    dalle_model: str = Field(
        default="dall-e-3",
        description="DALL-E model version"
    )
    dalle_size: str = Field(
        default="1024x1024",
        description="DALL-E image size"
    )
    dalle_quality: str = Field(
        default="hd",
        description="DALL-E image quality (standard or hd)"
    )
    
    # SDXL settings
    sdxl_model: str = Field(
        default="stabilityai/stable-diffusion-xl-base-1.0",
        description="SDXL model identifier"
    )
    
    # Midjourney settings
    midjourney_enabled: bool = Field(
        default=False,
        description="Enable Midjourney API (requires additional setup)"
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
