"""
Progress Logger
Tracks all completed subtasks with timestamps and status.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any


class ProgressLogger:
    """Logs progress of G-Manga pipeline development."""

    def __init__(self, log_file: str = "./PROGRESS_LOG.json"):
        """
        Initialize Progress Logger.

        Args:
            log_file: Path to progress log file
        """
        self.log_file = Path(log_file)
        self.log = self._load_log()

    def _load_log(self) -> Dict[str, Any]:
        """Load existing progress log."""
        if self.log_file.exists():
            with open(self.log_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "stages": {},
            "subtasks": [],
            "timestamps": {}
        }

    def _save_log(self) -> None:
        """Save progress log to file."""
        with open(self.log_file, 'w', encoding='utf-8') as f:
            json.dump(self.log, f, indent=2, ensure_ascii=False)

    def log_subtask(self, stage: str, subtask: str, status: str = "complete") -> None:
        """
        Log completion of a subtask.

        Args:
            stage: Stage number/name (e.g., "Stage 1", "Stage 2")
            subtask: Subtask name (e.g., "1.1.1 Implement URL Fetcher")
            status: Status (complete, in_progress, failed)
        """
        timestamp = datetime.now(timezone.utc).isoformat()

        # Check if already exists
        existing = [s for s in self.log["subtasks"] if s["stage"] == stage and s["subtask"] == subtask]

        if existing:
            # Update existing entry
            for entry in existing:
                entry["status"] = status
                entry["last_updated"] = timestamp
        else:
            # Add new entry
            self.log["subtasks"].append({
                "stage": stage,
                "subtask": subtask,
                "status": status,
                "created_at": timestamp,
                "last_updated": timestamp
            })

        self.log["timestamps"][f"{stage}_{subtask}"] = timestamp
        self._save_log()

        print(f"✓ Logged: [{stage}] {subtask} - {status}")

    def complete_subtask(self, stage: str, subtask: str) -> None:
        """Mark subtask as complete."""
        self.log_subtask(stage, subtask, "complete")

    def start_subtask(self, stage: str, subtask: str) -> None:
        """Mark subtask as in progress."""
        self.log_subtask(stage, subtask, "in_progress")

    def fail_subtask(self, stage: str, subtask: str, error: str = None) -> None:
        """Mark subtask as failed."""
        timestamp = datetime.now(timezone.utc).isoformat()

        existing = [s for s in self.log["subtasks"] if s["stage"] == stage and s["subtask"] == subtask]

        if existing:
            for entry in existing:
                entry["status"] = "failed"
                entry["error"] = error
                entry["last_updated"] = timestamp
        else:
            self.log["subtasks"].append({
                "stage": stage,
                "subtask": subtask,
                "status": "failed",
                "error": error,
                "created_at": timestamp,
                "last_updated": timestamp
            })

        self.log["timestamps"][f"{stage}_{subtask}"] = timestamp
        self._save_log()

        print(f"✗ Failed: [{stage}] {subtask} - {error}")

    def get_progress(self, stage: str = None) -> Dict[str, Any]:
        """
        Get progress of a stage or overall.

        Args:
            stage: Optional stage name to filter by

        Returns:
            Progress statistics
        """
        subtasks = self.log["subtasks"]

        if stage:
            # Filter by stage
            stage_subtasks = [s for s in subtasks if s["stage"] == stage]
            total = len(stage_subtasks)
            complete = len([s for s in stage_subtasks if s["status"] == "complete"])
            in_progress = len([s for s in stage_subtasks if s["status"] == "in_progress"])
            failed = len([s for s in stage_subtasks if s["status"] == "failed"])
            pending = total - complete - in_progress - failed

            return {
                "stage": stage,
                "total": total,
                "complete": complete,
                "in_progress": in_progress,
                "failed": failed,
                "pending": pending,
                "percentage": (complete / total * 100) if total > 0 else 0,
                "subtasks": stage_subtasks
            }
        else:
            # Overall progress
            stages = list(set([s["stage"] for s in subtasks]))

            stage_stats = []
            for s in stages:
                s_subtasks = [t for t in subtasks if t["stage"] == s]
                total = len(s_subtasks)
                complete = len([t for t in s_subtasks if t["status"] == "complete"])
                percentage = (complete / total * 100) if total > 0 else 0

                stage_stats.append({
                    "stage": s,
                    "total": total,
                    "complete": complete,
                    "percentage": percentage
                })

            total_subtasks = len(subtasks)
            total_complete = len([s for s in subtasks if s["status"] == "complete"])

            return {
                "total_subtasks": total_subtasks,
                "total_complete": total_complete,
                "overall_percentage": (total_complete / total_subtasks * 100) if total_subtasks > 0 else 0,
                "stages": stage_stats,
                "recent_activity": sorted([s["last_updated"] for s in subtasks], reverse=True)[:10]
            }

    def print_report(self) -> None:
        """Print formatted progress report."""
        progress = self.get_progress()

        print("=" * 70)
        print("G-Manga Development Progress")
        print("=" * 70)

        print(f"Overall Progress: {progress['overall_percentage']:.1f}%")
        print(f"  {progress['total_complete']}/{progress['total_subtasks']} subtasks complete")

        print("\nStage Breakdown:")
        print(f"{'Stage':<25} {'Complete':<6} {'Progress':<10}")
        print("-" * 70)

        for stage_stats in progress["stages"]:
            bar_width = 30
            filled = int(bar_width * stage_stats["percentage"] / 100)
            bar = "█" * filled + "░" * (bar_width - filled)

            print(f"{stage_stats['stage']:<25} {bar} {stage_stats['percentage']:>5}% ({stage_stats['complete']}/{stage_stats['total']})")

        print("\n" + "=" * 70)


def main():
    """Test Progress Logger."""
    logger = ProgressLogger()

    # Log Stage 1 completion (all 6 subtasks)
    print("Logging Stage 1 (Input)...")
    for subtask in ["1.1.1 Implement URL Fetcher", "1.1.2 Implement Text Parser", "1.1.3 Implement Metadata Extractor", "1.1.4 Create Project Schema", "1.1.5 Implement Project Initializer", "1.1.6 Integration Test: Input Stage"]:
        logger.complete_subtask("Stage 1", subtask)

    # Log Stage 2 completion (all 6 subtasks)
    print("\nLogging Stage 2 (Preprocessing)...")
    for subtask in ["2.1.1 Implement Text Cleaner", "2.1.2 Implement Chapter Segmenter", "2.1.3 Implement Scene Breakdown", "2.1.4 Create Scene Schema", "2.1.5 Implement State Persistence", "2.1.6 Integration Test: Preprocessing"]:
        logger.complete_subtask("Stage 2", subtask)

    # Log Stage 3 completion (all 7 subtasks)
    print("\nLogging Stage 3 (Story Planning)...")
    for subtask in ["3.1.1 Implement Visual Adaptation", "3.1.2 Implement Panel Breakdown", "3.1.3 Implement Storyboard Generator", "3.1.4 Create Storyboard Schema", "3.1.5 Implement Page Calculator", "3.1.6 Implement Storyboard Validator", "3.1.7 Integration Test: Story Planning"]:
        logger.complete_subtask("Stage 3", subtask)

    # Log Stage 4 partial (1/5 subtasks)
    print("\nLogging Stage 4 (Character Design) - Partial...")
    logger.complete_subtask("Stage 4", "4.1.1 Implement Character Extractor")

    # Print report
    logger.print_report()


if __name__ == "__main__":
    main()
