"""
Storyboard Review CLI - Stage 3.2
Interactive CLI for reviewing and editing storyboards.
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

import typer
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
from rich.text import Text
from rich.panel import Panel
from rich import print as rprint

# Add src to path for imports
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from stage3_story_planning.storyboard_storage import (
    StoryboardStorage, Storyboard, StoryboardPanel
)

app = typer.Typer(
    name="storyboard",
    help="Review and edit storyboards",
    add_completion=False
)

console = Console()


def find_project_dir(project_id: str) -> Optional[Path]:
    """Find project directory by searching common locations."""
    search_paths = [
        Path.cwd() / "projects",
        Path.cwd() / "output" / "projects",
    ]

    cli_dir = Path(__file__).parent.parent
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


def display_panel(panel: StoryboardPanel, index: int):
    """Display a single panel with details."""
    status_color = {
        "pending": "yellow",
        "approved": "green",
        "rejected": "red"
    }.get(panel.status, "white")

    panel_content = f"""
[bold]Panel {panel.panel_number}:[/bold] {panel.panel_id}
[cyan]Status:[/cyan] [{status_color}]{panel.status}[/]

[cyan]Description:[/cyan] {panel.description}

[cyan]Camera:[/cyan] {panel.camera} | [cyan]Mood:[/cyan] {panel.mood}
[cyan]Lighting:[/cyan] {panel.lighting or 'N/A'} | [cyan]Composition:[/cyan] {panel.composition or 'N/A'}
[cyan]Action:[/cyan] {panel.action or 'N/A'}
[cyan]Dialogue:[/cyan] {panel.dialogue or 'None'}
    """

    console.print(Panel(panel_content.strip(), title=f"Panel {index + 1}"))


@app.command()
def list(
    project_id: str = typer.Argument(..., help="Project ID"),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status"),
):
    """
    List all storyboards in a project.

    Examples:
        g-manga storyboard list dorian-gray-20260210
        g-manga storyboard list dorian-gray-20260210 --status draft
    """
    project_dir = find_project_dir(project_id)

    if not project_dir:
        console.print(f"[red]Error: Project '{project_id}' not found[/red]")
        raise typer.Exit(1)

    storage = StoryboardStorage(str(project_dir))
    storyboards = storage.list_storyboards()

    if not storyboards:
        console.print(f"[yellow]No storyboards found in project '{project_id}'[/yellow]")
        return

    # Filter by status if specified
    if status:
        storyboards = [sb for sb in storyboards if sb.get("status") == status]

    console.print(f"[bold]Storyboards in {project_id}[/bold]\n")

    table = Table(show_header=True, header_style="bold")
    table.add_column("ID")
    table.add_column("Scene")
    table.add_column("Chapter")
    table.add_column("Panels")
    table.add_column("Status")
    table.add_column("Updated")

    for sb in storyboards:
        status_color = {
            "draft": "yellow",
            "approved": "green",
            "rejected": "red"
        }.get(sb.get("status", "draft"), "white")

        table.add_row(
            sb["storyboard_id"],
            sb.get("scene_id", "N/A") or "N/A",
            str(sb.get("chapter_number", "N/A")),
            str(sb.get("panel_count", 0)),
            f"[{status_color}]{sb.get('status', 'draft')}[/]",
            sb.get("updated_at", "")[:10]
        )

    console.print(table)


@app.command()
def view(
    project_id: str = typer.Argument(..., help="Project ID"),
    storyboard_id: str = typer.Argument(..., help="Storyboard ID"),
):
    """
    View a storyboard with all panels.

    Examples:
        g-manga storyboard view dorian-gray-20260210 sb-001
    """
    project_dir = find_project_dir(project_id)

    if not project_dir:
        console.print(f"[red]Error: Project '{project_id}' not found[/red]")
        raise typer.Exit(1)

    storage = StoryboardStorage(str(project_dir))
    storyboard = storage.load_storyboard(storyboard_id)

    if not storyboard:
        console.print(f"[red]Error: Storyboard '{storyboard_id}' not found[/red]")
        raise typer.Exit(1)

    console.print(f"\n[bold]Storyboard: {storyboard.storyboard_id}[/bold]")
    console.print(f"Project: {storyboard.project_id}")
    console.print(f"Status: {storyboard.status}")
    console.print(f"Panels: {len(storyboard.panels)}\n")

    for i, panel in enumerate(storyboard.panels):
        display_panel(panel, i)
        console.print()  # Spacer


@app.command()
def edit(
    project_id: str = typer.Argument(..., help="Project ID"),
    storyboard_id: str = typer.Argument(..., help="Storyboard ID"),
    panel_id: str = typer.Argument(..., help="Panel ID to edit"),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="New description"),
    camera: Optional[str] = typer.Option(None, "--camera", "-c", help="New camera angle"),
    mood: Optional[str] = typer.Option(None, "--mood", "-m", help="New mood"),
):
    """
    Edit a panel in a storyboard.

    Examples:
        g-manga storyboard edit dorian-gray-20260210 sb-001 p1 -d "New description"
        g-manga storyboard edit dorian-gray-20260210 sb-001 p1 --camera wide --mood tense
    """
    project_dir = find_project_dir(project_id)

    if not project_dir:
        console.print(f"[red]Error: Project '{project_id}' not found[/red]")
        raise typer.Exit(1)

    storage = StoryboardStorage(str(project_dir))

    # Build updates dict
    updates = {}
    if description:
        updates["description"] = description
    if camera:
        updates["camera"] = camera
    if mood:
        updates["mood"] = mood

    if not updates:
        console.print("[yellow]Error: No updates specified. Use --help for options.[/yellow]")
        raise typer.Exit(1)

    storyboard = storage.update_panel(storyboard_id, panel_id, updates)

    if not storyboard:
        console.print(f"[red]Error: Storyboard or panel not found[/red]")
        raise typer.Exit(1)

    console.print(f"[green]✓ Panel {panel_id} updated in storyboard {storyboard_id}[/green]")


@app.command()
def reorder(
    project_id: str = typer.Argument(..., help="Project ID"),
    storyboard_id: str = typer.Argument(..., help="Storyboard ID"),
    panel_ids: List[str] = typer.Argument(..., help="Panel IDs in new order"),
):
    """
    Reorder panels in a storyboard.

    Examples:
        g-manga storyboard reorder dorian-gray-20260210 sb-001 p2 p1 p3 p4
    """
    project_dir = find_project_dir(project_id)

    if not project_dir:
        console.print(f"[red]Error: Project '{project_id}' not found[/red]")
        raise typer.Exit(1)

    storage = StoryboardStorage(str(project_dir))
    storyboard = storage.reorder_panels(storyboard_id, panel_ids)

    if not storyboard:
        console.print(f"[red]Error: Storyboard not found[/red]")
        raise typer.Exit(1)

    console.print(f"[green]✓ Storyboard {storyboard_id} reordered[/green]")
    console.print(f"  New panel order: {', '.join(panel_ids)}")


@app.command()
def add(
    project_id: str = typer.Argument(..., help="Project ID"),
    storyboard_id: str = typer.Argument(..., help="Storyboard ID"),
    description: str = typer.Option(..., "--description", "-d", help="Panel description"),
    camera: str = typer.Option("medium", "--camera", "-c", help="Camera angle"),
    mood: str = typer.Option("neutral", "--mood", "-m", help="Mood"),
    after: Optional[str] = typer.Option(None, "--after", "-a", help="Insert after this panel ID"),
):
    """
    Add a new panel to a storyboard.

    Examples:
        g-manga storyboard add dorian-gray-20260210 sb-001 -d "New panel" -c wide -m tense
        g-manga storyboard add dorian-gray-20260210 sb-001 -d "New panel" --after p3
    """
    project_dir = find_project_dir(project_id)

    if not project_dir:
        console.print(f"[red]Error: Project '{project_id}' not found[/red]")
        raise typer.Exit(1)

    storage = StoryboardStorage(str(project_dir))

    # Load storyboard to get current panels
    storyboard = storage.load_storyboard(storyboard_id)

    if not storyboard:
        console.print(f"[red]Error: Storyboard '{storyboard_id}' not found[/red]")
        raise typer.Exit(1)

    # Create new panel
    new_panel = StoryboardPanel(
        panel_id=f"p{len(storyboard.panels) + 1}",
        page_number=1,
        panel_number=len(storyboard.panels) + 1,
        description=description,
        camera=camera,
        mood=mood,
        status="pending"
    )

    storyboard = storage.add_panel(storyboard_id, new_panel, insert_after=after)

    if not storyboard:
        console.print(f"[red]Error: Failed to add panel[/red]")
        raise typer.Exit(1)

    console.print(f"[green]✓ Panel added to storyboard {storyboard_id}[/green]")


@app.command()
def remove(
    project_id: str = typer.Argument(..., help="Project ID"),
    storyboard_id: str = typer.Argument(..., help="Storyboard ID"),
    panel_id: str = typer.Argument(..., help="Panel ID to remove"),
):
    """
    Remove a panel from a storyboard.

    Examples:
        g-manga storyboard remove dorian-gray-20260210 sb-001 p3
    """
    project_dir = find_project_dir(project_id)

    if not project_dir:
        console.print(f"[red]Error: Project '{project_id}' not found[/red]")
        raise typer.Exit(1)

    storage = StoryboardStorage(str(project_dir))
    storyboard = storage.remove_panel(storyboard_id, panel_id)

    if not storyboard:
        console.print(f"[red]Error: Storyboard or panel not found[/red]")
        raise typer.Exit(1)

    console.print(f"[green]✓ Panel {panel_id} removed from storyboard {storyboard_id}[/green]")


@app.command()
def approve(
    project_id: str = typer.Argument(..., help="Project ID"),
    storyboard_id: str = typer.Argument(..., help="Storyboard ID"),
    panel_id: Optional[str] = typer.Option(None, "--panel", "-p", help="Specific panel to approve (default: all)"),
):
    """
    Approve a storyboard or specific panel.

    Examples:
        g-manga storyboard approve dorian-gray-20260210 sb-001
        g-manga storyboard approve dorian-gray-20260210 sb-001 --panel p1
    """
    project_dir = find_project_dir(project_id)

    if not project_dir:
        console.print(f"[red]Error: Project '{project_id}' not found[/red]")
        raise typer.Exit(1)

    storage = StoryboardStorage(str(project_dir))
    storyboard = storage.load_storyboard(storyboard_id)

    if not storyboard:
        console.print(f"[red]Error: Storyboard '{storyboard_id}' not found[/red]")
        raise typer.Exit(1)

    if panel_id:
        # Approve specific panel
        storyboard = storage.update_panel(storyboard_id, panel_id, {"status": "approved"})
        console.print(f"[green]✓ Panel {panel_id} approved[/green]")
    else:
        # Approve entire storyboard
        storyboard.status = "approved"
        for panel in storyboard.panels:
            panel.status = "approved"
        storage.save_storyboard(storyboard)
        console.print(f"[green]✓ Storyboard {storyboard_id} approved[/green]")


@app.command()
def reject(
    project_id: str = typer.Argument(..., help="Project ID"),
    storyboard_id: str = typer.Argument(..., help="Storyboard ID"),
    panel_id: Optional[str] = typer.Option(None, "--panel", "-p", help="Specific panel to reject (default: all)"),
    reason: Optional[str] = typer.Option(None, "--reason", "-r", help="Rejection reason"),
):
    """
    Reject a storyboard or specific panel.

    Examples:
        g-manga storyboard reject dorian-gray-20260210 sb-001
        g-manga storyboard reject dorian-gray-20260210 sb-001 --panel p1 --reason "Wrong mood"
    """
    project_dir = find_project_dir(project_id)

    if not project_dir:
        console.print(f"[red]Error: Project '{project_id}' not found[/red]")
        raise typer.Exit(1)

    storage = StoryboardStorage(str(project_dir))
    storyboard = storage.load_storyboard(storyboard_id)

    if not storyboard:
        console.print(f"[red]Error: Storyboard '{storyboard_id}' not found[/red]")
        raise typer.Exit(1)

    if panel_id:
        # Reject specific panel
        updates = {"status": "rejected"}
        if reason:
            updates["description"] = f"[REJECTED: {reason}] {storyboard.panels[0].description}"
        storyboard = storage.update_panel(storyboard_id, panel_id, updates)
        console.print(f"[green]✓ Panel {panel_id} rejected[/green]")
    else:
        # Reject entire storyboard
        storyboard.status = "rejected"
        for panel in storyboard.panels:
            panel.status = "rejected"
        storage.save_storyboard(storyboard)
        console.print(f"[green]✓ Storyboard {storyboard_id} rejected[/green]")


@app.command()
def export(
    project_id: str = typer.Argument(..., help="Project ID"),
    storyboard_id: str = typer.Argument(..., help="Storyboard ID"),
    format: str = typer.Option("json", "--format", "-f", help="Export format (json, text)"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file"),
):
    """
    Export a storyboard to file.

    Examples:
        g-manga storyboard export dorian-gray-20260210 sb-001
        g-manga storyboard export dorian-gray-20260210 sb-001 --format text --output ./storyboard.txt
    """
    project_dir = find_project_dir(project_id)

    if not project_dir:
        console.print(f"[red]Error: Project '{project_id}' not found[/red]")
        raise typer.Exit(1)

    storage = StoryboardStorage(str(project_dir))
    storyboard = storage.load_storyboard(storyboard_id)

    if not storyboard:
        console.print(f"[red]Error: Storyboard '{storyboard_id}' not found[/red]")
        raise typer.Exit(1)

    if format == "json":
        # Export as JSON
        data = {
            "storyboard_id": storyboard.storyboard_id,
            "project_id": storyboard.project_id,
            "scene_id": storyboard.scene_id,
            "chapter_number": storyboard.chapter_number,
            "status": storyboard.status,
            "panels": [
                {
                    "panel_id": panel.panel_id,
                    "page_number": panel.page_number,
                    "panel_number": panel.panel_number,
                    "description": panel.description,
                    "camera": panel.camera,
                    "mood": panel.mood,
                    "lighting": panel.lighting,
                    "composition": panel.composition,
                    "action": panel.action,
                    "dialogue": panel.dialogue,
                    "status": panel.status
                }
                for panel in storyboard.panels
            ]
        }

        content = json.dumps(data, indent=2, ensure_ascii=False)
        output_path = output or Path(f"{storyboard_id}.json")

    elif format == "text":
        # Export as readable text
        lines = [
            f"Storyboard: {storyboard.storyboard_id}",
            f"Project: {storyboard.project_id}",
            f"Status: {storyboard.status}",
            f"Panels: {len(storyboard.panels)}",
            "",
            "=" * 50,
            "PANELS",
            "=" * 50,
            ""
        ]

        for panel in storyboard.panels:
            lines.extend([
                f"Panel {panel.panel_number}: {panel.panel_id}",
                f"  Description: {panel.description}",
                f"  Camera: {panel.camera} | Mood: {panel.mood}",
                f"  Lighting: {panel.lighting or 'N/A'} | Composition: {panel.composition or 'N/A'}",
                f"  Action: {panel.action or 'N/A'}",
                f"  Dialogue: {panel.dialogue or 'None'}",
                f"  Status: {panel.status}",
                ""
            ])

        content = "\n".join(lines)
        output_path = output or Path(f"{storyboard_id}.txt")

    else:
        console.print(f"[red]Error: Unknown format '{format}'[/red]")
        raise typer.Exit(1)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    console.print(f"[green]✓ Storyboard exported to {output_path}[/green]")


@app.command()
def interactive(
    project_id: str = typer.Argument(..., help="Project ID"),
    storyboard_id: str = typer.Argument(..., help="Storyboard ID"),
):
    """
    Interactive storyboard review session.

    Examples:
        g-manga storyboard interactive dorian-gray-20260210 sb-001
    """
    project_dir = find_project_dir(project_id)

    if not project_dir:
        console.print(f"[red]Error: Project '{project_id}' not found[/red]")
        raise typer.Exit(1)

    storage = StoryboardStorage(str(project_dir))
    storyboard = storage.load_storyboard(storyboard_id)

    if not storyboard:
        console.print(f"[red]Error: Storyboard '{storyboard_id}' not found[/red]")
        raise typer.Exit(1)

    console.print(f"\n[bold]Interactive Storyboard Review[/bold]")
    console.print(f"Storyboard: {storyboard.storyboard_id}")
    console.print(f"Panels: {len(storyboard.panels)}\n")

    while True:
        console.print("\n[bold]Options:[/bold]")
        console.print("  [1] View all panels")
        console.print("  [2] Edit a panel")
        console.print("  [3] Reorder panels")
        console.print("  [4] Add a panel")
        console.print("  [5] Remove a panel")
        console.print("  [6] Approve/Reject panel")
        console.print("  [7] Export storyboard")
        console.print("  [q] Quit")

        choice = Prompt.ask("Choose option", choices=["1", "2", "3", "4", "5", "6", "7", "q"])

        if choice == "1":
            # View all panels
            for i, panel in enumerate(storyboard.panels):
                display_panel(panel, i)
                console.print()

        elif choice == "2":
            # Edit a panel
            panel_id = Prompt.ask("Enter panel ID to edit", choices=[p.panel_id for p in storyboard.panels])
            new_desc = Prompt.ask("New description", default=storyboard.panels[0].description if panel_id == storyboard.panels[0].panel_id else "")
            new_camera = Prompt.ask("New camera", default="medium")
            new_mood = Prompt.ask("New mood", default="neutral")

            updates = {}
            if new_desc:
                updates["description"] = new_desc
            updates["camera"] = new_camera
            updates["mood"] = new_mood

            storyboard = storage.update_panel(storyboard_id, panel_id, updates)
            console.print("[green]✓ Panel updated[/green]")

        elif choice == "3":
            # Reorder panels
            console.print("Current order: " + ", ".join([p.panel_id for p in storyboard.panels]))
            new_order = Prompt.ask("Enter new order (comma-separated panel IDs)").split(",")
            new_order = [p.strip() for p in new_order]
            storyboard = storage.reorder_panels(storyboard_id, new_order)
            console.print("[green]✓ Order updated[/green]")

        elif choice == "4":
            # Add a panel
            new_desc = Prompt.ask("Panel description")
            new_camera = Prompt.ask("Camera", default="medium")
            new_mood = Prompt.ask("Mood", default="neutral")

            new_panel = StoryboardPanel(
                panel_id=f"p{len(storyboard.panels) + 1}",
                page_number=1,
                panel_number=len(storyboard.panels) + 1,
                description=new_desc,
                camera=new_camera,
                mood=new_mood,
                status="pending"
            )

            after = Prompt.ask("Insert after panel ID (or press Enter to append)", default="")
            storyboard = storage.add_panel(storyboard_id, new_panel, insert_after=after if after else None)
            console.print("[green]✓ Panel added[/green]")

        elif choice == "5":
            # Remove a panel
            panel_id = Prompt.ask("Enter panel ID to remove", choices=[p.panel_id for p in storyboard.panels])
            storyboard = storage.remove_panel(storyboard_id, panel_id)
            console.print("[green]✓ Panel removed[/green]")

        elif choice == "6":
            # Approve/Reject
            action = Prompt.ask("Approve or reject", choices=["approve", "reject"])
            panel_id = Prompt.ask("Panel ID (or press Enter for all)", default="")
            reason = Prompt.ask("Reason (optional)", default="")

            if panel_id:
                if action == "approve":
                    storyboard = storage.update_panel(storyboard_id, panel_id, {"status": "approved"})
                else:
                    updates = {"status": "rejected"}
                    if reason:
                        updates["description"] = f"[REJECTED: {reason}]"
                    storyboard = storage.update_panel(storyboard_id, panel_id, updates)
            else:
                if action == "approve":
                    storyboard.status = "approved"
                    for panel in storyboard.panels:
                        panel.status = "approved"
                else:
                    storyboard.status = "rejected"
                    for panel in storyboard.panels:
                        panel.status = "rejected"
                storage.save_storyboard(storyboard)

            console.print(f"[green]✓ Storyboard {action}d[/green]")

        elif choice == "7":
            # Export
            export_format = Prompt.ask("Export format", choices=["json", "text"], default="json")
            output_path = Prompt.ask("Output file", default=f"{storyboard_id}.{export_format}")
            export_storyboard(project_id, storyboard_id, export_format, Path(output_path))
            console.print(f"[green]✓ Exported to {output_path}[/green]")

        elif choice == "q":
            break

        # Reload storyboard
        storyboard = storage.load_storyboard(storyboard_id)

    console.print("\n[bold]Review session ended[/bold]")


def main():
    """Main entry point."""
    app()


if __name__ == "__main__":
    app()
