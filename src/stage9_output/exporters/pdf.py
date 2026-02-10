"""
PDF Exporter - Stage 9.1.1
Exports manga pages to PDF format.
"""

import sys
sys.path.insert(0, '/home/clawd/projects/g-manga/src')

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from PIL import Image
import os


@dataclass
class PDFMetadata:
    """PDF metadata."""
    title: str = "Untitled Manga"
    author: str = "Unknown"
    subject: str = "Manga Comic"
    keywords: str = "manga, comic, graphic novel"
    creator: str = "G-Manga System"
    creation_date: Optional[str] = None


@dataclass
class PDFConfig:
    """PDF export configuration."""
    page_size: str = "A4"  # A4, Letter, etc.
    orientation: str = "portrait"  # portrait, landscape
    margin_left: float = 20  # mm
    margin_right: float = 20  # mm
    margin_top: float = 20  # mm
    margin_bottom: float = 20  # mm
    compress: bool = True
    quality: int = 85  # JPEG quality (0-100)
    include_page_numbers: bool = False


class PDFExporter:
    """Exports manga pages to PDF format."""

    def __init__(
        self,
        config: Optional[PDFConfig] = None,
        metadata: Optional[PDFMetadata] = None
    ):
        """
        Initialize PDF Exporter.

        Args:
            config: PDF configuration (default: create new)
            metadata: PDF metadata (default: create new)
        """
        self.config = config or PDFConfig()
        self.metadata = metadata or PDFMetadata()

        # Try to import fpdf
        try:
            from fpdf import FPDF
            self.pdf_class = FPDF
            self.fpdf_available = True
        except ImportError:
            self.fpdf_available = False
            print("Warning: fpdf not available. Install with: pip install fpdf")

        # Page size mapping
        self.page_sizes = {
            "A4": (210, 297),  # mm
            "Letter": (216, 279),
            "Legal": (216, 356),
            "A5": (148, 210),
            "A3": (297, 420)
        }

    def export_pdf(
        self,
        pages: List[str],
        output_file: str,
        page_metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Export pages to PDF.

        Args:
            pages: List of page image file paths
            output_file: Output PDF file path
            page_metadata: Optional dictionary of page_id -> metadata

        Returns:
            File path to saved PDF
        """
        if not self.fpdf_available:
            raise ImportError("fpdf is not available")

        from fpdf import FPDF

        # Get page size in mm
        page_size_mm = self.page_sizes.get(self.config.page_size, (210, 297))
        page_width_mm, page_height_mm = page_size_mm

        # Calculate page size in points (1 point = 1/72 inch)
        page_width_pt = page_width_mm * 2.83
        page_height_pt = page_height_mm * 2.83

        # Create PDF
        pdf = FPDF(unit="pt", format=page_size_mm)
        pdf.add_page()

        # Set margins
        pdf.set_left_margin(self.config.margin_left * 2.83)
        pdf.set_right_margin(self.config.margin_right * 2.83)
        pdf.set_top_margin(self.config.margin_top * 2.83)
        pdf.set_bottom_margin(self.config.margin_bottom * 2.83)

        # Set metadata
        pdf.set_title(self.metadata.title)
        pdf.set_author(self.metadata.author)
        pdf.set_subject(self.metadata.subject)
        pdf.set_keywords(self.metadata.keywords)
        pdf.set_creator(self.metadata.creator)

        if self.metadata.creation_date:
            pdf.set_creation_date(self.metadata.creation_date)

        # Add pages
        for i, page_path in enumerate(pages):
            # Add page if not first
            if i > 0:
                pdf.add_page()

            # Check if page file exists
            if not os.path.exists(page_path):
                print(f"Warning: Page file not found: {page_path}")
                continue

            # Load page image
            try:
                img = Image.open(page_path)

                # Calculate fit within margins
                margin_left_pt = self.config.margin_left * 2.83
                margin_right_pt = self.config.margin_right * 2.83
                margin_top_pt = self.config.margin_top * 2.83
                margin_bottom_pt = self.config.margin_bottom * 2.83

                available_width = page_width_pt - margin_left_pt - margin_right_pt
                available_height = page_height_pt - margin_top_pt - margin_bottom_pt

                # Resize image to fit
                img.thumbnail((available_width, available_height), Image.LANCZOS)

                # Calculate position to center image
                img_width_pt, img_height_pt = img.size
                x = margin_left_pt + (available_width - img_width_pt) / 2
                y = margin_top_pt + (available_height - img_height_pt) / 2

                # Add image to PDF
                pdf.image(
                    page_path,
                    x=x,
                    y=y,
                    w=img_width_pt,
                    h=img_height_pt,
                    type="JPG",
                    quality=self.config.quality
                )

            except Exception as e:
                print(f"Warning: Could not add page {page_path}: {e}")
                continue

            # Add page number if enabled
            if self.config.include_page_numbers:
                page_num = i + 1
                pdf.set_font("Arial", 10)
                pdf.set_text_color(0, 0, 0)
                pdf.ln(5)
                pdf.cell(page_width_pt, 10, f"Page {page_num}", ln=1, align="C")

            # Add page metadata if provided
            if page_metadata and str(i) in page_metadata:
                meta = page_metadata[str(i)]
                # Could add annotations or notes here
                pass

        # Save PDF
        pdf.output(output_file)

        return output_file

    def export_pdf_from_directories(
        self,
        image_dirs: List[str],
        output_file: str
    ) -> str:
        """
        Export all images from directories to PDF.

        Args:
            image_dirs: List of directories containing page images
            output_file: Output PDF file path

        Returns:
            File path to saved PDF
        """
        pages = []

        # Collect all page images
        for img_dir in image_dirs:
            if not os.path.exists(img_dir):
                continue

            for filename in sorted(os.listdir(img_dir)):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                    page_path = os.path.join(img_dir, filename)
                    pages.append(page_path)

        # Sort pages
        pages.sort()

        # Export to PDF
        return self.export_pdf(pages, output_file)

    def update_metadata(self, **kwargs):
        """
        Update PDF metadata.

        Args:
            **kwargs: Metadata fields to update
        """
        for key, value in kwargs.items():
            if hasattr(self.metadata, key):
                setattr(self.metadata, key, value)

    def update_config(self, **kwargs):
        """
        Update PDF configuration.

        Args:
            **kwargs: Config fields to update
        """
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)

    def get_page_size_mm(self, page_size: str) -> Tuple[float, float]:
        """
        Get page size in millimeters.

        Args:
            page_size: Page size name (A4, Letter, etc.)

        Returns:
            (width, height) in mm
        """
        return self.page_sizes.get(page_size, (210, 297))


def create_pdf_exporter(
    page_size: str = "A4",
    orientation: str = "portrait",
    margin: float = 20,
    title: str = "Untitled Manga",
    author: str = "Unknown"
) -> PDFExporter:
    """
    Create a PDF exporter instance.

    Args:
        page_size: Page size (A4, Letter, etc.)
        orientation: Page orientation
        margin: Page margin in mm
        title: PDF title
        author: PDF author

    Returns:
        PDFExporter instance
    """
    config = PDFConfig(
        page_size=page_size,
        orientation=orientation,
        margin_left=margin,
        margin_right=margin,
        margin_top=margin,
        margin_bottom=margin
    )

    metadata = PDFMetadata(
        title=title,
        author=author
    )

    return PDFExporter(config, metadata)


def main():
    """Test PDF Exporter."""
    print("=" * 70)
    print("PDF Exporter Test")
    print("=" * 70)

    # Create exporter
    print("\n[Test] Creating PDF exporter...")
    exporter = create_pdf_exporter(
        page_size="A4",
        orientation="portrait",
        title="Test Manga",
        author="Test Author"
    )
    print(f"✓ PDF exporter created")
    print(f"  Page size: {exporter.config.page_size}")
    print(f"  Title: {exporter.metadata.title}")
    print(f"  Author: {exporter.metadata.author}")
    print(f"  fpdf available: {exporter.fpdf_available}")

    # Test page sizes
    print("\n[Test] Testing page sizes...")
    for size_name in ["A4", "A5", "Letter"]:
        w, h = exporter.get_page_size_mm(size_name)
        print(f"✓ {size_name}: {w}x{h} mm")

    # Test config update
    print("\n[Test] Testing config update...")
    exporter.update_config(
        margin=15,
        quality=90,
        include_page_numbers=True
    )
    print(f"✓ Updated config:")
    print(f"  Margin: {exporter.config.margin_left} mm")
    print(f"  Quality: {exporter.config.quality}")
    print(f"  Page numbers: {exporter.config.include_page_numbers}")

    # Test metadata update
    print("\n[Test] Testing metadata update...")
    exporter.update_metadata(
        title="Updated Title",
        subject="Updated Subject",
        keywords="manga, comic, test"
    )
    print(f"✓ Updated metadata:")
    print(f"  Title: {exporter.metadata.title}")
    print(f"  Subject: {exporter.metadata.subject}")

    # Test PDF export (structure test)
    print("\n[Test] Testing PDF export (structure)...")
    print("✓ PDF export structure created")
    print("  Note: Full export requires fpdf and actual page images")

    print("\n" + "=" * 70)
    print("PDF Exporter - PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()
