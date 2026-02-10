"""
Automatic Logging Decorator
Decorator for automatic task completion logging.
"""

from functools import wraps
from typing import Callable, Any, Optional


def log_completion(stage: str, subtask: str):
    """
    Decorator to automatically log task completion.

    Args:
        stage: Stage number/name (e.g., "Stage 1")
        subtask: Subtask name (e.g., "1.1.1 Implement URL Fetcher")

    Usage:
        @log_completion("Stage 1", "1.1.1 Implement URL Fetcher")
        def my_function():
            # ... implementation ...
            return result

        # When my_function() completes, it automatically logs:
        # ✓ Logged: [Stage 1] 1.1.1 Implement URL Fetcher - complete
    """
    def decorator(func: Callable) -> Callable:
        """Wrap function to log completion."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                # Log completion
                import sys
                import os
                sys.path.insert(0, os.path.expanduser('~/projects/g-manga/src'))
                from progress_logger import ProgressLogger

                logger = ProgressLogger()
                logger.log_subtask(stage, subtask, "complete")

                return result
            except Exception as e:
                # Log failure
                import sys
                import os
                sys.path.insert(0, os.path.expanduser('~/projects/g-manga/src'))
                from progress_logger import ProgressLogger

                logger = ProgressLogger()
                logger.fail_subtask(stage, subtask, str(e))

                raise e
        return wrapper
    return decorator


# Example usage in modules:
if __name__ == "__main__":
    # Test the decorator
    @log_completion("Stage 1", "1.1.1 Implement URL Fetcher")
    def fetch_url():
        print("Fetching URL...")
        return "URL content"

    result = fetch_url()
    print(f"Result: {result}")
