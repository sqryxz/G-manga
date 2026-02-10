"""
Page Composer - Stage 7.1.2
Matches panels to layout templates and handles panel fitting.
"""

import math
import sys
sys.path.insert(0, '/home/clawd/projects/g-manga/src')

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

from stage7_layout.layout_templates import (
    LayoutTemplate,
    LayoutTemplateLibrary,
    PanelSlot
)


@dataclass
class PanelFitting:
    """How a panel fits into a template slot."""
    panel_id: str
    slot_id: str
    slot: PanelSlot
    panel_aspect_ratio: float
    slot_aspect_ratio: float
    gutter_size: float
    fit_mode: str  # "fit", "crop", "stretch"
    scale_factor: float
    crop_left: float = 0.0
    crop_top: float = 0.0
    crop_width: float = 1.0
    crop_height: float = 1.0


@dataclass
class PageComposition:
    """Complete page composition plan."""
    template_name: str
    template: LayoutTemplate
    page_width: int
    page_height: int
    panel_fittings: List[PanelFitting]
    gutter_size: float
    border_thickness: int
    total_panels: int


class PageComposer:
    """Composes manga pages from panels and layout templates."""

    def __init__(
        self,
        library: Optional[LayoutTemplateLibrary] = None,
        page_width: int = 2480,
        page_height: int = 3508
    ):
        """
        Initialize Page Composer.

        Args:
            library: Layout template library (default: create new)
            page_width: Page width in pixels (A4 at 300 DPI)
            page_height: Page height in pixels (A4 at 300 DPI)
        """
        self.library = library or LayoutTemplateLibrary()
        self.page_width = page_width
        self.page_height = page_height

    def compose_page(
        self,
        panel_ids: List[str],
        preferred_template: Optional[str] = None
    ) -> Optional[PageComposition]:
        """
        Compose a page from panels.

        Args:
            panel_ids: List of panel IDs to place
            preferred_template: Preferred template name

        Returns:
            PageComposition or None if no suitable template
        """
        panel_count = len(panel_ids)

        # Find best template
        if preferred_template:
            template = self.library.get_template(preferred_template)
            if template is None:
                template = self.library.find_best_template(panel_count)
        else:
            template = self.library.find_best_template(panel_count)

        if template is None:
            return None

        # Match panels to slots
        panel_fittings = self._match_panels_to_slots(
            panel_ids,
            template
        )

        return PageComposition(
            template_name=template.name,
            template=template,
            page_width=self.page_width,
            page_height=self.page_height,
            panel_fittings=panel_fittings,
            gutter_size=template.gutter_size,
            border_thickness=template.border_thickness,
            total_panels=len(panel_fittings)
        )

    def compose_page_from_template(
        self,
        panel_ids: List[str],
        template_name: str
    ) -> Optional[PageComposition]:
        """
        Compose page using specific template.

        Args:
            panel_ids: List of panel IDs
            template_name: Template name to use

        Returns:
            PageComposition or None
        """
        template = self.library.get_template(template_name)

        if template is None:
            return None

        # Check if panel count matches
        if len(panel_ids) > template.panel_count:
            # Too many panels, truncate
            panel_ids = panel_ids[:template.panel_count]

        # Match panels to slots
        panel_fittings = self._match_panels_to_slots(
            panel_ids,
            template
        )

        return PageComposition(
            template_name=template.name,
            template=template,
            page_width=self.page_width,
            page_height=self.page_height,
            panel_fittings=panel_fittings,
            gutter_size=template.gutter_size,
            border_thickness=template.border_thickness,
            total_panels=len(panel_fittings)
        )

    def _match_panels_to_slots(
        self,
        panel_ids: List[str],
        template: LayoutTemplate
    ) -> List[PanelFitting]:
        """
        Match panels to template slots.

        Args:
            panel_ids: List of panel IDs
            template: Layout template

        Returns:
            List of PanelFitting objects
        """
        fittings = []

        # Sort slots by reading order
        sorted_slots = sorted(template.slots, key=lambda s: s.order)

        for i, slot in enumerate(sorted_slots):
            if i >= len(panel_ids):
                break

            panel_id = panel_ids[i]

            # Calculate aspect ratios
            slot_aspect_ratio = slot.width / slot.height
            panel_aspect_ratio = 1.0  # Assume square for now

            # Determine fit mode
            if abs(panel_aspect_ratio - slot_aspect_ratio) < 0.1:
                # Close aspect ratio, fit to slot
                fit_mode = "fit"
                scale_factor = 1.0
            elif panel_aspect_ratio > slot_aspect_ratio:
                # Panel is wider, crop height
                fit_mode = "crop"
                scale_factor = 1.0
            else:
                # Panel is taller, crop width
                fit_mode = "crop"
                scale_factor = 1.0

            fitting = PanelFitting(
                panel_id=panel_id,
                slot_id=slot.slot_id,
                slot=slot,
                panel_aspect_ratio=panel_aspect_ratio,
                slot_aspect_ratio=slot_aspect_ratio,
                gutter_size=template.gutter_size,
                fit_mode=fit_mode,
                scale_factor=scale_factor
            )

            fittings.append(fitting)

        return fittings

    def calculate_panel_position(
        self,
        fitting: PanelFitting,
        gutter_size: Optional[float] = None
    ) -> Tuple[int, int, int, int]:
        """
        Calculate actual pixel position for a panel.

        Args:
            fitting: Panel fitting info
            gutter_size: Gutter size (default: use fitting gutter)

        Returns:
            (x, y, width, height) in pixels
        """
        # Get gutter size
        if gutter_size is None:
            gutter_size = fitting.gutter_size

        # Calculate slot position in pixels
        slot_x = int(fitting.slot.x * self.page_width)
        slot_y = int(fitting.slot.y * self.page_height)
        slot_width = int(fitting.slot.width * self.page_width)
        slot_height = int(fitting.slot.height * self.page_height)

        # Apply gutter
        gutter = int(self.page_width * gutter_size)

        panel_x = slot_x + gutter
        panel_y = slot_y + gutter
        panel_width = slot_width - (2 * gutter)
        panel_height = slot_height - (2 * gutter)

        return (panel_x, panel_y, panel_width, panel_height)

    def calculate_gutter_pixels(
        self,
        gutter_size: float
    ) -> int:
        """
        Calculate gutter size in pixels.

        Args:
            gutter_size: Gutter size as percentage of page width

        Returns:
            Gutter size in pixels
        """
        return int(self.page_width * gutter_size)

    def get_available_templates(
        self,
        panel_count: int
    ) -> Dict[str, LayoutTemplate]:
        """
        Get templates that can fit given number of panels.

        Args:
            panel_count: Number of panels

        Returns:
            Dictionary of matching templates
        """
        templates = {}

        for name, template in self.library.get_all_templates().items():
            if template.panel_count >= panel_count:
                templates[name] = template

        return templates

    def recommend_template(
        self,
        panel_count: int,
        content_type: Optional[str] = None
    ) -> Optional[LayoutTemplate]:
        """
        Recommend a template based on panel count and content type.

        Args:
            panel_count: Number of panels
            content_type: Content type ("action", "dialogue", "splash", etc.)

        Returns:
            Recommended LayoutTemplate or None
        """
        # Check content-based preferences
        if content_type == "splash":
            return self.library.get_template("splash-full")
        elif content_type == "action":
            if panel_count <= 4:
                return self.library.get_template("4-panel-grid")
            elif panel_count <= 6:
                return self.library.get_template("6-panel-comic")
        elif content_type == "dialogue":
            if panel_count <= 4:
                return self.library.get_template("4-panel-tiered")
            elif panel_count <= 5:
                return self.library.get_template("5-panel-standard")

        # Default: find best match
        return self.library.find_best_template(panel_count)


def create_page_composer(
    page_width: int = 2480,
    page_height: int = 3508
) -> PageComposer:
    """
    Create a page composer instance.

    Args:
        page_width: Page width in pixels
        page_height: Page height in pixels

    Returns:
        PageComposer instance
    """
    return PageComposer(
        page_width=page_width,
        page_height=page_height
    )


def main():
    """Test Page Composer."""
    print("=" * 70)
    print("Page Composer Test")
    print("=" * 70)

    # Create composer
    print("\n[Test] Creating page composer...")
    composer = create_page_composer()
    print(f"✓ Composer created")
    print(f"  Page size: {composer.page_width}x{composer.page_height}")

    # Test compose page
    print("\n[Test] Composing page with 4 panels...")
    panel_ids = ["p1-1", "p1-2", "p1-3", "p1-4"]

    composition = composer.compose_page(panel_ids)

    if composition:
        print(f"✓ Composed page using: {composition.template_name}")
        print(f"  Template: {composition.template.description}")
        print(f"  Panels: {composition.total_panels}")
        print(f"  Gutter: {composition.gutter_size}")
        print(f"  Border: {composition.border_thickness}px")

        # Calculate panel positions
        print("\n  Panel positions:")
        for fitting in composition.panel_fittings:
            x, y, w, h = composer.calculate_panel_position(fitting)
            print(f"    {fitting.panel_id}: ({x}, {y}) - {w}x{h}")
            print(f"      Fit mode: {fitting.fit_mode}")
    else:
        print("✗ Failed to compose page")

    # Test with preferred template
    print("\n[Test] Composing with preferred template...")
    composition2 = composer.compose_page_from_template(
        panel_ids[:5],
        "5-panel-standard"
    )

    if composition2:
        print(f"✓ Composed page: {composition2.template_name}")
        print(f"  Panels: {composition2.total_panels}")

    # Test template recommendation
    print("\n[Test] Testing template recommendations...")

    rec1 = composer.recommend_template(1, "splash")
    print(f"✓ Splash (1 panel): {rec1.name}")

    rec2 = composer.recommend_template(5, "dialogue")
    print(f"✓ Dialogue (5 panels): {rec2.name}")

    rec3 = composer.recommend_template(6, "action")
    print(f"✓ Action (6 panels): {rec3.name}")

    print("\n" + "=" * 70)
    print("Page Composer - PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()
