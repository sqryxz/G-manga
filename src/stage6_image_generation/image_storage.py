"""
Image Storage - Stage 6.1.7
Handles saving and storing generated images.
"""

import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from pathlib import Path

from .base import GenerationResult, ImageProvider


class ImageStorage:
    """Handles image file storage and metadata."""

    def __init__(
        self,
        project_dir: str,
        create_subdirs: bool = True
    ):
        """
        Initialize image storage.

        Args:
            project_dir: Project directory for storage
            create_subdirs: Create subdirectories (panels/, metadata/)
        """
        self.project_dir = project_dir
        self.panels_dir = os.path.join(project_dir, "output", "panels")
        self.metadata_file = os.path.join(self.panels_dir, "metadata.json")
        self.index_file = os.path.join(self.panels_dir, "index.json")

        # Create directories if needed
        if create_subdirs:
            os.makedirs(self.panels_dir, exist_ok=True)

        # Load existing metadata
        self.metadata = self._load_metadata()
        self.index = self._load_index()

        # Statistics
        self.images_saved = 0
        self.total_bytes = 0

    def save_image(
        self,
        result: GenerationResult,
        panel_id: str,
        scene_id: str,
        prompt: str,
        **kwargs
    ) -> str:
        """
        Save a generated image.

        Args:
            result: Generation result
            panel_id: Panel ID
            scene_id: Scene ID
            prompt: Original prompt
            **kwargs: Additional metadata

        Returns:
            File path to saved image
        """
        if not result.success or not result.image_bytes:
            raise ValueError("Cannot save failed generation")

        # Generate filename
        filename = f"{panel_id}.png"
        filepath = os.path.join(self.panels_dir, filename)

        # Save image
        with open(filepath, 'wb') as f:
            f.write(result.image_bytes)

        # Update statistics
        self.images_saved += 1
        self.total_bytes += len(result.image_bytes)

        # Update metadata
        self.metadata[panel_id] = {
            "panel_id": panel_id,
            "scene_id": scene_id,
            "prompt": prompt,
            "file": filename,
            "file_path": filepath,
            "file_size": len(result.image_bytes),
            "file_format": result.image_format,
            "provider": result.provider.value,
            "cost": result.cost,
            "generated_at": result.generated_at.isoformat() if result.generated_at else None,
            "metadata": result.metadata,
            **kwargs
        }

        # Update index
        self._update_index(panel_id, scene_id)

        # Save metadata
        self._save_metadata()

        return filepath

    def save_image_bytes(
        self,
        image_bytes: bytes,
        filename: str,
        panel_id: str,
        scene_id: str,
        prompt: str,
        **kwargs
    ) -> str:
        """
        Save raw image bytes.

        Args:
            image_bytes: Image data
            filename: Filename
            panel_id: Panel ID
            scene_id: Scene ID
            prompt: Original prompt
            **kwargs: Additional metadata

        Returns:
            File path to saved image
        """
        filepath = os.path.join(self.panels_dir, filename)

        # Save image
        with open(filepath, 'wb') as f:
            f.write(image_bytes)

        # Update statistics
        self.images_saved += 1
        self.total_bytes += len(image_bytes)

        # Update metadata
        self.metadata[panel_id] = {
            "panel_id": panel_id,
            "scene_id": scene_id,
            "prompt": prompt,
            "file": filename,
            "file_path": filepath,
            "file_size": len(image_bytes),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            **kwargs
        }

        # Update index
        self._update_index(panel_id, scene_id)

        # Save metadata
        self._save_metadata()

        return filepath

    def get_image(self, panel_id: str) -> Optional[bytes]:
        """
        Load an image by panel ID.

        Args:
            panel_id: Panel ID

        Returns:
            Image bytes or None
        """
        if panel_id not in self.metadata:
            return None

        filepath = self.metadata[panel_id]["file_path"]

        if not os.path.exists(filepath):
            return None

        with open(filepath, 'rb') as f:
            return f.read()

    def get_image_path(self, panel_id: str) -> Optional[str]:
        """
        Get file path for an image.

        Args:
            panel_id: Panel ID

        Returns:
            File path or None
        """
        if panel_id not in self.metadata:
            return None

        return self.metadata[panel_id]["file_path"]

    def get_metadata(self, panel_id: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for an image.

        Args:
            panel_id: Panel ID

        Returns:
            Metadata dictionary or None
        """
        return self.metadata.get(panel_id)

    def get_scene_panels(self, scene_id: str) -> List[Dict[str, Any]]:
        """
        Get all panels for a scene.

        Args:
            scene_id: Scene ID

        Returns:
            List of panel metadata
        """
        return [
            meta for meta in self.metadata.values()
            if meta.get("scene_id") == scene_id
        ]

    def delete_image(self, panel_id: str) -> bool:
        """
        Delete an image.

        Args:
            panel_id: Panel ID

        Returns:
            True if deleted, False otherwise
        """
        if panel_id not in self.metadata:
            return False

        filepath = self.metadata[panel_id]["file_path"]

        # Delete file
        if os.path.exists(filepath):
            os.remove(filepath)

        # Remove from metadata
        del self.metadata[panel_id]

        # Update index
        if scene_id := self.metadata.get(panel_id, {}).get("scene_id"):
            self._update_index(panel_id, scene_id, remove=True)

        # Save metadata
        self._save_metadata()

        return True

    def _load_metadata(self) -> Dict[str, Any]:
        """Load metadata from file."""
        if os.path.exists(self.metadata_file):
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _save_metadata(self):
        """Save metadata to file."""
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, indent=2, ensure_ascii=False)

    def _load_index(self) -> Dict[str, List[str]]:
        """Load index from file."""
        if os.path.exists(self.index_file):
            with open(self.index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _save_index(self):
        """Save index to file."""
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(self.index, f, indent=2, ensure_ascii=False)

    def _update_index(self, panel_id: str, scene_id: str, remove: bool = False):
        """
        Update scene index.

        Args:
            panel_id: Panel ID
            scene_id: Scene ID
            remove: If True, remove from index
        """
        if scene_id not in self.index:
            self.index[scene_id] = []

        if remove:
            if panel_id in self.index[scene_id]:
                self.index[scene_id].remove(panel_id)
        else:
            if panel_id not in self.index[scene_id]:
                self.index[scene_id].append(panel_id)

        self._save_index()

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get storage statistics.

        Returns:
            Dictionary with statistics
        """
        # Calculate total size in MB
        total_size_mb = self.total_bytes / (1024 * 1024)

        # Count by provider
        provider_counts = {}
        for meta in self.metadata.values():
            provider = meta.get("provider", "unknown")
            provider_counts[provider] = provider_counts.get(provider, 0) + 1

        # Count by scene
        scene_counts = {}
        for meta in self.metadata.values():
            scene_id = meta.get("scene_id", "unknown")
            scene_counts[scene_id] = scene_counts.get(scene_id, 0) + 1

        return {
            "images_saved": self.images_saved,
            "total_bytes": self.total_bytes,
            "total_size_mb": round(total_size_mb, 2),
            "panels_directory": self.panels_dir,
            "provider_counts": provider_counts,
            "scene_counts": scene_counts,
            "total_scenes": len(scene_counts)
        }

    def export_summary(self, output_file: str):
        """
        Export summary to JSON file.

        Args:
            output_file: Output file path
        """
        summary = {
            "statistics": self.get_statistics(),
            "metadata": self.metadata,
            "index": self.index,
            "exported_at": datetime.now(timezone.utc).isoformat()
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        print(f"✓ Exported summary to {output_file}")


def create_image_storage(
    project_dir: str,
    create_subdirs: bool = True
) -> ImageStorage:
    """
    Create an image storage instance.

    Args:
        project_dir: Project directory
        create_subdirs: Create subdirectories

    Returns:
        ImageStorage instance
    """
    return ImageStorage(
        project_dir=project_dir,
        create_subdirs=create_subdirs
    )


def main():
    """Test Image Storage."""
    print("=" * 70)
    print("Image Storage Test")
    print("=" * 70)

    import tempfile
    import shutil

    # Create temp directory
    temp_dir = tempfile.mkdtemp(prefix="g-manga-test-")

    try:
        # Create storage
        print("\n[Test] Creating image storage...")
        storage = create_image_storage(temp_dir)
        print(f"✓ Storage created at: {temp_dir}")
        print(f"  Panels dir: {storage.panels_dir}")

        # Test saving image
        print("\n[Test] Saving image...")
        fake_image = b'\x89PNG\r\n\x1a\n' + b'x' * 5000
        from stage6_image_generation.providers.base import GenerationResult, ProviderType

        result = GenerationResult(
            success=True,
            image_bytes=fake_image,
            image_format="png",
            provider=ProviderType.DALLE3,
            prompt="A cat",
            metadata={},
            cost=0.04
        )

        filepath = storage.save_image(
            result=result,
            panel_id="p1-1",
            scene_id="scene-1",
            prompt="A cat"
        )

        print(f"✓ Image saved to: {filepath}")

        # Test getting image
        print("\n[Test] Getting image...")
        loaded = storage.get_image("p1-1")
        print(f"✓ Loaded {len(loaded)} bytes")

        # Test metadata
        print("\n[Test] Getting metadata...")
        meta = storage.get_metadata("p1-1")
        print(f"✓ Panel ID: {meta['panel_id']}")
        print(f"  Scene ID: {meta['scene_id']}")
        print(f"  File size: {meta['file_size']} bytes")

        # Test statistics
        print("\n[Test] Getting statistics...")
        stats = storage.get_statistics()
        print(f"✓ Images saved: {stats['images_saved']}")
        print(f"  Total size: {stats['total_size_mb']} MB")

        # Test export summary
        print("\n[Test] Exporting summary...")
        export_file = os.path.join(temp_dir, "summary.json")
        storage.export_summary(export_file)
        print(f"✓ Summary exported to: {export_file}")

        # Test delete
        print("\n[Test] Deleting image...")
        deleted = storage.delete_image("p1-1")
        print(f"✓ Deleted: {deleted}")

        print("\n" + "=" * 70)
        print("Image Storage - PASSED")
        print("=" * 70)

    finally:
        # Cleanup
        shutil.rmtree(temp_dir)
        print(f"\n✓ Cleaned up temp directory: {temp_dir}")


if __name__ == "__main__":
    main()
