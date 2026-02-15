#!/usr/bin/env python3
"""
Character Consistency System for G-Manga Pipeline

This script enhances panel prompts by adding character reference data
to ensure visual consistency across all panels.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional


class CharacterConsistencySystem:
    """Manages character consistency across manga panels."""
    
    def __init__(self, project_root: str = "/home/clawd/projects/g-manga"):
        self.project_root = Path(project_root)
        self.character_mapping: Dict = {}
        self.character_aliases: Dict[str, str] = {
            "Dorian": "Dorian Gray",
            "Basil": "Basil Hallward",
            "Lord Henry": "Lord Henry Wotton",
            "Henry": "Lord Henry Wotton",
            "Wotton": "Lord Henry Wotton",
            "Hallward": "Basil Hallward",
            "Sibyl": "Sibyl Vane",
            "James": "James Vane",
            "Victoria": "Lady Victoria Wotton",
            "Alan": "Alan Campbell",
            "Lady Narborough": "Lady Narborough",
            "Adrian": "Adrian Singleton",
        }
    
    def load_character_mapping(self, mapping_path: str) -> Dict:
        """Load character mapping from JSON file."""
        path = self.project_root / mapping_path
        with open(path, 'r') as f:
            self.character_mapping = json.load(f)
        return self.character_mapping
    
    def detect_characters_in_text(self, text: str) -> List[str]:
        """Detect character names mentioned in text."""
        found_characters = []
        
        # More precise pattern matching - look for full names or clear mentions
        # Only match when character name appears as a distinct entity
        
        # First, check for full canonical names
        for canonical_name in self.character_aliases.values():
            # Use word boundary matching to avoid partial matches
            pattern = r'\b' + re.escape(canonical_name) + r'\b'
            if re.search(pattern, text, re.IGNORECASE):
                if canonical_name not in found_characters:
                    found_characters.append(canonical_name)
        
        # Also check for aliases that aren't just parts of other words
        for alias, canonical_name in self.character_aliases.items():
            # Skip single words that might match common text
            if len(alias) <= 3:
                continue
            pattern = r'\b' + re.escape(alias) + r'\b'
            if re.search(pattern, text, re.IGNORECASE):
                if canonical_name not in found_characters:
                    found_characters.append(canonical_name)
        
        return found_characters
    
    def get_character_reference(self, character_name: str) -> Optional[Dict]:
        """Get character reference data for a character."""
        if character_name not in self.character_mapping.get("characters", {}):
            return None
        
        char_data = self.character_mapping["characters"][character_name]
        return {
            "name": character_name,
            "reference_sheet": char_data.get("reference_sheet", ""),
            "appearance": self._build_appearance_string(char_data),
            "clothing": self._build_clothing_string(char_data),
            "color_palette": char_data.get("color_palette", {}),
            "key_features": char_data.get("key_features", []),
            "height": char_data.get("height", ""),
            "build": char_data.get("build", "")
        }
    
    def _build_appearance_string(self, char_data: Dict) -> str:
        """Build a concise appearance description."""
        parts = []
        if char_data.get("height"):
            parts.append(char_data["height"])
        if char_data.get("build"):
            parts.append(char_data["build"])
        
        key_features = char_data.get("key_features", [])
        if key_features:
            parts.extend(key_features[:3])  # Take first 3 key features
        
        return ", ".join(parts)
    
    def _build_clothing_string(self, char_data: Dict) -> str:
        """Build a clothing description."""
        clothing = char_data.get("clothing", [])
        if clothing:
            return ", ".join(clothing[:2])  # Take first 2 clothing items
        return ""
    
    def enhance_panel_prompt(self, panel_data: Dict) -> Dict:
        """Enhance a single panel with character references."""
        prompt = panel_data.get("prompt", "")
        characters = self.detect_characters_in_text(prompt)
        
        character_refs = []
        for char_name in characters:
            ref = self.get_character_reference(char_name)
            if ref:
                character_refs.append(ref)
        
        # Add character references to prompt
        enhanced_prompt = prompt
        if character_refs:
            char_ref_section = self._format_character_refs(character_refs)
            enhanced_prompt = f"{prompt}\n\nCHARACTER REFERENCES:\n{char_ref_section}"
        
        panel_data["prompt"] = enhanced_prompt
        panel_data["character_refs"] = character_refs
        panel_data["detected_characters"] = characters
        
        return panel_data
    
    def _format_character_refs(self, character_refs: List[Dict]) -> str:
        """Format character references for the prompt."""
        lines = []
        for ref in character_refs:
            lines.append(f"- {ref['name']}: {ref['appearance']}")
            if ref['clothing']:
                lines[-1] += f", {ref['clothing']}"
            lines[-1] += f" | Reference: {ref['reference_sheet']}"
        return "\n".join(lines)
    
    def process_panel_prompts(self, panel_prompts_path: str, output_path: str = None) -> Dict:
        """Process all panel prompts and add character references."""
        with open(self.project_root / panel_prompts_path, 'r') as f:
            panels = json.load(f)
        
        enhanced_panels = []
        for panel in panels:
            enhanced_panels.append(self.enhance_panel_prompt(panel))
        
        result = {
            "panels": enhanced_panels,
            "metadata": {
                "total_panels": len(enhanced_panels),
                "panels_with_characters": sum(1 for p in enhanced_panels if p.get("character_refs")),
                "processed_with_character_refs": True
            }
        }
        
        if output_path:
            output_file = self.project_root / output_path
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
        
        return result
    
    def generate_character_report(self) -> Dict:
        """Generate a report of character usage."""
        if not self.character_mapping:
            return {"error": "No character mapping loaded"}
        
        report = {
            "total_characters": len(self.character_mapping.get("characters", {})),
            "characters": {}
        }
        
        for name, data in self.character_mapping.get("characters", {}).items():
            report["characters"][name] = {
                "height": data.get("height", ""),
                "build": data.get("build", ""),
                "key_features": data.get("key_features", [])[:3],
                "reference_sheet": data.get("reference_sheet", ""),
                "color_palette": data.get("color_palette", {})
            }
        
        return report


def main():
    """Main entry point for the character consistency system."""
    system = CharacterConsistencySystem()
    
    # Load character mapping
    char_mapping_path = "output/projects/picture-of-dorian-gray-20260213-20260213/intermediate/character_mapping.json"
    system.load_character_mapping(char_mapping_path)
    
    # Process panel prompts
    panel_prompts_path = "output/projects/picture-of-dorian-gray-20260212-20260212/intermediate/panel_prompts.json"
    output_path = "output/projects/picture-of-dorian-gray-20260213-20260213/intermediate/panel_prompts.json"
    
    result = system.process_panel_prompts(panel_prompts_path, output_path)
    
    # Print summary
    print(f"Processed {result['metadata']['total_panels']} panels")
    print(f"Panels with character references: {result['metadata']['panels_with_characters']}")
    print(f"\nCharacter Report:")
    report = system.generate_character_report()
    print(f"Total characters defined: {report['total_characters']}")
    
    return result


if __name__ == "__main__":
    main()
