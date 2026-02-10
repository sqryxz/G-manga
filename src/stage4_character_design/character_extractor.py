"""
Character Extractor - Stage 4.1.1
Extracts characters and their appearance descriptions using LLM.
"""

import json
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class Character:
    """A character extracted from the text."""
    id: str
    name: str
    aliases: List[str]
    appearance: Dict[str, Any]  # Age, hair, build, clothing, features, etc.
    role: Optional[str] = None  # Protagonist, antagonist, supporting, etc.
    first_appearance: Optional[int] = None  # Chapter number first appeared


class CharacterExtractor:
    """Extracts characters from text using LLM."""

    def __init__(self, llm_client=None):
        """
        Initialize Character Extractor.

        Args:
            llm_client: Optional LLM client (for testing/mocking)
        """
        self.llm_client = llm_client

    def _build_prompt(self, chapter_text: str, chapter_number: int) -> str:
        """
        Build prompt for LLM character extraction.

        Args:
            chapter_text: The chapter text
            chapter_number: Chapter number

        Returns:
            Prompt string
        """
        prompt = f"""You are analyzing a novel chapter to identify and describe all characters.

**CHAPTER {chapter_number}:**
{chapter_text[:2000]}...

**YOUR TASK:**
Identify ALL characters mentioned in this chapter, including:
1. Main characters (appear multiple times, have significant roles)
2. Minor characters (appear once or few times)
3. Background characters (brief mentions, extras)

For EACH character, provide:

1. **Name** - The character's full name (e.g., "Basil Hallward")
2. **Aliases** - Any names they are called by (e.g., "Mr. Hallward", "Basil")
3. **Role** - Their role in the story (protagonist, antagonist, deuteragonist, supporting, background)
4. **First Appearance** - Chapter number where they first appeared (if known, otherwise null)
5. **Age** - Approximate age if mentioned (e.g., "late 20s", "30s", "middle-aged", "elderly")
6. **Gender** - Male, Female, Non-binary (if specified, otherwise null)
7. **Height** - Tall, average, short (if specified, otherwise null)
8. **Build** - Lean, muscular, thin, athletic, frail, etc.
9. **Hair** - Color (black, brown, blonde, red, gray, white, silver), style (short, long, curly, straight, balding), length
10. **Eyes** - Color (brown, blue, green, gray, blue), shape (round, almond, narrow)
11. **Skin Tone** - Pale, fair, tan, dark, etc. (if specified, otherwise null)
12. **Clothing** - General style and typical attire (e.g., "Victorian gentleman's suit", "painting smock", "evening gown", "bohemian artist's clothes")
13. **Distinguishing Features** - Any unique physical traits (scars, tattoos, glasses, distinctive jewelry, birthmarks, etc.)
14. **Personality Traits** - Key personality characteristics (e.g., "arrogant", "artistic", "mysterious", "charming", "humble", "intellectual", "cynical")

**INSTRUCTIONS:**
- Be thorough - include both visual descriptions and personality
- Be specific with physical details (hair color, eye color, clothing style)
- Note any distinctive traits that would make them recognizable in artwork
- If a character's appearance changes significantly, create multiple entries or note the changes
- For background characters, minimal description is acceptable
- Only include characters who appear or are directly mentioned in this chapter

**OUTPUT FORMAT:**
Return JSON in this exact format:
{{
  "characters": [
    {{
      "name": "Basil Hallward",
      "aliases": ["Basil", "Mr. Hallward"],
      "role": "protagonist",
      "first_appearance": {chapter_number},
      "age": "late 20s",
      "gender": "male",
      "height": "average",
      "build": "lean, artistic",
      "hair": {{
        "color": "dark brown",
        "style": "short",
        "length": "straight"
      }},
      "eyes": {{
        "color": "hazel",
        "shape": "almond"
      }},
      "skin_tone": "pale",
      "clothing": "painting smock with paint stains, simple shirt, dark trousers",
      "distinguishing_features": "Often has paint on his hands and clothes",
      "personality_traits": ["passionate", "devoted to art", "sensitive", "humble"]
    }},
    {{
      "name": "Lord Henry Wotton",
      "aliases": ["Lord Henry", "Harry"],
      "role": "deuteragonist",
      "first_appearance": null,
      "age": "late 20s",
      "gender": "male",
      "height": "tall",
      "build": "lean, aristocratic",
      "hair": {{
        "color": "golden blonde",
        "style": "short, curled",
        "length": "medium"
      }},
      "eyes": {{
        "color": "blue",
        "shape": "narrow"
      }},
      "skin_tone": "fair",
      "clothing": "elegant gentleman's attire, frock coat, silk cravat",
      "distinguishing_features": "Always looks bored and slightly cynical",
      "personality_traits": ["cynical", "witty", "hedonistic", "influential", "charismatic"]
    }}
  ]
}}

Be comprehensive but stay focused on characters who actually appear in the text."""
        return prompt

    def _parse_llm_response(self, response_text: str) -> List[Dict[str, Any]]:
        """
        Parse LLM response into character data.

        Args:
            response_text: Raw LLM response

        Returns:
            List of character dictionaries
        """
        # Extract JSON from response
        try:
            data = json.loads(response_text)
            return data.get("characters", [])
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code block
            import re
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(1))
                return data.get("characters", [])

            # Fallback: try to find JSON-like structure
            json_match = re.search(r'\{.*"characters".*\[.*\].*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group(0))
                    return data.get("characters", [])
                except:
                    pass

            raise ValueError("Failed to parse LLM response as JSON")

    def extract_characters(self, chapter_text: str, chapter_id: str, chapter_number: int) -> List[Dict[str, Any]]:
        """
        Extract characters from a chapter.

        Args:
            chapter_text: The chapter text
            chapter_id: Chapter ID
            chapter_number: Chapter number

        Returns:
            List of character data dictionaries
        """
        # Build prompt
        prompt = self._build_prompt(chapter_text, chapter_number)

        # Call LLM
        if self.llm_client:
            response = self.llm_client.call(prompt)
        else:
            # Mock response for testing
            response = self._mock_llm_response()

        # Parse response
        chars_data = self._parse_llm_response(response)

        # Add IDs and meta
        characters = []
        for i, char_data in enumerate(chars_data):
            # Generate ID (slug format)
            slug = re.sub(r"[^a-z0-9]+", "-", char_data.get("name", "unknown").lower())
            char_id = f"{chapter_id}-char-{i+1}"

            # Add ID and meta
            char_data["id"] = char_id
            char_data["chapter_id"] = chapter_id
            char_data["chapter_number"] = chapter_number
            char_data["extraction_method"] = "llm"

            characters.append(char_data)

        return characters

    def _mock_llm_response(self) -> str:
        """
        Mock LLM response for testing.

        Returns:
            Mock JSON response with sample characters
        """
        # Simplified mock - in production, use real LLM
        mock_response = {
            "characters": [
                {
                    "name": "Basil Hallward",
                    "aliases": ["Basil", "Mr. Hallward"],
                    "role": "protagonist",
                    "first_appearance": None,
                    "age": "late 20s",
                    "gender": "male",
                    "height": "average",
                    "build": "lean, artistic",
                    "hair": {
                        "color": "dark brown",
                        "style": "short",
                        "length": "straight"
                    },
                    "eyes": {
                        "color": "hazel",
                        "shape": "almond"
                    },
                    "skin_tone": "pale",
                    "clothing": "painting smock with paint stains, simple shirt, dark trousers",
                    "distinguishing_features": "Often has paint on his hands and clothes",
                    "personality_traits": ["passionate", "devoted to art", "sensitive"]
                }
            ]
        }

        return json.dumps(mock_response)


class MockLLMClient:
    """Mock LLM client for testing."""

    def call(self, prompt: str) -> str:
        """Return a mock response."""
        return '''{
  "characters": [
    {
      "name": "Basil Hallward",
      "aliases": ["Basil", "Mr. Hallward"],
      "role": "protagonist",
      "first_appearance": null,
      "age": "late 20s",
      "gender": "male",
      "height": "average",
      "build": "lean, artistic",
      "hair": {
        "color": "dark brown",
        "style": "short",
        "length": "straight"
      },
      "eyes": {
        "color": "hazel",
        "shape": "almond"
      },
      "skin_tone": "pale",
      "clothing": "painting smock with paint stains, simple shirt, dark trousers",
      "distinguishing_features": "Often has paint on his hands and clothes",
      "personality_traits": ["passionate", "devoted to art", "sensitive", "humble"]
    },
    {
      "name": "Lord Henry Wotton",
      "aliases": ["Lord Henry", "Harry"],
      "role": "deuteragonist",
      "first_appearance": null,
      "age": "late 20s",
      "gender": "male",
      "height": "tall",
      "build": "lean, aristocratic",
      "hair": {
        "color": "golden blonde",
        "style": "short, curled",
        "length": "medium"
      },
      "eyes": {
        "color": "blue",
        "shape": "narrow"
      },
      "skin_tone": "fair",
      "clothing": "elegant gentleman's attire, frock coat, silk cravat",
      "distinguishing_features": "Always looks bored and slightly cynical",
      "personality_traits": ["cynical", "witty", "hedonistic", "influential", "charismatic"]
    }
  ]
}'''


def main():
    """Test Character Extractor."""
    import sys
    sys.path.insert(0, '/home/clawd/projects/g-manga/src/stage1_input')
    sys.path.insert(0, '/home/clawd/projects/g-manga/src/stage2_preprocessing')
    sys.path.insert(0, '/home/clawd/projects/g-manga/src/stage3_story_planning')

    from url_fetcher import URLFetcher
    from text_parser import TextParser
    from metadata_extractor import MetadataExtractor
    from project import ProjectInitializer

    # Get chapter text
    test_url = "https://www.gutenberg.org/files/174/174-0.txt"

    fetcher = URLFetcher(cache_dir="/home/clawd/projects/g-manga/cache")
    raw_content = fetcher.fetch(test_url)

    parser = TextParser()
    cleaned_text, _ = parser.parse(raw_content)

    # Extract first chapter (simplified for testing)
    first_chapter_end = cleaned_text.find("CHAPTER II.")
    chapter_text = cleaned_text[:first_chapter_end] if first_chapter_end > 0 else cleaned_text[:2000]

    # Test with mock LLM
    extractor = CharacterExtractor(llm_client=MockLLMClient())

    characters = extractor.extract_characters(
        chapter_text,
        "chapter-1",
        1
    )

    print(f"Extracted {len(characters)} characters:")
    print()

    for char in characters:
        print(f"Character: {char['name']}")
        print(f"  ID: {char['id']}")
        print(f"  Aliases: {', '.join(char.get('aliases', []))}")
        print(f"  Role: {char.get('role', 'unknown')}")
        print(f"  Age: {char.get('age', 'unknown')}")
        print(f"  Gender: {char.get('gender', 'unknown')}")
        print(f"  Build: {char.get('build', 'unknown')}")
        print(f"  Hair: {char.get('hair', {}).get('color', 'unknown')}")
        print(f"  Personality: {', '.join(char.get('personality_traits', []))}")
        print()


if __name__ == "__main__":
    main()
