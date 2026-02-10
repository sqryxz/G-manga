"""
Logging Configuration - Centralized logging for G-Manga
"""

import logging
import sys
from pathlib import Path
from typing import Optional


# Default log format
DEFAULT_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logger(
    name: str = "g_manga",
    level: str = "INFO",
    log_file: Optional[str] = None,
    format_str: Optional[str] = None,
    date_format: Optional[str] = None,
    force: bool = True
) -> logging.Logger:
    """
    Set up a configured logger for G-Manga.

    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional file path for logging
        format_str: Custom format string
        date_format: Custom date format
        force: Reconfigure even if logger exists

    Returns:
        Configured logger instance
    """
    # Convert string level to int
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    log_level = level_map.get(level.upper(), logging.INFO)

    # Get or create logger
    logger = logging.getLogger(name)

    # Only configure if needed
    if force or not logger.handlers:
        logger.setLevel(log_level)

        # Create handler for stdout
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(log_level)

        # Set format
        fmt = format_str or DEFAULT_FORMAT
        date_fmt = date_format or DEFAULT_DATE_FORMAT
        formatter = logging.Formatter(fmt=fmt, datefmt=date_fmt)
        handler.setFormatter(formatter)

        logger.addHandler(handler)

        # Add file handler if specified
        if log_file:
            Path(log_file).parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a specific module.

    Args:
        name: Module name (usually __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(f"g_manga.{name}")


class LogContext:
    """Context manager for temporary log level changes."""

    def __init__(self, logger: logging.Logger, level: str = "DEBUG"):
        """
        Initialize context manager.

        Args:
            logger: Logger to modify
            level: Temporary log level
        """
        self.logger = logger
        self.original_level = logger.level
        self.temp_level = level

    def __enter__(self):
        """Enter context and set debug level."""
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
        }
        self.logger.setLevel(level_map.get(self.temp_level, logging.DEBUG))
        return self.logger

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and restore original level."""
        self.logger.setLevel(self.original_level)


class ProgressLogger:
    """Logger with progress tracking for long operations."""

    def __init__(self, logger: logging.Logger, total: int, description: str = "Processing"):
        """
        Initialize progress logger.

        Args:
            logger: Logger instance
            total: Total number of items
            description: Description of the operation
        """
        self.logger = logger
        self.total = total
        self.current = 0
        self.description = description
        self.start_time = None

    def update(self, items_processed: int = 1, message: str = ""):
        """
        Update progress.

        Args:
            items_processed: Number of items processed
            message: Status message
        """
        self.current += items_processed
        percentage = (self.current / self.total) * 100

        if message:
            self.logger.info(f"{self.description}: {self.current}/{self.total} ({percentage:.1f}%) - {message}")
        else:
            self.logger.info(f"{self.description}: {self.current}/{self.total} ({percentage:.1f}%)")

    def complete(self, final_message: str = "Completed"):
        """Log completion."""
        self.logger.info(f"{self.description}: 100% - {final_message}")


# Default logger instance
_default_logger: Optional[logging.Logger] = None


def get_default_logger() -> logging.Logger:
    """Get or create the default G-Manga logger."""
    global _default_logger

    if _default_logger is None:
        _default_logger = setup_logger("g_manga")

    return _default_logger


def configure_from_settings(settings) -> logging.Logger:
    """
    Configure logging from Settings object.

    Args:
        settings: Settings object with log_level and debug_mode

    Returns:
        Configured logger
    """
    level = "DEBUG" if settings.debug_mode else settings.log_level
    return setup_logger("g_manga", level=level)


if __name__ == "__main__":
    # Demo logging setup
    logger = setup_logger("g_manga.demo", level="DEBUG")

    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")

    # Progress logging
    progress = ProgressLogger(logger, total=10, description="Processing chapters")
    for i in range(10):
        progress.update(message=f"Chapter {i+1}")
    progress.complete("All chapters processed")
