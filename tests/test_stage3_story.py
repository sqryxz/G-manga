"""
Integration Test: Stage 3 - Story Planning (Simplified)
Tests Story Planning modules independently.
"""

import sys
sys.path.insert(0, '/home/clawd/projects/g-manga/src/stage1_input')
sys.path.insert(0, '/home/clawd/projects/g-manga/src/stage2_preprocessing')
sys.path.insert(0, '/home/clawd/projects/g-manga/src/stage3_story_planning')

from visual_adaptation import VisualAdaptation, MockLLMClient
from panel_breakdown import PanelBreakdown, MockLLMClient as PanelMockLLMClient
from storyboard_generator import StoryboardGenerator, MockLLMClient as StoryboardMockLLMClient
from page_calculator import PageCalculator
from storyboard_validator import StoryboardValidator
from models.project import (
    Scene, TextRange, VisualBeat, Panel,
    PanelDescription, Page, Storyboard
)


def test_story_planning_stage():
    """Test Story Planning modules independently."""
    print("=" * 70)
    print("Stage 3 Integration Test: Story Planning")
    print("=" * 70)

    # Test data
    scene_text = "The studio was filled with roses."
    scene_id = "scene-1"
    scene_number = 1
    scene_summary = "Two characters discuss art in a studio"

    # Step 1: Visual Adaptation (3.1.1)
    print("\n[1/6] Testing Visual Adaptation...")
    adaptation = VisualAdaptation(llm_client=MockLLMClient())

    visual_beats = adaptation.adapt_scene(scene_text, scene_id, scene_number)

    assert len(visual_beats) == 3, "Expected 3 beats"
    assert all(beat.scene_id == scene_id for beat in visual_beats), "Scene ID mismatch"

    print(f"Generated {len(visual_beats)} visual beats")

    # Step 2: Panel Breakdown (3.1.2)
    print("\n[2/6] Testing Panel Breakdown...")
    panel_breakdown = PanelBreakdown(llm_client=PanelMockLLMClient())

    test_visual_beats_list = [
        {
            "number": 1,
            "description": "Basil stands at his easel",
            "show_vs_tell": "show",
            "priority": 2,
            "visual_focus": "action"
        },
        {
            "number": 2,
            "description": "Lord Henry enters, examining painting",
            "show_vs_tell": "show",
            "priority": 2,
            "visual_focus": "action"
        },
        {
            "number": 3,
            "description": "They discuss art and beauty",
            "show_vs_tell": "tell",
            "priority": 2,
            "visual_focus": "dialogue"
        }
    ]

    result = panel_breakdown.breakdown_scene(
        test_visual_beats_list, scene_summary, scene_id, scene_number
    )

    assert result.panel_count == 4, "Expected 4 panels"

    print(f"Panel breakdown: {result.panel_count} panels, pacing={result.pacing}")

    # Step 3: Storyboard Generator (3.1.3)
    print("\n[3/6] Testing Storyboard Generator...")
    generator = StoryboardGenerator(llm_client=StoryboardMockLLMClient())

    panels = generator.generate_storyboard(
        scene_text, scene_id, scene_number,
        test_visual_beats_list, result
    )

    assert len(panels) == 4, "Expected 4 panels"

    print(f"Generated {len(panels)} panel descriptions")

    # Step 4: Page Calculator (3.1.4)
    print("\n[4/6] Testing Page Calculator...")
    calculator = PageCalculator()

    # Convert panels to simple format
    panels_data = [
        {
            "number": panel.panel_number,
            "type": panel.type
        } for panel in panels
    ]

    pages = calculator.calculate_pages(panels_data)

    assert len(pages) == 1, "Expected 1 page"

    print(f"Calculated {len(pages)} pages")

    # Step 5: Storyboard Validator (3.1.5)
    print("\n[5/6] Testing Storyboard Validator...")
    validator = StoryboardValidator()

    # Convert panels to validator format
    test_panels = []
    for panel in panels:
        test_panels.append({
            "id": panel.id,
            "page_number": panel.page_number,
            "panel_number": panel.panel_number,
            "type": panel.type,
            "description": panel.description,
            "camera": panel.camera,
            "mood": panel.mood,
            "dialogue": panel.dialogue,
            "narration": panel.narration,
            "characters": panel.characters,
            "props": panel.props
        })

    report = validator.validate_storyboard(test_panels)

    assert report["valid_percentage"] == 100, "Expected 100% valid"

    print(f"Validation report: {report['valid_percentage']}% valid")

    # Summary
    print("\n" + "=" * 70)
    print("Stage 3 Modules All Working")
    print("=" * 70)
    print("""
✅ Stage 3 Status:

Modules Implemented:
1. Visual Adaptation (3.1.1)
   - Visual beat generation with LLM prompts
   - Show vs. tell decisions
   - Priority assignment (1-5)
   - Visual focus categorization

2. Panel Breakdown (3.1.2)
   - Panel count calculation (4-8 panels per scene)
   - Panel type assignment (establishing, wide, medium, close-up, action, dialogue, splash)
   - Pacing determination (slow, normal, fast, action)
   - Camera planning per panel
   - Panel-to-visual-beat mapping

3. Storyboard Generator (3.1.3)
   - Detailed panel descriptions (2-4 sentences)
   - Camera, mood, lighting, composition
   - Dialogue and narration text
   - Character and prop lists
   - Batch processing (3-4 panels per LLM call)

4. Page Calculator (3.1.4)
   - Page composition from panels
   - Layout rules (4, 5, 6, 8 panels per page)
   - Panel-to-page assignment

5. Storyboard Validator (3.1.5)
   - Required field validation
   - Panel type validation
   - Camera angle validation
   - Description length validation (10-2000 chars)
   - Panel sequencing validation
   - Completeness reporting

Files Created:
- src/stage3_story_planning/visual_adaptation.py (8KB)
- src/stage3_story_planning/panel_breakdown.py (10KB)
- src/stage3_story_planning/storyboard_generator.py (16KB)
- src/stage3_story_planning/page_calculator.py (4KB)
- src/stage3_story_planning/storyboard_validator.py (7KB)

Next Steps:
- Add visual_beats.json to Stage 2 scene breakdown (LLM output)
- Complete integration test with real project (including Stage 2 scene data)
- Save to Kanban as complete
    """)

    print("\n" + "=" * 70)
    print("✅ Stage 3: Integration Test - PASSED")
    print("=" * 70)

    return True


if __name__ == "__main__":
    try:
        test_story_planning_stage()
    except AssertionError as e:
        print(f"\nTest FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\nTest ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
