"""
Layout Template Library - Stage 7.1.1
Defines manga page layout templates.
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class ReadingDirection(Enum):
    """Manga reading direction."""
    LEFT_TO_RIGHT = "left-to-right"  # Western style
    RIGHT_TO_LEFT = "right-to-left"  # Traditional manga


class PanelShape(Enum):
    """Panel shapes for layout templates."""
    RECTANGLE = "rectangle"
    SQUARE = "square"
    WIDE = "wide"
    TALL = "tall"
    L_SHAPE = "l-shape"
    DIAGONAL = "diagonal"


@dataclass
class PanelSlot:
    """A single panel slot in a layout template."""
    slot_id: str
    x: float  # X position (0.0 to 1.0)
    y: float  # Y position (0.0 to 1.0)
    width: float  # Width (0.0 to 1.0)
    height: float  # Height (0.0 to 1.0)
    order: int  # Reading order (1, 2, 3, ...)


@dataclass
class LayoutTemplate:
    """A manga page layout template."""
    name: str
    description: str
    panel_count: int
    reading_direction: ReadingDirection
    slots: List[PanelSlot]
    gutter_size: float = 0.01  # Space between panels (1% of page)
    border_thickness: float = 2  # Panel border thickness in px


class LayoutTemplateLibrary:
    """Library of manga layout templates."""

    def __init__(self):
        """Initialize layout template library."""
        self.templates = self._build_templates()

    def _build_templates(self) -> Dict[str, LayoutTemplate]:
        """
        Build all layout templates.

        Returns:
            Dictionary of template name -> LayoutTemplate
        """
        templates = {}

        # 4-panel layouts
        templates["4-panel-grid"] = self._create_4_panel_grid()
        templates["4-panel-staggered"] = self._create_4_panel_staggered()
        templates["4-panel-tiered"] = self._create_4_panel_tiered()

        # 5-panel layouts
        templates["5-panel-standard"] = self._create_5_panel_standard()
        templates["5-panel-asymmetric"] = self._create_5_panel_asymmetric()

        # 6-panel layouts
        templates["6-panel-grid"] = self._create_6_panel_grid()
        templates["6-panel-comic"] = self._create_6_panel_comic()

        # 8-panel layouts
        templates["8-panel-grid"] = self._create_8_panel_grid()

        # Special layouts
        templates["splash-full"] = self._create_splash_full()
        templates["splash-tiered"] = self._create_splash_tiered()
        templates["diagonal-flow"] = self._create_diagonal_flow()

        return templates

    def _create_4_panel_grid(self) -> LayoutTemplate:
        """Create 4-panel grid layout (2x2)."""
        slots = [
            # Top row
            PanelSlot("1", 0.015, 0.015, 0.48, 0.48, 1),
            PanelSlot("2", 0.505, 0.015, 0.48, 0.48, 2),
            # Bottom row
            PanelSlot("3", 0.015, 0.505, 0.48, 0.48, 3),
            PanelSlot("4", 0.505, 0.505, 0.48, 0.48, 4),
        ]

        return LayoutTemplate(
            name="4-panel-grid",
            description="Classic 2x2 grid layout",
            panel_count=4,
            reading_direction=ReadingDirection.LEFT_TO_RIGHT,
            slots=slots,
            gutter_size=0.01,
            border_thickness=2
        )

    def _create_4_panel_staggered(self) -> LayoutTemplate:
        """Create 4-panel staggered layout."""
        slots = [
            PanelSlot("1", 0.015, 0.015, 0.32, 0.48, 1),
            PanelSlot("2", 0.345, 0.015, 0.32, 0.48, 2),
            PanelSlot("3", 0.675, 0.015, 0.31, 0.48, 3),
            PanelSlot("4", 0.015, 0.505, 0.97, 0.48, 4),
        ]

        return LayoutTemplate(
            name="4-panel-staggered",
            description="4 panels: 3 top, 1 full-width bottom",
            panel_count=4,
            reading_direction=ReadingDirection.LEFT_TO_RIGHT,
            slots=slots,
            gutter_size=0.01,
            border_thickness=2
        )

    def _create_4_panel_tiered(self) -> LayoutTemplate:
        """Create 4-panel tiered layout."""
        slots = [
            PanelSlot("1", 0.015, 0.015, 0.97, 0.32, 1),
            PanelSlot("2", 0.015, 0.345, 0.48, 0.32, 2),
            PanelSlot("3", 0.505, 0.345, 0.48, 0.32, 3),
            PanelSlot("4", 0.015, 0.675, 0.97, 0.31, 4),
        ]

        return LayoutTemplate(
            name="4-panel-tiered",
            description="4 panels: 1 full-width top, 2 middle, 1 full-width bottom",
            panel_count=4,
            reading_direction=ReadingDirection.LEFT_TO_RIGHT,
            slots=slots,
            gutter_size=0.01,
            border_thickness=2
        )

    def _create_5_panel_standard(self) -> LayoutTemplate:
        """Create 5-panel standard layout."""
        slots = [
            PanelSlot("1", 0.015, 0.015, 0.48, 0.48, 1),
            PanelSlot("2", 0.505, 0.015, 0.48, 0.32, 2),
            PanelSlot("3", 0.505, 0.345, 0.48, 0.31, 3),
            PanelSlot("4", 0.015, 0.505, 0.32, 0.48, 4),
            PanelSlot("5", 0.345, 0.505, 0.64, 0.48, 5),
        ]

        return LayoutTemplate(
            name="5-panel-standard",
            description="5 panels: balanced distribution",
            panel_count=5,
            reading_direction=ReadingDirection.LEFT_TO_RIGHT,
            slots=slots,
            gutter_size=0.01,
            border_thickness=2
        )

    def _create_5_panel_asymmetric(self) -> LayoutTemplate:
        """Create 5-panel asymmetric layout."""
        slots = [
            PanelSlot("1", 0.015, 0.015, 0.97, 0.32, 1),
            PanelSlot("2", 0.015, 0.345, 0.32, 0.32, 2),
            PanelSlot("3", 0.345, 0.345, 0.32, 0.32, 3),
            PanelSlot("4", 0.675, 0.345, 0.31, 0.32, 4),
            PanelSlot("5", 0.015, 0.675, 0.97, 0.31, 5),
        ]

        return LayoutTemplate(
            name="5-panel-asymmetric",
            description="5 panels: full-width top, 4 middle, full-width bottom",
            panel_count=5,
            reading_direction=ReadingDirection.LEFT_TO_RIGHT,
            slots=slots,
            gutter_size=0.01,
            border_thickness=2
        )

    def _create_6_panel_grid(self) -> LayoutTemplate:
        """Create 6-panel grid layout (2x3)."""
        slots = [
            # Top row
            PanelSlot("1", 0.015, 0.015, 0.48, 0.32, 1),
            PanelSlot("2", 0.505, 0.015, 0.48, 0.32, 2),
            # Middle row
            PanelSlot("3", 0.015, 0.345, 0.48, 0.32, 3),
            PanelSlot("4", 0.505, 0.345, 0.48, 0.32, 4),
            # Bottom row
            PanelSlot("5", 0.015, 0.675, 0.48, 0.31, 5),
            PanelSlot("6", 0.505, 0.675, 0.48, 0.31, 6),
        ]

        return LayoutTemplate(
            name="6-panel-grid",
            description="6-panel 2x3 grid layout",
            panel_count=6,
            reading_direction=ReadingDirection.LEFT_TO_RIGHT,
            slots=slots,
            gutter_size=0.01,
            border_thickness=2
        )

    def _create_6_panel_comic(self) -> LayoutTemplate:
        """Create 6-panel comic layout."""
        slots = [
            PanelSlot("1", 0.015, 0.015, 0.48, 0.48, 1),
            PanelSlot("2", 0.505, 0.015, 0.48, 0.48, 2),
            PanelSlot("3", 0.015, 0.505, 0.32, 0.48, 3),
            PanelSlot("4", 0.345, 0.505, 0.32, 0.48, 4),
            PanelSlot("5", 0.675, 0.505, 0.31, 0.48, 5),
            PanelSlot("6", 0.015, 0.505, 0.99, 0.48, 6),
        ]

        return LayoutTemplate(
            name="6-panel-comic",
            description="6 panels: 2 large top, 3 middle, 1 large bottom",
            panel_count=6,
            reading_direction=ReadingDirection.LEFT_TO_RIGHT,
            slots=slots,
            gutter_size=0.01,
            border_thickness=2
        )

    def _create_8_panel_grid(self) -> LayoutTemplate:
        """Create 8-panel grid layout (4x2 or 2x4)."""
        slots = [
            # Row 1
            PanelSlot("1", 0.015, 0.015, 0.48, 0.24, 1),
            PanelSlot("2", 0.505, 0.015, 0.48, 0.24, 2),
            # Row 2
            PanelSlot("3", 0.015, 0.265, 0.48, 0.24, 3),
            PanelSlot("4", 0.505, 0.265, 0.48, 0.24, 4),
            # Row 3
            PanelSlot("5", 0.015, 0.515, 0.48, 0.24, 5),
            PanelSlot("6", 0.505, 0.515, 0.48, 0.24, 6),
            # Row 4
            PanelSlot("7", 0.015, 0.765, 0.48, 0.22, 7),
            PanelSlot("8", 0.505, 0.765, 0.48, 0.22, 8),
        ]

        return LayoutTemplate(
            name="8-panel-grid",
            description="8-panel 4x2 grid layout",
            panel_count=8,
            reading_direction=ReadingDirection.LEFT_TO_RIGHT,
            slots=slots,
            gutter_size=0.01,
            border_thickness=2
        )

    def _create_splash_full(self) -> LayoutTemplate:
        """Create full-page splash layout."""
        slots = [
            PanelSlot("1", 0.015, 0.015, 0.97, 0.97, 1),
        ]

        return LayoutTemplate(
            name="splash-full",
            description="Full-page splash panel",
            panel_count=1,
            reading_direction=ReadingDirection.LEFT_TO_RIGHT,
            slots=slots,
            gutter_size=0.01,
            border_thickness=2
        )

    def _create_splash_tiered(self) -> LayoutTemplate:
        """Create splash with tiered panels."""
        slots = [
            PanelSlot("1", 0.015, 0.015, 0.97, 0.48, 1),  # Large splash
            PanelSlot("2", 0.015, 0.505, 0.48, 0.48, 2),  # Bottom left
            PanelSlot("3", 0.505, 0.505, 0.48, 0.48, 3),  # Bottom right
        ]

        return LayoutTemplate(
            name="splash-tiered",
            description="Full-width splash top, 2 panels bottom",
            panel_count=3,
            reading_direction=ReadingDirection.LEFT_TO_RIGHT,
            slots=slots,
            gutter_size=0.01,
            border_thickness=2
        )

    def _create_diagonal_flow(self) -> LayoutTemplate:
        """Create diagonal flow layout."""
        slots = [
            PanelSlot("1", 0.015, 0.015, 0.48, 0.48, 1),
            PanelSlot("2", 0.505, 0.345, 0.48, 0.48, 2),
            PanelSlot("3", 0.015, 0.505, 0.48, 0.48, 3),
            PanelSlot("4", 0.505, 0.675, 0.48, 0.31, 4),
        ]

        return LayoutTemplate(
            name="diagonal-flow",
            description="4 panels with diagonal reading flow",
            panel_count=4,
            reading_direction=ReadingDirection.LEFT_TO_RIGHT,
            slots=slots,
            gutter_size=0.01,
            border_thickness=2
        )

    def get_template(self, name: str) -> Optional[LayoutTemplate]:
        """
        Get a layout template by name.

        Args:
            name: Template name

        Returns:
            LayoutTemplate or None
        """
        return self.templates.get(name)

    def get_all_templates(self) -> Dict[str, LayoutTemplate]:
        """
        Get all layout templates.

        Returns:
            Dictionary of templates
        """
        return self.templates

    def get_templates_by_panel_count(
        self,
        panel_count: int
    ) -> Dict[str, LayoutTemplate]:
        """
        Get templates with specific panel count.

        Args:
            panel_count: Number of panels

        Returns:
            Dictionary of matching templates
        """
        return {
            name: template
            for name, template in self.templates.items()
            if template.panel_count == panel_count
        }

    def find_best_template(
        self,
        panel_count: int,
        preferred_templates: Optional[List[str]] = None
    ) -> Optional[LayoutTemplate]:
        """
        Find best template for given panel count.

        Args:
            panel_count: Number of panels
            preferred_templates: List of preferred template names

        Returns:
            Best matching LayoutTemplate or None
        """
        # Check preferred templates first
        if preferred_templates:
            for name in preferred_templates:
                template = self.templates.get(name)
                if template and template.panel_count == panel_count:
                    return template

        # Find templates with exact match
        exact_matches = self.get_templates_by_panel_count(panel_count)

        if exact_matches:
            # Return first exact match
            return list(exact_matches.values())[0]

        # Find closest match (slightly more slots than needed)
        candidates = [
            template
            for template in self.templates.values()
            if template.panel_count >= panel_count
        ]

        if candidates:
            # Sort by panel count (smallest first)
            candidates.sort(key=lambda t: t.panel_count)
            return candidates[0]

        # No match found
        return None

    def export_templates_json(self, output_file: str):
        """
        Export all templates to JSON.

        Args:
            output_file: Output file path
        """
        import json

        templates_dict = {}
        for name, template in self.templates.items():
            templates_dict[name] = {
                "name": template.name,
                "description": template.description,
                "panel_count": template.panel_count,
                "reading_direction": template.reading_direction.value,
                "gutter_size": template.gutter_size,
                "border_thickness": template.border_thickness,
                "slots": [
                    {
                        "slot_id": slot.slot_id,
                        "x": slot.x,
                        "y": slot.y,
                        "width": slot.width,
                        "height": slot.height,
                        "order": slot.order
                    }
                    for slot in template.slots
                ]
            }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "templates": templates_dict,
                "total_templates": len(templates_dict)
            }, f, indent=2, ensure_ascii=False)

        print(f"✓ Exported {len(templates_dict)} templates to {output_file}")


def main():
    """Test Layout Template Library."""
    print("=" * 70)
    print("Layout Template Library Test")
    print("=" * 70)

    # Create library
    print("\n[Test] Creating layout template library...")
    library = LayoutTemplateLibrary()

    # Get all templates
    templates = library.get_all_templates()
    print(f"✓ Loaded {len(templates)} layout templates")

    # Display templates
    print("\n[Test] Available templates:")
    for name, template in templates.items():
        print(f"  {name}:")
        print(f"    {template.description}")
        print(f"    Panels: {template.panel_count}")
        print(f"    Reading: {template.reading_direction.value}")

    # Test get by panel count
    print("\n[Test] Getting templates by panel count...")
    four_panels = library.get_templates_by_panel_count(4)
    print(f"✓ Found {len(four_panels)} templates with 4 panels:")
    for name in four_panels.keys():
        print(f"  - {name}")

    # Test find best template
    print("\n[Test] Finding best templates...")
    best_5 = library.find_best_template(5)
    print(f"✓ Best for 5 panels: {best_5.name}")

    best_7 = library.find_best_template(7)
    print(f"✓ Best for 7 panels: {best_7.name}")

    # Test export
    print("\n[Test] Exporting templates...")
    library.export_templates_json("layout_templates_test.json")

    print("\n" + "=" * 70)
    print("Layout Template Library - PASSED")
    print("=" * 70)


def create_layout_library() -> LayoutTemplateLibrary:
    """
    Create a layout template library instance.

    Returns:
        LayoutTemplateLibrary instance
    """
    return LayoutTemplateLibrary()


if __name__ == "__main__":
    main()
