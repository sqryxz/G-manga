"""
Storyboard Validator - Stage 3.1.6
Validates storyboard completeness and quality.
"""

from typing import List, Dict, Any


class StoryboardValidator:
    """Validates storyboard panels."""

    def __init__(self):
        """Initialize Storyboard Validator."""
        self.required_fields = ["id", "page_number", "panel_number", "type", "description", "camera"]

        self.valid_types = ["establishing", "wide", "medium", "close-up", "extreme-close-up", "action", "dialogue", "splash"]

        self.valid_cameras = ["eye-level", "low-angle", "high-angle", "dutch-angle", "over-the-shoulder", "point-of-view"]

    def validate_panel(self, panel: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a single panel.

        Args:
            panel: Panel dictionary

        Returns:
            Validation result with 'valid' and 'errors' keys
        """
        errors = []

        # Check required fields
        for field in self.required_fields:
            if field not in panel or not panel[field]:
                errors.append(f"Missing required field: {field}")

        # Validate panel type
        if "type" in panel:
            if panel["type"] not in self.valid_types:
                errors.append(f"Invalid panel type: {panel['type']}")

        # Validate camera
        if "camera" in panel:
            if panel["camera"] not in self.valid_cameras:
                errors.append(f"Invalid camera angle: {panel['camera']}")

        # Validate description length
        if "description" in panel:
            desc = panel["description"]
            if not desc or len(desc) < 10:
                errors.append("Description too short (min 10 chars)")
            elif len(desc) > 2000:
                errors.append("Description too long (max 2000 chars)")

        # Validate panel number
        if "panel_number" in panel:
            if panel["panel_number"] <= 0:
                errors.append("Panel number must be positive")

        # Validate page number
        if "page_number" in panel:
            if panel["page_number"] <= 0:
                errors.append("Page number must be positive")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "panel_id": panel.get("id", "")
        }

    def validate_storyboard(self, panels: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate entire storyboard.

        Args:
            panels: List of panel dictionaries

        Returns:
            Validation report with summary and per-panel errors
        """
        total_panels = len(panels)
        valid_panels = []
        all_errors = []

        print(f"Validating {total_panels} panels...")

        for panel in panels:
            result = self.validate_panel(panel)
            if result["valid"]:
                valid_panels.append(panel)
            else:
                all_errors.extend([
                    f"Panel {panel.get('id', '?')}: {err}" for err in result["errors"]
                ])

        # Check panel numbering sequence
        panel_numbers = [p.get("panel_number", 0) for p in panels]
        if panel_numbers != sorted(panel_numbers):
            all_errors.append("Panel numbers not sequential")

        # Check page transitions
        page_numbers = [p.get("page_number", 0) for p in panels]
        pages = list(set(page_numbers))
        if sorted(pages) != list(range(min(pages), max(pages) + 1)):
            all_errors.append("Page numbers not sequential")

        report = {
            "total_panels": total_panels,
            "valid_panels": len(valid_panels),
            "invalid_panels": total_panels - len(valid_panels),
            "valid_percentage": (len(valid_panels) / total_panels * 100) if total_panels > 0 else 0,
            "all_errors": all_errors,
            "summary": self._generate_summary(valid_panels, all_errors)
        }

        return report

    def _generate_summary(self, valid_panels: List[Dict[str, Any]], errors: List[str]) -> str:
        """
        Generate validation summary.

        Args:
            valid_panels: List of valid panels
            errors: List of error messages

        Returns:
            Summary string
        """
        valid_count = len(valid_panels)
        error_count = len(errors)

        if error_count == 0:
            return "All {} panels are valid".format(valid_count)

        summary_lines = ["Valid panels: {}".format(valid_count), "Errors found: {}".format(error_count)]

        # Show first 10 errors
        for i, error in enumerate(errors[:10]):
            summary_lines.append(" {}. {}".format(i+1, error))

        if error_count > 10:
            summary_lines.append(" ... and {} more errors".format(error_count - 10))

        return "\n".join(summary_lines)


def main():
    """Test Storyboard Validator."""
    import sys
    sys.path.insert(0, '/home/clawd/projects/g-manga/src/stage3_story_planning')

    # Create test panels (some valid, some invalid)
    test_panels = [
        {
            "id": "p1-1",
            "page_number": 1,
            "panel_number": 1,
            "type": "establishing",
            "description": "Wide establishing shot of the art studio",
            "camera": "wide",
            "mood": "peaceful"
        },
        {
            "id": "p1-2",
            "page_number": 1,
            "panel_number": 2,
            "type": "medium",
            "description": "Too short"
        },
        {
            "id": "p1-3",
            "page_number": 1,
            "panel_number": 3,
            "type": "dialogue",
            "description": "Medium shot showing conversation between characters",
            "camera": "eye-level",
            "dialogue": [{"speaker": "Basil", "text": "Hello"}]
        },
        {
            "id": "p1-4",
            "page_number": 1,
            "panel_number": 4,
            "type": "close-up",
            "camera": "dutch-angle",
            "description": "Close-up of Basil's face"
        }
    ]

    validator = StoryboardValidator()
    report = validator.validate_storyboard(test_panels)

    print("=" * 60)
    print("Storyboard Validation Report")
    print("=" * 60)

    print("Total Panels: {}".format(report["total_panels"]))
    print("Valid Panels: {}".format(report["valid_panels"]))
    print("Invalid Panels: {}".format(report["invalid_panels"]))
    print("Valid Percentage: {:.1f}%".format(report["valid_percentage"]))
    print()

    print("Summary:")
    print(report["summary"])

    if report["invalid_panels"] > 0:
        print("\nValidation FAILED")
        sys.exit(1)
    else:
        print("\nValidation PASSED")


if __name__ == "__main__":
    main()
