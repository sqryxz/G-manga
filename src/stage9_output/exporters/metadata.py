"""
Metadata Exporter - Stage 9.1.4
Exports project metadata, storyboards, and statistics.
"""

import sys
sys.path.insert(0, '/home/clawd/projects/g-manga/src')

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import json
import os
from datetime import datetime


class MetadataFormat(Enum):
    """Metadata export formats."""
    JSON = "json"
    CSV = "csv"
    YAML = "yaml"


@dataclass
class ExportMetadata:
    """Metadata to export."""
    project_id: str
    project_name: str
    title: str
    author: str
    source_url: str
    created_at: str
    completed_at: str
    total_pages: int
    total_panels: int
    total_chapters: int
    total_scenes: int
    characters: List[Dict[str, Any]]
    chapters: List[Dict[str, Any]]
    export_stats: Dict[str, Any]


class MetadataExporter:
    """Exports project metadata in various formats."""

    def __init__(self, project_dir: str):
        """
        Initialize Metadata Exporter.

        Args:
            project_dir: Project directory path
        """
        self.project_dir = project_dir
        self.intermediate_dir = os.path.join(project_dir, "intermediate")
        self.output_dir = os.path.join(project_dir, "output")

    def load_project_data(self) -> Dict[str, Any]:
        """Load all project data from intermediate files."""
        data = {}

        # Load config
        config_path = os.path.join(self.project_dir, "config.json")
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                data['config'] = json.load(f)

        # Load state
        state_path = os.path.join(self.project_dir, "state.json")
        if os.path.exists(state_path):
            with open(state_path, 'r') as f:
                data['state'] = json.load(f)

        # Load chapters
        chapters_path = os.path.join(self.intermediate_dir, "chapters.json")
        if os.path.exists(chapters_path):
            with open(chapters_path, 'r') as f:
                data['chapters'] = json.load(f)

        # Load scenes
        scenes_path = os.path.join(self.intermediate_dir, "scenes.json")
        if os.path.exists(scenes_path):
            with open(scenes_path, 'r') as f:
                data['scenes'] = json.load(f)

        # Load characters
        characters_path = os.path.join(self.intermediate_dir, "characters.json")
        if os.path.exists(characters_path):
            with open(characters_path, 'r') as f:
                data['characters'] = json.load(f)

        # Load storyboard
        storyboard_path = os.path.join(self.intermediate_dir, "storyboard.json")
        if os.path.exists(storyboard_path):
            with open(storyboard_path, 'r') as f:
                data['storyboard'] = json.load(f)

        # Load panels
        panels_path = os.path.join(self.intermediate_dir, "panels.json")
        if os.path.exists(panels_path):
            with open(panels_path, 'r') as f:
                data['panels'] = json.load(f)

        return data

    def generate_export_metadata(self, format_type: str = "json") -> ExportMetadata:
        """
        Generate export metadata from project data.

        Args:
            format_type: Export format type

        Returns:
            ExportMetadata object
        """
        data = self.load_project_data()

        # Extract basic info from config
        config = data.get('config', {})
        metadata = config.get('metadata', {})

        # Count elements
        chapters = data.get('chapters', [])
        scenes = data.get('scenes', [])
        characters = data.get('characters', [])
        storyboard = data.get('storyboard', {})
        pages = storyboard.get('pages', [])
        panels = data.get('panels', [])

        # Calculate stats
        total_panels = len(panels) if panels else sum(len(p.get('panels', [])) for p in pages)

        export_meta = ExportMetadata(
            project_id=config.get('project_id', 'unknown'),
            project_name=config.get('project_name', 'Unknown'),
            title=metadata.get('title', 'Unknown'),
            author=metadata.get('author', 'Unknown'),
            source_url=metadata.get('source_url', ''),
            created_at=config.get('created_at', datetime.now().isoformat()),
            completed_at=datetime.now().isoformat(),
            total_pages=len(pages),
            total_panels=total_panels,
            total_chapters=len(chapters),
            total_scenes=len(scenes),
            characters=[{
                'id': c.get('id', ''),
                'name': c.get('name', ''),
                'aliases': c.get('aliases', []),
                'appearance': c.get('appearance', {})
            } for c in characters],
            chapters=[{
                'id': ch.get('id', ''),
                'number': ch.get('chapter_number', 0),
                'title': ch.get('title', ''),
                'num_scenes': len([s for s in scenes if s.get('chapter_id') == ch.get('id')])
            } for ch in chapters],
            export_stats={
                'export_format': format_type,
                'export_timestamp': datetime.now().isoformat(),
                'source_format': config.get('metadata', {}).get('format', 'text'),
                'generation_time_hours': 0,
                'api_calls': {
                    'gpt_requests': 0,
                    'image_generations': total_panels
                }
            }
        )

        return export_meta

    def export_metadata(
        self,
        output_dir: Optional[str] = None,
        format_type: str = "json"
    ) -> str:
        """
        Export project metadata.

        Args:
            output_dir: Output directory (default: project output dir)
            format_type: Export format (json, csv, yaml)

        Returns:
            Exported file path
        """
        if output_dir is None:
            output_dir = self.output_dir

        os.makedirs(output_dir, exist_ok=True)

        export_meta = self.generate_export_metadata(format_type)

        if format_type == "json":
            return self._export_json(export_meta, output_dir)
        elif format_type == "csv":
            return self._export_csv(export_meta, output_dir)
        elif format_type == "yaml":
            return self._export_yaml(export_meta, output_dir)
        else:
            raise ValueError(f"Unsupported format: {format_type}")

    def _export_json(self, export_meta: ExportMetadata, output_dir: str) -> str:
        """Export metadata as JSON."""
        output_path = os.path.join(output_dir, "metadata.json")

        export_data = {
            'project_info': {
                'project_id': export_meta.project_id,
                'project_name': export_meta.project_name,
                'title': export_meta.title,
                'author': export_meta.author,
                'source_url': export_meta.source_url,
                'created_at': export_meta.created_at,
                'completed_at': export_meta.completed_at
            },
            'statistics': {
                'total_pages': export_meta.total_pages,
                'total_panels': export_meta.total_panels,
                'total_chapters': export_meta.total_chapters,
                'total_scenes': export_meta.total_scenes,
                'total_characters': len(export_meta.characters)
            },
            'characters': export_meta.characters,
            'chapters': export_meta.chapters,
            'export_stats': export_meta.export_stats
        }

        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)

        return output_path

    def _export_csv(self, export_meta: ExportMetadata, output_dir: str) -> str:
        """Export metadata as CSV."""
        output_path = os.path.join(output_dir, "metadata.csv")

        with open(output_path, 'w') as f:
            # Project info
            f.write("Project Info\n")
            f.write(f"Project ID,{export_meta.project_id}\n")
            f.write(f"Project Name,{export_meta.project_name}\n")
            f.write(f"Title,{export_meta.title}\n")
            f.write(f"Author,{export_meta.author}\n")
            f.write(f"Source URL,{export_meta.source_url}\n")
            f.write(f"Created At,{export_meta.created_at}\n")
            f.write(f"Completed At,{export_meta.completed_at}\n\n")

            # Statistics
            f.write("Statistics\n")
            f.write(f"Total Pages,{export_meta.total_pages}\n")
            f.write(f"Total Panels,{export_meta.total_panels}\n")
            f.write(f"Total Chapters,{export_meta.total_chapters}\n")
            f.write(f"Total Scenes,{export_meta.total_scenes}\n\n")

            # Characters
            f.write("Characters\n")
            f.write("ID,Name,Aliases\n")
            for char in export_meta.characters:
                aliases = '; '.join(char.get('aliases', []))
                f.write(f"{char['id']},{char['name']},\"{aliases}\"\n")

        return output_path

    def _export_yaml(self, export_meta: ExportMetadata, output_dir: str) -> str:
        """Export metadata as YAML."""
        output_path = os.path.join(output_dir, "metadata.yaml")

        export_data = {
            'project': {
                'id': export_meta.project_id,
                'name': export_meta.project_name,
                'title': export_meta.title,
                'author': export_meta.author,
                'source_url': export_meta.source_url,
                'created_at': export_meta.created_at,
                'completed_at': export_meta.completed_at
            },
            'statistics': {
                'total_pages': export_meta.total_pages,
                'total_panels': export_meta.total_panels,
                'total_chapters': export_meta.total_chapters,
                'total_scenes': export_meta.total_scenes,
                'total_characters': len(export_meta.characters)
            },
            'characters': export_meta.characters,
            'chapters': export_meta.chapters,
            'export_stats': export_meta.export_stats
        }

        with open(output_path, 'w') as f:
            # Simple YAML writing without pyyaml dependency
            self._write_yaml(f, export_data, 0)

        return output_path

    def _write_yaml(self, f, data, indent: int):
        """Write YAML with simple indentation."""
        spaces = '  ' * indent

        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    f.write(f"{spaces}{key}:\n")
                    self._write_yaml(f, value, indent + 1)
                else:
                    f.write(f"{spaces}{key}: {value}\n")
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, (dict, list)):
                    f.write(f"{spaces}-\n")
                    self._write_yaml(f, item, indent + 1)
                else:
                    f.write(f"{spaces}- {item}\n")

    def export_character_sheet(
        self,
        output_dir: Optional[str] = None
    ) -> str:
        """
        Export detailed character reference sheet.

        Args:
            output_dir: Output directory

        Returns:
            Exported file path
        """
        if output_dir is None:
            output_dir = self.output_dir

        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "character_sheet.json")

        data = self.load_project_data()
        characters = data.get('characters', [])

        character_sheet = {
            'generated_at': datetime.now().isoformat(),
            'total_characters': len(characters),
            'characters': []
        }

        for char in characters:
            char_data = {
                'id': char.get('id', ''),
                'name': char.get('name', ''),
                'aliases': char.get('aliases', []),
                'appearance': char.get('appearance', {}),
                'reference_prompt': char.get('reference_prompt', ''),
                'first_appearance': char.get('first_appearance', ''),
                'relationships': char.get('relationships', [])
            }
            character_sheet['characters'].append(char_data)

        with open(output_path, 'w') as f:
            json.dump(character_sheet, f, indent=2)

        return output_path

    def export_story_summary(self, output_dir: Optional[str] = None) -> str:
        """
        Export story summary and chapter breakdown.

        Args:
            output_dir: Output directory

        Returns:
            Exported file path
        """
        if output_dir is None:
            output_dir = self.output_dir

        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "story_summary.json")

        data = self.load_project_data()
        chapters = data.get('chapters', [])
        scenes = data.get('scenes', [])
        storyboard = data.get('storyboard', {})

        summary = {
            'generated_at': datetime.now().isoformat(),
            'total_chapters': len(chapters),
            'total_scenes': len(scenes),
            'total_pages': len(storyboard.get('pages', [])),
            'chapters': []
        }

        for chapter in chapters:
            chapter_scenes = [s for s in scenes if s.get('chapter_id') == chapter.get('id')]
            chapter_data = {
                'id': chapter.get('id', ''),
                'number': chapter.get('chapter_number', 0),
                'title': chapter.get('title', ''),
                'num_scenes': len(chapter_scenes),
                'scenes': []
            }

            for scene in chapter_scenes:
                scene_data = {
                    'id': scene.get('id', ''),
                    'number': scene.get('scene_number', 0),
                    'summary': scene.get('summary', ''),
                    'location': scene.get('location', ''),
                    'characters': scene.get('characters', [])
                }
                chapter_data['scenes'].append(scene_data)

            summary['chapters'].append(chapter_data)

        with open(output_path, 'w') as f:
            json.dump(summary, f, indent=2)

        return output_path

    def get_export_info(self) -> Dict[str, Any]:
        """Get export information."""
        data = self.load_project_data()

        chapters = data.get('chapters', [])
        scenes = data.get('scenes', [])
        characters = data.get('characters', [])
        storyboard = data.get('storyboard', {})
        pages = storyboard.get('pages', [])

        return {
            'project_id': self.project_dir.split('/')[-1],
            'total_chapters': len(chapters),
            'total_scenes': len(scenes),
            'total_characters': len(characters),
            'total_pages': len(pages),
            'has_storyboard': bool(storyboard),
            'output_dir_exists': os.path.exists(self.output_dir)
        }


def create_metadata_exporter(project_dir: str) -> MetadataExporter:
    """
    Create a metadata exporter.

    Args:
        project_dir: Project directory path

    Returns:
        MetadataExporter instance
    """
    return MetadataExporter(project_dir)


def main():
    """Test Metadata Exporter."""
    print("=" * 70)
    print("Metadata Exporter Test")
    print("=" * 70)

    # Create test project structure
    import tempfile
    test_dir = tempfile.mkdtemp(prefix="g-manga-test-")
    print(f"\n[Test] Creating test project in: {test_dir}")

    # Create minimal config
    config = {
        "project_id": "test-project",
        "project_name": "Test Project",
        "metadata": {
            "title": "The Picture of Dorian Gray",
            "author": "Oscar Wilde",
            "source_url": "https://www.gutenberg.org/files/174/174-0.txt"
        },
        "created_at": "2026-02-06T10:00:00Z"
    }

    with open(os.path.join(test_dir, "config.json"), 'w') as f:
        json.dump(config, f)

    # Create intermediate directory
    os.makedirs(os.path.join(test_dir, "intermediate"))
    with open(os.path.join(test_dir, "intermediate", "chapters.json"), 'w') as f:
        json.dump([
            {"id": "chapter-1", "chapter_number": 1, "title": "The Studio"},
            {"id": "chapter-2", "chapter_number": 2, "title": "The Portrait"}
        ], f)

    with open(os.path.join(test_dir, "intermediate", "characters.json"), 'w') as f:
        json.dump([
            {
                "id": "char-001",
                "name": "Basil Hallward",
                "aliases": ["Basil"],
                "appearance": {"age": "late 20s", "hair": "dark"}
            }
        ], f)

    # Create output directory
    os.makedirs(os.path.join(test_dir, "output"))

    # Test exporter
    print("\n[Test] Creating metadata exporter...")
    exporter = create_metadata_exporter(test_dir)
    print(f"✓ Metadata exporter created")

    # Test info
    print("\n[Test] Getting export info...")
    info = exporter.get_export_info()
    print(f"✓ Export info:")
    print(f"  Project ID: {info['project_id']}")
    print(f"  Total chapters: {info['total_chapters']}")
    print(f"  Total characters: {info['total_characters']}")

    # Test metadata export
    print("\n[Test] Testing JSON export...")
    json_path = exporter.export_metadata(format_type="json")
    print(f"✓ JSON exported to: {json_path}")

    # Test CSV export
    print("\n[Test] Testing CSV export...")
    csv_path = exporter.export_metadata(format_type="csv")
    print(f"✓ CSV exported to: {csv_path}")

    # Test character sheet export
    print("\n[Test] Testing character sheet export...")
    char_path = exporter.export_character_sheet()
    print(f"✓ Character sheet exported to: {char_path}")

    # Test story summary export
    print("\n[Test] Testing story summary export...")
    summary_path = exporter.export_story_summary()
    print(f"✓ Story summary exported to: {summary_path}")

    # Read back JSON to verify
    print("\n[Test] Verifying JSON export...")
    with open(json_path, 'r') as f:
        exported_data = json.load(f)

    print(f"✓ Verified export:")
    print(f"  Project title: {exported_data['project_info']['title']}")
    print(f"  Statistics: {exported_data['statistics']}")

    # Cleanup
    import shutil
    shutil.rmtree(test_dir)

    print("\n" + "=" * 70)
    print("Metadata Exporter - PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()
