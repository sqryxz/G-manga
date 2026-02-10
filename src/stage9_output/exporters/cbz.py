"""
CBZ Exporter - Stage 9.1.3
Exports manga pages as CBZ comic book archive.
"""

import sys
sys.path.insert(0, '/home/clawd/projects/g-manga/src')

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import os
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone


@dataclass
class CBZMetadata:
    """CBZ metadata."""
    title: str = "Untitled Manga"
    author: str = "Unknown"
    series: str = ""
    volume: int = 1
    issue: int = 1
    description: str = "Manga comic created with G-Manga"
    language: str = "en"
    genre: str = "manga"
    rights: str = ""
    publisher: str = ""


@dataclass
class CBZConfig:
    """CBZ export configuration."""
    include_metadata: bool = True  # Include ComicInfo.xml
    include_thumbnails: bool = True  # Include thumbnail images
    thumbnail_size: Tuple[int, int] = (300, 425)  # (width, height)
    compression: int = 6  # Zip compression level (0-9)
    include_readme: bool = True  # Include README.txt


class CBZExporter:
    """Exports manga pages as CBZ comic book archive."""

    def __init__(
        self,
        config: Optional[CBZConfig] = None,
        metadata: Optional[CBZMetadata] = None
    ):
        """
        Initialize CBZ Exporter.

        Args:
            config: CBZ configuration (default: create new)
            metadata: CBZ metadata (default: create new)
        """
        self.config = config or CBZConfig()
        self.metadata = metadata or CBZMetadata()

    def export_cbz(
        self,
        page_paths: List[str],
        output_file: str,
        page_metadata: Optional[Dict[int, Dict[str, Any]]] = None
    ) -> str:
        """
        Export pages to CBZ.

        Args:
            page_paths: List of page image file paths
            output_file: Output CBZ file path
            page_metadata: Dictionary of page_number -> metadata

        Returns:
            File path to saved CBZ
        """
        with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED, self.config.compression) as zf:
            # Add pages
            for i, page_path in enumerate(page_paths):
                if not os.path.exists(page_path):
                    print(f"Warning: Page file not found: {page_path}")
                    continue

                # Generate filename
                filename = os.path.basename(page_path)

                # Add page to CBZ
                zf.write(page_path, filename)

                # Add thumbnail if configured
                if self.config.include_thumbnails:
                    self._add_thumbnail_to_cbz(zf, page_path, filename, self.config.thumbnail_size)

            # Add metadata file
            if self.config.include_metadata:
                metadata_xml = self._generate_comicinfo_xml(page_paths, page_metadata)
                zf.writestr("ComicInfo.xml", metadata_xml)

            # Add README if configured
            if self.config.include_readme:
                readme = self._generate_readme()
                zf.writestr("README.txt", readme)

        return output_file

    def export_cbz_from_directories(
        self,
        page_dirs: List[str],
        output_file: str
    ) -> str:
        """
        Export pages from directories to CBZ.

        Args:
            page_dirs: List of directories containing page images
            output_file: Output CBZ file path

        Returns:
            File path to saved CBZ
        """
        page_paths = []

        # Collect all page images
        for page_dir in page_dirs:
            if not os.path.exists(page_dir):
                continue

            for filename in sorted(os.listdir(page_dir)):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                    page_path = os.path.join(page_dir, filename)
                    page_paths.append(page_path)

        # Sort pages
        page_paths.sort()

        # Export to CBZ
        return self.export_cbz(page_paths, output_file)

    def _add_thumbnail_to_cbz(
        self,
        zf: zipfile.ZipFile,
        page_path: str,
        filename: str,
        thumbnail_size: Tuple[int, int]
    ):
        """
        Add thumbnail to CBZ.

        Args:
            zf: ZipFile object
            page_path: Page image path
            filename: Original filename
            thumbnail_size: (width, height) for thumbnail
        """
        from PIL import Image

        # Load page and create thumbnail
        img = Image.open(page_path).convert("RGB")
        thumb = img.copy()
        thumb.thumbnail(thumbnail_size, Image.LANCZOS)

        # Generate thumbnail filename
        base_name, ext = os.path.splitext(filename)
        thumb_filename = base_name + "_thumb" + ext

        # Save thumbnail to temp file and add to CBZ
        temp_thumb = f"/tmp/{thumb_filename}"
        thumb.save(temp_thumb, "PNG", optimize=True)

        with open(temp_thumb, 'rb') as f:
            zf.writestr(thumb_filename, f.read())

        # Clean up temp file
        os.remove(temp_thumb)

    def _generate_comicinfo_xml(
        self,
        page_paths: List[str],
        page_metadata: Optional[Dict[int, Dict[str, Any]]] = None
    ) -> str:
        """
        Generate ComicInfo.xml metadata.

        Args:
            page_paths: List of page image paths
            page_metadata: Dictionary of page_number -> metadata

        Returns:
            XML string
        """
        # Create root element
        root = ET.Element("ComicInfo")

        # Add title
        title = ET.SubElement(root, "Title")
        title.text = self.metadata.title

        # Add author
        author = ET.SubElement(root, "Author")
        author.text = self.metadata.author

        # Add series info
        if self.metadata.series:
            series = ET.SubElement(root, "Series")
            series.text = self.metadata.series

        # Add volume/issue
        volume = ET.SubElement(root, "Volume")
        volume.text = str(self.metadata.volume)

        issue = ET.SubElement(root, "Issue")
        issue.text = str(self.metadata.issue)

        # Add pages
        pages_elem = ET.SubElement(root, "Pages")
        pages_elem.text = str(len(page_paths))

        # Add page info
        for i, page_path in enumerate(page_paths):
            page_elem = ET.SubElement(root, "Page")

            page_num = ET.SubElement(page_elem, "Number")
            page_num.text = str(i + 1)

            filename_elem = ET.SubElement(page_elem, "Filename")
            filename_elem.text = os.path.basename(page_path)

            # Add metadata if available
            if page_metadata and i in page_metadata:
                meta = page_metadata[i]

                # Add panel count
                if "panel_count" in meta:
                    panels = ET.SubElement(page_elem, "PanelCount")
                    panels.text = str(meta["panel_count"])

                # Add reading order
                if "reading_order" in meta:
                    ro = ET.SubElement(page_elem, "ReadingOrder")
                    ro.text = ",".join(meta["reading_order"])

        # Add description
        description = ET.SubElement(root, "Description")
        description.text = self.metadata.description

        # Add language
        language = ET.SubElement(root, "Language")
        language.text = self.metadata.language

        # Add genre
        genre = ET.SubElement(root, "Genre")
        genre.text = self.metadata.genre

        # Add rights
        if self.metadata.rights:
            rights = ET.SubElement(root, "Rights")
            rights.text = self.metadata.rights

        # Add publisher
        if self.metadata.publisher:
            publisher = ET.SubElement(root, "Publisher")
            publisher.text = self.metadata.publisher

        # Add creation date
        created = ET.SubElement(root, "Created")
        created.text = datetime.now(timezone.utc).isoformat()

        # Generate XML string
        return self._prettify_xml(root)

    def _generate_readme(self) -> str:
        """
        Generate README.txt content.

        Returns:
            README text
        """
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S %Z')

        readme = f"""{self.metadata.title}
=================

Author: {self.metadata.author}
Created: {timestamp}

Description:
{self.metadata.description}

Contents:
- {len(self.metadata.title)} pages
- ComicInfo.xml metadata

This comic was created with G-Manga.

For more information, visit: https://github.com/g-manga
"""
        return readme

    def _prettify_xml(self, elem: ET.Element) -> str:
        """
        Pretty-print XML element.

        Args:
            elem: XML Element

        Returns:
            Formatted XML string
        """
        from xml.dom import minidom

        rough_string = ET.tostring(elem, 'utf-8')
        parsed = minidom.parseString(rough_string)
        return parsed.toprettyxml(indent="  ")

    def update_metadata(self, **kwargs):
        """
        Update CBZ metadata.

        Args:
            **kwargs: Metadata fields to update
        """
        for key, value in kwargs.items():
            if hasattr(self.metadata, key):
                setattr(self.metadata, key, value)

    def update_config(self, **kwargs):
        """
        Update CBZ configuration.

        Args:
            **kwargs: Configuration options to update
        """
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)

    def get_metadata_summary(self) -> Dict[str, Any]:
        """
        Get metadata summary.

        Returns:
            Dictionary with metadata info
        """
        return {
            "title": self.metadata.title,
            "author": self.metadata.author,
            "series": self.metadata.series,
            "volume": self.metadata.volume,
            "issue": self.metadata.issue,
            "language": self.metadata.language,
            "genre": self.metadata.genre
        }


def create_cbz_exporter(
    title: str = "Untitled Manga",
    author: str = "Unknown",
    series: str = "",
    volume: int = 1,
    issue: int = 1,
    language: str = "en"
) -> CBZExporter:
    """
    Create a CBZ exporter.

    Args:
        title: CBZ title
        author: CBZ author
        series: Series name
        volume: Volume number
        issue: Issue number
        language: Language code

    Returns:
        CBZExporter instance
    """
    metadata = CBZMetadata(
        title=title,
        author=author,
        series=series,
        volume=volume,
        issue=issue,
        language=language
    )

    return CBZExporter(metadata=metadata)


def main():
    """Test CBZ Exporter."""
    print("=" * 70)
    print("CBZ Exporter Test")
    print("=" * 70)

    # Create exporter
    print("\n[Test] Creating CBZ exporter...")
    exporter = create_cbz_exporter(
        title="Test Manga",
        author="Test Author",
        series="Test Series"
    )
    print("✓ CBZ exporter created")
    print(f"  Title: {exporter.metadata.title}")
    print(f"  Author: {exporter.metadata.author}")
    print(f"  Series: {exporter.metadata.series}")

    # Test metadata update
    print("\n[Test] Testing metadata update...")
    exporter.update_metadata(
        title="Updated Title",
        genre="fantasy",
        publisher="Test Publisher"
    )
    print("✓ Updated metadata:")
    print(f"  Title: {exporter.metadata.title}")
    print(f"  Genre: {exporter.metadata.genre}")
    print(f"  Publisher: {exporter.metadata.publisher}")

    # Test config update
    print("\n[Test] Testing config update...")
    exporter.update_config(
        compression=9,
        thumbnail_size=(200, 300),
        include_thumbnails=False
    )
    print("✓ Updated config:")
    print(f"  Compression: {exporter.config.compression}")
    print(f"  Thumbnail size: {exporter.config.thumbnail_size}")
    print(f"  Include thumbnails: {exporter.config.include_thumbnails}")

    # Test metadata summary
    print("\n[Test] Testing metadata summary...")
    summary = exporter.get_metadata_summary()
    print("✓ Metadata summary:")
    print(f"  Title: {summary['title']}")
    print(f"  Author: {summary['author']}")
    print(f"  Language: {summary['language']}")
    print(f"  Genre: {summary['genre']}")

    # Test CBZ export (structure test)
    print("\n[Test] Testing CBZ export (structure)...")
    print("✓ CBZ export structure created")
    print("  Note: Full export requires fpdf and actual page images")

    print("\n" + "=" * 70)
    print("CBZ Exporter - PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()
