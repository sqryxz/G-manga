"""
Page Calculator - Stage 3.1.5
Calculates page composition from panel breakdowns.
"""

from typing import List, Dict, Any


class PageCalculator:
    """Calculates page composition from panels."""

    def __init__(self):
        """Initialize Page Calculator."""
        # Layout rules
        self.panel_limits = {
            "4-panel": 4,
            "5-panel": 5,
            "6-panel": 6,
            "8-panel": 8
        }

        self.default_layout = "6-panel"  # Default to 6 panels per page

    def calculate_pages(self, panels: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Calculate page breakdown from panels.

        Args:
            panels: List of panel dictionaries with 'number', 'type', etc.

        Returns:
            List of page dictionaries
        """
        pages = []
        current_page = 1
        current_panels = []

        for panel in panels:
            # Check if we need a new page
            if len(current_panels) >= self.panel_limits[self.default_layout]:
                # Finalize current page
                pages.append({
                    "page_number": current_page,
                    "panels": current_panels.copy(),
                    "layout": self.default_layout,
                    "panel_count": len(current_panels)
                })

                # Start new page
                current_page += 1
                current_panels = [panel]
            else:
                # Add to current page
                current_panels.append(panel)

        # Don't forget the last page
        if current_panels:
            pages.append({
                "page_number": current_page,
                "panels": current_panels,
                "layout": self.default_layout,
                "panel_count": len(current_panels)
            })

        return pages

    def assign_page_numbers(self, panels: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Assign page numbers to panels.

        Args:
            panels: List of panel dictionaries

        Returns:
            List of panels with page_number added
        """
        pages = self.calculate_pages(panels)

        # Assign page numbers
        result = []
        for page in pages:
            for panel in page["panels"]:
                panel_copy = panel.copy()
                panel_copy["page_number"] = page["page_number"]
                result.append(panel_copy)

        return result

    def calculate_page_number(self, panel_id: str, scene_number: int) -> int:
        """
        Calculate page number for a single panel.

        Args:
            panel_id: Panel ID string (e.g., "p1-3" for scene 1, panel 3)
            scene_number: Scene number

        Returns:
            Page number (1-based)
        """
        # Parse panel number from ID
        try:
            panel_num = int(panel_id.split('-')[1]) if '-' in panel_id else 1
        except (ValueError, IndexError):
            panel_num = 1

        # Calculate based on panel limits
        panels_per_page = self.panel_limits.get(self.default_layout, 6)
        page_number = ((panel_num - 1) // panels_per_page) + 1

        return page_number


def main():
    """Test Page Calculator."""
    import sys
    sys.path.insert(0, '/home/clawd/projects/g-manga/src/stage3_story_planning')

    # Create test panels
    test_panels = [
        {"number": 1, "type": "establishing", "camera": "wide"},
        {"number": 2, "type": "medium", "camera": "eye-level"},
        {"number": 3, "type": "dialogue", "camera": "eye-level"},
        {"number": 4, "type": "close-up", "camera": "eye-level"},
        {"number": 5, "type": "medium", "camera": "eye-level"},
        {"number": 6, "type": "medium", "camera": "eye-level"},
        {"number": 7, "type": "dialogue", "camera": "eye-level"},
        {"number": 8, "type": "close-up", "camera": "close-up"},
        {"number": 9, "type": "action", "camera": "low-angle"},
        {"number": 10, "type": "wide", "camera": "wide"}
    ]

    calculator = PageCalculator()

    # Calculate pages
    pages = calculator.calculate_pages(test_panels)

    print(f"Calculated {len(pages)} pages from {len(test_panels)} panels:")
    print()

    for page in pages:
        print(f"Page {page['page_number']}:")
        print(f"  Layout: {page['layout']}")
        print(f"  Panels: {page['panel_count']}")
        print()

    # Assign page numbers
    panels_with_pages = calculator.assign_page_numbers(test_panels)

    print("Panels with page numbers:")
    for i, panel in enumerate(panels_with_pages[:5]):
        print(f"Panel {panel['number']} -> Page {panel['page_number']}, {panel.get('type', 'medium')}")


if __name__ == "__main__":
    main()
