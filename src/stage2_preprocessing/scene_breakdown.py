"""
Scene Breakdown - Stage 2.1.3
Identifies scene breaks within chapters using LLM.
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

# Use relative imports based on package structure
from models.project import Scene, TextRange
from common.mocking import MockLLMClient


class SceneBreakdown:
    """Breaks chapters into scenes using LLM."""

    def __init__(
        self,
        llm_client=None,
        model: Optional[str] = None,
        use_openrouter: bool = True
    ):
        """
        Initialize Scene Breakdown.

        Args:
            llm_client: Optional LLM client (for testing/mocking)
            model: Optional model name (defaults to config setting)
            use_openrouter: Use OpenRouter client if no client provided
        """
        self.llm_client = llm_client
        self.model = model
        self.use_openrouter = use_openrouter
        self.openrouter_client = None

        # Load model from config if not provided
        if self.model is None:
            try:
                from config import get_settings
                settings = get_settings()
                self.model = settings.get_llm_model("scene_breakdown")
            except ImportError:
                self.model = "openai/gpt-4o"

    def _get_openrouter_client(self):
        """Get or create OpenRouter client."""
        if self.openrouter_client is None:
            from common.openrouter import OpenRouterClient
            self.openrouter_client = OpenRouterClient()
        return self.openrouter_client

    def _call_llm(self, prompt: str) -> str:
        """Call LLM with prompt."""
        if self.llm_client:
            return self.llm_client.generate(prompt, model=self.model)

        if self.use_openrouter:
            client = self._get_openrouter_client()
            result = client.generate(prompt, model=self.model)
            if result.success:
                return result.text
            else:
                raise RuntimeError(f"OpenRouter error: {result.error}")

        raise ValueError("No LLM client configured")

    def _build_prompt(self, chapter_text: str, chapter_number: int) -> str:
        """
        Build prompt for LLM scene breakdown.

        Args:
            chapter_text: The chapter text
            chapter_number: Chapter number

        Returns:
            Prompt string
        """
        prompt = f"""You are analyzing a chapter from a novel to identify natural scene breaks.

A scene is a continuous sequence of events that occurs:
1. In the same location
2. Without significant time jumps
3. With the same set of characters (or characters entering/exiting naturally)

Chapter {chapter_number}:
{chapter_text}

Please identify ALL scenes in this chapter. For each scene, provide:
1. Scene number (starting from 1)
2. A 1-2 sentence summary of what happens
3. The location where it takes place
4. All characters present in the scene
5. Approximate percentage of chapter where this scene ends (0-100%)

Return your response as JSON in this exact format:
{{
  "scenes": [
    {{
      "number": 1,
      "summary": "Two characters have a conversation in a studio",
      "location": "Basil's studio",
      "characters": ["Basil", "Lord Henry"],
      "end_percentage": 35
    }},
    {{
      "number": 2,
      "summary": "...",
      "location": "...",
      "characters": [...],
      "end_percentage": 70
    }}
  ]
}}

Focus on:
- Location changes (new location = new scene)
- Time jumps (hours/days passing = new scene)
- Character entrances/exits that change the dynamic

Be thorough but don't over-segment. A scene can be 5-50 paragraphs."""
        return prompt

    def _parse_llm_response(self, response_text: str) -> List[Dict[str, Any]]:
        """
        Parse LLM response into scene data.

        Args:
            response_text: Raw LLM response

        Returns:
            List of scene data dictionaries
        """
        # Extract JSON from response
        try:
            # Try direct JSON parsing
            data = json.loads(response_text)
            return data.get("scenes", [])
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code block
            import re
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(1))
                return data.get("scenes", [])

            # Fallback: try to find JSON-like structure
            json_match = re.search(r'\{.*"scenes".*\[.*\].*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group(0))
                    return data.get("scenes", [])
                except:
                    pass

            raise ValueError("Failed to parse LLM response as JSON")

    def _calculate_line_ranges(self, scenes_data: List[Dict[str, Any]], chapter_lines: int) -> List[Dict[str, Any]]:
        """
        Calculate line ranges for scenes based on percentages.

        Args:
            scenes_data: Parsed scene data
            chapter_lines: Total number of lines in chapter

        Returns:
            Scene data with line ranges added
        """
        enriched = []

        start_line = 0

        for i, scene_data in enumerate(scenes_data):
            # Calculate end line from percentage
            if i + 1 < len(scenes_data):
                end_percentage = scene_data.get("end_percentage", 100)
                end_line = int(chapter_lines * end_percentage / 100)
            else:
                end_line = chapter_lines

            # Add line ranges
            enriched_scene = {
                **scene_data,
                "start_line": start_line,
                "end_line": end_line
            }
            enriched.append(enriched_scene)

            # Next scene starts where this one ends
            start_line = end_line

        return enriched

    def breakdown_chapter(self, chapter_text: str, chapter_id: str, chapter_number: int) -> List[Scene]:
        """
        Break a chapter into scenes.

        Args:
            chapter_text: The chapter text
            chapter_id: Chapter ID (e.g., "chapter-1")
            chapter_number: Chapter number

        Returns:
            List of Scene objects
        """
        # Build prompt
        prompt = self._build_prompt(chapter_text, chapter_number)

        # Call LLM
        if self.llm_client:
            response = self.llm_client.call(prompt)
        else:
            # Mock response for testing
            response = self._mock_llm_response(chapter_number)

        # Parse response
        scenes_data = self._parse_llm_response(response)

        # Calculate line ranges
        chapter_lines = len(chapter_text.split("\n"))
        scenes_data = self._calculate_line_ranges(scenes_data, chapter_lines)

        # Create Scene objects
        scenes = []
        for scene_data in scenes_data:
            # Extract scene text
            lines = chapter_text.split("\n")
            scene_lines = lines[scene_data["start_line"]:scene_data["end_line"]]
            scene_text = "\n".join(scene_lines)

            scene = Scene(
                id=f"{chapter_id}-scene-{scene_data['number']}",
                chapter_id=chapter_id,
                number=scene_data["number"],
                summary=scene_data.get("summary", ""),
                location=scene_data.get("location", "Unknown"),
                characters=scene_data.get("characters", []),
                text_range=TextRange(
                    start=scene_data["start_line"],
                    end=scene_data["end_line"]
                )
            )
            # Add text separately (not part of Pydantic model)
            scene.text = scene_text
            scenes.append(scene)

        return scenes

    def _mock_llm_response(self, chapter_number: int) -> str:
        """
        Mock LLM response for testing.

        Args:
            chapter_number: Chapter number

        Returns:
            Mock JSON response
        """
        # Simplified mock - in production, use real LLM
        mock_response = f'''{{
  "scenes": [
    {{
      "number": 1,
      "summary": "Introduction of main characters in an art studio discussing beauty and art",
      "location": "Basil's art studio",
      "characters": ["Basil Hallward", "Lord Henry Wotton"],
      "end_percentage": 100
    }}
  ]
}}'''
        return mock_response


class MockLLMClient:
    """Mock LLM client for testing."""

    def call(self, prompt: str) -> str:
        """Return a mock response."""
        return '''{
  "scenes": [
    {
      "number": 1,
      "summary": "Two characters discuss art and beauty in a studio",
      "location": "Basil's studio",
      "characters": ["Basil", "Lord Henry"],
      "end_percentage": 100
    }
  ]
}'''


def main():
    """Test Scene Breakdown."""
    import sys
    sys.path.insert(0, '/home/clawd/projects/g-manga/src/stage1_input')
    sys.path.insert(0, '/home/clawd/projects/g-manga/src/stage2_preprocessing')

    from url_fetcher import URLFetcher
    from text_parser import TextParser
    from chapter_segmenter import ChapterSegmenter

    # Get test text
    test_url = "https://www.gutenberg.org/files/174/174-0.txt"

    fetcher = URLFetcher()
    raw = fetcher.fetch(test_url)

    parser = TextParser()
    cleaned, _ = parser.parse(raw)

    # Segment into chapters
    segmenter = ChapterSegmenter()
    chapters = segmenter.segment(cleaned)
    chapters = segmenter.extract_text(chapters, cleaned)

    # Break down first chapter
    if chapters:
        chapter = chapters[0]
        print(f"Processing: Chapter {chapter.chapter_number}")
        print(f"Title: {chapter.title}")
        print(f"Length: {len(chapter.text):,} characters")
        print()

        # Use mock LLM for testing
        breakdown = SceneBreakdown(llm_client=MockLLMClient())
        scenes = breakdown.breakdown_chapter(chapter.text, f"chapter-{chapter.chapter_number}", chapter.chapter_number)

        print(f"Found {len(scenes)} scenes:")
        print()
        for scene in scenes:
            print(f"Scene {scene.scene_number}: {scene.summary}")
            print(f"  Location: {scene.location}")
            print(f"  Characters: {', '.join(scene.characters)}")
            print(f"  Lines: {scene.start_line} - {scene.end_line}")
            print()


if __name__ == "__main__":
    main()
