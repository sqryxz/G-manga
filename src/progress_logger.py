"""
Progress Logger
Tracks all completed subtasks with timestamps and status.
Supports both manual and automatic logging.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass
from functools import wraps


@dataclass
class ProgressLog:
    """Progress log entry."""
    id: str
    stage: str
    subtask: str
    status: str  # complete, in_progress, failed
    created_at: str
    last_updated: str
    error: Optional[str] = None


class ProgressLogger:
    """Logs progress of G-Manga pipeline development.

    Supports both manual logging and automatic decorator-based logging.
    """

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

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        return datetime.now(timezone.utc).isoformat()

    def log_subtask(self, stage: str, subtask: str, status: str = "complete") -> None:
        """
        Log completion of a subtask.

        Args:
            stage: Stage number/name (e.g., "Stage 1", "Stage 2")
            subtask: Subtask name (e.g., "1.1.1 Implement URL Fetcher")
            status: Status (complete, in_progress, failed)
        """
        timestamp = self._get_timestamp()

        # Check if already exists
        subtask_key = f"{stage}_{subtask}"
        existing = [s for s in self.log["subtasks"] if s.get("id") == subtask_key]

        if existing:
            # Update existing entry
            for entry in existing:
                entry["status"] = status
                entry["last_updated"] = timestamp
        else:
            # Add new entry
            self.log["subtasks"].append({
                "id": subtask_key,
                "stage": stage,
                "subtask": subtask,
                "status": status,
                "created_at": timestamp,
                "last_updated": timestamp
            })

        self.log["timestamps"][subtask_key] = timestamp
        self._save_log()

        print(f"✓ Logged: [{stage}] {subtask} - {status}")

    def start_subtask(self, stage: str, subtask: str) -> None:
        """
        Mark subtask as in progress.

        Args:
            stage: Stage number/name
            subtask: Subtask name
        """
        timestamp = self._get_timestamp()

        # Check if already exists
        subtask_key = f"{stage}_{subtask}"
        existing = [s for s in self.log["subtasks"] if s.get("id") == subtask_key]

        if existing:
            # Update existing entry
            for entry in existing:
                entry["status"] = "in_progress"
                entry["last_updated"] = timestamp
        else:
            # Add new entry
            self.log["subtasks"].append({
                "id": subtask_key,
                "stage": stage,
                "subtask": subtask,
                "status": "in_progress",
                "created_at": timestamp,
                "last_updated": timestamp
            })

        self.log["timestamps"][subtask_key] = timestamp
        self._save_log()

        print(f"🔄 Started: [{stage}] {subtask}")

    def fail_subtask(self, stage: str, subtask: str, error: str) -> None:
        """
        Mark subtask as failed.

        Args:
            stage: Stage number/name
            subtask: Subtask name
            error: Error message
        """
        timestamp = self._get_timestamp()

        # Check if already exists
        subtask_key = f"{stage}_{subtask}"
        existing = [s for s in self.log["subtasks"] if s.get("id") == subtask_key]

        if existing:
            # Update existing entry
            for entry in existing:
                entry["status"] = "failed"
                entry["error"] = error
                entry["last_updated"] = timestamp
        else:
            # Add new entry
            self.log["subtasks"].append({
                "id": subtask_key,
                "stage": stage,
                "subtask": subtask,
                "status": "failed",
                "created_at": timestamp,
                "last_updated": timestamp,
                "error": error
            })

        self.log["timestamps"][subtask_key] = timestamp
        self._save_log()

        print(f"✗ Failed: [{stage}] {subtask} - {error}")

    def get_progress(self, stage: Optional[str] = None) -> Dict[str, Any]:
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

            print(f"{stage_stats['stage']:<25} {bar} {stage_stats['percentage']:>5.1f}% ({stage_stats['complete']}/{stage_stats['total']})")

        print("=" * 70)


def main():
    """Test Progress Logger with automatic logging."""
    print("=" * 70)
    print("Testing Automatic Logging System")
    print("=" * 70)

    logger = ProgressLogger()

    # Simulate completing Stage 1.1.1
    print("\n[Test] Logging Stage 1.1.1 completion...")
    logger.log_subtask("Stage 1", "1.1.1 Implement URL Fetcher")
    
    # Simulate starting Stage 1.1.2
    print("\n[Test] Logging Stage 1.1.2 start...")
    logger.start_subtask("Stage 1", "1.1.2 Implement Text Parser")
    
    # Print report
    print("\n[Test] Progress report:")
    logger.print_report()

    print("\n[Test] Logging decorator example:")
    print("\nTo use automatic logging in modules, import the decorator:")
    print("from progress_logger import ProgressLogger")
    print("\nThen decorate your function:")
    print("@ProgressLogger.log_completion('Stage 1', '1.1.1 Implement URL Fetcher')")
    print("\nExample:")
    print("class URLFetcher:")
    print("    def __init__(self, cache_dir: str = None):")
    print("        from src.common.log_completion import ProgressLogger")
    print("        self.logger = ProgressLogger()")
    print("        \n    def fetch(self, url: str):")
    print("        # ... fetch logic ...")
    print("        # When complete, return content")
    print("\n    @ProgressLogger.log_completion('Stage 1', '1.1.1 Implement URL Fetcher')")
    print("        return self")
    print("\n  fetch = log_completion('Stage 1', '1.1.1 Implement URL Fetcher')(fetch)")


if __name__ == "__main__":
    main()
