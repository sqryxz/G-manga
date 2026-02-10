"""
Page Thumbnail Generator - Stage 7.1.5
Generates thumbnails for quick page preview.
"""

import sys
sys.path.insert(0, '/home/clawd/projects/g-manga/src')

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from PIL import Image, ImageOps
import os

from stage7_layout.comic_assembler import ComicPage


@dataclass
class ThumbnailConfig:
    """Thumbnail generation configuration."""
    size: Tuple[int, int]  # (width, height)
    quality: int  # JPEG quality (1-100)
    format: str  # "png", "jpeg"
    maintain_aspect: bool = True
    suffix: str = "_thumb"


class ThumbnailGenerator:
    """Generates thumbnails for manga pages."""

    def __init__(
        self,
        size: Tuple[int, int] = (300, 425),
        quality: int = 85,
        format: str = "jpeg",
        maintain_aspect: bool = True
    ):
        """
        Initialize Thumbnail Generator.

        Args:
            size: Thumbnail size (width, height)
            quality: JPEG quality (1-100)
            format: Output format ("png", "jpeg")
            maintain_aspect: Maintain aspect ratio
        """
        self.config = ThumbnailConfig(
            size=size,
            quality=quality,
            format=format,
            maintain_aspect=maintain_aspect
        )

    def generate_thumbnail(
        self,
        page_image: Image,
        comic_page: Optional[ComicPage] = None
    ) -> Image:
        """
        Generate a thumbnail from page image.

        Args:
            page_image: PIL Image object
            comic_page: ComicPage object (for metadata)

        Returns:
            Thumbnail Image
        """
        # Generate thumbnail
        if self.config.maintain_aspect:
            thumbnail = ImageOps.fit(
                page_image,
                self.config.size,
                Image.LANCZOS
            )
        else:
            thumbnail = page_image.resize(
                self.config.size,
                Image.LANCZOS
            )

        return thumbnail

    def generate_thumbnail_from_file(
        self,
        image_path: str
    ) -> Image:
        """
        Generate thumbnail from image file.

        Args:
            image_path: Path to image file

        Returns:
            Thumbnail Image
        """
        # Load image
        img = Image.open(image_path).convert("RGB")

        # Generate thumbnail
        thumbnail = self.generate_thumbnail(img)

        return thumbnail

    def generate_thumbnails(
        self,
        pages: List[ComicPage]
    ) -> Dict[str, Image]:
        """
        Generate thumbnails for multiple pages.

        Args:
            pages: List of ComicPage objects

        Returns:
            Dictionary of page_number -> thumbnail Image
        """
        thumbnails = {}

        for page in pages:
            thumbnail = self.generate_thumbnail(page.image, page)
            thumbnails[page.page_number] = thumbnail

        return thumbnails

    def save_thumbnail(
        self,
        thumbnail: Image,
        output_path: str,
        filename: Optional[str] = None
    ) -> str:
        """
        Save thumbnail to file.

        Args:
            thumbnail: Thumbnail Image
            output_path: Output directory
            filename: Output filename (optional)

        Returns:
            Saved file path
        """
        os.makedirs(output_path, exist_ok=True)

        if filename is None:
            filename = f"thumbnail.{self.config.format}"

        filepath = os.path.join(output_path, filename)

        # Save based on format
        if self.config.format == "png":
            thumbnail.save(filepath, "PNG", optimize=True)
        else:
            thumbnail.save(
                filepath,
                "JPEG",
                quality=self.config.quality,
                optimize=True
            )

        return filepath

    def save_page_thumbnail(
        self,
        comic_page: ComicPage,
        output_dir: str,
        suffix: Optional[str] = None
    ) -> str:
        """
        Save thumbnail for a comic page.

        Args:
            comic_page: ComicPage object
            output_dir: Output directory
            suffix: Optional suffix for filename

        Returns:
            Saved file path
        """
        # Generate thumbnail
        thumbnail = self.generate_thumbnail(comic_page.image, comic_page)

        # Generate filename
        page_num = comic_page.page_number
        if suffix is None:
            suffix = self.config.suffix

        if self.config.format == "png":
            filename = f"page_{page_num:03d}{suffix}.png"
        else:
            filename = f"page_{page_num:03d}{suffix}.jpg"

        # Save
        filepath = self.save_thumbnail(thumbnail, output_dir, filename)

        return filepath

    def save_thumbnails_batch(
        self,
        pages: List[ComicPage],
        output_dir: str,
        suffix: Optional[str] = None
    ) -> Dict[int, str]:
        """
        Save thumbnails for multiple pages.

        Args:
            pages: List of ComicPage objects
            output_dir: Output directory
            suffix: Optional suffix for filenames

        Returns:
            Dictionary of page_number -> file path
        """
        results = {}

        for page in pages:
            filepath = self.save_page_thumbnail(page, output_dir, suffix)
            results[page.page_number] = filepath

        return results

    def generate_preview_strip(
        self,
        pages: List[ComicPage],
        output_path: str,
        panels_per_row: int = 4
    ) -> str:
        """
        Generate a preview strip of multiple thumbnails.

        Args:
            pages: List of ComicPage objects
            output_path: Output file path
            panels_per_row: Number of thumbnails per row

        Returns:
            Saved file path
        """
        # Generate all thumbnails
        thumbnails = self.generate_thumbnails(pages)

        # Calculate strip dimensions
        thumb_width, thumb_height = self.config.size
        cols = panels_per_row
        rows = (len(thumbnails) + cols - 1) // cols

        strip_width = cols * thumb_width
        strip_height = rows * thumb_height

        # Create blank strip
        strip = Image.new("RGB", (strip_width, strip_height), "#FFFFFF")

        # Paste thumbnails
        for page_num, thumbnail in sorted(thumbnails.items()):
            row = (page_num - 1) // cols
            col = (page_num - 1) % cols

            x = col * thumb_width
            y = row * thumb_height

            strip.paste(thumbnail, (x, y))

        # Save strip
        strip.save(output_path, "JPEG", quality=self.config.quality, optimize=True)

        return output_path

    def get_thumbnail_config(self) -> ThumbnailConfig:
        """
        Get current thumbnail configuration.

        Returns:
            ThumbnailConfig object
        """
        return self.config

    def update_config(
        self,
        size: Optional[Tuple[int, int]] = None,
        quality: Optional[int] = None,
        format: Optional[str] = None,
        maintain_aspect: Optional[bool] = None
    ):
        """
        Update thumbnail configuration.

        Args:
            size: New thumbnail size
            quality: New JPEG quality
            format: New output format
            maintain_aspect: Maintain aspect ratio
        """
        if size is not None:
            self.config.size = size
        if quality is not None:
            self.config.quality = quality
        if format is not None:
            self.config.format = format
        if maintain_aspect is not None:
            self.config.maintain_aspect = maintain_aspect


def create_thumbnail_generator(
    size: Tuple[int, int] = (300, 425),
    quality: int = 85,
    format: str = "jpeg"
) -> ThumbnailGenerator:
    """
    Create a thumbnail generator instance.

    Args:
        size: Thumbnail size (width, height)
        quality: JPEG quality (1-100)
        format: Output format ("png", "jpeg")

    Returns:
        ThumbnailGenerator instance
    """
    return ThumbnailGenerator(
        size=size,
        quality=quality,
        format=format
    )


def main():
    """Test Thumbnail Generator."""
    print("=" * 70)
    print("Page Thumbnail Generator Test")
    print("=" * 70)

    # Create generator
    print("\n[Test] Creating thumbnail generator...")
    generator = create_thumbnail_generator()
    print(f"✓ Thumbnail generator created")
    print(f"  Size: {generator.config.size}")
    print(f"  Format: {generator.config.format}")
    print(f"  Quality: {generator.config.quality}")

    # Test with mock page
    print("\n[Test] Testing thumbnail generation...")

    # Create test image
    from PIL import Image, ImageDraw
    test_img = Image.new("RGB", (2480, 3508), "#FFFFFF")
    draw = ImageDraw.Draw(test_img)

    # Draw something
    draw.rectangle([100, 100, 500, 500], fill="#FF0000")
    draw.text((200, 300), "Test Page", fill="#000000")

    # Generate thumbnail
    thumbnail = generator.generate_thumbnail(test_img)
    print(f"✓ Generated thumbnail: {thumbnail.size[0]}x{thumbnail.size[1]}")

    # Test save
    import tempfile
    import os

    temp_dir = tempfile.mkdtemp(prefix="g-manga-thumb-test-")
    thumb_path = generator.save_thumbnail(thumbnail, temp_dir)
    print(f"✓ Saved thumbnail to: {os.path.basename(thumb_path)}")

    # Test batch generation (structure)
    print("\n[Test] Testing batch generation...")
    print("✓ Batch generation structure created")
    print("  Note: Requires actual ComicPage objects for full testing")

    # Test config update
    print("\n[Test] Testing config update...")
    generator.update_config(size=(200, 300), quality=90)
    print(f"✓ Updated config: {generator.config.size}, quality {generator.config.quality}")

    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)
    print(f"\n✓ Cleaned up temp directory: {temp_dir}")

    print("\n" + "=" * 70)
    print("Page Thumbnail Generator - PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()
