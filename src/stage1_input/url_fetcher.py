"""
URL Fetcher - Stage 1.1.1
Fetches content from Project Gutenberg URLs with retry logic and caching.
"""

import logging
import requests
import time
import hashlib
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from common.logging import get_logger


class URLFetcher:
    """Fetches and caches content from URLs with retry logic."""

    def __init__(self, cache_dir: str = None, timeout: int = 30):
        """
        Initialize the URL Fetcher.

        Args:
            cache_dir: Directory to cache downloaded content. Defaults to ./cache/downloads/
            timeout: Request timeout in seconds
        """
        self.logger = get_logger(__name__)
        self.cache_dir = Path(cache_dir) if cache_dir else Path("./cache/downloads")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout

        # User agent for Gutenberg compatibility
        self.headers = {
            "User-Agent": "Mozilla/5.0 (compatible; G-Manga/0.1; +https://github.com/sqryxz/g-manga)"
        }

        # Retry configuration
        self.max_retries = 3
        self.base_delay = 1  # seconds
        self.max_delay = 10  # seconds

    def _get_cache_key(self, url: str) -> str:
        """Generate a cache key from URL."""
        return hashlib.md5(url.encode()).hexdigest()

    def _get_cache_path(self, url: str) -> Path:
        """Get cache file path for a URL."""
        cache_key = self._get_cache_key(url)
        # Extract extension from URL if possible
        parsed = urlparse(url)
        extension = Path(parsed.path).suffix or ".txt"
        return self.cache_dir / f"{cache_key}{extension}"

    def _load_from_cache(self, url: str) -> Optional[str]:
        """
        Load content from cache if available.

        Args:
            url: The URL to check cache for

        Returns:
            Cached content as string, or None if not cached
        """
        cache_path = self._get_cache_path(url)
        if cache_path.exists():
            self.logger.debug(f"Cache hit for URL: {url}")
            return cache_path.read_text(encoding="utf-8")
        return None

    def _save_to_cache(self, url: str, content: str) -> None:
        """
        Save content to cache.

        Args:
            url: The URL this content came from
            content: The content to cache
        """
        cache_path = self._get_cache_path(url)
        cache_path.write_text(content, encoding="utf-8")
        self.logger.debug(f"Cached content for URL: {url}")

    def fetch(self, url: str, use_cache: bool = True, timeout: Optional[int] = None) -> str:
        """
        Fetch content from a URL with retry logic and caching.

        Args:
            url: The URL to fetch
            use_cache: Whether to use cached content if available
            timeout: Request timeout in seconds (overrides default)

        Returns:
            The fetched content as string

        Raises:
            requests.RequestException: If all retries fail
        """
        request_timeout = timeout or self.timeout

        # Check cache first
        if use_cache:
            cached = self._load_from_cache(url)
            if cached:
                self.logger.info(f"Using cached content for {url}")
                return cached

        self.logger.info(f"Fetching URL: {url}")

        # Fetch with retries
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                response = requests.get(
                    url,
                    headers=self.headers,
                    timeout=request_timeout
                )
                response.raise_for_status()

                content = response.text
                content_length = len(content)

                # Cache the content
                self._save_to_cache(url, content)

                self.logger.info(f"Successfully fetched {url} ({content_length:,} characters)")
                return content

            except requests.RequestException as e:
                last_exception = e
                self.logger.warning(f"Attempt {attempt + 1}/{self.max_retries} failed: {e}")

                if attempt < self.max_retries - 1:
                    # Exponential backoff with jitter
                    delay = min(
                        self.base_delay * (2 ** attempt) + (time.time() % 1),
                        self.max_delay
                    )
                    self.logger.debug(f"Retrying in {delay:.1f} seconds...")
                    time.sleep(delay)

        # All retries failed
        error_msg = f"Failed to fetch {url} after {self.max_retries} attempts. Last error: {last_exception}"
        self.logger.error(error_msg)
        raise requests.RequestException(error_msg) from last_exception

    def clear_cache(self) -> None:
        """Clear all cached files."""
        count = 0
        for cache_file in self.cache_dir.iterdir():
            if cache_file.is_file():
                cache_file.unlink()
                count += 1
        self.logger.info(f"Cleared {count} cached files")


def main():
    """Test the URL Fetcher with a Project Gutenberg URL."""
    # Example: The Picture of Dorian Gray
    test_url = "https://www.gutenberg.org/files/174/174-0.txt"

    fetcher = URLFetcher()
    content = fetcher.fetch(test_url)

    print(f"Fetched {len(content)} characters")
    print(f"First 200 characters:\n{content[:200]}")


if __name__ == "__main__":
    main()
