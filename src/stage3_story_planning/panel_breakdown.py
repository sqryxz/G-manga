"""
Panel Breakdown - Stage 3.1.2
Determines panel types and pacing using LLM.
"""

import json
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class PanelBreakdown:
    """Panel plan for a scene."""
    panel_count: int = 0
    panel_types: List[str] = None  # "establishing", "wide", "medium", "close-up", etc.
    pacing: str = "normal"  # "slow", "normal", "fast", "action"
    camera_plan: List[str] = None  # Camera angles for each panel
    # Store breakdown data for validation
    breakdown_data: Dict[str, Any] = None
    panels: List[Dict[str, Any]] = None


class PanelBreakdown:
    """Breaks scenes into panels using LLM."""

    def __init__(self, llm_client=None):
        """
        Initialize Panel Breakdown.

        Args:
            llm_client: Optional LLM client (for testing/mocking)
        """
        self.llm_client = llm_client

        # Valid panel types
        self.panel_types = [
            "establishing", "wide", "medium", "close-up",
            "extreme-close-up", "action", "dialogue", "splash"
        ]

    def _build_prompt(self, visual_beats: List, scene_summary: str) -> str:
        """
        Build prompt for LLM panel breakdown.

        Args:
            visual_beats: List of visual beats from visual adaptation
            scene_summary: Scene summary text

        Returns:
            Prompt string
        """
        # Handle both dict and dataclass/BaseModel objects
        beats_list = []
        for i, beat in enumerate(visual_beats):
            if hasattr(beat, 'get'):
                # It's a dict
                desc = beat.get('description', '')
            elif hasattr(beat, 'description'):
                # It has description attribute
                desc = beat.description
            else:
                desc = str(beat)
            beats_list.append(f"{i+1}. {desc}")

        beats_text = "\n".join(beats_list)

        prompt = f"""You are planning a manga panel breakdown for a scene.

**SCENE SUMMARY:**
{scene_summary}

**VISUAL BEATS:**
{beats_text}

**PANEL PLANNING GUIDELINES:**

1. Panel Count: Determine optimal number of panels (4-8 typically)
   - Action scenes: More panels (6-8) for dynamic flow
   - Dialogue scenes: Fewer panels (4-6) to focus on conversation
   - Slow/contemplative: Fewer panels (4-5) to build atmosphere
   - Transitions: May need extra panel for clarity

2. Panel Types: Choose appropriate type for each panel:
   - "establishing" - Wide shot setting the scene
   - "wide" - Full body shot, good for dialogue
   - "medium" - Waist up, good balance of action and expression
   - "close-up" - Head/shoulders, good for emotions
   - "extreme-close-up" - Eyes, mouth, detailed expression
   - "action" - Dynamic composition, movement, impact
   - "dialogue" - Focus on conversation, minimal background

3. Pacing: Determine overall pacing:
   - "slow" - Contemplative, atmospheric
   - "normal" - Standard storytelling flow
   - "fast" - Action, quick exchanges, urgency
   - "action" - Combat, chase, high tension

4. Camera: Plan camera angles:
   - "eye-level" - Standard, neutral perspective
   - "low-angle" - Make character look powerful/imposing
   - "high-angle" - Make character look vulnerable/small
   - "dutch-angle" - Tilted, disorienting or uneasy
   - "over-the-shoulder" - Conversation, character focus
   - "point-of-view" - Character's perspective

Please plan the panel breakdown for this scene and return JSON in this exact format:
{{
  "panel_count": 5,
  "pacing": "normal",
  "panels": [
    {{
      "number": 1,
      "type": "establishing",
      "camera": "wide",
      "visual_beat_ref": 1
    }},
    {{
      "number": 2,
      "type": "medium",
      "camera": "eye-level",
      "visual_beat_ref": 2
    }}
  ]
}}

**VALID PANEL TYPES:**
{', '.join(self.panel_types)}

**VALID PACING:** "slow", "normal", "fast", "action"

Be specific and match panels to the visual beats provided. Each panel should capture one or more visual beats."""
        return prompt

    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse LLM response into panel breakdown data.

        Args:
            response_text: Raw LLM response

        Returns:
            Panel breakdown dictionary
        """
        # Extract JSON from response
        try:
            data = json.loads(response_text)
            return data
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code block
            import re
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(1))
                return data

            # Fallback: try to find JSON-like structure
            json_match = re.search(r'\{.*"panels".*\[.*\].*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group(0))
                    return data
                except:
                    pass

            raise ValueError("Failed to parse LLM response as JSON")

    def breakdown_scene(self, visual_beats: List[Dict[str, Any]], scene_summary: str, scene_id: str) -> PanelBreakdown:
        """
        Break a scene into panels.

        Args:
            visual_beats: List of visual beats from visual adaptation
            scene_summary: Scene summary
            scene_id: Scene ID

        Returns:
            PanelBreakdown object
        """
        # Build prompt
        prompt = self._build_prompt(visual_beats, scene_summary)

        # Call LLM
        if self.llm_client:
            response = self.llm_client.generate(prompt)
        else:
            # Mock response for testing
            response = self._mock_llm_response(visual_beats, scene_summary)

        # Parse response
        breakdown_data = self._parse_llm_response(response)

        # Validate
        panel_count = breakdown_data.get("panel_count", 0)
        panels = breakdown_data.get("panels", [])
        pacing = breakdown_data.get("pacing", "normal")

        # Validate panel types
        for panel in panels:
            if panel.get("type") not in self.panel_types:
                raise ValueError(f"Invalid panel type: {panel.get('type')}")

        # Create PanelBreakdown object
        panel_types = [p.get("type") for p in panels]
        camera_plan = [p.get("camera") for p in panels]

        result = PanelBreakdown()
        result.panel_count = panel_count
        result.panel_types = panel_types
        result.pacing = pacing
        result.camera_plan = camera_plan
        result.breakdown_data = breakdown_data
        result.panels = panels

        return result

    def _mock_llm_response(self, visual_beats: List[Dict[str, Any]], scene_summary: str) -> str:
        """
        Mock LLM response for testing.

        Args:
            visual_beats: List of visual beats
            scene_summary: Scene summary

        Returns:
            Mock JSON response
        """
        panel_count = min(6, max(4, len(visual_beats)))

        pacing = "normal" if len(visual_beats) < 5 else "action"

        panels = []
        for i in range(panel_count):
            beat = visual_beats[i] if i < len(visual_beats) else visual_beats[-1]

            # Determine panel type
            if hasattr(beat, 'get'):
                beat_desc = beat.get("description", "").lower()
            elif hasattr(beat, 'description'):
                beat_desc = beat.description.lower()
            else:
                beat_desc = str(beat).lower()
            if "dialogue" in beat_desc:
                panel_type = "dialogue"
            elif "enter" in beat_desc or "walk" in beat_desc:
                panel_type = "wide"
            elif "close" in beat_desc or "face" in beat_desc:
                panel_type = "close-up"
            elif i == 0:
                panel_type = "establishing"
            else:
                panel_type = "medium"

            panels.append({
                "number": i + 1,
                "type": panel_type,
                "camera": "eye-level",
                "visual_beat_ref": i + 1
            })

        mock_response = {
            "panel_count": panel_count,
            "pacing": pacing,
            "panels": panels
        }

        return json.dumps(mock_response)


class MockLLMClient:
    """Mock LLM client for testing."""

    def call(self, prompt: str) -> str:
        """Return a mock response."""
        return '''{
  "panel_count": 4,
  "pacing": "normal",
  "panels": [
    {
      "number": 1,
      "type": "establishing",
      "camera": "wide",
      "visual_beat_ref": 1
    },
    {
      "number": 2,
      "type": "medium",
      "camera": "eye-level",
      "visual_beat_ref": 2
    },
    {
      "number": 3,
      "type": "dialogue",
      "camera": "eye-level",
      "visual_beat_ref": 3
    },
    {
      "number": 4,
      "type": "close-up",
      "camera": "eye-level",
      "visual_beat_ref": 4
    }
  ]
}'''


def main():
    """Test Panel Breakdown."""
    import sys
    sys.path.insert(0, '/home/clawd/projects/g-manga/src/stage3_story_planning')

    # Create test visual beats
    test_visual_beats = [
        {
            "number": 1,
            "description": "Basil stands at his easel, brush in hand, looking at his painting"
        },
        {
            "number": 2,
            "description": "Lord Henry enters the studio, examining the painting with interest"
        },
        {
            "number": 3,
            "description": "Dialogue between Basil and Lord Henry about art and beauty"
        }
    ]

    test_scene_summary = "Two characters discuss art and beauty in a studio"

    # Test with mock LLM
    breakdown = PanelBreakdown(llm_client=MockLLMClient())

    result = breakdown.breakdown_scene(test_visual_beats, test_scene_summary, "scene-1")

    print(f"Panel Breakdown:")
    print(f"  Panel Count: {result.panel_count}")
    print(f"  Pacing: {result.pacing}")
    print(f"  Panel Types: {', '.join(result.panel_types)}")
    print(f"  Camera Plan: {', '.join(result.camera_plan)}")
    print()

    print("Panels:")
    for panel in result.panels:
        print(f"  Panel {panel['number']}:")
        print(f"    Type: {panel['type']}")
        print(f"    Camera: {panel['camera']}")
        print(f"    Visual Beat Ref: {panel['visual_beat_ref']}")


if __name__ == "__main__":
    main()
