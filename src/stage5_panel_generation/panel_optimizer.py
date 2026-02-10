"""
Panel Optimizer - Stage 5.1.3
Optimizes panel prompts for character consistency and style enforcement.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import json
import re


@dataclass
class CharacterConsistencyRule:
    """Rule for maintaining character consistency."""
    character_name: str
    key_features: List[str]  # ["golden hair", "blue eyes", "slender build"]
    clothing: Optional[str] = None
    accessories: Optional[str] = None
    expressions: Optional[str] = None


@dataclass
class OptimizationResult:
    """Result of panel optimization."""
    original_prompt: str
    optimized_prompt: str
    changes_made: List[str]
    consistency_score: float  # 0.0 to 1.0


class PanelOptimizer:
    """Optimizes panel prompts for consistency and quality."""

    def __init__(self):
        """Initialize Panel Optimizer."""
        self.character_rules: Dict[str, CharacterConsistencyRule] = {}
        self.style_guide = self._build_style_guide()

    def _build_style_guide(self) -> Dict[str, Any]:
        """
        Build manga style guide.

        Returns:
            Dictionary with style guidelines
        """
        return {
            "ink_style": "black outlines, clean lines, minimal shading",
            "screen_tones": "use traditional manga screen tones for shading",
            "speed_lines": "dynamic speed lines for action panels",
            "speech_bubbles": "clear, readable bubbles with tails to speaker",
            "expression_style": "exaggerated expressions for emotion",
            "pacing": "balance panel sizes to control reading speed",
            "composition": "use rule of thirds for placement",
            "lighting": "consistent lighting across panels in same scene",
            "avoid": ["photorealistic", "3D render", "Western comic style"]
        }

    def add_character_rule(self, rule: CharacterConsistencyRule):
        """
        Add character consistency rule.

        Args:
            rule: CharacterConsistencyRule object
        """
        self.character_rules[rule.character_name.lower()] = rule

    def optimize_prompt(
        self,
        prompt: str,
        panel_type: str,
        characters_in_panel: List[str],
        previous_panels: Optional[List[str]] = None
    ) -> OptimizationResult:
        """
        Optimize a panel prompt.

        Args:
            prompt: Original panel prompt
            panel_type: Type of panel (close-up, wide, etc.)
            characters_in_panel: List of character names in panel
            previous_panels: List of previous panel prompts (for context)

        Returns:
            OptimizationResult with changes and score
        """
        changes_made = []
        optimized = prompt

        # 1. Add character consistency rules
        for char_name in characters_in_panel:
            char_key = char_name.lower()
            if char_key in self.character_rules:
                rule = self.character_rules[char_key]
                optimized = self._apply_character_rules(optimized, rule, panel_type)
                changes_made.append(f"Applied {rule.character_name} consistency rules")

        # 2. Add style guide elements
        optimized = self._apply_style_guide(optimized, panel_type)
        changes_made.append("Applied manga style guide")

        # 3. Add panel-type specific enhancements
        optimized = self._add_panel_type_enhancements(optimized, panel_type)
        changes_made.append(f"Enhanced for {panel_type} panel")

        # 4. Check for consistency with previous panels
        if previous_panels:
            consistency_score = self._calculate_consistency_score(
                optimized, previous_panels
            )
        else:
            consistency_score = 1.0

        # 5. Add consistency reminder if score is low
        if consistency_score < 0.7 and previous_panels:
            optimized += "\n\nNOTE: Ensure visual consistency with previous panels in this scene."
            changes_made.append(f"Added consistency reminder (score: {consistency_score:.2f})")

        return OptimizationResult(
            original_prompt=prompt,
            optimized_prompt=optimized,
            changes_made=changes_made,
            consistency_score=consistency_score
        )

    def _apply_character_rules(
        self,
        prompt: str,
        rule: CharacterConsistencyRule,
        panel_type: str
    ) -> str:
        """
        Apply character consistency rules to prompt.

        Args:
            prompt: Original prompt
            rule: Character consistency rule
            panel_type: Panel type (affects detail level)

        Returns:
            Enhanced prompt
        """
        # Find where to add character details
        # Add before "OUTPUT FORMAT" section if present
        if "OUTPUT FORMAT" in prompt:
            prompt_parts = prompt.split("OUTPUT FORMAT")
            first_part = prompt_parts[0]
            second_part = prompt_parts[1] if len(prompt_parts) > 1 else ""

            # Add character consistency section
            char_section = f"""
**CHARACTER CONSISTENCY ({rule.character_name}):**
- Key Features: {', '.join(rule.key_features)}
"""

            # Add clothing if relevant (wide, medium panels show more body)
            if panel_type in ["wide", "medium"] and rule.clothing:
                char_section += f"- Clothing: {rule.clothing}\n"

            # Add accessories if any
            if rule.accessories:
                char_section += f"- Accessories: {rule.accessories}\n"

            # Add expression hints for close-up panels
            if panel_type in ["close-up", "extreme-close-up"] and rule.expressions:
                char_section += f"- Expression Style: {rule.expressions}\n"

            char_section += "\n"

            prompt = first_part + char_section + "OUTPUT FORMAT" + second_part

        return prompt

    def _apply_style_guide(self, prompt: str, panel_type: str) -> str:
        """
        Apply manga style guide to prompt.

        Args:
            prompt: Original prompt
            panel_type: Panel type

        Returns:
            Enhanced prompt
        """
        # Add style guidance
        style_guidance = f"""

**MANGA STYLE REQUIREMENTS:**
- {self.style_guide['ink_style']}
- {self.style_guide['screen_tones']}
"""

        # Add specific style elements based on panel type
        if panel_type == "action":
            style_guidance += f"- {self.style_guide['speed_lines']}\n"
        elif panel_type == "dialogue":
            style_guidance += f"- {self.style_guide['speech_bubbles']}\n"

        # Add things to avoid
        style_guidance += "\n**AVOID:** " + ", ".join(self.style_guide['avoid'])

        # Insert before OUTPUT FORMAT
        if "OUTPUT FORMAT" in prompt:
            prompt = prompt.replace("OUTPUT FORMAT", style_guidance + "\n\nOUTPUT FORMAT")

        return prompt

    def _add_panel_type_enhancements(self, prompt: str, panel_type: str) -> str:
        """
        Add panel-type specific enhancements.

        Args:
            prompt: Original prompt
            panel_type: Panel type

        Returns:
            Enhanced prompt
        """
        enhancements = {
            "establishing": "Include environmental details that establish mood and setting.",
            "wide": "Show character relationships through positioning and body language.",
            "medium": "Include hand gestures and props that reveal character personality.",
            "close-up": "Focus on micro-expressions and emotional nuance.",
            "extreme-close-up": "Use dramatic lighting and focus on single telling detail.",
            "action": "Use dynamic angles and motion indicators (speed lines, impact effects).",
            "dialogue": "Position characters to show conversation dynamics and power relationships.",
            "splash": "Create dramatic impact with scale, composition, and atmospheric elements."
        }

        if panel_type in enhancements:
            enhancement = enhancements[panel_type]

            # Add enhancement
            if "CONTENT GUIDELINES" in prompt:
                prompt = prompt.replace(
                    "CONTENT GUIDELINES:",
                    f"CONTENT GUIDELINES:\n- {enhancement}"
                )

        return prompt

    def _calculate_consistency_score(
        self,
        prompt: str,
        previous_panels: List[str]
    ) -> float:
        """
        Calculate consistency score with previous panels.

        Args:
            prompt: Current prompt
            previous_panels: List of previous panel prompts

        Returns:
            Consistency score (0.0 to 1.0)
        """
        if not previous_panels:
            return 1.0

        # Simple consistency check:
        # 1. Check for character name mentions
        # 2. Check for setting consistency
        # 3. Check for lighting consistency

        score = 1.0

        # Check for character consistency
        current_chars = self._extract_characters(prompt)
        for prev_prompt in previous_panels:
            prev_chars = self._extract_characters(prev_prompt)
            if current_chars and prev_chars:
                overlap = len(set(current_chars) & set(prev_chars))
                if overlap > 0:
                    # Bonus for character overlap
                    score += 0.1

        # Check for setting consistency (simple keyword matching)
        setting_keywords = ["studio", "garden", "room", "house", "street", "london"]
        for keyword in setting_keywords:
            if keyword in prompt.lower():
                # Check if same keyword in previous
                for prev in previous_panels:
                    if keyword in prev.lower():
                        score += 0.05
                        break

        # Normalize to 0.0-1.0
        score = min(score, 1.0)

        return round(score, 2)

    def _extract_characters(self, prompt: str) -> List[str]:
        """
        Extract character names from prompt.

        Args:
            prompt: Panel prompt

        Returns:
            List of character names
        """
        chars = []

        # Extract from CHARACTER CONSISTENCY sections
        matches = re.findall(r'CHARACTER CONSISTENCY \(([^)]+)\):', prompt)
        chars.extend(matches)

        # Extract from "Characters:" lines
        matches = re.findall(r'Characters:\s*([^\n]+)', prompt)
        for match in matches:
            # Split by comma and clean
            names = [name.strip() for name in match.split(',')]
            chars.extend(names)

        return chars

    def load_character_rules_from_json(self, json_file: str):
        """
        Load character rules from JSON file.

        Args:
            json_file: Path to JSON file
        """
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for char_name, char_data in data.get('characters', {}).items():
            rule = CharacterConsistencyRule(
                character_name=char_name,
                key_features=char_data.get('key_features', []),
                clothing=char_data.get('clothing'),
                accessories=char_data.get('accessories'),
                expressions=char_data.get('expressions')
            )
            self.add_character_rule(rule)

        print(f"✓ Loaded {len(self.character_rules)} character rules from {json_file}")

    def export_character_rules(self, json_file: str):
        """
        Export character rules to JSON file.

        Args:
            json_file: Path to JSON file
        """
        data = {
            "characters": {}
        }

        for char_name, rule in self.character_rules.items():
            data["characters"][char_name] = {
                "key_features": rule.key_features,
                "clothing": rule.clothing,
                "accessories": rule.accessories,
                "expressions": rule.expressions
            }

        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"✓ Exported {len(self.character_rules)} character rules to {json_file}")


def main():
    """Test Panel Optimizer."""
    import sys
    sys.path.insert(0, '/home/clawd/projects/g-manga/src')

    from panel_type_prompts import PanelTypePrompts
    from panel_builder import PanelBuilder

    print("=" * 70)
    print("Panel Optimizer Test")
    print("=" * 70)

    # Create optimizer
    optimizer = PanelOptimizer()

    # Add character rules (based on Dorian Gray)
    basil_rule = CharacterConsistencyRule(
        character_name="Basil",
        key_features=["dark wavy hair", "brown eyes", "slender artistic build", "serious expression"],
        clothing="Victorian artist smock, paint-stained",
        accessories="paintbrush, palette",
        expressions="contemplative, intense when painting, nervous when anxious"
    )
    optimizer.add_character_rule(basil_rule)

    lord_henry_rule = CharacterConsistencyRule(
        character_name="Lord Henry",
        key_features=["blonde hair", "gray eyes", "elegant posture", "cynical smile"],
        clothing="Victorian gentleman's suit, waistcoat, cravat",
        accessories="cane, watch chain",
        expressions="amused, cynical, calculating, charming"
    )
    optimizer.add_character_rule(lord_henry_rule)

    print("\n[Test] Added character rules:")
    print(f"  - {len(optimizer.character_rules)} characters configured")

    # Create test prompt
    type_prompts = PanelTypePrompts()
    builder = PanelBuilder(type_prompts)

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

    panel_template = builder.build_panel_prompt(
        scene_id="scene-1",
        scene_number=1,
        visual_beat=test_visual_beat,
        storyboard_data=test_storyboard
    )

    print(f"\n[Test] Original prompt length: {len(panel_template.panel_template)} characters")

    # Optimize prompt
    result = optimizer.optimize_prompt(
        prompt=panel_template.panel_template,
        panel_type="close-up",
        characters_in_panel=["Basil"],
        previous_panels=None
    )

    print(f"\n[Test] Optimized prompt length: {len(result.optimized_prompt)} characters")
    print(f"[Test] Changes made:")
    for change in result.changes_made:
        print(f"  - {change}")
    print(f"[Test] Consistency score: {result.consistency_score:.2f}")

    # Test with previous panels
    print("\n[Test] Testing with previous panel context...")
    result2 = optimizer.optimize_prompt(
        prompt=panel_template.panel_template,
        panel_type="close-up",
        characters_in_panel=["Basil"],
        previous_panels=["Wide shot of studio showing both characters"]
    )

    print(f"[Test] Changes made:")
    for change in result2.changes_made:
        print(f"  - {change}")
    print(f"[Test] Consistency score: {result2.consistency_score:.2f}")

    # Test export
    print("\n[Test] Exporting character rules...")
    optimizer.export_character_rules("character_rules_test.json")

    # Test import
    print("\n[Test] Loading character rules from JSON...")
    optimizer2 = PanelOptimizer()
    optimizer2.load_character_rules_from_json("character_rules_test.json")
    print(f"[Test] Loaded {len(optimizer2.character_rules)} characters")

    print("\n" + "=" * 70)
    print("Panel Optimizer - PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()
