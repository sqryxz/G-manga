"""Module 2: Analysis Engine - Main Orchestrator"""

import json
import re
from typing import List, Optional, Dict, Any
from pathlib import Path

from .schemas import (
    Character, Location, PlotBeat, Dialogue, KeyQuote, AnalysisResult
)


class AnalysisEngine:
    """
    Orchestrates all analysis extractors.
    
    Extracts:
    - Characters (2A)
    - Locations (2B)
    - Plot Beats (2C)
    - Dialogue (2D)
    - Key Quotes
    """
    
    def __init__(self, llm_client=None, model: str = "aurora-alpha"):
        self.llm_client = llm_client
        self.model = model
        
    def analyze(self, chapters: List[Any]) -> AnalysisResult:
        """Run full analysis on chapters."""
        
        all_characters = []
        all_locations = []
        all_beats = []
        all_dialogue = []
        all_quotes = []
        
        for chapter in chapters:
            chapter_num = chapter.number if hasattr(chapter, 'number') else 0
            chapter_text = chapter.text if hasattr(chapter, 'text') else str(chapter)
            
            # Extract using LLM if available
            if self.llm_client:
                chars, locs, beats, dial, quotes = self._llm_extract(
                    chapter_text, chapter_num
                )
            else:
                chars, locs, beats, dial, quotes = self._regex_fallback(
                    chapter_text, chapter_num
                )
            
            all_characters.extend(chars)
            all_locations.extend(locs)
            all_beats.extend(beats)
            all_dialogue.extend(dial)
            all_quotes.extend(quotes)
        
        # Merge cross-chapter data
        merged = self._merge_chapters(
            all_characters, all_locations, chapters
        )
        
        return AnalysisResult(
            characters=merged['characters'],
            locations=merged['locations'],
            plot_beats=all_beats,
            dialogue=all_dialogue,
            key_quotes=all_quotes
        )
    
    def _llm_extract(self, text: str, chapter_num: int):
        """Extract using LLM with structured prompts."""
        
        # Character extraction prompt
        char_prompt = f"""Extract all named characters from this chapter of The Picture of Dorian Gray.

Return JSON array with objects containing:
- name: character's full name
- aliases: other names they are known by
- first_appearance: the sentence where they first appear (quote exactly)
- role: protagonist, antagonist, supporting, or minor
- physical_descriptions: list of physical descriptions from text (quote exactly)

Chapter text:
{text[:3000]}

Return ONLY valid JSON, no other text."""

        # Location extraction prompt
        loc_prompt = f"""Extract all locations mentioned in this chapter of The Picture of Dorian Gray.

Return JSON array with objects containing:
- name: location name
- location_type: interior or exterior
- privacy: public or private
- descriptions: list of descriptions from text (quote exactly)

Chapter text:
{text[:3000]}

Return ONLY valid JSON, no other text."""

        # Plot beat extraction prompt
        beats_prompt = f"""Break this chapter into discrete story beats. A beat is a single narrative unit: an action, revelation, decision, or emotional shift.

Return JSON array with objects containing:
- beat_number: sequential number
- description: what happens in this beat
- is_major: true if this is a major plot point, false otherwise
- beat_type: action, revelation, decision, or emotional

Chapter text:
{text[:4000]}

Return ONLY valid JSON, no other text."""

        # Dialogue extraction prompt
        dial_prompt = f"""Extract all dialogue from this chapter.

Return JSON array with objects containing:
- speaker: who says this
- quote: the exact dialogue
- context: what's happening (1 sentence)
- tone: emotional tone (neutral, angry, happy, sad, excited, etc.)

Chapter text:
{text[:3000]}

Return ONLY valid JSON, no other text."""

        results = {}
        
        try:
            # Extract characters
            char_response = self.llm_client.generate(char_prompt, model=self.model)
            char_text = char_response.text if hasattr(char_response, 'text') else str(char_response)
            chars = self._parse_json_array(char_text, 'characters')
            for c in chars:
                c['chapter_first_appeared'] = chapter_num
            results['characters'] = [Character(**c) for c in chars]
        except Exception as e:
            print(f"Character extraction error: {e}")
            results['characters'] = []
        
        try:
            # Extract locations
            loc_response = self.llm_client.generate(loc_prompt, model=self.model)
            loc_text = loc_response.text if hasattr(loc_response, "text") else str(loc_response)
            locs = self._parse_json_array(loc_text, 'locations')
            results['locations'] = [Location(**{**l, 'chapters_appeared': [chapter_num]}) for l in locs]
        except Exception as e:
            print(f"Location extraction error: {e}")
            results['locations'] = []
        
        try:
            # Extract plot beats
            beats_response = self.llm_client.generate(beats_prompt, model=self.model)
            beats_text = beats_response.text if hasattr(beats_response, "text") else str(beats_response)
            beats = self._parse_json_array(beats_text, 'plot_beats')
            for b in beats:
                b['chapter'] = chapter_num
            results['plot_beats'] = [PlotBeat(**b) for b in beats]
        except Exception as e:
            print(f"Plot beat extraction error: {e}")
            results['plot_beats'] = []
        
        try:
            # Extract dialogue
            dial_response = self.llm_client.generate(dial_prompt, model=self.model)
            dial_text = dial_response.text if hasattr(dial_response, "text") else str(dial_response)
            dial = self._parse_json_array(dial_text, 'dialogue')
            print(f"DEBUG: Parsed {len(dial)} dialogue items")
            for d in dial:
                print(f"  {d}")
            for d in dial:
                d['chapter'] = chapter_num
            results['dialogue'] = [Dialogue(**d) for d in dial]
        except Exception as e:
            import traceback
            print(f"Dialogue extraction error: {e}")
            traceback.print_exc()
            results['dialogue'] = []
        
        results['key_quotes'] = []
        
        return (
            results.get('characters', []),
            results.get('locations', []),
            results.get('plot_beats', []),
            results.get('dialogue', []),
            results.get('key_quotes', [])
        )
    
    def _parse_json_array(self, response: str, field: str) -> List[Dict]:
        """Parse JSON array from LLM response."""
        try:
            # Clean up response (remove code block markers)
            import re
            cleaned = re.sub(r'^```json\s*', '', response.strip())
            cleaned = re.sub(r'\s*```$', '', cleaned)
            cleaned = re.sub(r'^```\s*', '', cleaned)
            cleaned = re.sub(r'\s*```$', '', cleaned)
            
            # Try to find JSON array
            match = re.search(r'\[[\s\S]*\]', cleaned)
            if match:
                return json.loads(match.group())
        except json.JSONDecodeError as e:
            print(f"JSON parse error for {field}: {e}")
        return []
    
    def _regex_fallback(self, text: str, chapter_num: int):
        """Fallback extraction using regex when LLM unavailable."""
        
        characters = []
        locations = []
        plot_beats = []
        dialogue = []
        key_quotes = []
        
        # Simple quote extraction for dialogue
        quote_pattern = r'"([^"]+)"'
        matches = re.findall(quote_pattern, text)
        for i, quote in enumerate(matches[:10]):  # Limit to first 10
            dialogue.append(Dialogue(
                speaker="Unknown",
                quote=quote,
                context="",
                tone="neutral",
                chapter=chapter_num
            ))
        
        return characters, locations, plot_beats, dialogue, key_quotes
    
    def _merge_chapters(self, characters: List[Character], 
                       locations: List[Location], chapters: List[Any]):
        """Merge data across chapters."""
        
        # Deduplicate characters by name
        char_dict = {}
        for c in characters:
            if c.name.lower() not in char_dict:
                char_dict[c.name.lower()] = c
            else:
                # Merge aliases
                existing = char_dict[c.name.lower()]
                for alias in c.aliases:
                    if alias not in existing.aliases:
                        existing.aliases.append(alias)
        
        # Deduplicate locations by name
        loc_dict = {}
        for l in locations:
            if l.name.lower() not in loc_dict:
                loc_dict[l.name.lower()] = l
            else:
                existing = loc_dict[l.name.lower()]
                if l.chapters_appeared and l.chapters_appeared[0] not in existing.chapters_appeared:
                    existing.chapters_appeared.extend(l.chapters_appeared)
        
        return {
            'characters': list(char_dict.values()),
            'locations': list(loc_dict.values())
        }
    
    def save(self, result: AnalysisResult, output_path: str):
        """Save analysis result to JSON file."""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)
