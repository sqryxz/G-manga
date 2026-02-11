"""
Visual Adaptation - Stage 3.1.1
Converts prose to visual storytelling beats using LLM.
"""

import json
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class VisualBeat:
    """A visual beat in a scene."""
    id: str
    scene_id: str
    beat_number: int
    description: str
    show_vs_tell: str
    priority: int
    visual_focus: str  # What to emphasize visually


class VisualAdaptation:
    """Adapts scenes to visual storytelling beats using LLM."""

    def __init__(self, llm_client=None):
        """
        Initialize Visual Adaptation.

        Args:
            llm_client: Optional LLM client (for testing/mocking)
        """
        self.llm_client = llm_client

    def _build_prompt(self, scene_text: str, scene_id: str, scene_number: int) -> str:
        """
        Build prompt for LLM visual adaptation.

        Args:
            scene_text: The scene text
            scene_id: Scene ID
            scene_number: Scene number

        Returns:
            Prompt string
        """
        prompt = f"""You are adapting a scene from a novel into visual storytelling beats for a manga.

Your goal is to identify what should be SHOWN visually vs. what can be TOLD through narration or dialogue.

**SHOW VS TELL:**
- SHOW: Visualize through art (characters in frame, action, facial expressions, gestures)
- TELL: Convey through dialogue boxes, narration text, or captions

**VISUAL BEATS:**
Break the scene into 3-7 visual beats. Each beat should:
1. Focus on one key moment or action
2. Be visually clear and specific
3. Have a single visual focus (characters, action, or environment)
4. Include the dialogue that occurs in that moment
5. Note if narration should be used instead of art

Scene {scene_number}:
{scene_text}

Please analyze this scene and provide visual beats in this exact JSON format:
{{
  "visual_beats": [
    {{
      "number": 1,
      "description": "Basil mixes paints on his palette while Lord Henry watches",
      "show_vs_tell": "show",
      "priority": 2,
      "visual_focus": "action"
    }},
    {{
      "number": 2,
      "description": "Close-up of Basil's hands mixing colors",
      "show_vs_tell": "show",
      "priority": 1,
      "visual_focus": "detail"
    }},
    {{
      "number": 3,
      "description": "Lord Henry's dialogue about beauty",
      "show_vs_tell": "tell",
      "priority": 2,
      "visual_focus": "dialogue"
    }}
  ]
}}

**PRIORITY SCALE:**
1 = Critical (essential to scene understanding)
2 = High (important context)
3 = Medium (nice to have)
4 = Low (optional detail)
5 = Minimal (can skip if needed)

**VISUAL FOCUS:**
- "action" - Character movement or interaction
- "dialogue" - Conversation between characters
- "expression" - Facial emotions or reactions
- "detail" - Close-up on objects or props
- "environment" - Background, location, atmosphere
- "establishing" - Wide shot setting the scene

Be thorough but stay focused on the most visual moments. Dialogue-heavy moments may need fewer beats, while action scenes need more."""
        return prompt

    def _parse_llm_response(self, response_text: str) -> List[Dict[str, Any]]:
        """
        Parse LLM response into visual beat data.

        Args:
            response_text: Raw LLM response

        Returns:
            List of visual beat data dictionaries
        """
        # Extract JSON from response
        try:
            data = json.loads(response_text)
            return data.get("visual_beats", [])
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code block
            import re
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(1))
                return data.get("visual_beats", [])

            # Fallback: try to find JSON-like structure
            json_match = re.search(r'\{.*"visual_beats".*\[.*\].*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group(0))
                    return data.get("visual_beats", [])
                except:
                    pass

            raise ValueError("Failed to parse LLM response as JSON")

    def adapt_scene(self, scene_text: str, scene_id: str, scene_number: int) -> List[VisualBeat]:
        """
        Adapt a scene into visual beats.

        Args:
            scene_text: The scene text
            scene_id: Scene ID
            scene_number: Scene number

        Returns:
            List of VisualBeat objects
        """
        # Build prompt
        prompt = self._build_prompt(scene_text, scene_id, scene_number)

        # Call LLM
        if self.llm_client:
            response = self.llm_client.generate(prompt)
        else:
            # Mock response for testing
            response = self._mock_llm_response(scene_text)

        # Parse response
        beats_data = self._parse_llm_response(response)

        # Create VisualBeat objects
        beats = []
        for beat_data in beats_data:
            beat = VisualBeat(
                id=f"{scene_id}-beat-{beat_data['number']}",
                scene_id=scene_id,
                beat_number=beat_data["number"],
                description=beat_data.get("description", ""),
                show_vs_tell=beat_data.get("show_vs_tell", "both"),
                priority=beat_data.get("priority", 3),
                visual_focus=beat_data.get("visual_focus", "action")
            )
            beats.append(beat)

        return beats

    def _mock_llm_response(self, scene_text: str) -> str:
        """
        Mock LLM response for testing.

        Args:
            scene_text: Scene text

        Returns:
            Mock JSON response
        """
        # Simplified mock - in production, use real LLM
        first_line = scene_text.split('\n')[0] if scene_text else ""

        mock_response = f'''{{
  "visual_beats": [
    {{
      "number": 1,
      "description": "{first_line[:100]}...",
      "show_vs_tell": "show",
      "priority": 2,
      "visual_focus": "action"
    }}
  ]
}}'''
        return mock_response


class MockLLMClient:
    """Mock LLM client for testing."""

    def call(self, prompt: str) -> str:
        """Return a mock response."""
        return '''{
  "visual_beats": [
    {
      "number": 1,
      "description": "Basil stands at his easel, brush in hand, looking at his painting",
      "show_vs_tell": "show",
      "priority": 2,
      "visual_focus": "action"
    },
    {
      "number": 2,
      "description": "Lord Henry enters the studio, examining the painting with interest",
      "show_vs_tell": "show",
      "priority": 2,
      "visual_focus": "action"
    },
    {
      "number": 3,
      "description": "Dialogue between Basil and Lord Henry about art and beauty",
      "show_vs_tell": "tell",
      "priority": 3,
      "visual_focus": "dialogue"
    }
  ]
}'''


def main():
    """Test Visual Adaptation."""
    import sys
    sys.path.insert(0, '/home/clawd/projects/g-manga/src/stage2_preprocessing')

    from scene_breakdown import Scene

    # Create test scene
    test_scene_text = """CHAPTER I.

The studio was filled with the rich odour of roses, and when the light summer wind stirred amongst the trees of the garden, there came through the open door the heavy scent of the lilac, or the more delicate perfume of the pink-flowering thorn.

Lord Henry Wotton could just catch the gleam of the honey-sweet and honey-coloured blossoms of a laburnum, whose tremulous branches seemed hardly able to bear the burden of a beauty so flame-like as theirs."""

    # Test with mock LLM
    adaptation = VisualAdaptation(llm_client=MockLLMClient())

    beats = adaptation.adapt_scene(test_scene_text, "scene-1", 1)

    print(f"Adapted scene into {len(beats)} visual beats:")
    print()

    for beat in beats:
        print(f"Beat {beat.beat_number}: {beat.description}")
        print(f"  Show vs Tell: {beat.show_vs_tell}")
        print(f"  Priority: {beat.priority}")
        print(f"  Focus: {beat.visual_focus}")
        print(f"  ID: {beat.id}")
        print()


if __name__ == "__main__":
    main()
