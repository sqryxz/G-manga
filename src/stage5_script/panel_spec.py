"""Module 5: Panel Specifications - Layout templates and composition"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Tuple


class PanelLayout(Enum):
    """Pre-defined panel layouts."""
    SPLASH = "splash"  # Single full-page panel
    TWO_VERTICAL = "two_vertical"  # Two panels stacked
    TWO_HORIZONTAL = "two_horizontal"  # Two panels side by side
    THREE_TOP_HEAVY = "three_top_heavy"  # One wide top, two smaller bottom
    FOUR_GRID = "four_grid"  # 2x2 grid
    FIVE_DYNAMIC = "five_dynamic"  # Mixed sizes
    SIX_STANDARD = "six_standard"  # 3x2 grid
    SIX_DYNAMIC = "six_dynamic"  # Mixed 6-panel layout


@dataclass
class PanelPosition:
    """Position and size of a panel on a page."""
    x: int  # X coordinate (0-100 percentage)
    y: int  # Y coordinate (0-100 percentage)
    width: int  # Width (percentage)
    height: int  # Height (percentage)


# Standard page dimensions (A4 at 300 DPI)
PAGE_WIDTH = 2480
PAGE_HEIGHT = 3508
GUTTER = 20  # Gap between panels
BORDER = 3  # Panel border width


class PanelLayoutTemplates:
    """Pre-defined layout templates for manga pages."""
    
    LAYOUTS = {
        PanelLayout.SPLASH: [
            PanelPosition(0, 0, 100, 100)
        ],
        PanelLayout.TWO_VERTICAL: [
            PanelPosition(0, 0, 100, 48),
            PanelPosition(0, 52, 100, 48)
        ],
        PanelLayout.TWO_HORIZONTAL: [
            PanelPosition(0, 0, 48, 100),
            PanelPosition(52, 0, 48, 100)
        ],
        PanelLayout.THREE_TOP_HEAVY: [
            PanelPosition(0, 0, 100, 60),
            PanelPosition(0, 64, 48, 36),
            PanelPosition(52, 64, 48, 36)
        ],
        PanelLayout.FOUR_GRID: [
            PanelPosition(0, 0, 48, 48),
            PanelPosition(52, 0, 48, 48),
            PanelPosition(0, 52, 48, 48),
            PanelPosition(52, 52, 48, 48)
        ],
        PanelLayout.SIX_STANDARD: [
            PanelPosition(0, 0, 32, 33),
            PanelPosition(34, 0, 32, 33),
            PanelPosition(68, 0, 32, 33),
            PanelPosition(0, 37, 32, 29),
            PanelPosition(34, 37, 32, 29),
            PanelPosition(68, 37, 32, 29),
            PanelPosition(0, 70, 100, 30)  # Wide bottom
        ],
        PanelLayout.SIX_DYNAMIC: [
            PanelPosition(0, 0, 60, 40),  # Large top-left
            PanelPosition(64, 0, 36, 60),  # Tall right
            PanelPosition(0, 44, 36, 26),  # Medium below left
            PanelPosition(40, 44, 24, 26),  # Small center
            PanelPosition(68, 64, 32, 36),  # Medium right-bottom
            PanelPosition(0, 74, 60, 26)   # Wide bottom
        ],
        PanelLayout.FIVE_DYNAMIC: [
            PanelPosition(0, 0, 50, 50),
            PanelPosition(54, 0, 46, 35),
            PanelPosition(54, 39, 46, 27),
            PanelPosition(0, 54, 48, 46),
            PanelPosition(52, 70, 48, 30)
        ]
    }
    
    @classmethod
    def get_layout(cls, layout_type: str) -> List[PanelPosition]:
        """Get panel positions for a layout type."""
        try:
            layout = PanelLayout(layout_type)
            return cls.LAYOUTS.get(layout, cls.LAYOUTS[PanelLayout.SIX_STANDARD])
        except ValueError:
            return cls.LAYOUTS[PanelLayout.SIX_STANDARD]
    
    @classmethod
    def get_default_layout(cls, panel_count: int) -> PanelLayout:
        """Get appropriate layout based on panel count."""
        if panel_count == 1:
            return PanelLayout.SPLASH
        elif panel_count == 2:
            return PanelLayout.TWO_VERTICAL
        elif panel_count == 3:
            return PanelLayout.THREE_TOP_HEAVY
        elif panel_count == 4:
            return PanelLayout.FOUR_GRID
        elif panel_count == 5:
            return PanelLayout.FIVE_DYNAMIC
        else:
            return PanelLayout.SIX_STANDARD


@dataclass
class PanelComposition:
    """Composition guidelines for a panel."""
    rule_of_thirds: bool = True
    focal_point: Tuple[int, int] = (50, 50)  # Percentage x, y
    leading_lines: bool = False
    symmetry: bool = False
    depth_layers: int = 3  # Foreground, midground, background


@dataclass
class PanelTiming:
    """Timing information for action panels."""
    panels_for_action: int = 1  # How many panels for this action
    motion_lines: bool = False
    speed_lines: bool = False
    freeze_frame: bool = False
