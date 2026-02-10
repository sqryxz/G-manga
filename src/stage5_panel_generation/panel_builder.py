"""
Panel Builder - Stage 5.1.2
Combines panel type prompts with storyboard data.
"""

from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class PanelTemplate:
    """Template for a panel."""
    panel_id: str
    scene_id: str
    panel_number: int
    panel_type: str
    description: str
    camera: str
    mood: str
    lighting: str
    composition: str
    characters: List[str]
    dialogue: List[Dict[str, str]]
    narration: str
    text_range: List[int]  # [start_line, end_line]
    panel_template: str  # Full generated prompt for this panel


class PanelBuilder:
    """Builds panel prompts from type templates and storyboard data."""

    def __init__(self, panel_type_prompts):
        """
        Initialize Panel Builder.

        Args:
            panel_type_prompts: PanelTypePrompts instance
        """
        self.panel_type_prompts = panel_type_prompts

    def build_panel_prompt(self, scene_id: str, scene_number: int, visual_beat: Dict[str, Any], storyboard_data: Dict[str, Any]) -> PanelTemplate:
        """
        Build a panel prompt from scene data.

        Args:
            scene_id: Scene ID
            scene_number: Scene number
            visual_beat: Visual beat data
            storyboard_data: Storyboard data (panel descriptions, etc.)

        Returns:
            PanelTemplate object
        """
        # Determine panel type
        panel_type = self._determine_panel_type(visual_beat)

        # Get panel type prompt object
        if panel_type not in self.panel_type_prompts.prompts:
            raise ValueError(f"Unknown panel type: {panel_type}")

        type_prompt_obj = self.panel_type_prompts.prompts[panel_type]

        # Build context from storyboard data
        context = {
            "setting": storyboard_data.get("setting", "unknown"),
            "characters": storyboard_data.get("characters", []),
            "mood": storyboard_data.get("mood", "neutral"),
            "lighting": storyboard_data.get("lighting", "natural"),
            "previous_panel_type": storyboard_data.get("previous_panel_type", "none")
        }

        # Get full prompt string
        prompt_string = self.panel_type_prompts.get_prompt(panel_type, context)

        # Build custom prompt extension
        prompt_extension = f"""

**SCENE:**
- Scene ID: {scene_id}
- Scene Number: {scene_number}
- Visual Beat: {visual_beat.get("description", "")}

**PANEL REQUIREMENTS:**
- Panel Type: {panel_type}
- Characters: {', '.join(context.get("characters", []))}

**CONTENT GUIDELINES:**
"""

        # Add specific content based on visual beat description
        beat_desc = visual_beat.get("description", "")
        if beat_desc:
            prompt_extension += f"- {beat_desc}\n"

        # Add characters from context
        chars = context.get("characters", [])
        if chars:
            prompt_extension += f"\n- Characters in frame: {', '.join(chars)}\n"

        # Add dialogue if present
        if visual_beat.get("show_vs_tell") == "tell":
            dialogue = visual_beat.get("dialogue", "")
            if dialogue:
                prompt_extension += f"\n- Narration/Dialogue: {dialogue}\n"

        # Add visual direction
        if visual_beat.get("show_vs_tell") == "show":
            prompt_extension += f"\n- Visual Focus: {visual_beat.get("visual_focus", "action")}\n"

        # Add specific instructions from storyboard
        notes = storyboard_data.get("notes", "")
        if notes:
            prompt_extension += f"\n- Notes: {notes}\n"

        prompt_extension += f"""

**OUTPUT FORMAT:**
Provide a 2-4 sentence panel description that includes:
1. What's happening (action, expression, interaction)
2. Character positions and poses
3. Background and setting details
4. Mood and atmosphere
5. Lighting and color palette suggestions

Focus on being specific and visually clear for manga artists. Include details that would help an AI image generator create consistent character art.
"""

        # Combine prompts
        full_prompt = prompt_string + "\n" + prompt_extension

        return PanelTemplate(
            panel_id=f"p{scene_number}-{visual_beat.get('number', 1)}",
            scene_id=scene_id,
            panel_number=visual_beat.get("number", 1),
            panel_type=panel_type,
            description=visual_beat.get("description", ""),
            camera=type_prompt_obj.camera_guidance,
            mood=context.get("mood", "neutral"),
            lighting=context.get("lighting", "natural"),
            composition=type_prompt_obj.composition_tips,
            characters=list(set(context.get("characters", []))),
            dialogue=visual_beat.get("dialogue", []),
            narration=visual_beat.get("narration", ""),
            text_range=visual_beat.get("text_range", []),
            panel_template=full_prompt
        )

    def _determine_panel_type(self, visual_beat: Dict[str, Any]) -> str:
        """
        Determine panel type from visual beat.

        Args:
            visual_beat: Visual beat data

        Returns:
            Panel type string
        """
        desc = visual_beat.get("description", "").lower()
        camera = visual_beat.get("camera", "")

        # Analyze description keywords
        if "establish" in desc:
            return "establishing"
        elif "wide" in desc:
            return "wide"
        elif "action" in desc or "running" in desc or "fight" in desc:
            return "action"
        elif "dialogue" in desc or "talk" in desc or "say" in desc:
            return "dialogue"
        elif "face" in desc or "expression" in desc or "eye" in desc:
            return "close-up"
        elif "extreme" in desc or "detail" in desc or "close" in desc:
            return "extreme-close-up"
        elif "background" in desc or "setting" in desc or "location" in desc:
            return "establishing"

        # Check camera keyword
        if "low-angle" in camera:
            return "wide"
        elif "high-angle" in camera:
            return "close-up"
        elif "dutch" in camera:
            return "action"

        # Default to medium
        return "medium"


def main():
    """Test Panel Builder."""
    import sys
    sys.path.insert(0, '/home/clawd/projects/g-manga/src')
    sys.path.insert(0, '/home/clawd/projects/g-manga/src/stage5_panel_generation')

    from panel_type_prompts import PanelTypePrompts
    from models.project import Panel

    # Test panel type prompts
    type_prompts = PanelTypePrompts()

    print("=" * 70)
    print("Panel Builder Test")
    print("=" * 70)

    # Test getting all prompts
    print("\n[Test] Getting all panel type prompts...")
    all_prompts = type_prompts.get_all_prompts()

    print(f"✓ Found {len(all_prompts)} panel types:")
    for panel_type, prompt in all_prompts.items():
        print(f"  {panel_type}: {prompt.description[:60]}...")
        print(f"    Dos: {len(prompt.dont_list)}")
        print(f"    Examples: {len(prompt.examples)}")

    # Test building a panel
    print("\n[Test] Building a close-up panel...")
    test_visual_beat = {
        "number": 1,
        "description": "Close-up of Basil's face showing concern",
        "show_vs_tell": "show",
        "camera": "eye-level",
        "visual_focus": "expression",
        "dialogue": [{"speaker": "Basil", "text": "I... I don't know if I can show it."}],
        "text_range": [100, 105]
    }

    test_storyboard = {
        "setting": "art studio",
        "characters": ["Basil", "Lord Henry"],
        "mood": "contemplative",
        "notes": "Basil is conflicted about showing his painting"
    }

    builder = PanelBuilder(type_prompts)

    panel_template = builder.build_panel_prompt(
        scene_id="scene-1",
        scene_number=1,
        visual_beat=test_visual_beat,
        storyboard_data=test_storyboard
    )

    print(f"✓ Built panel template:")
    print(f"  Panel ID: {panel_template.panel_id}")
    print(f"  Panel Type: {panel_template.panel_type}")
    print(f"  Description: {panel_template.description[:60]}...")
    print(f"  Characters: {', '.join(panel_template.characters)}")
    print(f"  Prompt length: {len(panel_template.panel_template)} characters")

    print("\n" + "=" * 70)
    print("Panel Builder - PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()
