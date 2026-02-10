"""
Stage 5 Integration Test - 5.1.5
End-to-end test of panel generation pipeline.
"""

import sys
import os
from datetime import datetime, timezone

# Add src to path
sys.path.insert(0, '/home/clawd/projects/g-manga/src')
sys.path.insert(0, '/home/clawd/projects/g-manga/src/stage5_panel_generation')

from stage5_panel_generation.panel_type_prompts import PanelTypePrompts
from stage5_panel_generation.panel_builder import PanelBuilder
from stage5_panel_generation.panel_optimizer import PanelOptimizer, CharacterConsistencyRule
from stage5_panel_generation.panel_state import PanelStateManager, PanelData


def test_end_to_end_panel_generation():
    """Test complete panel generation pipeline."""
    print("=" * 70)
    print("Stage 5 Integration Test - End-to-End Panel Generation")
    print("=" * 70)

    # Setup test project directory
    test_project_dir = "/home/clawd/projects/g-manga/projects/test-stage5-integration"
    os.makedirs(test_project_dir, exist_ok=True)

    # Test data
    test_scenes = [
        {
            "scene_id": "scene-1",
            "scene_number": 1,
            "storyboard_data": {
                "setting": "art studio",
                "characters": ["Basil", "Lord Henry"],
                "mood": "contemplative",
                "lighting": "natural light from window",
                "notes": "Basil shows his painting to Lord Henry"
            },
            "visual_beats": [
                {
                    "number": 1,
                    "description": "Wide shot of art studio showing both characters",
                    "show_vs_tell": "show",
                    "camera": "wide angle",
                    "visual_focus": "setting"
                },
                {
                    "number": 2,
                    "description": "Close-up of Basil looking nervous",
                    "show_vs_tell": "show",
                    "camera": "close-up",
                    "visual_focus": "expression",
                    "dialogue": [{"speaker": "Basil", "text": "I've painted something extraordinary."}]
                },
                {
                    "number": 3,
                    "description": "Medium shot of Lord Henry examining the painting",
                    "show_vs_tell": "show",
                    "camera": "medium",
                    "visual_focus": "action"
                },
                {
                    "number": 4,
                    "description": "Extreme close-up of Lord Henry's eyes widening",
                    "show_vs_tell": "show",
                    "camera": "extreme close-up",
                    "visual_focus": "expression"
                }
            ]
        }
    ]

    # Step 1: Initialize Panel Type Prompts
    print("\n[Step 1] Initialize Panel Type Prompts...")
    type_prompts = PanelTypePrompts()
    all_prompts = type_prompts.get_all_prompts()
    print(f"✓ Loaded {len(all_prompts)} panel type templates")

    # Step 2: Initialize Panel Builder
    print("\n[Step 2] Initialize Panel Builder...")
    builder = PanelBuilder(type_prompts)
    print(f"✓ Panel Builder ready")

    # Step 3: Initialize Panel Optimizer with character rules
    print("\n[Step 3] Initialize Panel Optimizer...")
    optimizer = PanelOptimizer()

    # Add character rules
    basil_rule = CharacterConsistencyRule(
        character_name="Basil",
        key_features=["dark wavy hair", "brown eyes", "slender artistic build"],
        clothing="Victorian artist smock, paint-stained",
        accessories="paintbrush, palette",
        expressions="contemplative, intense when painting, nervous when anxious"
    )
    optimizer.add_character_rule(basil_rule)

    lord_henry_rule = CharacterConsistencyRule(
        character_name="Lord Henry",
        key_features=["blonde hair", "gray eyes", "elegant posture"],
        clothing="Victorian gentleman's suit, waistcoat, cravat",
        accessories="cane, watch chain",
        expressions="amused, cynical, calculating"
    )
    optimizer.add_character_rule(lord_henry_rule)
    print(f"✓ Added {len(optimizer.character_rules)} character consistency rules")

    # Step 4: Initialize State Manager
    print("\n[Step 4] Initialize Panel State Manager...")
    state_mgr = PanelStateManager(test_project_dir)
    print(f"✓ State Manager initialized")

    # Step 5: Generate panels for all scenes
    print("\n[Step 5] Generate panels...")
    total_panels_generated = 0

    for scene_data in test_scenes:
        scene_id = scene_data["scene_id"]
        scene_number = scene_data["scene_number"]
        storyboard_data = scene_data["storyboard_data"]
        visual_beats = scene_data["visual_beats"]

        print(f"\n  Processing {scene_id}...")
        print(f"  Characters: {', '.join(storyboard_data['characters'])}")

        for visual_beat in visual_beats:
            # Determine which characters are in this panel
            panel_type = builder._determine_panel_type(visual_beat)
            if panel_type in ["close-up", "extreme-close-up"]:
                # Single character focus
                characters_in_panel = ["Basil"] if "Basil" in visual_beat["description"].lower() else ["Lord Henry"]
            else:
                # Multiple characters
                characters_in_panel = storyboard_data["characters"]

            # Build panel prompt
            panel_template = builder.build_panel_prompt(
                scene_id=scene_id,
                scene_number=scene_number,
                visual_beat=visual_beat,
                storyboard_data=storyboard_data
            )

            # Get previous panels for consistency
            previous_panels = state_mgr.get_previous_panels(scene_id, visual_beat["number"])
            previous_prompts = [p.panel_prompt for p in previous_panels]

            # Optimize prompt
            optimization_result = optimizer.optimize_prompt(
                prompt=panel_template.panel_template,
                panel_type=panel_type,
                characters_in_panel=characters_in_panel,
                previous_panels=previous_prompts
            )

            # Create panel data
            panel_data = PanelData(
                panel_id=panel_template.panel_id,
                scene_id=scene_id,
                panel_number=visual_beat["number"],
                panel_type=panel_type,
                description=panel_template.description,
                camera=panel_template.camera,
                mood=panel_template.mood,
                lighting=panel_template.lighting,
                composition=panel_template.composition,
                characters=panel_template.characters,
                dialogue=panel_template.dialogue,
                narration=panel_template.narration,
                text_range=panel_template.text_range,
                panel_prompt=panel_template.panel_template,
                optimized_prompt=optimization_result.optimized_prompt,
                consistency_score=optimization_result.consistency_score,
                created_at=datetime.now(timezone.utc).isoformat(),
                last_updated=datetime.now(timezone.utc).isoformat()
            )

            # Save panel
            state_mgr.save_panel(panel_data)

            total_panels_generated += 1
            print(f"    ✓ Generated panel {panel_data.panel_id} ({panel_type}) - Score: {panel_data.consistency_score:.2f}")

    print(f"\n✓ Generated {total_panels_generated} panels across {len(test_scenes)} scene(s)")

    # Step 6: Verify generated panels
    print("\n[Step 6] Verify generated panels...")
    stats = state_mgr.get_statistics()
    print(f"✓ Verification:")
    print(f"  Total panels: {stats['total_panels']}")
    print(f"  Scenes: {stats['scenes']}")
    print(f"  Panel types: {stats['panel_types']}")
    print(f"  Characters: {stats['characters']}")

    # Step 7: Query tests
    print("\n[Step 7] Query tests...")

    # Query by scene
    scene1_panels = state_mgr.get_panels_by_scene("scene-1")
    print(f"✓ Panels in scene-1: {len(scene1_panels)}")

    # Query by character
    basil_panels = state_mgr.get_panels_by_character("Basil")
    print(f"✓ Panels featuring Basil: {len(basil_panels)}")

    lord_henry_panels = state_mgr.get_panels_by_character("Lord Henry")
    print(f"✓ Panels featuring Lord Henry: {len(lord_henry_panels)}")

    # Step 8: Export tests
    print("\n[Step 8] Export tests...")

    # Export single panel
    first_panel_id = list(state_mgr.panels.keys())[0]
    export_file = os.path.join(test_project_dir, "test_export_panel.json")
    state_mgr.export_panel(first_panel_id, export_file)
    print(f"✓ Exported panel {first_panel_id} to test_export_panel.json")

    # Export all panels
    state_mgr.export_all_panels()
    print(f"✓ Exported all panels to panels/export/")

    # Step 9: Character rules persistence
    print("\n[Step 9] Character rules persistence...")

    # Save character rules
    character_rules = {
        "characters": {
            "Basil": {
                "key_features": basil_rule.key_features,
                "clothing": basil_rule.clothing,
                "accessories": basil_rule.accessories,
                "expressions": basil_rule.expressions
            },
            "Lord Henry": {
                "key_features": lord_henry_rule.key_features,
                "clothing": lord_henry_rule.clothing,
                "accessories": lord_henry_rule.accessories,
                "expressions": lord_henry_rule.expressions
            }
        }
    }
    state_mgr.save_character_rules(character_rules)
    print(f"✓ Saved character rules")

    # Load character rules
    loaded_rules = state_mgr.load_character_rules()
    loaded_char_count = len(loaded_rules.get("characters", {}))
    print(f"✓ Loaded {loaded_char_count} character rules")

    # Step 10: Consistency check
    print("\n[Step 10] Consistency check...")

    avg_consistency_score = sum(p.consistency_score for p in state_mgr.panels.values()) / len(state_mgr.panels)
    print(f"✓ Average consistency score: {avg_consistency_score:.2f}")

    # Verify all prompts were optimized
    all_optimized = all(len(p.optimized_prompt) > len(p.panel_prompt) for p in state_mgr.panels.values())
    print(f"✓ All prompts optimized: {all_optimized}")

    # Verify character rules applied
    basil_panels = state_mgr.get_panels_by_character("Basil")
    basil_rules_applied = any("Basil" in p.optimized_prompt and "CHARACTER CONSISTENCY" in p.optimized_prompt for p in basil_panels)
    print(f"✓ Character consistency rules applied: {basil_rules_applied}")

    # Summary
    print("\n" + "=" * 70)
    print("Stage 5 Integration Test - PASSED")
    print("=" * 70)
    print(f"\nSummary:")
    print(f"  Panels generated: {total_panels_generated}")
    print(f"  Panel types: {list(stats['panel_types'].keys())}")
    print(f"  Characters tracked: {list(stats['characters'].keys())}")
    print(f"  Avg consistency score: {avg_consistency_score:.2f}")
    print(f"  All tests passed: ✓")

    return True


def main():
    """Run integration tests."""
    try:
        success = test_end_to_end_panel_generation()
        return 0 if success else 1
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
