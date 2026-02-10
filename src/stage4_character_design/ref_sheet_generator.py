"""
Ref Sheet Generator - Stage 4.1.4
Creates reference sheet prompts for character consistency.
"""

from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class RefSheetPrompt:
    """Reference sheet prompt data for a character."""
    character_id: str
    character_name: str
    role: str
    description: str
    style_tags: List[str]
    full_body_shot: str
    expressions: List[str]
    clothing_variants: List[str]


class RefSheetGenerator:
    """Generates reference sheet prompts for characters."""

    def __init__(self, style_config: Dict[str, Any] = None):
        """
        Initialize Ref Sheet Generator.

        Args:
            style_config: Style configuration for manga art
        """
        self.style_config = style_config or self._default_style_config()

    def _default_style_config(self) -> Dict[str, Any]:
        """Get default style configuration."""
        return {
            "art_style": "manga",
            "color": "black_and_white",
            "line_weight": "medium",
            "shading": "screen_tones",
            "detail_level": "high"
        }

    def _build_prompt(self, character: Dict[str, Any]) -> str:
        """
        Build prompt for reference sheet generation.

        Args:
            character: Character data

        Returns:
            Prompt string
        """
        style = self.style_config

        prompt = f"""You are creating a character reference sheet for manga artists.

**CHARACTER:**
- Name: {character.get('name', 'Unknown')}
- Role: {character.get('role', 'Unknown')}
- Age: {character.get('age', 'Unknown')}
- Gender: {character.get('gender', 'Unknown')}
- Build: {character.get('build', 'Unknown')}
- Height: {character.get('height', 'Unknown')}

**APPEARANCE:**
"""
        # Add appearance details
        appearance = character.get('appearance', {})
        if appearance:
            prompt += f"- Hair: {appearance.get('hair', {}).get('color', 'Unknown')}, {appearance.get('hair', {}).get('style', 'Unknown')}, {appearance.get('hair', {}).get('length', 'Unknown')}\n"
            prompt += f"- Eyes: {appearance.get('eyes', {}).get('color', 'Unknown')}, {appearance.get('eyes', {}).get('shape', 'Unknown')}\n"
            prompt += f"- Skin Tone: {appearance.get('skin_tone', 'Unknown')}\n"
            prompt += f"- Clothing: {appearance.get('clothing', 'Unknown')}\n"

        # Add distinguishing features
        features = character.get('distinguishing_features', [])
        if features:
            prompt += f"\n**DISTINGUISHING FEATURES:**\n"
            for feature in features:
                prompt += f"- {feature}\n"

        # Add personality traits
        traits = character.get('personality_traits', [])
        if traits:
            prompt += f"\n**PERSONALITY TRAITS:**\n"
            for trait in traits:
                prompt += f"- {trait}\n"

        # Style tags based on role
        role = character.get('role', '')
        style_tags = []

        if 'protagonist' in role:
            style_tags = ["main_character", "detailed", "dynamic", "expressive"]
        elif 'antagonist' in role:
            style_tags = ["sharp_lines", "intense", "dramatic", "dynamic"]
        elif 'supporting' in role:
            style_tags = ["clean_lines", "soft_expression", "friendly", "helpful"]
        else:
            style_tags = ["neutral_expression", "standard_lines", "clear_lines"]

        prompt += f"""
**STYLE SPECIFICATIONS:**
- Art Style: {style['art_style']}
- Color: {style['color']}
- Line Weight: {style['line_weight']}
- Shading: {style['shading']}
- Detail Level: {style['detail_level']}
- Style Tags: {', '.join(style_tags)}

**REFERENCE SHEET CONTENT:**
Generate 4 different views:

1. **Full Body Shot** (3/4 view)
   - Character standing or walking
   - Natural, relaxed pose
   - Show full body and clothing
   - Clean, crisp lines
   - Neutral or happy expression

2. **Close-up Portrait** (front view)
   - Head and shoulders
   - Focus on facial features (eyes, expression)
   - Characteristic expression reflecting personality
   - Show hair style clearly

3. **Side/Profile View** (3/4 view)
   - Character from the side
   - Show profile, nose, jawline
   - Demonstrate clothing details

4. **Expression Variety** (2 different expressions)
   - Expression 1: {traits[0] if traits else 'neutral'}
   - Expression 2: {traits[1] if len(traits) > 1 else 'neutral'}

**INSTRUCTIONS FOR ARTIST:**
- Keep character proportions consistent across all views
- Pay attention to distinguishing features (scars, unique hair style)
- Capture personality in facial expressions and posture
- Use clean, manga-style lines with good contrast
- Include shading for depth (hatching, screentones)

Return reference sheet as image descriptions for each view.
"""
        return prompt

    def generate_ref_sheet(self, character: Dict[str, Any]) -> RefSheetPrompt:
        """
        Generate reference sheet prompt data for a character.

        Args:
            character: Character data

        Returns:
            RefSheetPrompt object
        """
        # Build prompt
        prompt = self._build_prompt(character)

        # Generate expressions
        traits = character.get('personality_traits', [])
        expressions = [traits[0] if traits else 'neutral']
        if len(traits) > 1:
            expressions.append(traits[1])
        else:
            expressions.extend(['confused', 'angry'])

        # Generate clothing variants
        clothing = character.get('clothing', 'Victorian suit')
        clothing_variants = [
            clothing,
            f"{clothing}, slightly disheveled",
            f"{clothing}, with coat"
        ]

        # Style tags
        role = character.get('role', '')
        style_tags = []
        if 'protagonist' in role:
            style_tags = ["main_character", "detailed"]
        elif 'antagonist' in role:
            style_tags = ["sharp", "intense"]
        elif 'supporting' in role:
            style_tags = ["soft", "friendly"]

        # Full body shot description
        full_body_shot = f"Full body shot of {character.get('name', 'character')} in their {character.get('clothing', 'clothing')}. {character.get('build', 'lean build')} figure. {character.get('height', 'average height')}."

        return RefSheetPrompt(
            character_id=character.get('id', ''),
            character_name=character.get('name', 'Unknown'),
            role=character.get('role', 'Unknown'),
            description=character.get('distinguishing_features', ''),
            style_tags=style_tags,
            full_body_shot=full_body_shot,
            expressions=expressions,
            clothing_variants=clothing_variants
        )

    def generate_batch(self, characters: List[Dict[str, Any]]) -> List[RefSheetPrompt]:
        """
        Generate reference sheets for multiple characters.

        Args:
            characters: List of character data

        Returns:
            List of RefSheetPrompt objects
        """
        ref_sheets = []
        for character in characters:
            ref_sheet = self.generate_ref_sheet(character)
            ref_sheets.append(ref_sheet)

        return ref_sheets


def main():
    """Test Ref Sheet Generator."""
    import sys
    sys.path.insert(0, '/home/clawd/projects/g-manga/src')

    from models.project import Character

    # Create test character
    test_character = {
        "id": "char-basil",
        "name": "Basil Hallward",
        "role": "protagonist",
        "age": "late 20s",
        "gender": "male",
        "height": "average",
        "build": "lean, artistic",
        "hair": {"color": "dark brown", "style": "short", "length": "straight"},
        "eyes": {"color": "hazel", "shape": "almond"},
        "skin_tone": "pale",
        "clothing": "painting smock, simple shirt, dark trousers",
        "distinguishing_features": "Paint stains on hands and clothes",
        "personality_traits": ["passionate", "devoted", "sensitive", "humble"]
    }

    # Test generator
    generator = RefSheetGenerator()

    ref_sheet = generator.generate_ref_sheet(test_character)

    print("=" * 70)
    print("Reference Sheet Generator Test")
    print("=" * 70)

    print(f"Character: {ref_sheet.character_name}")
    print(f"Role: {ref_sheet.role}")
    print(f"Expressions: {', '.join(ref_sheet.expressions)}")
    print(f"Clothing variants: {len(ref_sheet.clothing_variants)}")
    print(f"\nFull Body Shot:\n  {ref_sheet.full_body_shot}")

    print("\n" + "=" * 70)
    print("Style Tags: " + ", ".join(ref_sheet.style_tags))
    print("=" * 70)


if __name__ == "__main__":
    main()
