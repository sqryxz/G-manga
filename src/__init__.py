"""G-Manga - Transform Project Gutenberg literature into manga-styled comics"""

__version__ = "0.1.0"
__author__ = "sqryxz"

from .config import Settings, get_settings
from .cli import main as cli_main

__all__ = ["Settings", "get_settings", "__version__", "cli_main"]
