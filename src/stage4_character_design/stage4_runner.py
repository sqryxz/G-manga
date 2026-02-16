"""
Stage 4 Runner - Character Design Pipeline
Combines extraction, enrichment, and reference sheet generation.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import asdict

from .character_extractor import CharacterExtractor
from .ref_sheet_generator import RefSheetGenerator, RefSheetPrompt


class Stage4Runner:
    """Runs the complete Stage 4 character design pipeline."""
    
    def __init__(self, llm_client=None, style_config: Dict[str, Any] = None):
        self.extractor = CharacterExtractor(llm_client=llm_client)
        self.ref_generator = RefSheetGenerator(style_config=style_config)
        self.llm_client = llm_client
    
    def run(
        self,
        stage2_analysis: Dict[str, Any],
        output_dir: str,
        chapters: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run complete Stage 4 pipeline.
        
        Args:
            stage2_analysis: Stage 2 analysis result (characters, plot beats, etc.)
            output_dir: Directory to save output files
            chapters: Optional chapter data for enrichment
        
        Returns:
            Dict with results and file paths
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Start with characters from Stage 2
        characters = stage2_analysis.get('characters', [])
        
        # Enrich characters with relationships and key scenes from plot beats
        characters = self._enrich_characters(
            characters, 
            stage2_analysis.get('plot_beats', []),
            chapters or []
        )
        
        # Generate reference sheets for each character
        ref_sheets = []
        for char in characters:
            ref_sheet = self._create_ref_sheet(char)
            ref_sheets.append(ref_sheet)
            
            # Save individual character JSON
            char_filename = self._sanitize_filename(char['name']) + '.json'
            char_path = output_path / 'characters' / char_filename
            char_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(char_path, 'w') as f:
                json.dump(char, f, indent=2)
        
        # Save master characters.json index
        master_index = self._create_master_index(characters, ref_sheets)
        master_path = output_path / 'characters.json'
        with open(master_path, 'w') as f:
            json.dump(master_index, f, indent=2)
        
        # Save all reference sheets
        ref_sheets_path = output_path / 'reference_sheets.json'
        with open(ref_sheets_path, 'w') as f:
            json.dump([asdict(rs) for rs in ref_sheets], f, indent=2)
        
        return {
            'characters': characters,
            'character_count': len(characters),
            'ref_sheets_count': len(ref_sheets),
            'output_files': {
                'master_index': str(master_path),
                'reference_sheets': str(ref_sheets_path),
                'individual_characters': str(output_path / 'characters')
            }
        }
    
    def _enrich_characters(
        self,
        characters: List[Dict[str, Any]],
        plot_beats: List[Dict[str, Any]],
        chapters: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Enrich characters with relationships and key scenes from plot beats."""
        
        # Build character name lookup
        char_names = {}
        for char in characters:
            name = char.get('name', '')
            char_names[name.lower()] = char
            for alias in char.get('aliases', []):
                char_names[alias.lower()] = char
        
        # Find relationships from plot beats
        relationships_found = {char['name']: {} for char in characters}
        scenes_found = {char['name']: [] for char in characters}
        
        # Keywords for relationship types
        rel_keywords = {
            'friend': ['friend', 'companion', 'associate'],
            'family': ['father', 'mother', 'son', 'daughter', 'brother', 'sister', 'wife', 'husband', 'uncle', 'aunt'],
            'employer': ['employer', 'employee', 'servant', 'assistant', 'secretary'],
            'enemy': ['enemy', 'foe', 'rival', 'opponent'],
            'lover': ['love', 'lover', 'romance', 'affection'],
            'professional': ['doctor', 'lawyer', 'client', 'patient']
        }
        
        for beat in plot_beats:
            description = beat.get('description', '').lower()
            chapter = beat.get('chapter', 0)
            
            # Find character mentions in beat
            for char in characters:
                char_name_lower = char.get('name', '').lower()
                if char_name_lower in description:
                    # Look for relationship keywords
                    for rel_type, keywords in rel_keywords.items():
                        for keyword in keywords:
                            if keyword in description:
                                # Find other characters mentioned
                                for other_char in characters:
                                    other_name = other_char.get('name', '').lower()
                                    if other_name != char_name_lower and other_name in description:
                                        relationships_found[char['name']][other_char['name']] = rel_type
                    
                    # Add as key scene if major
                    if beat.get('is_major', False):
                        scenes_found[char['name']].append({
                            'chapter': chapter,
                            'description': beat.get('description', '')[:100],
                            'importance': 'major' if beat.get('is_major') else 'minor'
                        })
        
        # Update characters with enriched data
        for char in characters:
            name = char.get('name', '')
            
            # Add relationships
            if name in relationships_found and relationships_found[name]:
                char['relationships'] = relationships_found[name]
            else:
                char['relationships'] = {}
            
            # Add key scenes
            if name in scenes_found and scenes_found[name]:
                char['key_scenes'] = scenes_found[name]
            else:
                char['key_scenes'] = []
            
            # Ensure personality_traits exists
            if 'personality_traits' not in char:
                char['personality_traits'] = []
        
        return characters
    
    def _create_ref_sheet(self, character: Dict[str, Any]) -> RefSheetPrompt:
        """Create reference sheet for a character."""
        return self.ref_generator.generate_ref_sheet(character)
    
    def _create_master_index(
        self,
        characters: List[Dict[str, Any]],
        ref_sheets: List[RefSheetPrompt]
    ) -> Dict[str, Any]:
        """Create master characters index."""
        return {
            'metadata': {
                'total_characters': len(characters),
                'generated_by': 'Stage 4 Character Design',
                'fields': [
                    'character_id', 'name', 'aliases', 'role',
                    'physical_description', 'personality_traits',
                    'relationships', 'key_scenes', 'visual_notes'
                ]
            },
            'characters': [
                {
                    'character_id': char.get('name', '').lower().replace(' ', '_'),
                    'name': char.get('name', ''),
                    'aliases': char.get('aliases', []),
                    'role': char.get('role', 'unknown'),
                    'first_appearance': char.get('chapter_first_appeared'),
                    'physical_description': {
                        'age': char.get('age'),
                        'gender': char.get('gender'),
                        'height': char.get('height'),
                        'build': char.get('build'),
                        'hair': char.get('hair'),
                        'eyes': char.get('eyes'),
                        'skin_tone': char.get('skin_tone'),
                        'clothing': char.get('clothing'),
                        'distinguishing_features': char.get('distinguishing_features', '')
                    },
                    'personality_traits': char.get('personality_traits', []),
                    'relationships': char.get('relationships', {}),
                    'key_scenes': char.get('key_scenes', []),
                    'visual_notes': char.get('distinguishing_features', '')
                }
                for char in characters
            ]
        }
    
    def _sanitize_filename(self, name: str) -> str:
        """Sanitize character name for filename."""
        import re
        return re.sub(r'[^a-z0-9]+', '_', name.lower())


def main():
    """Test Stage 4 runner."""
    import sys
    sys.path.insert(0, 'src')
    
    # Load Stage 2 analysis
    with open('output/projects/strange-case-of-dr-jekyll-and-20260216-20260215/intermediate/analysis.json') as f:
        stage2_data = json.load(f)
    
    # Run Stage 4
    runner = Stage4Runner()
    result = runner.run(
        stage2_analysis=stage2_data,
        output_dir='output/projects/strange-case-of-dr-jekyll-and-20260216-20260215/character_design'
    )
    
    print(f"Generated {result['character_count']} character reference sheets")
    print(f"Output: {result['output_files']['master_index']}")


if __name__ == "__main__":
    main()
