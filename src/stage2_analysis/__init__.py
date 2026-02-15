"""Module 2: Analysis Engine

Extracts structured narrative data from raw text:
- Characters (2A)
- Locations (2B)
- Plot Beats (2C)
- Dialogue (2D)
- Key Quotes
"""

from .schemas import (
    Character,
    Location,
    PlotBeat,
    Dialogue,
    KeyQuote,
    AnalysisResult
)
from .analysis_engine import AnalysisEngine

__all__ = [
    'Character',
    'Location', 
    'PlotBeat',
    'Dialogue',
    'KeyQuote',
    'AnalysisResult',
    'AnalysisEngine'
]
