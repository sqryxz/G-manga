"""
Storyboard Generator - Stage 3.1.3
Generates detailed panel descriptions using LLM.
"""

import json
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class PanelDescription:
    """Detailed description for a single panel."""
    id: str
    page_number: int
    panel_number: int
    type: str
    description: str
    camera: str
    mood: str
    lighting: str
    composition: str
    dialogue: List[Dict[str, str]]
    narration: str
    characters: List[str]
    props: List[str]  # Objects/background elements


class StoryboardGenerator:
    """Generates storyboard panels using LLM."""

    def __init__(self, llm_client=None):
        """
        Initialize Storyboard Generator.

        Args:
            llm_client: Optional LLM client (for testing/mocking)
        """
        self.llm_client = llm_client

    def _build_prompt(self, scene_text: str, scene_id: str, visual_beats: List[Dict[str, Any]], panel_plan: List[Dict[str, Any]]) -> str:
        """
        Build prompt for LLM storyboard generation.

        Args:
            scene_text: The scene text
            scene_id: Scene ID
            visual_beats: List of visual beats
            panel_plan: Panel breakdown plan

        Returns:
            Prompt string
        """
        # Map visual beats to panel references
        beats_map = {beat['number']: beat for beat in visual_beats}
        panels_map = {panel['number']: panel for panel in panel_plan}

        beats_text = "\n".join([
            f"Beat {beat['number']}: {beat.get('description', '')}" for beat in visual_beats
        ])

        panels_text = "\n".join([
            f"Panel {panel['number']}: Type={panel.get('type', 'medium')}, Camera={panel.get('camera', 'eye-level')}" for panel in panel_plan
        ])

        prompt = f"""You are creating detailed manga panel descriptions for a storyboard.

**SCENE CONTEXT:**
{scene_text}

**VISUAL BEATS:**
{beats_text}

**PANEL PLAN:**
{panels_text}

**YOUR TASK:**
Generate detailed descriptions for each panel. For each panel, provide:

1. **Panel Description** - 2-4 sentences describing exactly what's visible
   - Include character positions, poses, and actions
   - Describe background and environment details
   - Note any important props or objects

2. **Mood** - Emotional tone of the panel (e.g., "tense", "warm", "mysterious", "energetic")

3. **Lighting** - How light affects the scene (e.g., "bright natural light", "dim candlelight", "harsh fluorescent")

4. **Composition** - How elements are arranged (e.g., "symmetrical", "dynamic diagonal", "rule-of-thirds", "central focus")

5. **Dialogue** - Any spoken dialogue in this panel (list with speakers)
   - Format: {{"speaker": "Name", "text": "Quote"}}
   - Empty list if no dialogue

6. **Narration** - Any narration text to include (empty if none)

7. **Characters** - List of characters visible in this panel

8. **Props** - List of important objects/elements (e.g., "easel", "painting", "wine glass")

**STORYBOARD FORMAT:**
Return JSON in this exact format:
{{
  "panels": [
    {{
      "number": 1,
      "type": "establishing",
      "description": "Wide shot of Basil's studio showing multiple easels and paintings on walls. Natural light streams through large windows.",
      "camera": "wide",
      "mood": "peaceful, artistic",
      "lighting": "bright natural sunlight",
      "composition": "wide establishing shot with depth",
      "dialogue": [],
      "narration": "",
      "characters": ["Basil", "Lord Henry"],
      "props": ["easel", "paintings", "windows", "palette"]
    }},
    {{
      "number": 2,
      "type": "medium",
      "description": "Basil stands at his easel with brush in hand, his expression focused and contemplative. The painting is partially visible behind him.",
      "camera": "medium",
      "mood": "contemplative, serene",
      "lighting": "soft, warm golden hour",
      "composition": "character-focused with painting in background",
      "dialogue": [
        {{"speaker": "Lord Henry", "text": "That's a remarkable piece of work."}}
      ],
      "narration": "",
      "characters": ["Basil", "Lord Henry"],
      "props": ["brush", "palette", "easel", "painting"]
    }}
  ]
}}

**STYLE NOTES:**
- Be specific and descriptive but concise
- Focus on what's visible to draw (avoid internal thoughts/feelings)
- Match the panel type and camera angle specified in the plan
- Include details that would help an illustrator (colors, textures, expressions)

Generate descriptions for all {len(panel_plan)} panels specified in the panel plan."""
        return prompt

    def _parse_llm_response(self, response_text: str) -> List[Dict[str, Any]]:
        """
        Parse LLM response into panel data.

        Args:
            response_text: Raw LLM response

        Returns:
            List of panel data dictionaries
        """
        # Extract JSON from response
        try:
            data = json.loads(response_text)
            return data.get("panels", [])
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code block
            import re
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(1))
                return data.get("panels", [])

            # Fallback: try to find JSON-like structure
            json_match = re.search(r'\{.*"panels".*\[.*\].*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group(0))
                    return data.get("panels", [])
                except:
                    pass

            raise ValueError("Failed to parse LLM response as JSON")

    def generate_storyboard(self, scene_text: str, scene_id: str, scene_number: int, visual_beats: List[Dict[str, Any]], panel_plan: Dict[str, Any]) -> List[PanelDescription]:
        """
        Generate storyboard for a scene.

        Args:
            scene_text: The scene text
            scene_id: Scene ID
            scene_number: Scene number
            visual_beats: List of visual beats
            panel_plan: Panel breakdown plan

        Returns:
            List of PanelDescription objects
        """
        # Build prompt
        panels_list = panel_plan.get("panels", [])
        prompt = self._build_prompt(scene_text, scene_id, visual_beats, panels_list)

        # Call LLM
        if self.llm_client:
            response = self.llm_client.call(prompt)
        else:
            # Mock response for testing
            response = self._mock_llm_response(panels_list)

        # Parse response
        panels_data = self._parse_llm_response(response)

        # Create PanelDescription objects
        panels = []
        for i, panel_data in enumerate(panels_data):
            panel = PanelDescription(
                id=f"p{scene_number}-{panel_data['number']}",
                page_number=1,  # Will be calculated by page calculator
                panel_number=panel_data["number"],
                type=panel_data.get("type", "medium"),
                description=panel_data.get("description", ""),
                camera=panel_data.get("camera", "eye-level"),
                mood=panel_data.get("mood", "neutral"),
                lighting=panel_data.get("lighting", "natural"),
                composition=panel_data.get("composition", "centered"),
                dialogue=panel_data.get("dialogue", []),
                narration=panel_data.get("narration", ""),
                characters=panel_data.get("characters", []),
                props=panel_data.get("props", [])
            )
            panels.append(panel)

        return panels

    def _mock_llm_response(self, panels: List[Dict[str, Any]]) -> str:
        """
        Mock LLM response for testing.

        Args:
            panels: Panel breakdown plan

        Returns:
            Mock JSON response
        """
        mock_panels = []

        for i, panel in enumerate(panels):
            # Generate mock descriptions based on panel type
            panel_type = panel.get("type", "medium")

            if panel_type == "establishing":
                mock_panels.append({
                    "number": i + 1,
                    "type": "establishing",
                    "description": "Wide establishing shot of the art studio. Natural light streams through large windows. Multiple easels and paintings visible along the walls.",
                    "camera": "wide",
                    "mood": "peaceful, artistic",
                    "lighting": "bright natural sunlight",
                    "composition": "wide establishing shot with depth",
                    "dialogue": [],
                    "narration": "",
                    "characters": ["Basil", "Lord Henry"],
                    "props": ["easel", "paintings", "windows", "palette"]
                })
            elif panel_type == "dialogue":
                mock_panels.append({
                    "number": i + 1,
                    "type": "dialogue",
                    "description": "Medium shot of two characters talking. Basil looks concerned while Lord Henry appears relaxed and interested.",
                    "camera": "eye-level",
                    "mood": "contemplative",
                    "lighting": "soft, warm golden hour",
                    "composition": "balanced two-shot",
                    "dialogue": [{"speaker": "Lord Henry", "text": "That's a remarkable piece of work."}],
                    "narration": "",
                    "characters": ["Basil", "Lord Henry"],
                    "props": ["easel", "painting"]
                })
            elif panel_type == "close-up":
                mock_panels.append({
                    "number": i + 1,
                    "type": "close-up",
                    "description": "Close-up of Basil's face showing concern and artistic intensity. Eyes slightly narrowed in thought.",
                    "camera": "close-up",
                    "mood": "serious, contemplative",
                    "lighting": "side-lit from window",
                    "composition": "character close-up",
                    "dialogue": [],
                    "narration": "",
                    "characters": ["Basil"],
                    "props": []
                })
            else:
                # Default medium shot
                mock_panels.append({
                    "number": i + 1,
                    "type": "medium",
                    "description": "Medium shot showing the interaction between the two characters. Background elements visible but out of focus.",
                    "camera": "eye-level",
                    "mood": "neutral",
                    "lighting": "natural ambient",
                    "composition": "standard two-character composition",
                    "dialogue": [],
                    "narration": "",
                    "characters": ["Basil", "Lord Henry"],
                    "props": ["studio furniture"]
                })

        mock_response = {
            "panels": mock_panels
        }

        return json.dumps(mock_response)


class MockLLMClient:
    """Mock LLM client for testing."""

    def call(self, prompt: str) -> str:
        """Return a mock response."""
        return '''{
  "panels": [
    {
      "number": 1,
      "type": "establishing",
      "description": "Wide establishing shot of Basil's art studio. Multiple easels with paintings line the walls. Natural light streams through large windows. Dust motes dance in the light beams.",
      "camera": "wide",
      "mood": "peaceful, artistic",
      "lighting": "bright natural sunlight",
      "composition": "wide establishing shot with depth",
      "dialogue": [],
      "narration": "",
      "characters": ["Basil"],
      "props": ["easel", "paintings", "windows", "palette", "canvas"]
    },
    {
      "number": 2,
      "type": "medium",
      "description": "Medium shot of Basil at his easel, brush in hand. His expression is focused and slightly tense. The painting on the easel shows a portrait in progress.",
      "camera": "medium",
      "mood": "contemplative",
      "lighting": "warm, golden hour light from window",
      "composition": "character-focused with painting in background",
      "dialogue": [],
      "narration": "",
      "characters": ["Basil"],
      "props": ["easel", "brush", "palette", "painting"]
    },
    {
      "number": 3,
      "type": "dialogue",
      "description": "Medium two-shot of Basil and Lord Henry. Basil looks concerned while Lord Henry gestures toward the painting with interest.",
      "camera": "eye-level",
      "mood": "inquisitive",
      "lighting": "soft, ambient",
      "composition": "balanced conversational composition",
      "dialogue": [{"speaker": "Lord Henry", "text": "That's quite remarkable."}],
      "narration": "",
      "characters": ["Basil", "Lord Henry"],
      "props": ["easel", "painting"]
    },
    {
      "number": 4,
      "type": "close-up",
      "description": "Close-up on Basil's face showing hesitation and concern. His eyes are slightly downcast. Hand gripping the paintbrush tightly.",
      "camera": "close-up",
      "mood": "apprehensive",
      "lighting": "softer, side-lit",
      "composition": "central character focus",
      "dialogue": [],
      "narration": "",
      "characters": ["Basil"],
      "props": ["paintbrush"]
    }
  ]
}'''


def main():
    """Test Storyboard Generator."""
    import sys
    sys.path.insert(0, '/home/clawd/projects/g-manga/src/stage3_story_planning')
    sys.path.insert(0, '/home/clawd/projects/g-manga/src/stage2_preprocessing')
    sys.path.insert(0, '/home/clawd/projects/g-manga/src')

    from visual_adaptation import VisualBeat

    # Create test data
    test_scene_text = "The studio was filled with the rich odour of roses."

    test_visual_beats = [
        {"number": 1, "description": "Basil stands at easel"},
        {"number": 2, "description": "Lord Henry enters"},
        {"number": 3, "description": "They talk about art"}
    ]

    # Create mock panel plan (simple dict for testing)
    panel_plan = {
        "panel_count": 4,
        "panel_types": ["establishing", "medium", "dialogue", "close-up"],
        "pacing": "normal",
        "camera_plan": ["wide", "eye-level", "eye-level", "close-up"],
        "panels": [
            {"number": 1, "type": "establishing", "camera": "wide"},
            {"number": 2, "type": "medium", "camera": "eye-level"},
            {"number": 3, "type": "dialogue", "camera": "eye-level"},
            {"number": 4, "type": "close-up", "camera": "close-up"}
        ]
    }

    # Test with mock LLM
    generator = StoryboardGenerator(llm_client=MockLLMClient())

    panels = generator.generate_storyboard(
        test_scene_text,
        "scene-1",
        1,
        test_visual_beats,
        panel_plan
    )

    print(f"Generated storyboard with {len(panels)} panels:")
    print()

    for i, panel in enumerate(panels):
        print(f"Panel {panel.panel_number}:")
        print(f"  Type: {panel.type}")
        print(f"  Camera: {panel.camera}")
        print(f"  Mood: {panel.mood}")
        print(f"  Lighting: {panel.lighting}")
        print(f"  Description: {panel.description[:100]}...")
        print(f"  Characters: {', '.join(panel.characters)}")
        print(f"  Props: {', '.join(panel.props)}")
        print()


if __name__ == "__main__":
    main()
