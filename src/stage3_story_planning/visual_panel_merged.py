"""
Visual Panel Merged - Stage 3.1.1
Combines Visual Beats + Panel Specifications into a single LLM call.
Converts prose scene text directly to visual beats with detailed panel specs.
"""

import json
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class PanelSpec:
    """
    Individual panel specification within a beat.
    
    Attributes:
        panel_number: Panel identifier (e.g., "1.1", "1.2", "2.1")
        shot_type: Shot type (ECU, CU, MS, FS, WS, EWS)
        angle: Camera angle (Eye-Level, High, Low, Dutch, etc.)
        focus: Primary focus of the panel
        text_type: Type of text (dialogue, narration, sound_effect, none)
        text_content: The actual text content for the panel
    """
    panel_number: str
    shot_type: str
    angle: str
    focus: str
    text_type: str = "none"
    text_content: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "panel_number": self.panel_number,
            "shot_type": self.shot_type,
            "angle": self.angle,
            "focus": self.focus,
            "text_type": self.text_type,
            "text_content": self.text_content
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PanelSpec":
        """Create from dictionary."""
        return cls(
            panel_number=data.get("panel_number", ""),
            shot_type=data.get("shot_type", ""),
            angle=data.get("angle", ""),
            focus=data.get("focus", ""),
            text_type=data.get("text_type", "none"),
            text_content=data.get("text_content", "")
        )


@dataclass
class BeatWithPanels:
    """
    Visual beat with embedded panel specifications.
    
    Attributes:
        scene_id: ID of the scene this beat belongs to
        beat_number: Sequential beat number (1, 2, 3...)
        description: Description of the visual beat
        priority: Priority level (1=Critical, 5=Low)
        visual_focus: What to emphasize (action, expression, dialogue, etc.)
        show: What to show visually
        tell: What to convey through text/narration
        panels: List of PanelSpec objects for this beat
    """
    scene_id: str
    beat_number: int
    description: str
    priority: int = 3
    visual_focus: str = "action"
    show: str = ""
    tell: str = ""
    panels: List[PanelSpec] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "scene_id": self.scene_id,
            "beat_number": self.beat_number,
            "description": self.description,
            "priority": self.priority,
            "visual_focus": self.visual_focus,
            "show": self.show,
            "tell": self.tell,
            "panels": [p.to_dict() for p in self.panels]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BeatWithPanels":
        """Create from dictionary."""
        panels = [
            PanelSpec.from_dict(p) if isinstance(p, dict) else p
            for p in data.get("panels", [])
        ]
        return cls(
            beat_number=data.get("beat_number", 0),
            description=data.get("description", ""),
            priority=data.get("priority", 3),
            visual_focus=data.get("visual_focus", "action"),
            show=data.get("show", ""),
            tell=data.get("tell", ""),
            panels=panels
        )


# =============================================================================
# Valid Constants
# =============================================================================

# Shot types for panels
SHOT_TYPES = ["ECU", "CU", "MS", "FS", "WS", "EWS"]

# Camera angles
CAMERA_ANGLES = [
    "Eye-Level", "High", "Low", "Dutch", 
    "Bird's Eye", "Worm's Eye", "Over-Shoulder", "POV"
]

# Text types
TEXT_TYPES = ["dialogue", "narration", "sound_effect", "caption", "none"]

# Pacing options
PACING_OPTIONS = ["Slow", "Normal", "Fast", "Action"]

# Visual focus options
VISUAL_FOCUS_OPTIONS = [
    "action", "dialogue", "expression", "detail", 
    "environment", "establishing", "reaction"
]

# Priority scale
PRIORITY_SCALE = [1, 2, 3, 4, 5]


# =============================================================================
# VisualPanelMerged Class
# =============================================================================

class VisualPanelMerged:
    """
    Combined Visual Beats + Panel Specifications.
    
    Single LLM call to convert scene text to:
    - Visual beats (4-8 per scene)
    - Show vs Tell per beat
    - Panel breakdown per beat with shot types and camera angles
    - Scene-level summary (pacing, total panels)
    
    Merges Stage 3.1.1 (Visual Adaptation) and Stage 3.1.2 (Panel Breakdown)
    into one optimized workflow.
    """
    
    def __init__(self, llm_client=None):
        """
        Initialize VisualPanelMerged.
        
        Args:
            llm_client: Optional LLM client for API calls (default: None, uses mock)
        """
        self.llm_client = llm_client
    
    # =========================================================================
    # Prompt Building
    # =========================================================================
    
    def _build_prompt(self, scene_text: str, scene_id: str, scene_number: int) -> str:
        """
        Build comprehensive prompt for LLM to generate visual beats with panel specs.
        
        Args:
            scene_text: The scene prose text
            scene_id: Unique scene identifier
            scene_number: Sequential scene number
            
        Returns:
            Complete prompt string for LLM
        """
        prompt = f"""You are a manga storyboard artist converting prose scenes into visual storytelling.

Your task: Analyze the scene and create a complete visual breakdown with:
1. Visual beats (4-8) capturing key moments
2. Show vs Tell strategy per beat
3. Panel breakdown per beat with shot types and camera angles
4. Scene-level pacing and total panel count

================================================================================
**SCENE CONTEXT**
================================================================================
Scene ID: {scene_id}
Scene Number: {scene_number}

**SCENE TEXT:**
{scene_text}

================================================================================
**VISUAL BEATS (4-8 per scene)**
================================================================================
Each beat represents a key moment. For each beat:
- beat_number: Sequential number (1, 2, 3...)
- description: What happens in this beat
- priority: 1=Critical (essential), 2=High (important), 3=Medium, 4=Low, 5=Minimal
- visual_focus: action, dialogue, expression, detail, environment, establishing, reaction
- show: What to visualize (art), be specific about poses, expressions, actions
- tell: What text to include (dialogue, narration, captions) - keep minimal

================================================================================
**SHOW VS TELL GUIDELINES**
================================================================================
- SHOW: Action, facial expressions, gestures, body language, environment details
- TELL: Internal monologue, backstory, atmosphere that can't be shown visually
- Prioritize SHOW (visuals are the strength of manga)
- Use TELL sparingly for internal thoughts or necessary context

================================================================================
**PANEL BREAKDOWN PER BEAT**
================================================================================
Each beat contains 1-3 panels. For each panel:
- panel_number: Beat-based numbering (e.g., 1.1, 1.2, 2.1, 3.1, 3.2, 3.3)
- shot_type: ECU (Extreme Close-Up), CU (Close-Up), MS (Medium Shot), 
             FS (Full Shot), WS (Wide Shot), EWS (Extreme Wide Shot)
- angle: Eye-Level, High, Low, Dutch, Bird's Eye, Worm's Eye, Over-Shoulder, POV
- focus: Primary subject focus
- text_type: dialogue, narration, sound_effect, caption, none
- text_content: Actual text (keep dialogue natural, narration concise)

================================================================================
**SHOT TYPE GUIDES**
================================================================================
- ECU: Eyes, mouth, hands - maximum emotional detail
- CU: Head and shoulders - character expressions, reactions
- MS: Waist up - balance of character and action
- FS: Full body - character movement, gestures
- WS: Character with environment - establishing context
- EWS: Full scene/location - setting atmosphere

================================================================================
**CAMERA ANGLE EFFECTS**
================================================================================
- Eye-Level: Neutral, standard perspective
- High (Bird's Eye): Looking down - character looks small/vulnerable
- Low (Worm's Eye): Looking up - character looks powerful/imposing
- Dutch: Tilted - unease, disorientation, tension
- Over-Shoulder: Behind character - conversation, looking at subject
- POV: Character's eyes - reader experiences through character

================================================================================
**PACING GUIDELINES**
================================================================================
Determine overall scene pacing:
- Slow: Atmospheric, contemplative, emotional moments (fewer panels, more detail)
- Normal: Standard storytelling flow
- Fast: Quick exchanges, building tension
- Action: Combat, chase, high-energy sequences (more panels for dynamism)

================================================================================
**OUTPUT FORMAT - EXACT JSON**
================================================================================
Return ONLY valid JSON in this format (no markdown, no explanation):

{{
  "scene_summary": {{
    "scene_id": "{scene_id}",
    "scene_number": {scene_number},
    "scene_pacing": "Normal",
    "total_panels": 12
  }},
  "visual_beats": [
    {{
      "beat_number": 1,
      "description": "Basil prepares his painting tools while Lord Henry observes",
      "priority": 2,
      "visual_focus": "action",
      "show": "Basil's hands carefully mixing paints on palette, focused expression, Lord Henry leaning against doorframe with knowing smile",
      "tell": "",
      "panels": [
        {{
          "panel_number": "1.1",
          "shot_type": "CU",
          "angle": "Eye-Level",
          "focus": "Basil's hands mixing paints",
          "text_type": "none",
          "text_content": ""
        }},
        {{
          "panel_number": "1.2",
          "shot_type": "MS",
          "angle": "Over-Shoulder",
          "focus": "Basil at work, Lord Henry watching",
          "text_type": "dialogue",
          "text_content": "LORD HENRY: Every portrait is a crime, Basil. A crime of dedication."
        }}
      ]
    }}
  ]
}}

================================================================================
**VALIDATION RULES**
================================================================================
- Beat numbers: 1, 2, 3... (sequential)
- Panel numbers: beat.panel (1.1, 1.2, 2.1, 3.1...)
- Priority: 1-5 (1=Critical, 5=Minimal)
- Shot types: ECU, CU, MS, FS, WS, EWS
- Angles: Eye-Level, High, Low, Dutch, Bird's Eye, Worm's Eye, Over-Shoulder, POV
- Text types: dialogue, narration, sound_effect, caption, none
- Total panels: Typically 8-16 depending on scene complexity
- Panels per beat: 1-3 panels
- Beats per scene: 4-8 beats

================================================================================
Begin your analysis and return the complete visual breakdown now."""
        return prompt
    
    # =========================================================================
    # Response Parsing
    # =========================================================================
    
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
        Parse LLM response into structured data.
        
        Args:
            response_text: Raw LLM response text
            
        Returns:
            Parsed dictionary with scene_summary and visual_beats
            
        Raises:
            ValueError: If JSON cannot be parsed
        """
        # Try direct JSON parsing first
        try:
            data = json.loads(response_text)
            return data
        except json.JSONDecodeError:
            pass
        
        # Try to extract JSON using brace matching (most robust)
        json_str = self._extract_json_from_braces(response_text)
        if json_str:
            try:
                data = json.loads(json_str)
                return data
            except json.JSONDecodeError:
                pass
        
        # Try to extract JSON from markdown code block
        json_match = re.search(
            r'```(?:json)?\s*(\{.*?\})\s*```', 
            response_text, 
            re.DOTALL
        )
        if json_match:
            try:
                data = json.loads(json_match.group(1))
                return data
            except json.JSONDecodeError:
                pass
        
        # Try to find JSON-like structure with visual_beats
        json_match = re.search(
            r'\{.*?"scene_summary".*?".*?".*?"visual_beats".*?\[.*?\].*?\}',
            response_text,
            re.DOTALL
        )
        if json_match:
            try:
                data = json.loads(json_match.group(0))
                return data
            except json.JSONDecodeError:
                pass
        
        # Last resort: try any JSON object with visual_beats
        json_match = re.search(r'\{[^{}]*"visual_beats"[^{}]*\}', response_text, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group(0))
                return data
            except json.JSONDecodeError:
                pass
        
        raise ValueError(
            f"Failed to parse LLM response as JSON. Response:\n{response_text[:500]}..."
        )
    
    def _validate_beat_data(self, beat_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and normalize beat data with duck typing support.
        
        Args:
            beat_data: Beat data (dict or object with attributes)
            
        Returns:
            Normalized dictionary
            
        Raises:
            ValueError: If required fields are missing
        """
        # Handle duck typing - convert to dict if needed
        if hasattr(beat_data, 'to_dict'):
            # It's a BeatWithPanels or similar object
            beat_dict = beat_data.to_dict()
        elif hasattr(beat_data, '__dict__'):
            # It's an object with attributes
            beat_dict = vars(beat_data)
        elif isinstance(beat_data, dict):
            beat_dict = beat_data.copy()
        else:
            beat_dict = {"description": str(beat_data)}
        
        # Ensure required fields
        if "beat_number" not in beat_dict:
            raise ValueError(f"Missing 'beat_number' in beat data: {beat_data}")
        
        if "description" not in beat_dict:
            raise ValueError(f"Missing 'description' in beat data: {beat_data}")
        
        # Set defaults
        beat_dict.setdefault("priority", 3)
        beat_dict.setdefault("visual_focus", "action")
        beat_dict.setdefault("show", "")
        beat_dict.setdefault("tell", "")
        beat_dict.setdefault("panels", [])
        
        return beat_dict
    
    def _validate_panel_data(self, panel_data: Dict[str, Any]) -> PanelSpec:
        """
        Validate and normalize panel data.
        
        Args:
            panel_data: Panel data (dict or object)
            
        Returns:
            PanelSpec object
            
        Raises:
            ValueError: If required fields are missing or invalid
        """
        # Handle duck typing
        if hasattr(panel_data, 'to_dict'):
            panel_dict = panel_data.to_dict()
        elif hasattr(panel_data, '__dict__'):
            panel_dict = vars(panel_data)
        elif isinstance(panel_data, dict):
            panel_dict = panel_data.copy()
        else:
            raise ValueError(f"Invalid panel data type: {type(panel_data)}")
        
        # Ensure required fields
        if "panel_number" not in panel_dict:
            raise ValueError(f"Missing 'panel_number' in panel: {panel_data}")
        
        if "shot_type" not in panel_dict:
            raise ValueError(f"Missing 'shot_type' in panel: {panel_data}")
        
        if "angle" not in panel_dict:
            raise ValueError(f"Missing 'angle' in panel: {panel_data}")
        
        if "focus" not in panel_dict:
            raise ValueError(f"Missing 'focus' in panel: {panel_data}")
        
        # Set defaults
        panel_dict.setdefault("text_type", "none")
        panel_dict.setdefault("text_content", "")
        
        return PanelSpec(
            panel_number=panel_dict["panel_number"],
            shot_type=panel_dict["shot_type"],
            angle=panel_dict["angle"],
            focus=panel_dict["focus"],
            text_type=panel_dict["text_type"],
            text_content=panel_dict["text_content"]
        )
    
    # =========================================================================
    # Main Adaptation Method
    # =========================================================================
    
    def adapt_scene(
        self, 
        scene_text: str, 
        scene_id: str, 
        scene_number: int
    ) -> List[BeatWithPanels]:
        """
        Adapt a scene into visual beats with panel specifications.
        
        This is the main entry point - it:
        1. Builds a comprehensive prompt from the scene text
        2. Calls the LLM (or mock)
        3. Parses and validates the response
        4. Returns BeatWithPanels objects
        
        Args:
            scene_text: The prose scene text to adapt
            scene_id: Unique identifier for this scene
            scene_number: Sequential scene number
            
        Returns:
            List of BeatWithPanels objects, each containing PanelSpec objects
            
        Raises:
            ValueError: If parsing fails or required data is missing
        """
        # Build prompt
        prompt = self._build_prompt(scene_text, scene_id, scene_number)
        
        # Call LLM or use mock
        if self.llm_client:
            response = self.llm_client.generate(prompt)
        else:
            response = self._mock_llm_response(scene_text, scene_id, scene_number)
        
        # Parse response
        parsed_data = self._parse_llm_response(response)
        
        # Extract scene summary (optional, for logging/metadata)
        scene_summary = parsed_data.get("scene_summary", {})
        scene_pacing = scene_summary.get("scene_pacing", "Normal")
        total_panels = scene_summary.get("total_panels", 0)
        
        # Validate scene summary
        if scene_summary:
            # Ensure scene_id and scene_number match
            if scene_summary.get("scene_id") != scene_id:
                scene_summary["scene_id"] = scene_id
            if scene_summary.get("scene_number") != scene_number:
                scene_summary["scene_number"] = scene_number
        
        # Extract and validate beats
        beats_data = parsed_data.get("visual_beats", [])
        if not beats_data:
            raise ValueError("No visual beats found in LLM response")
        
        # Convert to BeatWithPanels objects
        beats_with_panels = []
        for beat_data in beats_data:
            beat_dict = self._validate_beat_data(beat_data)
            
            # Convert panels to PanelSpec objects
            panels = []
            for panel_data in beat_dict.get("panels", []):
                try:
                    panel = self._validate_panel_data(panel_data)
                    panels.append(panel)
                except ValueError as e:
                    # Skip invalid panels but log warning
                    import warnings
                    warnings.warn(f"Skipping invalid panel: {e}")
            
            beat = BeatWithPanels(
                scene_id=scene_id,
                beat_number=beat_dict["beat_number"],
                description=beat_dict["description"],
                priority=beat_dict["priority"],
                visual_focus=beat_dict["visual_focus"],
                show=beat_dict["show"],
                tell=beat_dict["tell"],
                panels=panels
            )
            beats_with_panels.append(beat)
        
        return beats_with_panels
    
    # =========================================================================
    # Mock LLM Response (for testing)
    # =========================================================================
    
    def _mock_llm_response(
        self, 
        scene_text: str, 
        scene_id: str, 
        scene_number: int
    ) -> str:
        """
        Generate mock LLM response for testing.
        
        Args:
            scene_text: Scene text for context
            scene_id: Scene ID
            scene_number: Scene number
            
        Returns:
            Mock JSON response string
        """
        # Extract first lines for context
        first_lines = scene_text.strip().split('\n')[:3]
        context = ' '.join(first_lines)
        
        # Determine pacing based on text length
        text_length = len(scene_text)
        if text_length > 500:
            scene_pacing = "Normal"
            total_panels = 10
        elif "action" in context.lower() or "run" in context.lower() or "fight" in context.lower():
            scene_pacing = "Action"
            total_panels = 14
        elif "silence" in context.lower() or "quiet" in context.lower() or "thought" in context.lower():
            scene_pacing = "Slow"
            total_panels = 8
        else:
            scene_pacing = "Normal"
            total_panels = 10
        
        mock_response = {
            "scene_summary": {
                "scene_id": scene_id,
                "scene_number": scene_number,
                "scene_pacing": scene_pacing,
                "total_panels": total_panels
            },
            "visual_beats": [
                {
                    "beat_number": 1,
                    "description": f"Opening establishing shot: {context[:100]}...",
                    "priority": 1,
                    "visual_focus": "establishing",
                    "show": "Wide view of the setting, atmospheric mood established",
                    "tell": "",
                    "panels": [
                        {
                            "panel_number": "1.1",
                            "shot_type": "WS",
                            "angle": "Bird's Eye",
                            "focus": "Environment/setting",
                            "text_type": "caption",
                            "text_content": "Setting the scene..."
                        }
                    ]
                },
                {
                    "beat_number": 2,
                    "description": "Main character introduction or action",
                    "priority": 2,
                    "visual_focus": "action",
                    "show": "Character in dynamic pose, entering frame",
                    "tell": "",
                    "panels": [
                        {
                            "panel_number": "2.1",
                            "shot_type": "MS",
                            "angle": "Eye-Level",
                            "focus": "Character",
                            "text_type": "none",
                            "text_content": ""
                        }
                    ]
                },
                {
                    "beat_number": 3,
                    "description": "Key dialogue or interaction",
                    "priority": 2,
                    "visual_focus": "dialogue",
                    "show": "Two characters facing each other, expressions visible",
                    "tell": "",
                    "panels": [
                        {
                            "panel_number": "3.1",
                            "shot_type": "CU",
                            "angle": "Over-Shoulder",
                            "focus": "Speaker character",
                            "text_type": "dialogue",
                            "text_content": "Dialogue placeholder..."
                        },
                        {
                            "panel_number": "3.2",
                            "shot_type": "CU",
                            "angle": "Eye-Level",
                            "focus": "Listener reaction",
                            "text_type": "none",
                            "text_content": ""
                        }
                    ]
                },
                {
                    "beat_number": 4,
                    "description": "Scene culmination or transition",
                    "priority": 2,
                    "visual_focus": "expression",
                    "show": "Character emotional response",
                    "tell": "",
                    "panels": [
                        {
                            "panel_number": "4.1",
                            "shot_type": "ECU",
                            "angle": "Eye-Level",
                            "focus": "Face/expression",
                            "text_type": "narration",
                            "text_content": "Internal thought..."
                        }
                    ]
                },
                {
                    "beat_number": 5,
                    "description": "Closing beat or cliffhanger",
                    "priority": 3,
                    "visual_focus": "reaction",
                    "show": "Wide shot showing aftermath or transition",
                    "tell": "",
                    "panels": [
                        {
                            "panel_number": "5.1",
                            "shot_type": "WS",
                            "angle": "Low",
                            "focus": "Scene context",
                            "text_type": "none",
                            "text_content": ""
                        }
                    ]
                }
            ]
        }
        
        return json.dumps(mock_response, indent=2)
    
    # =========================================================================
    # Utility Methods
    # =========================================================================
    
    def beats_to_json(self, beats: List[BeatWithPanels]) -> str:
        """
        Convert beats to JSON string.
        
        Args:
            beats: List of BeatWithPanels objects
            
        Returns:
            JSON string representation
        """
        data = {
            "visual_beats": [beat.to_dict() for beat in beats]
        }
        return json.dumps(data, indent=2)
    
    def beats_from_json(self, json_str: str) -> List[BeatWithPanels]:
        """
        Parse beats from JSON string.
        
        Args:
            json_str: JSON string
            
        Returns:
            List of BeatWithPanels objects
        """
        data = json.loads(json_str)
        beats_data = data.get("visual_beats", [])
        return [BeatWithPanels.from_dict(b) for b in beats_data]


# =============================================================================
# Mock LLM Client for Testing
# =============================================================================

class MockLLMClient:
    """Mock LLM client for testing VisualPanelMerged."""
    
    def generate(self, prompt: str) -> str:
        """
        Generate mock response.
        
        Args:
            prompt: The prompt text
            
        Returns:
            Mock JSON response
        """
        return '''{
  "scene_summary": {
    "scene_id": "scene-1",
    "scene_number": 1,
    "scene_pacing": "Normal",
    "total_panels": 12
  },
  "visual_beats": [
    {
      "beat_number": 1,
      "description": "Basil stands before his easel, paintbrush in hand, contemplating his portrait",
      "priority": 1,
      "visual_focus": "expression",
      "show": "Basil's intense focus on canvas, slight furrow in brow, natural light from window",
      "tell": "",
      "panels": [
        {
          "panel_number": "1.1",
          "shot_type": "CU",
          "angle": "Eye-Level",
          "focus": "Basil's face",
          "text_type": "none",
          "text_content": ""
        }
      ]
    },
    {
      "beat_number": 2,
      "description": "Lord Henry enters the studio with his characteristic knowing smile",
      "priority": 2,
      "visual_focus": "action",
      "show": "Lord Henry sweeping into frame, elegant posture, confident stride",
      "tell": "",
      "panels": [
        {
          "panel_number": "2.1",
          "shot_type": "WS",
          "angle": "Low",
          "focus": "Lord Henry entering",
          "text_type": "none",
          "text_content": ""
        },
        {
          "panel_number": "2.2",
          "shot_type": "MS",
          "angle": "Over-Shoulder",
          "focus": "Lord Henry's face",
          "text_type": "dialogue",
          "text_content": "LORD HENRY: I have come to see your latest masterpiece, Basil."
        }
      ]
    },
    {
      "beat_number": 3,
      "description": "The two friends discuss the portrait of Dorian Gray",
      "priority": 2,
      "visual_focus": "dialogue",
      "show": "Both characters in frame, contrast in their postures - Basil serious, Henry languid",
      "tell": "",
      "panels": [
        {
          "panel_number": "3.1",
          "shot_type": "MS",
          "angle": "Eye-Level",
          "focus": "Both characters",
          "text_type": "dialogue",
          "text_content": "BASIL: It is not finished, Henry. There is something about him I cannot capture."
        },
        {
          "panel_number": "3.2",
          "shot_type": "CU",
          "angle": "High",
          "focus": "Dorian's portrait visible in background",
          "text_type": "none",
          "text_content": ""
        }
      ]
    },
    {
      "beat_number": 4,
      "description": "Lord Henry examines the portrait closely, fascinated",
      "priority": 2,
      "visual_focus": "detail",
      "show": "Lord Henry leaning toward portrait, intense interest, portrait taking center frame",
      "tell": "",
      "panels": [
        {
          "panel_number": "4.1",
          "shot_type": "ECU",
          "angle": "Bird's Eye",
          "focus": "Portrait details",
          "text_type": "caption",
          "text_content": "The portrait seemed somehow different..."
        }
      ]
    },
    {
      "beat_number": 5,
      "description": "Lord Henry's provocative theory about the portrait",
      "priority": 3,
      "visual_focus": "expression",
      "show": "Lord Henry gesturing dramatically, Basil watching warily",
      "tell": "I believe that if this portrait were to change, it would be you who would suffer.",
      "panels": [
        {
          "panel_number": "5.1",
          "shot_type": "CU",
          "angle": "Dutch",
          "focus": "Lord Henry's face",
          "text_type": "dialogue",
          "text_content": "LORD HENRY: The mystery of change... that would be a crime worth committing."
        }
      ]
    },
    {
      "beat_number": 6,
      "description": "Scene ends with tension and implication",
      "priority": 3,
      "visual_focus": "reaction",
      "show": "Basil's uneasy expression, portrait looming in background",
      "tell": "",
      "panels": [
        {
          "panel_number": "6.1",
          "shot_type": "WS",
          "angle": "Eye-Level",
          "focus": "Full studio scene",
          "text_type": "none",
          "text_content": ""
        }
      ]
    }
  ]
}'''


# =============================================================================
# Main Test
# =============================================================================

def main():
    """Test VisualPanelMerged with sample scene."""
    
    # Sample scene text
    sample_scene = """The studio was filled with the rich odour of roses, and when the light summer wind stirred amongst the trees of the garden, there came through the open door the heavy scent of the lilac, or the more delicate perfume of the pink-flowering thorn.

Basil Hallward was bending over his palette, mixing paints with careful attention. The afternoon light fell across his shoulder, illuminating the canvas where a young man's portrait was taking shape.

Lord Henry Wotton swept into the studio with his characteristic languid grace. "I have come to see your latest masterpiece, Basil," he said, settling into a chair.

Basil turned, brush still in hand. "It is not finished, Henry. There is something about him I cannot capture."

Lord Henry rose and approached the portrait. The young man in the painting was beautiful - dangerously so. "Perhaps it is because you have put too much of yourself into it," he suggested, his dark eyes gleaming. "Every portrait is a crime, Basil. A crime of dedication." He gestured dramatically. "But imagine if this portrait were to change over time, while the subject remained forever young. Would that not be a terrible thing?"

Basil frowned. "What do you mean, Henry?"

"I mean," Lord Henry said slowly, "that beauty is a form of genius - it is beyond criticism. And if this young man were to become corrupt, would the portrait bear the weight of his sins? Would it show what he truly is, while his face remained innocent?" He smiled that knowing smile. "That would be a mystery worth exploring."

The studio fell silent. Outside, a bird sang. The roses perfumed the air. But between the two men, something had shifted - a seed of doubt had been planted, a dangerous thought let loose upon the world."""

    # Test with mock LLM
    print("=" * 80)
    print("Testing VisualPanelMerged")
    print("=" * 80)
    
    adapter = VisualPanelMerged(llm_client=MockLLMClient())
    
    try:
        beats = adapter.adapt_scene(sample_scene, "scene-1", 1)
        
        print(f"\n✓ Successfully adapted scene into {len(beats)} visual beats")
        print(f"  Total panels: {sum(len(b.panels) for b in beats)}")
        
        for beat in beats:
            print(f"\n--- Beat {beat.beat_number} ---")
            print(f"  Description: {beat.description[:80]}...")
            print(f"  Priority: {beat.priority} | Focus: {beat.visual_focus}")
            print(f"  Show: {beat.show[:60]}..." if beat.show else "  Show: (none)")
            print(f"  Panels ({len(beat.panels)}):")
            for panel in beat.panels:
                print(f"    {panel.panel_number}: {panel.shot_type} | {panel.angle} | {panel.focus}")
                if panel.text_type != "none":
                    print(f"      [{panel.text_type}]: {panel.text_content[:50]}...")
        
        # Test JSON conversion
        json_output = adapter.beats_to_json(beats)
        print(f"\n✓ JSON output length: {len(json_output)} chars")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("Test complete")
    print("=" * 80)


if __name__ == "__main__":
    main()
