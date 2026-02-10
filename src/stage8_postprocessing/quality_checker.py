"""
Quality Checker - Stage 8.1.3
Generates review checklists for manga pages.
"""

import sys
sys.path.insert(0, '/home/clawd/projects/g-manga/src')

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import json
from datetime import datetime, timezone

from stage8_postprocessing.speech_bubble import SpeechBubbleRenderer, BubblePosition
from stage8_postprocessing.sfx_generator import SFXGenerator, SFXPosition


class CheckSeverity(Enum):
    """Severity levels for quality issues."""
    CRITICAL = "critical"  # Must fix before output
    WARNING = "warning"  # Should fix if possible
    INFO = "info"  # Informational


@dataclass
class QualityCheck:
    """Single quality check."""
    check_id: str
    category: str  # "panels", "bubbles", "sfx", "text", "layout"
    severity: CheckSeverity
    message: str
    panel_id: Optional[str] = None
    suggestion: Optional[str] = None
    auto_fixable: bool = False


class QualityChecker:
    """Generates review checklists for manga pages."""

    def __init__(
        self,
        bubble_renderer: Optional[SpeechBubbleRenderer] = None,
        sfx_generator: Optional[SFXGenerator] = None
    ):
        """
        Initialize Quality Checker.

        Args:
            bubble_renderer: Speech bubble renderer (optional)
            sfx_generator: SFX generator (optional)
        """
        self.bubble_renderer = bubble_renderer
        self.sfx_generator = sfx_generator

    def check_page_quality(
        self,
        page_data: Dict[str, Any]
    ) -> List[QualityCheck]:
        """
        Check quality of a manga page.

        Args:
            page_data: Page data with panels, bubbles, SFX

        Returns:
            List of QualityCheck objects
        """
        checks = []

        # 1. Check panel coverage
        checks.extend(self._check_panel_coverage(page_data))

        # 2. Check speech bubble placement
        if self.bubble_renderer and page_data.get("bubbles"):
            checks.extend(self._check_bubble_placement(page_data))

        # 3. Check SFX placement
        if self.sfx_generator and page_data.get("sfx"):
            checks.extend(self._check_sfx_placement(page_data))

        # 4. Check reading order
        checks.extend(self._check_reading_order(page_data))

        # 5. Check text readability
        checks.extend(self._check_text_readability(page_data))

        # 6. Check consistency
        checks.extend(self._check_consistency(page_data))

        return checks

    def _check_panel_coverage(
        self,
        page_data: Dict[str, Any]
    ) -> List[QualityCheck]:
        """
        Check panel coverage and overlap.

        Args:
            page_data: Page data

        Returns:
            List of QualityCheck objects
        """
        checks = []
        panels = page_data.get("panels", [])

        if not panels:
            checks.append(QualityCheck(
                check_id="panel-001",
                category="panels",
                severity=CheckSeverity.CRITICAL,
                message="No panels found on page"
            ))
            return checks

        # Check for panel count
        if len(panels) < 2:
            checks.append(QualityCheck(
                check_id="panel-002",
                category="panels",
                severity=CheckSeverity.WARNING,
                message="Low panel count (" + str(len(panels)) + "), consider adding more panels"
            ))
        elif len(panels) > 8:
            checks.append(QualityCheck(
                check_id="panel-003",
                category="panels",
                severity=CheckSeverity.WARNING,
                message="High panel count (" + str(len(panels)) + "), may appear crowded"
            ))

        # Check for panel overlap (simplified)
        panel_positions = {}
        for panel in panels:
            panel_id = panel.get("panel_id")
            pos = panel.get("position")
            if pos:
                px, py, pw, ph = pos.get("x"), pos.get("y"), pos.get("width"), pos.get("height")

                # Check for overlap with existing panels
                for existing_id, existing_pos in panel_positions.items():
                    ex, ey, ew, eh = existing_pos.get("x"), existing_pos.get("y"), existing_pos.get("width"), existing_pos.get("height")

                    # Check overlap
                    overlap = not (
                        px >= ex + ew or
                        px + pw <= ex or
                        py >= ey + eh or
                        py + ph <= ey
                    )

                    if overlap:
                        checks.append(QualityCheck(
                            check_id="panel-overlap-" + panel_id + "-" + existing_id,
                            category="panels",
                            severity=CheckSeverity.WARNING,
                            message="Panels " + panel_id + " and " + existing_id + " may overlap",
                            panel_id=panel_id,
                            suggestion="Consider adjusting panel sizes or layout"
                        ))

                panel_positions[panel_id] = pos

        return checks

    def _check_bubble_placement(
        self,
        page_data: Dict[str, Any]
    ) -> List[QualityCheck]:
        """
        Check speech bubble placement and readability.

        Args:
            page_data: Page data

        Returns:
            List of QualityCheck objects
        """
        checks = []
        bubbles = page_data.get("bubbles", [])
        panels = page_data.get("panels", [])

        if not bubbles:
            return checks

        # Check for bubble-panel collisions
        for bubble in bubbles:
            bubble_pos = bubble.get("position")
            if not bubble_pos:
                continue

            bx, by = bubble_pos.get("x"), bubble_pos.get("y")
            bw, bh = bubble_pos.get("width"), bubble_pos.get("height")

            # Check if bubble overlaps with any panel
            for panel in panels:
                panel_pos = panel.get("position")
                if not panel_pos:
                    continue

                px, py = panel_pos.get("x"), panel_pos.get("y")
                pw, ph = panel_pos.get("width"), panel_pos.get("height")

                # Check overlap
                collision = not (
                    bx >= px + pw or
                    bx + bw <= px or
                    by >= py + ph or
                    by + bh <= py
                )

                if collision:
                    checks.append(QualityCheck(
                        check_id="bubble-collision-" + bubble.get("panel_id") + "-" + panel.get("panel_id"),
                        category="bubbles",
                        severity=CheckSeverity.WARNING,
                        message="Speech bubble for " + bubble.get("panel_id") + " overlaps with panel " + panel.get("panel_id"),
                        panel_id=bubble.get("panel_id"),
                        suggestion="Reposition bubble away from panel faces"
                    ))
                    break  # Only report first collision per bubble

        return checks

    def _check_sfx_placement(
        self,
        page_data: Dict[str, Any]
    ) -> List[QualityCheck]:
        """
        Check SFX placement and clarity.

        Args:
            page_data: Page data

        Returns:
            List of QualityCheck objects
        """
        checks = []
        sfx_list = page_data.get("sfx", [])

        if not sfx_list:
            return checks

        # Check for SFX-panel overlaps
        for sfx in sfx_list:
            sfx_pos = sfx.get("position")
            if not sfx_pos:
                continue

            sx, sy = sfx_pos.get("x"), sfx_pos.get("y")
            sw, sh = sfx_pos.get("width", 50), sfx_pos.get("height", 50)

            # Check if SFX is too close to text bubbles
            bubbles = page_data.get("bubbles", [])
            for bubble in bubbles:
                bubble_pos = bubble.get("position")
                if not bubble_pos:
                    continue

                bx, by = bubble_pos.get("x"), bubble_pos.get("y")
                bw, bh = bubble_pos.get("width"), bubble_pos.get("height")

                # Check proximity (within 50px)
                if abs(sx - bx) < 50 and abs(sy - by) < 50:
                    checks.append(QualityCheck(
                        check_id="sfx-proximity-" + sfx.get("sfx_id"),
                        category="sfx",
                        severity=CheckSeverity.INFO,
                        message="SFX " + sfx.get("sfx_id") + " is close to bubble",
                        suggestion="Ensure SFX does not obscure text"
                    ))
                    break

        return checks

    def _check_reading_order(
        self,
        page_data: Dict[str, Any]
    ) -> List[QualityCheck]:
        """
        Check reading order and flow.

        Args:
            page_data: Page data

        Returns:
            List of QualityCheck objects
        """
        checks = []
        reading_order = page_data.get("reading_order", [])
        panels = page_data.get("panels", [])

        if not reading_order or not panels:
            return checks

        # Check if reading order matches panel numbers
        if len(reading_order) != len(panels):
            checks.append(QualityCheck(
                check_id="reading-order-001",
                category="layout",
                severity=CheckSeverity.CRITICAL,
                message="Reading order count (" + str(len(reading_order)) + ") does not match panel count (" + str(len(panels)) + ")",
                auto_fixable=True
            ))

        # Check for logical flow (simplified)
        for i in range(len(reading_order) - 1):
            current = reading_order[i]
            next_id = reading_order[i + 1]

            # Find panel positions
            current_panel = None
            next_panel = None
            for p in panels:
                if p.get("panel_id") == current:
                    current_panel = p
                elif p.get("panel_id") == next_id:
                    next_panel = p

            if not current_panel or not next_panel:
                continue

            cp = current_panel.get("position", {})
            np = next_panel.get("position", {})

            if cp and np:
                # Check if next panel is to the right or below
                is_right = np.get("x") > cp.get("x")
                is_below = np.get("y") > cp.get("y")

                if not (is_right or is_below):
                    checks.append(QualityCheck(
                        check_id="reading-order-" + str(i) + "-" + str(i+1),
                        category="layout",
                        severity=CheckSeverity.WARNING,
                        message="Reading order may not follow natural reading flow",
                        suggestion="Consider using a standard manga reading order (left-to-right, top-to-bottom)"
                    ))

        return checks

    def _check_text_readability(
        self,
        page_data: Dict[str, Any]
    ) -> List[QualityCheck]:
        """
        Check text readability and legibility.

        Args:
            page_data: Page data

        Returns:
            List of QualityCheck objects
        """
        checks = []
        bubbles = page_data.get("bubbles", [])

        for bubble in bubbles:
            text = bubble.get("text", "")

            if not text:
                checks.append(QualityCheck(
                    check_id="text-empty-" + bubble.get("bubble_id"),
                    category="text",
                    severity=CheckSeverity.WARNING,
                    message="Speech bubble has no text"
                ))
                continue

            # Check text length
            if len(text) > 200:
                checks.append(QualityCheck(
                    check_id="text-length-" + bubble.get("bubble_id"),
                    category="text",
                    severity=CheckSeverity.WARNING,
                    message="Speech bubble text is very long (" + str(len(text)) + " characters)",
                    panel_id=bubble.get("panel_id"),
                    suggestion="Consider splitting into multiple bubbles"
                ))

            # Check for readability issues
            if len(text.split()) < 2:
                checks.append(QualityCheck(
                    check_id="text-short-" + bubble.get("bubble_id"),
                    category="text",
                    severity=CheckSeverity.INFO,
                    message="Speech bubble has only one word: " + text,
                    panel_id=bubble.get("panel_id"),
                    suggestion="Consider adding more dialogue or combining with nearby panel"
                ))

        return checks

    def _check_consistency(
        self,
        page_data: Dict[str, Any]
    ) -> List[QualityCheck]:
        """
        Check visual consistency across panels.

        Args:
            page_data: Page data

        Returns:
            List of QualityCheck objects
        """
        checks = []
        panels = page_data.get("panels", [])

        if not panels:
            return checks

        # Check panel type variety
        panel_types = [p.get("type", "medium") for p in panels]
        unique_types = set(panel_types)

        if len(unique_types) < 2:
            checks.append(QualityCheck(
                check_id="consistency-001",
                category="panels",
                severity=CheckSeverity.INFO,
                message="Low panel type variety (only " + str(unique_types) + ")",
                suggestion="Consider using a mix of panel types for visual interest"
            ))
        elif len(unique_types) > 5:
            checks.append(QualityCheck(
                check_id="consistency-002",
                category="panels",
                severity=CheckSeverity.WARNING,
                message="High panel type variety (" + str(len(unique_types)) + "), may lack visual consistency",
                suggestion="Consider standardizing panel types more"
            ))

        # Check for missing establishing panels
        has_establishing = any(t == "establishing" for t in panel_types)
        if not has_establishing and len(panels) >= 3:
            checks.append(QualityCheck(
                check_id="consistency-003",
                category="panels",
                severity=CheckSeverity.INFO,
                message="No establishing panel found in first few panels",
                suggestion="Consider starting with a wide or establishing shot"
            ))

        return checks

    def generate_review_notes(
        self,
        page_checks: List[QualityCheck]
    ) -> str:
        """
        Generate human-readable review notes.

        Args:
            page_checks: List of QualityCheck objects

        Returns:
            Markdown-formatted review notes
        """
        if not page_checks:
            return "No quality issues found."

        # Group checks by severity
        critical = [c for c in page_checks if c.severity == CheckSeverity.CRITICAL]
        warnings = [c for c in page_checks if c.severity == CheckSeverity.WARNING]
        info = [c for c in page_checks if c.severity == CheckSeverity.INFO]

        # Build review notes
        notes = "# Quality Review\n\n"

        if critical:
            notes += "## Critical Issues\n\n"
            for check in critical:
                notes += "- **" + check.category.upper() + ":** " + check.message + "\n"
                if check.suggestion:
                    notes += "  " + u"💡 " + check.suggestion + "\n"
                if check.panel_id:
                    notes += "  " + u"📍 " + "Panel: " + check.panel_id + "\n"
            notes += "\n"

        if warnings:
            notes += "## Warnings\n\n"
            for check in warnings:
                notes += "- **" + check.category.upper() + ":** " + check.message + "\n"
                if check.suggestion:
                    notes += "  " + u"💡 " + check.suggestion + "\n"
                if check.panel_id:
                    notes += "  " + u"📍 " + "Panel: " + check.panel_id + "\n"
            notes += "\n"

        if info:
            notes += "## Information\n\n"
            for check in info:
                notes += "- **" + check.category.upper() + ":** " + check.message + "\n"
                if check.suggestion:
                    notes += "  " + u"💡 " + check.suggestion + "\n"
            notes += "\n"

        # Add summary
        notes += "---\n\n"
        notes += "**Total Issues:** " + str(len(page_checks)) + "\n"
        notes += "  - Critical: " + str(len(critical)) + "\n"
        notes += "  - Warnings: " + str(len(warnings)) + "\n"
        notes += "  - Info: " + str(len(info)) + "\n"

        # Auto-fixable count
        auto_fixable = sum(1 for c in page_checks if c.auto_fixable)
        if auto_fixable > 0:
            notes += "\n**Auto-fixable:** " + str(auto_fixable) + "\n"

        return notes

    def export_review_notes(
        self,
        page_checks: List[QualityCheck],
        output_file: str
    ):
        """
        Export review notes to file.

        Args:
            page_checks: List of QualityCheck objects
            output_file: Output file path
        """
        notes = self.generate_review_notes(page_checks)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(notes)

        print("✓ Exported review notes to " + output_file)

    def get_quality_score(
        self,
        page_checks: List[QualityCheck]
    ) -> float:
        """
        Calculate overall quality score.

        Args:
            page_checks: List of QualityCheck objects

        Returns:
            Quality score (0.0 to 1.0)
        """
        if not page_checks:
            return 1.0

        # Calculate score based on severity
        score = 1.0
        for check in page_checks:
            if check.severity == CheckSeverity.CRITICAL:
                score -= 0.3
            elif check.severity == CheckSeverity.WARNING:
                score -= 0.1
            elif check.severity == CheckSeverity.INFO:
                score -= 0.02

        return max(0.0, min(1.0, score))


def create_quality_checker(
    bubble_renderer: Optional[SpeechBubbleRenderer] = None,
    sfx_generator: Optional[SFXGenerator] = None
) -> QualityChecker:
    """
    Create a quality checker instance.

    Args:
        bubble_renderer: Speech bubble renderer (optional)
        sfx_generator: SFX generator (optional)

    Returns:
        QualityChecker instance
    """
    return QualityChecker(
        bubble_renderer=bubble_renderer,
        sfx_generator=sfx_generator
    )


def main():
    """Test Quality Checker."""
    print("=" * 70)
    print("Quality Checker Test")
    print("=" * 70)

    # Create checker
    print("\n[Test] Creating quality checker...")
    checker = create_quality_checker()
    print("✓ Quality checker created")

    # Test with mock page data
    print("\n[Test] Checking page quality...")

    mock_page_data = {
        "panels": [
            {"panel_id": "p1-1", "type": "wide", "position": {"x": 100, "y": 100, "width": 1142, "height": 1635}},
            {"panel_id": "p1-2", "type": "close-up", "position": {"x": 1276, "y": 76, "width": 1142, "height": 1635}},
            {"panel_id": "p1-3", "type": "medium", "position": {"x": 61, "y": 1795, "width": 1142, "height": 1635}},
            {"panel_id": "p1-4", "type": "close-up", "position": {"x": 1276, "y": 1795, "width": 1142, "height": 1635}},
        ],
        "bubbles": [
            {"bubble_id": "b1", "panel_id": "p1-1", "text": "Hello, world!", "position": {"x": 1000, "y": 800, "width": 200, "height": 100}},
            {"bubble_id": "b2", "panel_id": "p1-2", "text": "A", "position": {"x": 1400, "y": 800, "width": 100, "height": 80}},
        ],
        "sfx": [
            {"sfx_id": "sfx1", "text": "BOOM!", "type": "impact", "position": {"x": 1240, "y": 1754}},
            {"sfx_id": "sfx2", "text": "WHOOSH", "type": "speed", "position": {"x": 2280, "y": 3358}},
        ],
        "reading_order": ["p1-1", "p1-2", "p1-3", "p1-4"]
    }

    checks = checker.check_page_quality(mock_page_data)
    print("✓ Found " + str(len(checks)) + " quality issues")

    # Display checks
    print("\n  Quality issues:")
    for check in checks[:10]:  # Show first 10
        print("    [" + check.severity.value.upper() + "] " + check.category + ": " + check.message)
        if check.suggestion:
            print("      💡 " + check.suggestion)

    # Test review notes generation
    print("\n[Test] Generating review notes...")
    notes = checker.generate_review_notes(checks)
    print("✓ Generated " + str(len(notes)) + " characters of review notes")

    # Test quality score
    print("\n[Test] Calculating quality score...")
    score = checker.get_quality_score(checks)
    print("✓ Quality score: " + str(score))

    # Test export
    print("\n[Test] Exporting review notes...")
    checker.export_review_notes(checks, "review_notes_test.md")
    print("✓ Exported to review_notes_test.md")

    print("\n" + "=" * 70)
    print("Quality Checker - PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()
