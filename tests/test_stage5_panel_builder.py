import sys
sys.path.insert(0, '/home/clawd/projects/g-manga/src')

from panel_type_prompts import PanelTypePrompts
from panel_builder import PanelBuilder
from models.project import Panel

def test_panel_builder():
    type_prompts = PanelTypePrompts()
    builder = PanelBuilder(type_prompts)

    test_visual_beat = {
        'number': 1,
        'description': 'Close-up of Basil',
        'show_vs_tell': 'show',
        'camera': 'eye-level',
        'visual_focus': 'expression',
        'dialogue': [{'speaker': 'Basil', 'text': 'I do not know'}],
        'text_range': [100, 105]
    }

    test_storyboard = {
        'setting': 'art studio',
        'characters': ['Basil', 'Lord Henry'],
        'mood': 'contemplative'
    }

    panel_template = builder.build_panel_prompt(
        scene_id='scene-1',
        scene_number=1,
        visual_beat=test_visual_beat,
        storyboard_data=test_storyboard
    )

    print("Panel Template Test:")
    print("  Panel ID: " + panel_template.panel_id)
    print("  Panel Type: " + panel_template.panel_type)
    print("  Description: " + panel_template.description[:60] + "...")
    print("  Characters: " + ", ".join(panel_template.characters))
    print()

    print("Panel Builder: PASSED")
    print("=" * 70)


if __name__ == "__main__":
    test_panel_builder()
