"""
Project Initializer - Stage 1.1.5
Creates and initializes G-Manga projects.
"""

import json
import hashlib
from pathlib import Path
from typing import Optional
from datetime import datetime

# For testing - adjust path
import sys
sys.path.insert(0, '/home/clawd/projects/g-manga/src')
from models.project import Project, Metadata, generate_project_id


class ProjectInitializer:
    """Creates and initializes new G-Manga projects."""

    def __init__(self, base_dir: str = "./projects"):
        """
        Initialize Project Initializer.

        Args:
            base_dir: Base directory for projects
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def create_project(self, name: str, metadata: Metadata) -> Project:
        """
        Create a new G-Manga project.

        Args:
            name: Project name
            metadata: Project metadata

        Returns:
            Initialized Project object
        """
        # Generate unique project ID
        project_id = generate_project_id(name)

        # Create project directory structure
        project_dir = self.base_dir / project_id
        project_dir.mkdir(exist_ok=True)

        # Create subdirectories
        subdirs = [
            "cache",
            "intermediate",
            "output/panels",
            "output/pages",
            "output/thumbnails",
            "src"
        ]
        for subdir in subdirs:
            (project_dir / subdir).mkdir(parents=True, exist_ok=True)

        # Create Project object
        project = Project(
            id=project_id,
            name=name,
            metadata=metadata
        )

        # Save initial state
        self._save_config(project_dir, project)
        self._save_state(project_dir, project)

        return project

    def _save_config(self, project_dir: Path, project: Project) -> None:
        """
        Save project configuration.

        Args:
            project_dir: Project directory
            project: Project object
        """
        config = {
            "id": project.id,
            "name": project.name,
            "metadata": project.metadata.model_dump(),
            "created_at": project.created_at.isoformat(),
            "version": "1.0"
        }

        config_path = project_dir / "config.json"
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

    def _save_state(self, project_dir: Path, project: Project) -> None:
        """
        Save project state.

        Args:
            project_dir: Project directory
            project: Project object
        """
        state = {
            "id": project.id,
            "current_stage": "input",
            "stages_completed": [],
            "updated_at": project.updated_at.isoformat(),
            "checksum": self._compute_checksum(project)
        }

        state_path = project_dir / "state.json"
        with open(state_path, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)

    def _compute_checksum(self, project: Project) -> str:
        """
        Compute checksum of project data.

        Args:
            project: Project object

        Returns:
            MD5 checksum string
        """
        data = f"{project.id}{project.name}{len(project.chapters)}{len(project.scenes)}"
        return hashlib.md5(data.encode()).hexdigest()

    def load_project(self, project_id: str) -> Optional[Project]:
        """
        Load an existing project.

        Args:
            project_id: Project ID

        Returns:
            Project object or None if not found
        """
        project_dir = self.base_dir / project_id

        if not project_dir.exists():
            return None

        config_path = project_dir / "config.json"
        if not config_path.exists():
            return None

        # Load config
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # Reconstruct Project
        metadata = Metadata(**config["metadata"])

        project = Project(
            id=config["id"],
            name=config["name"],
            metadata=metadata
        )

        project.created_at = datetime.fromisoformat(config["created_at"])

        return project

    def list_projects(self) -> list:
        """
        List all projects.

        Returns:
            List of project info dicts
        """
        projects = []

        for project_dir in self.base_dir.iterdir():
            if not project_dir.is_dir():
                continue

            config_path = project_dir / "config.json"
            if not config_path.exists():
                continue

            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)

                projects.append({
                    "id": config["id"],
                    "name": config["name"],
                    "title": config["metadata"]["title"],
                    "author": config["metadata"]["author"],
                    "created_at": config["created_at"]
                })
            except (json.JSONDecodeError, KeyError):
                continue

        return sorted(projects, key=lambda p: p["created_at"], reverse=True)


def main():
    """Test Project Initializer."""
    import sys
    sys.path.insert(0, '/home/clawd/projects/g-manga/src/stage1_input')

    from url_fetcher import URLFetcher
    from text_parser import TextParser
    from metadata_extractor import MetadataExtractor

    # Fetch and parse a test text
    test_url = "https://www.gutenberg.org/files/174/174-0.txt"

    fetcher = URLFetcher()
    raw_content = fetcher.fetch(test_url)

    parser = TextParser()
    cleaned_text, _ = parser.parse(raw_content)

    extractor = MetadataExtractor()
    metadata_data = extractor.extract(cleaned_text, source_url=test_url)

    # Create metadata object
    metadata = Metadata(**metadata_data.model_dump() if hasattr(metadata_data, 'model_dump') else metadata_data.__dict__)

    # Create project
    initializer = ProjectInitializer(base_dir="/home/clawd/projects/g-manga/projects")
    project = initializer.create_project("Dorian Gray", metadata)

    print(f"✓ Project created: {project.id}")
    print(f"  Name: {project.name}")
    print(f"  Title: {project.metadata.title}")
    print(f"  Author: {project.metadata.author}")
    print(f"  Directory: /home/clawd/projects/g-manga/projects/{project.id}")

    # List all projects
    print("\nAll projects:")
    for p in initializer.list_projects():
        print(f"  - {p['name']} ({p['title']})")


if __name__ == "__main__":
    main()
