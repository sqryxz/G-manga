"""
G-Manga - Entry point for python -m g_manga

Usage:
    python -m g_manga [command] [options]
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent
sys.path.insert(0, str(src_path))

from cli import app

if __name__ == "__main__":
    app()
