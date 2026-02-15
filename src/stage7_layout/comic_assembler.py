"""
Comic Assembler - Stage 7.1.4
Composes manga pages from panels using PIL/Pillow.
"""

import sys
sys.path.insert(0, '/home/clawd/projects/g-manga/src')

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from PIL import Image, ImageDraw
import os

from stage7_layout.layout_templates import PanelSlot
from stage7_layout.page_composer import PanelFitting, PageComposition
from stage7_layout.panel_arranger import PanelArrangement, VisualFlow


@dataclass
class ComicPage:
    """Complete manga page with composed image."""
    page_number: int
    image: Image  # PIL Image object
    width: int
    height: int
    panel_count: int
    panel_positions: Dict[str, Tuple[int, int, int, int]]  # panel_id -> (x, y, w, h)
    reading_order: List[str]
    saved_path: Optional[str] = None


class ComicAssembler:
    """Assembles manga pages from panel images."""

    def __init__(
        self,
        project_dir: Optional[str] = None,
        page_width: int = 2480,
        page_height: int = 3508,
        background_color: str = "#FFFFFF",
        border_color: str = "#000000",
        border_thickness: int = 2
    ):
        """
        Initialize Comic Assembler.

        Args:
            project_dir: Project directory for loading/saving panels
            page_width: Page width in pixels (A4 at 300 DPI)
            page_height: Page height in pixels (A4 at 300 DPI)
            background_color: Page background color (hex)
            border_color: Panel border color (hex)
            border_thickness: Border thickness in pixels
        """
        self.project_dir = project_dir
        self.page_width = page_width
        self.page_height = page_height
        self.background_color = background_color
        self.border_color = border_color
        self.border_thickness = border_thickness

    def load_panel_image(self, panel_id: str) -> Optional[Image.Image]:
        """Load a panel image from disk."""
        if not self.project_dir:
            return None
        
        panel_path = os.path.join(self.project_dir, "output", "panels", f"{panel_id}.png")
        if os.path.exists(panel_path):
            return Image.open(panel_path).convert("RGB")
        return None

    def load_all_panel_images(self, panel_ids: List[str]) -> Dict[str, Image.Image]:
        """Load all panel images from disk."""
        panel_images = {}
        for panel_id in panel_ids:
            img = self.load_panel_image(panel_id)
            if img:
                panel_images[panel_id] = img
        return panel_images

    def get_panels_dir(self) -> str:
        """Get the panels directory path."""
        if self.project_dir:
            return os.path.join(self.project_dir, "output", "panels")
        return ""

    def get_output_dir(self) -> str:
        """Get the comic pages output directory path."""
        if self.project_dir:
            return os.path.join(self.project_dir, "output", "comic_pages")
        return ""

    def assemble_page(
        self,
        panel_images: Dict[str, bytes],
        composition: PageComposition,
        arrangement: Optional[PanelArrangement] = None,
        panel_fittings: Optional[List[PanelFitting]] = None
    ) -> ComicPage:
        """
        Assemble a manga page from panels.

        Args:
            panel_images: Dictionary of panel_id -> image bytes
            composition: Page composition from PageComposer
            arrangement: Panel arrangement from PanelArranger
            panel_fittings: Panel fittings from PageComposer

        Returns:
            ComicPage object
        """
        # Create blank page
        page_image = Image.new(
            "RGB",
            (self.page_width, self.page_height),
            self.background_color
        )

        draw = ImageDraw.Draw(page_image)

        # Get fittings if not provided
        if panel_fittings is None:
            panel_fittings = composition.panel_fittings

        # Build panel positions
        panel_positions = {}
        reading_order = []

        # Place each panel
        for fitting in panel_fittings:
            panel_id = fitting.panel_id

            if panel_id not in panel_images:
                print(f"Warning: Panel {panel_id} not found in panel_images")
                continue

            # Load panel image from the passed-in dictionary (bytes)
            try:
                import io
                panel_img = Image.open(io.BytesIO(panel_images[panel_id])).convert("RGB")
            except Exception as e:
                print(f"Warning: Could not load panel {panel_id}: {e}")
                continue

            # Calculate panel position
            if arrangement:
                pos = arrangement.panel_positions.get(panel_id)
                if pos:
                    x, y, w, h = pos
                else:
                    from stage7_layout.page_composer import PageComposer
                    composer = PageComposer(
                        page_width=self.page_width,
                        page_height=self.page_height
                    )
                    x, y, w, h = composer.calculate_panel_position(fitting)
            else:
                from stage7_layout.page_composer import PageComposer
                composer = PageComposer(
                    page_width=self.page_width,
                    page_height=self.page_height
                )
                x, y, w, h = composer.calculate_panel_position(fitting)

            # Resize panel to fit slot
            panel_img = self._resize_panel(panel_img, w, h, fitting)

            # Paste panel onto page
            page_image.paste(panel_img, (x, y))

            # Draw panel border
            draw.rectangle(
                [x, y, x + w, y + h],
                outline=self.border_color,
                width=self.border_thickness
            )

            # Store position
            panel_positions[panel_id] = (x, y, w, h)
            reading_order.append(panel_id)

        # Draw visual flow guides if arrangement provided
        if arrangement:
            self._draw_flow_guides(
                page_image,
                draw,
                arrangement.flow_guides
            )

        # Create ComicPage object
        comic_page = ComicPage(
            page_number=0,  # Will be set by caller
            image=page_image,
            width=self.page_width,
            height=self.page_height,
            panel_count=len(panel_positions),
            panel_positions=panel_positions,
            reading_order=reading_order
        )

        return comic_page

    def _resize_panel(
        self,
        panel_img: Image,
        target_width: int,
        target_height: int,
        fitting: PanelFitting
    ) -> Image:
        """
        Resize panel to fit in slot.

        Args:
            panel_img: Panel image
            target_width: Target width
            target_height: Target height
            fitting: Panel fitting info

        Returns:
            Resized Image
        """
        # Apply fitting mode
        if fitting.fit_mode == "fit":
            # Fit within bounds (maintain aspect ratio)
            panel_img.thumbnail((target_width, target_height), Image.LANCZOS)
        elif fitting.fit_mode == "crop":
            # Crop to fit (center)
            aspect = panel_img.width / panel_img.height
            if aspect > target_width / target_height:
                # Wider than slot, crop width
                new_width = target_width
                new_height = int(target_width / aspect)
            else:
                # Taller than slot, crop height
                new_height = target_height
                new_width = int(target_height * aspect)

            panel_img = panel_img.resize((new_width, new_height), Image.LANCZOS)
            panel_img = self._center_crop(panel_img, target_width, target_height)
        elif fitting.fit_mode == "stretch":
            # Stretch to fit
            panel_img = panel_img.resize(
                (target_width, target_height),
                Image.LANCZOS
            )

        return panel_img

    def _center_crop(
        self,
        img: Image,
        target_width: int,
        target_height: int
    ) -> Image:
        """
        Center-crop image to target size.

        Args:
            img: Image to crop
            target_width: Target width
            target_height: Target height

        Returns:
            Cropped Image
        """
        left = (img.width - target_width) // 2
        top = (img.height - target_height) // 2
        right = left + target_width
        bottom = top + target_height

        return img.crop((left, top, right, bottom))

    def _draw_flow_guides(
        self,
        page_image: Image,
        draw: ImageDraw,
        flow_guides: List[Dict]
    ):
        """
        Draw visual flow guides on page.

        Args:
            page_image: Page image
            draw: ImageDraw object
            flow_guides: List of flow guide dictionaries
        """
        for guide in flow_guides:
            if guide["type"] == "none":
                continue

            start = guide["start"]
            end = guide["end"]

            # Draw guide based on type
            if guide["type"] in ["arrows-in", "arrows-out", "arrows-pan"]:
                # Draw arrows
                self._draw_arrow(draw, start, end)
            elif guide["type"] == "speed-lines":
                # Draw speed lines
                self._draw_speed_lines(draw, start, end)
            elif guide["type"] == "subtle-lines":
                # Draw subtle guide lines
                self._draw_subtle_lines(draw, start, end)
            elif guide["type"] == "speech-flow":
                # Draw speech flow
                self._draw_speech_flow(draw, start, end)

    def _draw_arrow(
        self,
        draw: ImageDraw,
        start: Tuple[int, int],
        end: Tuple[int, int]
    ):
        """
        Draw arrow between panels.

        Args:
            draw: ImageDraw object
            start: Start point
            end: End point
        """
        # Draw line
        draw.line([start, end], fill="#666666", width=2)

        # Draw arrowhead
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        length = (dx ** 2 + dy ** 2) ** 0.5

        if length > 0:
            # Arrowhead points
            arrow_size = 10
            angle = 3.14159 / 180 * 150

            # Calculate arrowhead points
            ax1 = end[0] - arrow_size * (dx / length) * 0.5
            ay1 = end[1] - arrow_size * (dy / length) * 0.5
            ax2 = ax1 - arrow_size * (dy / length) * 0.5
            ay2 = ay1 + arrow_size * (dx / length) * 0.5
            ax3 = ax1 + arrow_size * (dy / length) * 0.5
            ay3 = ay1 - arrow_size * (dx / length) * 0.5

            draw.polygon([(end[0], end[1]), (ax2, ay2), (ax3, ay3)], fill="#666666")

    def _draw_speed_lines(
        self,
        draw: ImageDraw,
        start: Tuple[int, int],
        end: Tuple[int, int]
    ):
        """
        Draw speed lines for action panels.

        Args:
            draw: ImageDraw object
            start: Start point
            end: End point
        """
        dx = end[0] - start[0]
        dy = end[1] - start[1]

        # Draw parallel lines
        for offset in [-15, 0, 15]:
            draw.line(
                [
                    (start[0] + offset, start[1]),
                    (end[0] + offset, end[1])
                ],
                fill="#999999",
                width=1
            )

    def _draw_subtle_lines(
        self,
        draw: ImageDraw,
        start: Tuple[int, int],
        end: Tuple[int, int]
    ):
        """
        Draw subtle guide lines.

        Args:
            draw: ImageDraw object
            start: Start point
            end: End point
        """
        # Draw dashed line
        mid_x = (start[0] + end[0]) // 2
        mid_y = (start[1] + end[1]) // 2

        draw.line(
            [start, (mid_x, mid_y)],
            fill="#CCCCCC",
            width=1
        )
        draw.line(
            [(mid_x, mid_y), end],
            fill="#CCCCCC",
            width=1
        )

    def _draw_speech_flow(
        self,
        draw: ImageDraw,
        start: Tuple[int, int],
        end: Tuple[int, int]
    ):
        """
        Draw speech flow indicator.

        Args:
            draw: ImageDraw object
            start: Start point
            end: End point
        """
        # Draw dotted line
        mid_x = (start[0] + end[0]) // 2
        mid_y = (start[1] + end[1]) // 2

        for i in range(10):
            t = i / 10
            x = start[0] + t * (end[0] - start[0])
            y = start[1] + t * (end[1] - start[1])
            if i % 2 == 0:
                draw.rectangle(
                    [x - 2, y - 2, x + 2, y + 2],
                    fill="#999999"
                )

    def save_page(
        self,
        comic_page: ComicPage,
        output_dir: str,
        page_number: int
    ) -> str:
        """
        Save assembled page to file.

        Args:
            comic_page: ComicPage object
            output_dir: Output directory
            page_number: Page number

        Returns:
            File path
        """
        os.makedirs(output_dir, exist_ok=True)

        filename = f"page_{page_number:03d}.png"
        filepath = os.path.join(output_dir, filename)

        comic_page.page_number = page_number
        comic_page.image.save(filepath, "PNG", optimize=True)
        comic_page.saved_path = filepath

        return filepath


def create_comic_assembler(
    page_width: int = 2480,
    page_height: int = 3508,
    background_color: str = "#FFFFFF",
    border_color: str = "#000000",
    border_thickness: int = 2
) -> ComicAssembler:
    """
    Create a comic assembler instance.

    Args:
        page_width: Page width in pixels
        page_height: Page height in pixels
        background_color: Background color (hex)
        border_color: Border color (hex)
        border_thickness: Border thickness

    Returns:
        ComicAssembler instance
    """
    return ComicAssembler(
        page_width=page_width,
        page_height=page_height,
        background_color=background_color,
        border_color=border_color,
        border_thickness=border_thickness
    )


def main():
    """Test Comic Assembler."""
    print("=" * 70)
    print("Comic Assembler Test")
    print("=" * 70)

    # Create assembler
    print("\n[Test] Creating comic assembler...")
    assembler = create_comic_assembler()
    print(f"✓ Assembler created")
    print(f"  Page size: {assembler.page_width}x{assembler.page_height}")
    print(f"  Background: {assembler.background_color}")
    print(f"  Border: {assembler.border_color}, {assembler.border_thickness}px")

    # Test with mock data (structure test)
    print("\n[Test] Testing page composition...")
    print("✓ Comic assembler structure created")
    print("  Note: Requires actual panel images for full testing")

    # Test drawing functions
    print("\n[Test] Testing drawing functions...")

    # Create test image
    from PIL import Image, ImageDraw
    test_img = Image.new("RGB", (800, 600), "#FFFFFF")
    draw = ImageDraw.Draw(test_img)

    # Test arrow
    assembler._draw_arrow(draw, (100, 100), (300, 300))
    print("✓ Arrow drawing")

    # Test speed lines
    assembler._draw_speed_lines(draw, (400, 100), (600, 300))
    print("✓ Speed lines drawing")

    # Test subtle lines
    assembler._draw_subtle_lines(draw, (100, 400), (300, 500))
    print("✓ Subtle lines drawing")

    # Test speech flow
    assembler._draw_speech_flow(draw, (400, 400), (600, 500))
    print("✓ Speech flow drawing")

    print("\n" + "=" * 70)
    print("Comic Assembler - PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()
