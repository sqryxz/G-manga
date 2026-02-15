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
        model: Optional[str] = None
    ):
        """
        Initialize Scene Breakdown.

        Args:
            llm_client: Optional LLM client (for testing/mocking)
            model: Optional model name (defaults to config setting)
        """
        self.llm_client = llm_client
        self.model = model
        self.openrouter_client = None

        # Load model from config if not provided
        if self.model is None:
            try:
                from config import get_settings
                settings = get_settings()
                # Use OpenRouter with GPT-4o for scene breakdown
                self.model = "openai/gpt-4o"
                self.provider = "openrouter"
            except ImportError:
                self.model = "openai/gpt-4o"
                self.provider = "openrouter"
        else:
            self.provider = "openrouter"

    def _get_openrouter_client(self):
        """Get or create OpenRouter client."""
        if self.openrouter_client is None:
            from common.openrouter import OpenRouterClient
            self.openrouter_client = OpenRouterClient()
        return self.openrouter_client

    def _call_llm(self, prompt: str) -> str:
        """Call LLM with prompt."""
        if self.provider == "openrouter":
            client = self._get_openrouter_client()
            result = client.generate(prompt, model=self.model)
        else:
            client = self._get_openrouter_client()
            result = client.generate(prompt, model=self.model)
        
        if result.success:
            # Validate response is not empty
            if not result.text or not result.text.strip():
                raise RuntimeError("LLM returned empty response")
            return result.text
        else:
            raise RuntimeError(f"LLM error: {result.error}")

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

Break this chapter into distinct scenes. For each scene, provide:
1. Scene number (starting from 1)
2. Location/setting
3. Time (if changed from previous scene)
4. Characters present
5. Key action/purpose (1-2 sentences)
6. Approximate word count or percentage of chapter

Use scene breaks where there's a shift in: location, time, POV, or significant narrative purpose.

Chapter {chapter_number}:
{chapter_text}

Return your response as JSON in this exact format:
{{
  "scenes": [
    {{
      "number": 1,
      "location": "Basil's studio",
      "time": "afternoon",
      "characters": ["Basil Hallward", "Lord Henry Wotton"],
      "action": "Basil introduces Dorian to Lord Henry, expressing concern about his artwork",
      "end_percentage": 35
    }},
    {{
      "number": 2,
      "location": "Garden",
      "time": "later that afternoon",
      "characters": ["Dorian Gray", "Lord Henry Wotton"],
      "action": "Lord Henry corrupts Dorian's worldview with hedonistic philosophy",
      "end_percentage": 70
    }}
  ]
}}

Be thorough but don't over-segment. A scene should be at least 5% of the chapter unless there's a clear break."""
        return prompt

    def _parse_llm_response(self, response_text: str) -> List[Dict[str, Any]]:
        """
        Parse LLM response into scene data.

        Args:
            response_text: Raw LLM response

        Returns:
            List of scene data dictionaries
        """
        import json
        import re
        
        # Validate response is not empty
        if not response_text or not response_text.strip():
            raise ValueError("LLM response is empty")
        
        # Extract JSON from response
        try:
            # Try direct JSON parsing
            data = json.loads(response_text)
            
            # Handle both {"scenes": [...]} and [...] (direct list)
            if isinstance(data, list):
                scenes = data
            else:
                scenes = data.get("scenes", [])
            
            if not scenes:
                raise ValueError("No scenes found in LLM response")
            return scenes
        except json.JSONDecodeError as e:
            # Try to extract JSON from markdown code block
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group(1))
                    scenes = data.get("scenes", [])
                    if scenes:
                        return scenes
                except json.JSONDecodeError:
                    pass

            # Try to find any JSON-like structure with scenes
            scenes_data = []
            scene_pattern = re.compile(r'\{\s*"number"\s*:\s*\d+.*?\}(?=\s*\{|\s*\])', re.DOTALL)
            for match in scene_pattern.finditer(response_text):
                try:
                    scene = json.loads(match.group(0))
                    scenes_data.append(scene)
                except json.JSONDecodeError:
                    continue
            
            if scenes_data:
                return scenes_data

            raise ValueError(f"Failed to parse LLM response as JSON: {str(e)[:200]}")

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
                # Ensure end_percentage is at least 1 to avoid end_line=0
                end_percentage = max(1, end_percentage)
                end_line = int(chapter_lines * end_percentage / 100)
            else:
                end_line = chapter_lines

            # Ensure end_line is always greater than start_line
            if end_line <= start_line:
                end_line = start_line + max(1, int(chapter_lines * 0.05))  # At least 5% or 1 line

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

        # Call LLM with retry logic
        response = None
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if self.llm_client:
                    llm_response = self.llm_client.generate(prompt, model=self.model)
                    response = llm_response if isinstance(llm_response, str) else getattr(llm_response, 'text', '')
                else:
                    # Use OpenRouter client
                    response = self._call_llm(prompt)
                
                if response and response.strip():
                    break
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    import time
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                # If all retries fail, continue to fallback
        
        # If still no valid response, use simple heuristic fallback
        if not response or not response.strip():
            scenes_data = self._fallback_scene_breakdown(chapter_text, chapter_number)
        else:
            # Parse response
            try:
                scenes_data = self._parse_llm_response(response)
            except ValueError:
                # If parsing fails, use fallback
                scenes_data = self._fallback_scene_breakdown(chapter_text, chapter_number)

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
                summary=scene_data.get("action", "") or scene_data.get("summary", ""),
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

    def _fallback_scene_breakdown(self, chapter_text: str, chapter_number: int) -> List[Dict[str, Any]]:
        """
        Fallback scene breakdown using simple heuristics when LLM fails.
        
        Args:
            chapter_text: The chapter text
            chapter_number: Chapter number
            
        Returns:
            List of scene data dictionaries
        """
        # Split text into paragraphs to find potential scene breaks
        paragraphs = chapter_text.split('\n\n')
        total_chars = len(chapter_text)
        
        # Create 3 scenes evenly distributed
        scenes = []
        char_count = 0
        
        for i in range(3):
            scene_chars = total_chars // 3 if i < 2 else total_chars - (total_chars // 3 * 2)
            end_percentage = int((char_count + scene_chars) / total_chars * 100)
            
            scenes.append({
                "number": i + 1,
                "location": "Unknown",
                "time": "Unknown",
                "characters": [],
                "action": f"Scene {i+1} of Chapter {chapter_number}",
                "end_percentage": end_percentage
            })
            char_count += scene_chars
        
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
