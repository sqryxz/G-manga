"""
Integration Test: Stage 3 - Story Planning (Modules Only)
Tests Story Planning modules independently with fixed mock classes.
"""

import sys
import json
sys.path.insert(0, '/home/clawd/projects/g-manga/src')
sys.path.insert(0, '/home/clawd/projects/g-manga/src/stage1_input')
sys.path.insert(0, '/home/clawd/projects/g-manga/src/stage2_preprocessing')
sys.path.insert(0, '/home/clawd/projects/g-manga/src/stage3_story_planning')

from visual_adaptation import VisualAdaptation
from panel_breakdown import PanelBreakdown
from storyboard_generator import StoryboardGenerator
from page_calculator import PageCalculator
from storyboard_validator import StoryboardValidator
from models.project import (
    Scene, Chapter, TextRange, VisualBeat, Panel,
    PanelDescription, Page, Storyboard
)


class MockLLMClient:
    """Mock LLM client for testing."""

    def call(self, prompt: str) -> str:
        return json.dumps({
            "visual_beats": [
                {"number": 1, "description": "Basil stands at easel", "show_vs_tell": "show", "priority": 2},
                {"number": 2, "description": "Lord Henry enters", "show_vs_tell": "show", "priority": 2},
                {"number": 3, "description": "They discuss art", "show_vs_tell": "tell", "priority": 3}
            ]
        })


def test_visual_adaptation():
    print("Test 1: Visual Adaptation")
    adaptation = VisualAdaptation(llm_client=MockLLMClient())

    scene_text = "The studio was filled with roses."
    scene_id = "scene-test"
    scene_number = 1
    scene_summary = "Test scene"

    visual_beats = adaptation.adapt_scene(scene_text, scene_id, scene_number)

    assert len(visual_beats) == 3, f"Expected 3 beats, got {len(visual_beats)}"
    print("  PASS")


def test_panel_breakdown():
    print("Test 2: Panel Breakdown")
    panel_breakdown = PanelBreakdown(llm_client=MockLLMClient())

    visual_beats = [
        {"number": 1, "description": "Basil stands", "show_vs_tell": "show", "priority": 2},
        {"number": 2, "description": "Lord enters", "show_vs_tell": "show", "priority": 2},
        {"number": 3, "description": "They talk", "show_vs_tell": "tell", "priority": 3}
    ]
    scene_summary = "Test scene"
    scene_id = "scene-test"
    scene_number = 1

    result = panel_breakdown.breakdown_scene(visual_beats, scene_summary, scene_id, scene_number)

    assert result.panel_count == 3, f"Expected 3 panels, got {result.panel_count}"
    assert result.pacing == "normal", f"Expected normal pacing, got {result.pacing}"
    print("  PASS")


def test_storyboard_generator():
    print("Test 3: Storyboard Generator")
    generator = StoryboardGenerator(llm_client=MockLLMClient())

    scene_text = "The studio was filled with roses."
    scene_id = "scene-test"
    scene_number = 1
    scene_summary = "Test scene"

    panel_plan = {
        "panel_count": 3,
        "pacing": "normal",
        "panels": [
            {"number": 1, "type": "establishing", "camera": "wide"},
            {"number": 2, "type": "medium", "camera": "eye-level"},
            {"number": 3, "type": "dialogue", "camera": "eye-level"}
        ]
    }

    panels = generator.generate_storyboard(
        scene_text, scene_id, scene_number,
        [{"number": 1, "description": "Basil stands"}, {"number": 2, "description": "Lord enters"}, {"number": 3, "description": "They talk"}],
        scene_number, panel_plan
    )

    assert len(panels) == 3, f"Expected 3 panels, got {len(panels)}"
    print("  PASS")


def test_page_calculator():
    print("Test 4: Page Calculator")
    calculator = PageCalculator()

    panel_data = [
        {"number": 1, "type": "establishing", "camera": "wide"},
        {"number": 2, "type": "medium", "camera": "eye-level"},
        {"number": 3, "type": "dialogue", "camera": "eye-level"}
    ]

    pages = calculator.calculate_pages(panel_data)

    assert len(pages) == 1, f"Expected 1 page, got {len(pages)}"
    assert pages[0]["panel_count"] == 3, f"Expected 3 panels, got {pages[0]['panel_count']}"
    print("  PASS")


def test_storyboard_validator():
    print("Test 5: Storyboard Validator")
    validator = StoryboardValidator()

    test_panels = [
        {
            "id": "p1-1",
            "page_number": 1,
            "panel_number": 1,
            "type": "establishing",
            "camera": "wide",
            "description": "Wide establishing shot of art studio.",
            "mood": "peaceful",
            "dialogue": [],
            "narration": "",
            "characters": ["Basil"],
            "props": ["easel"]
        },
        {
            "id": "p1-2",
            "page_number": 1,
            "panel_number": 2,
            "type": "medium",
            "camera": "eye-level",
            "description": "Basil stands at easel.",
            "mood": "contemplative",
            "dialogue": [],
            "narration": "",
            "characters": ["Basil"],
            "props": []
        },
        {
            "id": "p1-3",
            "page_number": 1,
            "panel_number": 3,
            "type": "dialogue",
            "camera": "eye-level",
            "description": "They discuss art.",
            "mood": "neutral",
            "dialogue": [],
            "narration": "",
            "characters": ["Basil", "Lord Henry"],
            "props": []
        }
    ]

    report = validator.validate_storyboard(test_panels)

    assert report["valid_percentage"] == 100, f"Expected 100% valid, got {report['valid_percentage']}%"
    print("  PASS")


def test_all():
    print("=" * 70)
    print("Stage 3: Story Planning - Module Tests")
    print("=" * 70)
    print()

    all_tests_passed = True

    try:
        test_visual_adaptation()
        test_panel_breakdown()
        test_storyboard_generator()
        test_page_calculator()
        test_storyboard_validator()
    except AssertionError as e:
        print(f"\nTest FAILED: {e}")
        all_tests_passed = False
    except Exception as e:
        print(f"\nTest ERROR: {e}")
        import traceback
        traceback.print_exc()
        all_tests_passed = False

    print()
    print("=" * 70)
    print("Summary")
    print("=" * 70)
    print(f"All tests passed: {all_tests_passed}")

    if all_tests_passed:
        print("All modules are working correctly!")
        print("Stage 3 is ready for integration with Stage 2 (preprocessing)")
        return 0
    else:
        print("Some modules need fixes before integration")
        return 1


if __name__ == "__main__":
    sys.exit(test_all())
