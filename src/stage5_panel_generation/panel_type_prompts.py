"""
Panel Type Prompts - Stage 5.1.1
Defines prompt templates for different panel types.
"""

from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class PanelTypePrompt:
    """Prompt template for a specific panel type."""
    panel_type: str
    description: str
    camera_guidance: str
    composition_tips: str
    examples: List[str]
    dont_list: List[str]  # Things to avoid in this panel type


class PanelTypePrompts:
    """Defines prompt templates for all panel types."""

    def __init__(self):
        """Initialize panel type prompts."""
        self.prompts = self._build_all_prompts()

    def _build_all_prompts(self) -> Dict[str, PanelTypePrompt]:
        """
        Build prompt templates for all panel types.

        Returns:
            Dictionary mapping panel type to prompt template
        """
        prompts = {}

        # 1. ESTABLISHING PANEL
        prompts["establishing"] = PanelTypePrompt(
            panel_type="establishing",
            description="Wide shot establishing scene location and atmosphere. Shows the entire setting to orient the reader.",
            camera_guidance="Use wide angle or fish-eye lens to capture full scene. Place horizon line according to rule of thirds (1/3 from top, 1/3 from bottom).",
            composition_tips="Include background elements that establish context (buildings, landscape, weather). Characters should be small but visible.",
            examples=[
                "Wide shot of Victorian London street with fog rolling in",
                "Art studio interior showing multiple easels and paintings on walls",
                "Basil's garden with rose bushes and statue in background"
            ],
            dont_list=[
                "Close-up of faces (use close-up instead)",
                "Focus on single character (use medium or close-up)",
                "Too much detail in background (keep establishing clean)"
            ]
        )

        # 2. WIDE PANEL
        prompts["wide"] = PanelTypePrompt(
            panel_type="wide",
            description="Full body shot (waist up) showing characters in context. Good for dialogue between two or three characters or action sequences.",
            camera_guidance="Use standard eye-level or slight high-angle. Ensure characters are centered in frame with proper headroom.",
            composition_tips="Frame multiple characters with enough space between them. Place dialogue speakers near their dialogue text.",
            examples=[
                "Basil and Lord Henry talking in studio, both visible",
                "Basil painting while Lord Henry watches",
                "Three characters: Basil, Lord Henry, and Dorian"
            ],
            dont_list=[
                "Close-up (use close-up instead)",
                "Extreme close-up (use close-up or extreme-close-up)",
                "Tilted camera (use action or dutch-angle instead)"
            ]
        )

        # 3. MEDIUM PANEL
        prompts["medium"] = PanelTypePrompt(
            panel_type="medium",
            description="Chest-up shot showing upper body. Ideal for character introductions or reactions while maintaining context.",
            camera_guidance="Use straight-on or slightly high angle. Show character from waist up with some background visible.",
            composition_tips="Include hand gestures or props that characters are holding. Show facial expressions clearly.",
            examples=[
                "Basil mixing paints on canvas, brush in hand",
                "Lord Henry examining a painting with critical look",
                "Character reaction to shocking news"
            ],
            dont_list=[
                "Close-up of face (use close-up)",
                "Full body (use wide or medium)",
                "Low angle (use high-angle)"
            ]
        )

        # 4. CLOSE-UP PANEL
        prompts["close-up"] = PanelTypePrompt(
            panel_type="close-up",
            description="Head and shoulders shot focusing on character's facial expression, eyes, and emotional state. Maximum emotional impact.",
            camera_guidance="Use telephoto lens or equivalent (85mm+). Focus entirely on character's face. Ensure eyes are in sharp focus.",
            composition_tips="Minimal background (blurred or plain). Character should fill most of frame. Include subtle details like tears, sweat, or wrinkles.",
            examples=[
                "Close-up of Basil looking contemplative at his easel",
                "Dorian's face showing realization and horror",
                "Lord Henry's cynical smile with raised eyebrow"
            ],
            dont_list=[
                "Include background scenery (keep it minimal)",
                "Show body below shoulders (use medium instead)",
                "Distracting elements (use plain or medium)"
            ]
        )

        # 5. EXTREME CLOSE-UP PANEL
        prompts["extreme-close-up"] = PanelTypePrompt(
            panel_type="extreme-close-up",
            description="Tight shot focusing on single feature (eyes, mouth, tear, sweat drop). Intense emotional focus.",
            camera_guidance="Use macro lens or extreme telephoto (100mm+). Fill entire frame with single feature. No empty space around subject.",
            composition_tips="Feature should be centered and fill 60-70% of frame. Use dramatic lighting (rim light, strong contrast). Background should be black or very dark.",
            examples=[
                "Single tear rolling down cheek",
                "Sweat bead on temple",
                "Eye dilated pupil in fear",
                "Close-up on trembling hands holding paintbrush"
            ],
            dont_list=[
                "Include other facial features (focus on one)",
                "Show body parts (use close-up)",
                "Soft lighting (use high contrast instead)",
                "Include scenery (keep background minimal)"
            ]
        )

        # 6. ACTION PANEL
        prompts["action"] = PanelTypePrompt(
            panel_type="action",
            description="Dynamic panel showing movement, impact, or transformation. Use motion blur or speed lines to convey action. Characters should be positioned mid-movement.",
            camera_guidance="Use Dutch angle or diagonal composition to suggest dynamism. Freeze character at peak of action with motion blur on limbs. Use speed lines for fast movement.",
            composition_tips="Position characters along implied diagonal (top-left to bottom-right or reverse). Include motion indicators (speed lines, blur, dust). Show impact through character poses and environment effects.",
            examples=[
                "Basil smashing his painting in rage",
                "Dorian stabbing portrait with knife",
                "Lord Henry laughing while watching a dramatic scene",
                "Basil running through garden in panic"
            ],
            dont_list=[
                "Static pose (use medium or wide instead)",
                "Talking heads (use dialogue or close-up)",
                "Clean background (include environmental effects)"
            ]
        )

        # 7. DIALOGUE PANEL
        prompts["dialogue"] = PanelTypePrompt(
            panel_type="dialogue",
            description="Panel focused on conversation between characters. Dialogue bubbles dominate visual space. Characters should be clearly visible and readable.",
            camera_guidance="Use straight-on or slight angle. Ensure both characters' faces are visible. Position dialogue bubbles to avoid overlapping characters or important action.",
            composition_tips="Place dialogue speakers in foreground. Use speech bubble tails to indicate speaker. Ensure text is readable (clear font, adequate size). Background should support dialogue without clutter.",
            examples=[
                "Basil and Lord Henry talking about art",
                "Dorian explaining his philosophy to Basil",
                "Three-way conversation with interruptions"
            ],
            dont_list=[
                "Include action (use dialogue or action instead)",
                "Show only one character (use close-up or wide)",
                "Include environmental details (keep focus on dialogue)"
            ]
        )

        # 8. SPLASH PANEL
        prompts["splash"] = PanelTypePrompt(
            panel_type="splash",
            description="Full-page or double-page spread that serves as dramatic highlight. Typically shows key character, emotional moment, or major plot development. Maximum visual impact.",
            camera_guidance="Use panoramic or very wide angle to capture scope. Subject (usually character) should be dominant and fill significant portion of page.",
            composition_tips="Subject should be centered or placed according to rule of thirds. Use atmospheric elements (rain, rays, dust, clouds) to enhance mood. Consider dramatic lighting from one direction (e.g., sunset glow from right).",
            examples=[
                "Dorian standing before portrait, showing his youth and beauty",
                "Basil's body discovered in attic, dramatic reveal",
                "Lord Henry's death scene with dark, moody atmosphere"
            ],
            dont_list=[
                "Show multiple characters equally (use focus on protagonist)",
                "Include complex background (keep it dramatic but focused)",
                "Use panel borders (splash should span full page)"
            ]
        )

        return prompts

    def get_prompt(self, panel_type: str, context: Dict[str, Any] = None) -> str:
        """
        Get prompt template for a specific panel type.

        Args:
            panel_type: Panel type (establishing, wide, medium, close-up, etc.)
            context: Additional context (characters, mood, setting)

        Returns:
            Prompt string
        """
        if panel_type not in self.prompts:
            raise ValueError(f"Unknown panel type: {panel_type}")

        prompt_template = self.prompts[panel_type]

        # Build prompt with context
        prompt = f"""You are creating a manga panel.

**PANEL TYPE:** {prompt_template.panel_type.upper()}

**DESCRIPTION:** {prompt_template.description}

**CAMERA GUIDANCE:** {prompt_template.camera_guidance}

**COMPOSITION TIPS:** {prompt_template.composition_tips}

**EXAMPLES:**
{', '.join(f"  - {ex}" for ex in prompt_template.examples[:3])}

**DOS AND DONTS:**
{', '.join(f"  ✗ DO: {dont}" for dont in prompt_template.dont_list[:3])}

"""
        # Add context if provided
        if context:
            prompt += f"\n**CONTEXT:**\n"
            prompt += f"Setting: {context.get('setting', 'studio/garden')}\n"
            prompt += f"Characters: {', '.join(context.get('characters', []))}\n"
            prompt += f"Mood: {context.get('mood', 'neutral')}\n"
            prompt += f"Previous Panel: {context.get('previous_panel_type', 'none')}\n"

        prompt += f"""

**YOUR TASK:**
Create a {prompt_template.panel_type} manga panel for this scene.

**REQUIREMENTS:**
1. Follow the description and composition tips above
2. Use the camera guidance specified
3. Avoid the items in the DOS AND DONTS list
4. Include dialogue text if this is a conversation panel
5. Add relevant environmental details (lighting, weather, atmosphere)
6. Ensure characters are consistent with previous panels
7. Use manga-style inking (black outlines, clean lines, screen tones)

**OUTPUT FORMAT:**
Provide a detailed panel description (2-4 sentences) that an illustrator can use directly.

Focus on what's visible in the panel - character positions, actions, expressions, background elements. Include specific details about lighting, color, and mood.
"""
        return prompt

    def get_all_prompts(self) -> Dict[str, PanelTypePrompt]:
        """
        Get all panel type prompts.

        Returns:
            Dictionary of all panel types and their prompts
        """
        return self.prompts

    def export_prompts_json(self, output_file: str = "panel_prompts.json") -> None:
        """
        Export all prompts to JSON for easy reference.

        Args:
            output_file: File path for JSON output
        """
        import json

        # Convert dataclass to dict
        prompts_dict = {}
        for panel_type, prompt in self.prompts.items():
            prompts_dict[panel_type] = {
                "panel_type": prompt.panel_type,
                "description": prompt.description,
                "camera_guidance": prompt.camera_guidance,
                "composition_tips": prompt.composition_tips,
                "examples": prompt.examples,
                "dont_list": prompt.dont_list
            }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "panel_types": prompts_dict,
                "total_types": len(prompts_dict)
            }, f, indent=2, ensure_ascii=False)

        print(f"✓ Exported {len(prompts_dict)} panel type prompts to {output_file}")


def main():
    """Test Panel Type Prompts."""
    prompts = PanelTypePrompts()

    # Test getting a specific prompt
    print("Testing get_prompt()...")
    prompt = prompts.get_prompt("close-up", context={
        "setting": "art studio",
        "characters": ["Basil", "Lord Henry"],
        "mood": "contemplative",
        "previous_panel_type": "medium"
    })

    print("✓ Generated close-up prompt")
    print(f"\nPrompt length: {len(prompt)} characters")
    print(f"\nFirst 200 chars:\n{prompt[:200]}")

    # Test getting all prompts
    print("\n\nTesting get_all_prompts()...")
    all_prompts = prompts.get_all_prompts()

    print(f"✓ Total panel types: {len(all_prompts)}")
    print("\nPanel Types:")
    for panel_type, prompt in all_prompts.items():
        print(f"  {panel_type}:")
        print(f"    Description: {prompt.description[:100]}...")
        print(f"    Dos: {len(prompt.dont_list)}")

    # Test export
    print("\n\nTesting export_prompts_json()...")
    prompts.export_prompts_json("panel_prompts_test.json")


if __name__ == "__main__":
    main()
