"""
Detailed Storyboard Generator - Stage 3.1.2
Generates detailed panel descriptions with comprehensive visual specifications.
"""

import json
import re
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field, asdict


@dataclass
class DetailedPanel:
    """
    Detailed description for a single manga panel.
    
    Attributes:
        panel_number: Sequential panel number within the scene
        shot_type: Type of shot (establishing, medium, close-up, dialogue, action, insert)
        angle: Camera angle (eye-level, low, high, bird's eye, worm's eye, Dutch)
        description: Detailed visual description (3-5 sentences)
        mood: Emotional tone/atmosphere of the panel
        lighting: Lighting description and quality
        composition: Visual arrangement and framing
        color_notes: Optional color palette or tint notes
        dialogue: Optional dialogue lines with speaker
        narration: Optional narration text for this panel
        characters: List of characters visible in this panel
        props: List of important objects/elements
        reference_notes: Optional reference images or style notes
    """
    panel_number: int
    shot_type: str
    angle: str
    description: str
    mood: str
    lighting: str
    composition: str
    color_notes: Optional[str] = None
    dialogue: List[Dict[str, str]] = field(default_factory=list)
    narration: str = ""
    characters: List[str] = field(default_factory=list)
    props: List[str] = field(default_factory=list)
    reference_notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class VisualBeat:
    """
    A visual beat representing a key moment or action in a scene.
    
    Attributes:
        number: Beat number
        description: Description of the visual action/moment
    """
    number: int
    description: str


@dataclass
class PanelSpec:
    """
    Specification for a single panel in the storyboard.
    
    Attributes:
        number: Panel number
        shot_type: Type of shot for this panel
        angle: Camera angle for this panel
        focus: What's the focus/subject of this panel
    """
    number: int
    shot_type: str
    angle: str
    focus: str


class DetailedStoryboardGenerator:
    """
    Generates detailed manga panel descriptions using LLM.
    
    This class creates comprehensive storyboard descriptions including
    mood, lighting, composition, color notes, and reference information
    for each panel.
    """

    def __init__(self, llm_client=None):
        """
        Initialize Detailed Storyboard Generator.
        
        Args:
            llm_client: Optional LLM client (for testing/mocking)
        """
        self.llm_client = llm_client

    def _get_attr(self, obj: Any, key: str, default: Any = None) -> Any:
        """
        Get attribute from dict or dataclass using duck typing.
        
        Args:
            obj: Object to get attribute from (dict or dataclass)
            key: Attribute key
            default: Default value if not found
            
        Returns:
            Attribute value or default
        """
        if isinstance(obj, dict):
            return obj.get(key, default)
        elif hasattr(obj, key):
            return getattr(obj, key)
        else:
            return default

    def _build_prompt(
        self, 
        scene_text: str, 
        visual_beats: List[Union[Dict, VisualBeat]], 
        panel_specs: List[Union[Dict, PanelSpec]]
    ) -> str:
        """
        Build prompt for LLM detailed storyboard generation.
        
        Args:
            scene_text: The scene text to visualize
            visual_beats: List of visual beats for the scene
            panel_specs: Panel specifications (shot type, angle, focus)
            
        Returns:
            Prompt string for LLM
        """
        # Format visual beats
        beats_text = "\n".join([
            f"  Beat {self._get_attr(beat, 'number')}: {self._get_attr(beat, 'description', '')}"
            for beat in visual_beats
        ])
        
        # Format panel specs
        panels_text = "\n".join([
            f"  Panel {self._get_attr(spec, 'number')}: "
            f"Shot={self._get_attr(spec, 'shot_type', 'medium')}, "
            f"Angle={self._get_attr(spec, 'angle', 'eye-level')}, "
            f"Focus={self._get_attr(spec, 'focus', 'character')}"
            for spec in panel_specs
        ])
        
        prompt = f"""You are creating a detailed manga storyboard with comprehensive visual descriptions.

**SCENE TEXT:**
{scene_text}

**VISUAL BEATS (Key Visual Moments):**
{beats_text}

**PANEL SPECIFICATIONS:**
{panels_text}

**YOUR TASK:**
Generate detailed descriptions for each panel specified above. Each description should be 3-5 sentences and include comprehensive visual information.

For each panel, provide:

1. **Description (3-5 sentences)**:
   - Exact composition and what's visible in frame
   - Character positions, poses, and expressions
   - Background elements and environment details
   - Action or activity taking place
   - Specific visual details that would help an illustrator

2. **Mood**: Emotional atmosphere (e.g., "tense and foreboding", "warm and nostalgic", "mysterious and suspenseful", "energetic and dynamic")

3. **Lighting**: Light description including:
   - Source (natural, artificial, dramatic)
   - Quality (bright, dim, harsh, soft)
   - Direction (from window, backlit, side-lit)
   - Color temperature (warm, cool, neutral)

4. **Composition**: Visual arrangement including:
   - Framing (rule-of-thirds, central, symmetrical)
   - Depth (shallow, deep, layered)
   - Focus (sharp, shallow depth of field)
   - Movement lines or action flow

5. **Color Notes** (optional):
   - Color palette suggestions
   - Tints or color themes
   - Emphasis colors

6. **Dialogue**: Any spoken lines in this panel
   - Format: [{{"speaker": "Name", "text": "Quote"}}]
   - Empty array if no dialogue

7. **Narration**: Any narration text appearing in this panel
   - Can include internal monologue, exposition
   - Empty string if none

8. **Characters**: List of all characters visible in this panel

9. **Props**: Important objects, items, or elements visible
   - Include relevant background props
   - Exclude generic environment elements

10. **Reference Notes** (optional):
    - Style references
    - Inspiration sources
    - Technical notes for illustrator

**STORYBOARD OUTPUT FORMAT:**
Return JSON in this exact format:
{{
  "storyboard": [
    {{
      "panel_number": 1,
      "shot_type": "establishing",
      "angle": "eye-level",
      "description": "Wide shot of Basil's art studio bathed in warm afternoon light. Multiple easels stand throughout the room, each holding completed paintings. Sunlight streams through large windows on the left, casting long golden rectangles across the wooden floor. Basil stands at his main easel in the center, brush in hand, with his latest portrait partially visible.",
      "mood": "peaceful, artistic, contemplative",
      "lighting": "warm golden hour sunlight from large windows, soft shadows",
      "composition": "rule-of-thirds with Basil positioned at right intersection",
      "color_notes": "Warm color palette with emphasis on earth tones and golden yellow highlights",
      "dialogue": [],
      "narration": "",
      "characters": ["Basil Hallward"],
      "props": ["easel", "paintings", "windows", "palette", "brush"],
      "reference_notes": "Reference classical atelier interior photographs"
    }},
    {{
      "panel_number": 2,
      "shot_type": "medium",
      "angle": "eye-level",
      "description": "Medium shot focusing on Basil and Lord Henry in conversation. Basil's back is partially turned as he works on his portrait, while Lord Henry enters from the right side of frame. Lord Henry's elegant dark suit contrasts with Basil's paint-stained smock. The painting on the easel shows a young man with striking features, visible in the background.",
      "mood": "curious, sardonic, artistic tension",
      "lighting": "split lighting with window light on Basil, ambient on Lord Henry",
      "composition": "two-shot with balanced framing, painting in background creating depth",
      "color_notes": "Cool contrast between Lord Henry's dark attire and warm studio atmosphere",
      "dialogue": [
        {{"speaker": "Lord Henry", "text": "That's a remarkable piece of work, Basil."}}
      ],
      "narration": "",
      "characters": ["Basil Hallward", "Lord Henry Wotton"],
      "props": ["easel", "portrait painting", "gentleman's suit"],
      "reference_notes": "Study Victorian-era interior portraits"
    }}
  ],
  "characters_appearing": ["Basil Hallward", "Lord Henry Wotton"],
  "props_introduced": ["portrait painting"]
}}

**STYLE REQUIREMENTS:**
- Be VISUAL: Describe what can be SEEN, not internal thoughts or feelings
- Be SPECIFIC: Include exact details (colors, positions, expressions, textures)
- Be CONSISTENT: Maintain visual continuity across panels
- Be ACTIONABLE: Include details an illustrator can directly use
- MATCH the panel specifications (shot type and angle)
- Consider MANGA STYLE: Panel composition, reading flow, dramatic moments

Generate detailed descriptions for all {len(panel_specs)} panels specified."""
        return prompt

    def _extract_json_from_braces(self, text: str) -> Optional[str]:
        """
        Extract valid JSON by finding matching brace pairs.
        Handles nested braces by counting depth.
        
        Args:
            text: Text containing JSON
            
        Returns:
            Extracted JSON string or None if not found
        """
        start_idx = text.find('{')
        if start_idx == -1:
            return None
        
        depth = 0
        in_string = False
        escape_next = False
        
        for i, char in enumerate(text[start_idx:], start_idx):
            if escape_next:
                escape_next = False
                continue
            
            if char == '\\':
                escape_next = True
                continue
            
            if char == '"' and not escape_next:
                in_string = not in_string
                continue
            
            if in_string:
                continue
            
            if char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0:
                    return text[start_idx:i + 1]
        
        return None

    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse LLM response into structured storyboard data.
        
        Args:
            response_text: Raw LLM response
            
        Returns:
            Dictionary with storyboard data
        """
        # Clean up response text - remove common wrapper phrases
        cleaned_text = response_text.strip()
        
        # Try direct JSON parsing first
        try:
            data = json.loads(cleaned_text)
            return self._normalize_response(data)
        except json.JSONDecodeError:
            pass
        
        # Try to extract JSON from markdown code block
        code_block_match = re.search(
            r'```(?:json)?\s*', 
            response_text, 
            re.DOTALL
        )
        if code_block_match:
            # Find the content between code block markers
            start_pos = code_block_match.end()
            end_pattern = r'\s*```'
            end_match = re.search(end_pattern, response_text[start_pos:], re.DOTALL)
            
            if end_match:
                json_content = response_text[start_pos:start_pos + end_match.start()].strip()
                try:
                    data = json.loads(json_content)
                    return self._normalize_response(data)
                except json.JSONDecodeError:
                    pass
        
        # Try extracting JSON using brace matching
        json_str = self._extract_json_from_braces(response_text)
        if json_str:
            try:
                data = json.loads(json_str)
                return self._normalize_response(data)
            except json.JSONDecodeError:
                pass
        
        # Try to find JSON with "storyboard" key using brace matching
        storyboard_pattern = r'\{[^}]*"storyboard"[^}]*\}'
        json_match = re.search(storyboard_pattern, response_text, re.DOTALL)
        if json_match:
            try:
                json_str = self._extract_json_from_braces(json_match.group(0))
                if json_str:
                    data = json.loads(json_str)
                    return self._normalize_response(data)
            except json.JSONDecodeError:
                pass
        
        # Last resort: try to parse any JSON-like content
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        all_matches = re.findall(json_pattern, response_text, re.DOTALL)
        for match in all_matches:
            try:
                data = json.loads(match)
                return self._normalize_response(data)
            except json.JSONDecodeError:
                continue
        
        # Provide diagnostic information
        preview = response_text[:500] if len(response_text) > 500 else response_text
        raise ValueError(
            f"Failed to parse LLM response as JSON. "
            f"Response preview: {repr(preview)}"
        )

    def _normalize_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize response data to consistent format.
        
        Args:
            data: Raw parsed data
            
        Returns:
            Normalized data with storyboard array
        """
        # Handle various response formats
        if isinstance(data, list):
            # Response is a list directly
            return {"storyboard": data}
        
        if "storyboard" not in data:
            # Try to find panels array
            if "panels" in data:
                return {"storyboard": data["panels"]}
            # Wrap single panel
            if "panel_number" in data:
                return {"storyboard": [data]}
            raise ValueError("No storyboard or panels array found in response")
        
        return data

    def generate(
        self, 
        scene_text: str, 
        visual_beats: List[Union[Dict, VisualBeat]], 
        panel_specs: List[Union[Dict, PanelSpec]]
    ) -> List[DetailedPanel]:
        """
        Generate detailed storyboard panels for a scene.
        
        Args:
            scene_text: The scene text to visualize
            visual_beats: List of visual beats (can be dicts or VisualBeat objects)
            panel_specs: Panel specifications (can be dicts or PanelSpec objects)
            
        Returns:
            List of DetailedPanel objects
        """
        # Build prompt
        prompt = self._build_prompt(scene_text, visual_beats, panel_specs)
        
        # Call LLM or use mock
        if self.llm_client:
            response = self.llm_client.generate(prompt)
        else:
            response = self._mock_llm_response(panel_specs)
        
        # Parse response
        storyboard_data = self._parse_llm_response(response)
        panels_data = storyboard_data.get("storyboard", [])
        
        # Create DetailedPanel objects
        panels = []
        for panel_data in panels_data:
            panel = DetailedPanel(
                panel_number=panel_data.get("panel_number", len(panels) + 1),
                shot_type=panel_data.get("shot_type", "medium"),
                angle=panel_data.get("angle", "eye-level"),
                description=panel_data.get("description", ""),
                mood=panel_data.get("mood", "neutral"),
                lighting=panel_data.get("lighting", "natural"),
                composition=panel_data.get("composition", "balanced"),
                color_notes=panel_data.get("color_notes"),
                dialogue=panel_data.get("dialogue", []),
                narration=panel_data.get("narration", ""),
                characters=panel_data.get("characters", []),
                props=panel_data.get("props", []),
                reference_notes=panel_data.get("reference_notes")
            )
            panels.append(panel)
        
        return panels

    def generate_with_context(
        self, 
        scene_text: str,
        scene_id: str,
        scene_number: int,
        visual_beats: List[Union[Dict, VisualBeat]],
        panel_specs: List[Union[Dict, PanelSpec]],
        previous_panels: List[DetailedPanel] = None,
        characters_in_scene: List[str] = None
    ) -> Dict[str, Any]:
        """
        Generate detailed storyboard with full scene context.
        
        This method includes additional context like previous panels for
        continuity and character tracking across panels.
        
        Args:
            scene_text: The scene text to visualize
            scene_id: Scene identifier
            scene_number: Scene number
            visual_beats: List of visual beats
            panel_specs: Panel specifications
            previous_panels: Previous panels for continuity (optional)
            characters_in_scene: Characters appearing in this scene (optional)
            
        Returns:
            Dictionary with storyboard data and metadata
        """
        panels = self.generate(scene_text, visual_beats, panel_specs)
        
        # Track characters and props across panels
        all_characters = set()
        all_props = set()
        
        for panel in panels:
            for char in panel.characters:
                all_characters.add(char)
            for prop in panel.props:
                all_props.add(prop)
        
        return {
            "storyboard_id": f"sb-{scene_id}",
            "scene_id": scene_id,
            "scene_number": scene_number,
            "panel_count": len(panels),
            "panels": [panel.to_dict() for panel in panels],
            "characters_appearing": sorted(list(all_characters)),
            "props_appearing": sorted(list(all_props)),
            "created_with_continuity": previous_panels is not None
        }

    def _mock_llm_response(
        self, 
        panel_specs: List[Union[Dict, PanelSpec]]
    ) -> str:
        """
        Generate mock LLM response for testing.
        
        Args:
            panel_specs: Panel specifications
            
        Returns:
            Mock JSON response string
        """
        mock_panels = []
        
        for i, spec in enumerate(panel_specs):
            panel_num = self._get_attr(spec, 'number', i + 1)
            shot_type = self._get_attr(spec, 'shot_type', 'medium')
            angle = self._get_attr(spec, 'angle', 'eye-level')
            
            # Generate description based on shot type
            if shot_type == "establishing":
                description = (
                    f"Wide establishing shot showing the art studio interior. "
                    f"Natural light streams through large windows on the left wall. "
                    f"Multiple easels are positioned throughout the room, each holding completed paintings. "
                    f"The overall atmosphere suggests an artist's private sanctuary, filled with creative work. "
                    f"The camera angle is {angle}, providing a comprehensive view of the space."
                )
                mood = "peaceful, artistic, contemplative"
                lighting = "bright natural sunlight with soft shadows"
                composition = f"wide establishing shot with depth, {angle} angle perspective"
            elif shot_type == "close-up":
                description = (
                    f"Close-up shot focusing intently on the character's face. "
                    f"The expression reveals deep concentration mixed with subtle concern. "
                    f"Details like the slight furrow of eyebrows and focused eyes are visible. "
                    f"The background is intentionally blurred to emphasize the emotional state. "
                    f"Camera angle is {angle}, creating intimate visual contact with the subject."
                )
                mood = "intense, contemplative, vulnerable"
                lighting = "soft side-lighting emphasizing facial features"
                composition = f"tight close-up framing, {angle} angle for emotional impact"
            elif shot_type == "dialogue":
                description = (
                    f"Medium two-shot capturing the interaction between two characters. "
                    f"The composition balances both figures in the frame with slight emphasis on the speaker. "
                    f"Body language suggests contrasting personalities - one relaxed, one tense. "
                    f"The background includes elements of the studio, providing context without distraction. "
                    f"Shot type is {shot_type} from {angle} perspective."
                )
                mood = "engaging, sardonic, artistic tension"
                lighting = "balanced split lighting between characters"
                composition = "balanced two-shot, conversational framing"
            else:
                # Default medium shot
                description = (
                    f"Medium shot showing character action within the scene. "
                    f"The character is positioned slightly off-center, engaging with their environment. "
                    f"Expression and posture convey the intended emotional tone of the moment. "
                    f"Relevant props and background elements are visible but not distracting. "
                    f"Shot is captured from {angle} for natural visual flow."
                )
                mood = "neutral, focused"
                lighting = "natural ambient lighting"
                composition = f"balanced medium shot, {angle} camera angle"
            
            mock_panels.append({
                "panel_number": panel_num,
                "shot_type": shot_type,
                "angle": angle,
                "description": description,
                "mood": mood,
                "lighting": lighting,
                "composition": composition,
                "color_notes": "Warm earth tones with emphasis on natural colors",
                "dialogue": [],
                "narration": "",
                "characters": ["Basil Hallward", "Lord Henry Wotton"] if shot_type in ["dialogue", "establishing"] else ["Basil Hallward"],
                "props": ["easel", "paintings", "palette", "brush"] if i == 0 else ["easel", "portrait painting"],
                "reference_notes": f"Reference {shot_type} shot compositions in classical art"
            })
        
        response = {
            "storyboard": mock_panels
        }
        
        return json.dumps(response)


class MockLLMClient:
    """Mock LLM client for testing DetailedStoryboardGenerator."""
    
    def generate(self, prompt: str) -> str:
        """Return a mock storyboard response."""
        return '''{
  "storyboard": [
    {
      "panel_number": 1,
      "shot_type": "establishing",
      "angle": "eye-level",
      "description": "Wide establishing shot of Basil's art studio filled with afternoon light. Multiple easels hold completed paintings along the walls. Large windows on the left allow golden sunlight to stream across wooden floors. Basil stands at his main easel in the center, brush in hand, working on a portrait. The overall atmosphere conveys artistic sanctuary and creative solitude.",
      "mood": "peaceful, artistic, contemplative",
      "lighting": "warm golden hour sunlight from windows, soft natural shadows",
      "composition": "rule-of-thirds with Basil at right intersection point",
      "color_notes": "Warm earth tones, golden yellow highlights, rich browns",
      "dialogue": [],
      "narration": "",
      "characters": ["Basil Hallward"],
      "props": ["easel", "paintings", "windows", "palette", "brush", "portrait canvas"],
      "reference_notes": "Reference classical atelier interior photographs"
    },
    {
      "panel_number": 2,
      "shot_type": "medium",
      "angle": "eye-level",
      "description": "Medium shot of Basil and Lord Henry in conversation. Basil's back is partially turned toward the viewer as he works. Lord Henry enters from the right side of frame, elegant in dark Victorian attire. The painting on the easel shows a portrait of a young man with striking features, visible in the background. Their body language suggests an interesting dynamic between artist and observer.",
      "mood": "curious, sardonic, artistic tension",
      "lighting": "split lighting - window light illuminating Basil, ambient light on Lord Henry",
      "composition": "balanced two-shot with painting creating depth in background",
      "color_notes": "Cool contrast between Lord Henry's dark suit and warm studio tones",
      "dialogue": [
        {"speaker": "Lord Henry", "text": "That's a remarkable piece of work, Basil."}
      ],
      "narration": "",
      "characters": ["Basil Hallward", "Lord Henry Wotton"],
      "props": ["easel", "portrait painting", "gentleman's suit", "walking cane"],
      "reference_notes": "Study Victorian interior portraits with dual figures"
    },
    {
      "panel_number": 3,
      "shot_type": "close-up",
      "angle": "slightly-raised",
      "description": "Close-up of Basil's face showing subtle emotional reaction to Lord Henry's comment. His expression reveals both pride and slight unease. Paint-stained fingers grip the brush tightly. Eyes are slightly narrowed in thought. The background is softly blurred, focusing attention entirely on Basil's reaction. The lighting catches the slight tension in his jaw.",
      "mood": "subtly tense, proud, vulnerable",
      "lighting": "soft side-lighting from window, creating gentle shadows on face",
      "composition": "tight close-up centered on face, shallow depth of field",
      "color_notes": "Natural skin tones with slight pallor indicating concern",
      "dialogue": [],
      "narration": "",
      "characters": ["Basil Hallward"],
      "props": ["paintbrush", "paint-stained fingers"],
      "reference_notes": "Reference close-up portrait techniques for emotional subtlety"
    },
    {
      "panel_number": 4,
      "shot_type": "reaction",
      "angle": "eye-level",
      "description": "Medium shot capturing the moment of interaction. Lord Henry moves closer to examine the portrait while Basil watches with mixture of pride and apprehension. The composition allows both characters to be read clearly. The portrait on the easel is now more visible, showing a young man with extraordinary beauty. Their spatial relationship suggests Lord Henry's dominating personality.",
      "mood": "intense, observational, artistic appreciation",
      "lighting": "balanced ambient studio lighting with focus on portrait",
      "composition": "dynamic two-shot with portrait as focal point",
      "color_notes": "Rich contrast between portrait vibrancy and studio environment",
      "dialogue": [
        {"speaker": "Lord Henry", "text": "I should like to know him myself."}
      ],
      "narration": "",
      "characters": ["Basil Hallward", "Lord Henry Wotton"],
      "props": ["easel", "portrait painting", "two gentlemen"],
      "reference_notes": "Reference Victorian conversation pieces"
    }
  ],
  "characters_appearing": ["Basil Hallward", "Lord Henry Wotton"],
  "props_introduced": ["portrait painting", "paintbrush", "easel"]
}'''


def main():
    """Test DetailedStoryboardGenerator."""
    import sys
    sys.path.insert(0, '/home/clawd/projects/g-manga/src')
    sys.path.insert(0, '/home/clawd/projects/g-manga/src/stage3_story_planning')
    
    # Test data
    scene_text = """The studio was filled with the rich odour of roses."""

    visual_beats = [
        {"number": 1, "description": "Basil working in his studio"},
        {"number": 2, "description": "Lord Henry arrives and compliments the painting"},
        {"number": 3, "description": "Basil's nervous reaction to the portrait"}
    ]

    panel_specs = [
        {"number": 1, "shot_type": "establishing", "angle": "eye-level", "focus": "studio environment"},
        {"number": 2, "shot_type": "medium", "angle": "eye-level", "focus": "conversation"},
        {"number": 3, "shot_type": "close-up", "angle": "slightly-raised", "focus": "Basil's face"},
        {"number": 4, "shot_type": "reaction", "angle": "eye-level", "focus": "interaction"}
    ]

    # Test with mock LLM
    generator = DetailedStoryboardGenerator(llm_client=MockLLMClient())

    # Test simple generate
    panels = generator.generate(scene_text, visual_beats, panel_specs)
    
    print(f"Generated {len(panels)} detailed panels:")
    print()
    
    for i, panel in enumerate(panels):
        print(f"Panel {panel.panel_number}:")
        print(f"  Shot Type: {panel.shot_type}")
        print(f"  Angle: {panel.angle}")
        print(f"  Mood: {panel.mood}")
        print(f"  Lighting: {panel.lighting}")
        print(f"  Composition: {panel.composition}")
        print(f"  Description: {panel.description[:150]}...")
        print(f"  Characters: {', '.join(panel.characters)}")
        print(f"  Props: {', '.join(panel.props)}")
        if panel.color_notes:
            print(f"  Color Notes: {panel.color_notes}")
        print()
    
    # Test generate_with_context
    print("=" * 60)
    print("Testing generate_with_context:")
    print("=" * 60)
    print()
    
    context_result = generator.generate_with_context(
        scene_text=scene_text,
        scene_id="scene-1-1",
        scene_number=1,
        visual_beats=visual_beats,
        panel_specs=panel_specs
    )
    
    print(f"Storyboard ID: {context_result['storyboard_id']}")
    print(f"Scene: {context_result['scene_id']}")
    print(f"Panel Count: {context_result['panel_count']}")
    print(f"Characters: {', '.join(context_result['characters_appearing'])}")
    print(f"Props: {', '.join(context_result['props_appearing'])}")


if __name__ == "__main__":
    main()
