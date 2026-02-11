"""
G-Manga CLI - Command-line interface for the manga generation pipeline.

Usage:
    g-manga generate --url <url> [--output <dir>]
    g-manga generate --file <path> [--output <dir>]
    g-manga resume --project-id <id>
    g-manga status --project-id <id>
    g-manga export --project-id <id> --format <pdf|cbz|images>
    g-manga list
    g-manga --help
"""

import json
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

import typer
from rich.console import Console
from rich.table import Table
from rich.text import Text

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config import Settings, get_settings
from models.project import Project, Metadata, generate_project_id
from stage1_input.url_fetcher import URLFetcher
from stage1_input.text_parser import TextParser
from stage1_input.metadata_extractor import MetadataExtractor
from stage1_input.project import ProjectInitializer

app = typer.Typer(
    name="g-manga",
    help="Transform Project Gutenberg literature into manga-styled comics",
    add_completion=False
)

console = Console()


def find_project_dir(project_id: str) -> Optional[Path]:
    """Find project directory by searching common locations."""
    # Common locations to search
    search_paths = [
        Path.cwd() / "projects",
        Path.cwd() / "output" / "projects",
    ]

    # Also try g-manga root
    cli_dir = Path(__file__).parent
    g_manga_root = cli_dir.parent
    search_paths.extend([
        g_manga_root / "projects",
        g_manga_root / "output" / "projects",
    ])

    for search_path in search_paths:
        project_dir = search_path / project_id
        if project_dir.exists():
            return project_dir

    return None


def get_projects_dir() -> Path:
    """Get the projects directory path."""
    settings = get_settings()
    projects_path = Path(settings.storage.projects_dir)

    # If relative path, make it relative to the g-manga root
    if not projects_path.is_absolute():
        # Try to find the g-manga root
        cli_dir = Path(__file__).parent
        g_manga_root = cli_dir.parent
        projects_path = g_manga_root / projects_path

    return projects_path


def load_project_state(project_id: str) -> Optional[dict]:
    """Load project state from disk."""
    project_dir = find_project_dir(project_id)

    if not project_dir:
        return None

    state_path = project_dir / "state.json"

    if not state_path.exists():
        return None

    with open(state_path, 'r') as f:
        return json.load(f)


def save_project_state(project_id: str, state: dict) -> None:
    """Save project state to disk."""
    project_dir = find_project_dir(project_id)

    if not project_dir:
        raise FileNotFoundError(f"Project '{project_id}' not found")

    state_path = project_dir / "state.json"

    with open(state_path, 'w') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


@app.command()
def generate(
    url: Optional[str] = typer.Option(None, "--url", "-u", help="Project Gutenberg URL to fetch"),
    file: Optional[Path] = typer.Option(None, "--file", "-f", help="Local text file path"),
    output: str = typer.Option("output", "--output", "-o", help="Output directory for project"),
    project_name: Optional[str] = typer.Option(None, "--name", "-n", help="Project name (auto-generated if not provided)"),
    use_mock: bool = typer.Option(True, "--mock/--no-mock", help="Use mock data for testing (default: True)"),
):
    """
    Generate manga from a Gutenberg URL or local file.

    Examples:
        g-manga generate --url "https://www.gutenberg.org/files/174/174-0.txt"
        g-manga generate --file ./book.txt --name "My Project"
        g-manga generate --url "https://www.gutenberg.org/files/174/174-0.txt" --no-mock
    """
    if not url and not file:
        console.print("[red]Error: Either --url or --file must be provided[/red]")
        raise typer.Exit(1)

    console.print("[bold green]🚀 Starting G-Manga pipeline...[/bold green]")

    try:
        settings = get_settings()
        settings.storage.output_dir = output
    except Exception:
        pass

    # Stage 1: Fetch and parse content
    console.print("\n[bold]Stage 1: Fetching and parsing content...[/bold]")

    fetcher = URLFetcher()
    parser = TextParser()
    extractor = MetadataExtractor()

    if url:
        console.print(f"Fetching from URL: {url}")
        raw_content = fetcher.fetch(url)
        source_url = url
    else:
        console.print(f"Reading from file: {file}")
        raw_content = file.read_text(encoding="utf-8")
        source_url = str(file.absolute())

    console.print("Parsing content...")
    cleaned_text, content_type = parser.parse(raw_content)

    console.print("Extracting metadata...")
    metadata_data = extractor.extract(cleaned_text, source_url=source_url)

    # Create metadata object
    if hasattr(metadata_data, 'model_dump'):
        metadata_dict = metadata_data.model_dump()
    else:
        metadata_dict = metadata_data.__dict__ if hasattr(metadata_data, '__dict__') else metadata_data

    metadata = Metadata(**metadata_dict)

    # Determine project name
    if project_name:
        name = project_name
    else:
        name = metadata.title or "untitled-project"

    # Create project
    console.print(f"\n[bold]Creating project: {name}[/bold]")

    projects_dir = Path(output) / "projects"
    initializer = ProjectInitializer(base_dir=str(projects_dir))
    project = initializer.create_project(name, metadata)

    # Store raw and cleaned text in project
    project.raw_text = raw_content
    project.cleaned_text = cleaned_text

    # Save updated project
    config_path = projects_dir / project.id / "config.json"
    with open(config_path, 'w') as f:
        config = {
            "id": project.id,
            "name": project.name,
            "metadata": project.metadata.model_dump(),
            "created_at": project.created_at.isoformat(),
            "version": "1.0"
        }
        json.dump(config, f, indent=2, ensure_ascii=False)

    console.print(f"[bold green]✓ Project created: {project.id}[/bold green]")
    console.print(f"  Title: {metadata.title}")
    console.print(f"  Author: {metadata.author}")
    console.print(f"  Location: {projects_dir / project.id}")
    console.print(f"  Characters in text: {len(cleaned_text):,}")

    # Initialize state
    project_dir = projects_dir / project.id
    state = {
        "id": project.id,
        "current_stage": "input",
        "stages_completed": ["input"],
        "updated_at": datetime.now().isoformat(),
        "use_mock": use_mock,
        "progress": {
            "input": {"status": "completed", "progress": 100}
        }
    }

    state_path = project_dir / "state.json"
    with open(state_path, 'w') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

    # Pipeline would continue here with stages 2-9
    console.print(f"\n[bold yellow]⚠️  Pipeline stages 2-9 not yet implemented in CLI[/bold yellow]")
    console.print(f"   Use 'g-manga resume --project-id {project.id}' when pipeline is complete")

    console.print(f"\n[bold green]✓ Generation started successfully![/bold green]")


@app.command()
def resume(
    project_id: str = typer.Argument(..., help="Project ID to resume"),
    from_stage: Optional[str] = typer.Option(None, "--from", help="Stage to resume from (default: current stage)"),
    use_mock: Optional[bool] = typer.Option(None, "--mock/--no-mock", help="Override mock mode"),
):
    """
    Resume pipeline execution from a checkpoint.

    Examples:
        g-manga resume dorian-gray-20260210
        g-manga resume dorian-gray-20260210 --from stage3
    """
    state = load_project_state(project_id)

    if not state:
        console.print(f"[red]Error: Project '{project_id}' not found[/red]")
        raise typer.Exit(1)

    current_stage = state.get("current_stage", "unknown")
    stages_completed = state.get("stages_completed", [])

    console.print(f"[bold]Resuming project: {project_id}[/bold]")
    console.print(f"  Current stage: {current_stage}")
    console.print(f"  Stages completed: {', '.join(stages_completed) if stages_completed else 'None'}")

    if from_stage:
        console.print(f"  Resuming from: {from_stage}")
    else:
        from_stage = current_stage

    # Pipeline resume logic would go here
    console.print(f"\n[bold yellow]⚠️  Resume functionality not yet fully implemented[/bold yellow]")
    console.print(f"   Current stage: {current_stage}")

    # Update state (placeholder)
    state["updated_at"] = datetime.now().isoformat()
    save_project_state(project_id, state)

    console.print(f"\n[bold green]✓ Resume initiated[/bold green]")


@app.command()
def status(
    project_id: str = typer.Argument(..., help="Project ID to check"),
):
    """
    Show detailed project status.

    Examples:
        g-manga status dorian-gray-20260210
    """
    state = load_project_state(project_id)

    if not state:
        console.print(f"[red]Error: Project '{project_id}' not found[/red]")
        raise typer.Exit(1)

    console.print(f"[bold]Project Status: {project_id}[/bold]\n")

    # Create status table
    table = Table(show_header=True, header_style="bold")
    table.add_column("Property", style="cyan")
    table.add_column("Value")

    table.add_row("Current Stage", state.get("current_stage", "Unknown"))
    table.add_row("Stages Completed", ", ".join(state.get("stages_completed", [])) or "None")
    table.add_row("Last Updated", state.get("updated_at", "Unknown"))
    table.add_row("Use Mock", str(state.get("use_mock", True)))

    # Progress details
    progress = state.get("progress", {})
    if progress:
        table.add_row("", "")
        table.add_row("Progress Details", "")
        for stage, data in progress.items():
            status_icon = "✓" if data.get("status") == "completed" else "○"
            table.add_row(f"  {status_icon} {stage}", f"{data.get('progress', 0)}%")

    console.print(table)


@app.command()
def export(
    project_id: str = typer.Argument(..., help="Project ID to export"),
    format: str = typer.Option(..., "--format", "-f", help="Export format (pdf, cbz, images)"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output directory"),
):
    """
    Export project to various formats.

    Examples:
        g-manga export dorian-gray-20260210 --format pdf
        g-manga export dorian-gray-20260210 --format cbz --output ./exports
    """
    valid_formats = ["pdf", "cbz", "images"]
    if format not in valid_formats:
        console.print(f"[red]Error: Invalid format '{format}'. Valid options: {', '.join(valid_formats)}[/red]")
        raise typer.Exit(1)

    state = load_project_state(project_id)

    if not state:
        console.print(f"[red]Error: Project '{project_id}' not found[/red]")
        raise typer.Exit(1)

    console.print(f"[bold]Exporting project: {project_id}[/bold]")
    console.print(f"  Format: {format}")
    console.print(f"  Output: {output or 'default output directory'}")

    # Export logic would go here
    if format == "pdf":
        console.print("[yellow]PDF export not yet implemented[/yellow]")
    elif format == "cbz":
        console.print("[yellow]CBZ export not yet implemented[/yellow]")
    elif format == "images":
        console.print("[yellow]Images export not yet implemented[/yellow]")

    console.print(f"\n[bold green]✓ Export initiated[/bold green]")


@app.command()
def list():
    """
    List all projects.
    """
    # Search in multiple locations
    search_paths = [
        Path.cwd() / "projects",
        Path.cwd() / "output" / "projects",
    ]

    cli_dir = Path(__file__).parent
    g_manga_root = cli_dir.parent
    search_paths.extend([
        g_manga_root / "projects",
        g_manga_root / "output" / "projects",
    ])

    projects = []
    seen_ids = set()

    for projects_dir in search_paths:
        if not projects_dir.exists():
            continue

        for project_dir in projects_dir.iterdir():
            if not project_dir.is_dir() or project_dir.name in seen_ids:
                continue

            config_path = project_dir / "config.json"
            state_path = project_dir / "state.json"

            if not config_path.exists():
                continue

            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)

                state = {}
                if state_path.exists():
                    with open(state_path, 'r') as f:
                        state = json.load(f)

                projects.append({
                    "id": config["id"],
                    "name": config["name"],
                    "title": config["metadata"]["title"],
                    "author": config["metadata"]["author"],
                    "created_at": config["created_at"],
                    "current_stage": state.get("current_stage", "unknown")
                })
                seen_ids.add(project_dir.name)
            except (json.JSONDecodeError, KeyError):
                continue

    if not projects:
        console.print("No projects found.")
        return

    console.print(f"[bold]Projects ({len(projects)})[/bold]\n")

    table = Table(show_header=True, header_style="bold")
    table.add_column("ID")
    table.add_column("Name")
    table.add_column("Title")
    table.add_column("Author")
    table.add_column("Stage")
    table.add_column("Created")

    for p in sorted(projects, key=lambda x: x["created_at"], reverse=True):
        table.add_row(
            p["id"],
            p["name"],
            p["title"][:30] + "..." if len(p["title"]) > 30 else p["title"],
            p["author"],
            p["current_stage"],
            p["created_at"][:10]
        )

    console.print(table)


@app.command()
def info():
    """
    Show G-Manga version and configuration info.
    """
    console.print("[bold]G-Manga Information[/bold]\n")

    try:
        from __init__ import __version__
        console.print(f"Version: {__version__}")
    except ImportError:
        console.print("Version: Unknown")

    console.print(f"Python: {sys.version}")
    console.print(f"Projects directory: {get_projects_dir()}")

    try:
        settings = get_settings()
        console.print(f"Default output directory: {settings.storage.output_dir}")
        console.print(f"LLM provider: {settings.llm.provider}")
        console.print(f"Image provider: {settings.image.default_provider}")
    except Exception as e:
        console.print(f"[yellow]Could not load settings: {e}[/yellow]")


@app.command()
def version():
    """
    Show version information.
    """
    try:
        from __init__ import __version__
        console.print(__version__)
    except ImportError:
        console.print("0.1.0")


def main():
    """Main entry point."""
    app()


if __name__ == "__main__":
    app()
