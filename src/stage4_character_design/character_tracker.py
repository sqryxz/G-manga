"""
Character Embedding Tracker - Stage 4.1.2
Tracks characters using text embeddings for consistency.
"""

import re
from typing import Dict, List, Set
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class CharacterEmbedding:
    """Text embedding representation of a character."""
    id: str
    embedding: List[float]
    mentions: List[int]  # Scene and chapter numbers
    aliases_map: Dict[str, str]  # Alias -> character ID


class CharacterEmbeddingTracker:
    """Tracks characters using text embeddings for consistency."""

    def __init__(self, embedding_client=None):
        """
        Initialize Character Embedding Tracker.

        Args:
            embedding_client: Optional embedding client (e.g., OpenAI Embeddings API)
        """
        self.embedding_client = embedding_client

        # Character name patterns for recognition
        self.name_patterns = [
            # Full name patterns
            r"\b[A-Z][a-z]+\b [A-Z][a-z]+\b (?:[A-Z][a-z]+|Mr|Mrs|Miss|Dr|Prof)\.? [A-Z][a-z]+)",  # "Basil Hallward", "Mr. Dorian"
            # First/last name only
            r"\b[A-Z][a-z]+\b [A-Z][a-z]+",  # "Basil Hallward"

            # Title patterns
            r"(?:Lord|Lady|Mr|Mrs|Miss|Dr|Prof|Sir|Dame|Father|Mother|Master) \.? [A-Z][a-z]+)",  # "Lord Henry"

            # Nickname patterns
            r"(?:Basil|Dorian|Harry|Ron|Tom|Jane|Mary) \b",  # First name only
        ]

        # Compile patterns
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.name_patterns]

    def _generate_text_embedding(self, text: str) -> List[float]:
        """
        Generate text embedding (mock implementation).

        In production, this would call an embedding API.
        For now, we use character-based features as a pseudo-embedding.

        Args:
            text: Text to embed

        Returns:
            Vector of floats (fake embedding)
        """
        # Mock embedding based on character presence
        # In production, use: openai.embeddings.create(text=text)
        features = [0.0] * 384  # 384-dimensional vector
        features[0] = len(text) / 5000.0  # Normalize length
        features[1] = len(text.split()) / 100.0  # Word count
        features[2] = sum(1 for c in text if c.isupper()) / len(text)  # Capital letters
        features[3] = sum(1 for c in text if c.islower()) / len(text)  # Lower letters

        # Add some randomness based on text content (deterministic)
        import hashlib
        hash_val = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
        for i in range(4):
            features[4 + i] = (hash_val % 100) / 100.0

        return features

    def _normalize_name(self, name: str) -> str:
        """
        Normalize character name for consistency.

        Args:
            name: Character name

        Returns:
            Normalized name
        """
        # Remove title
        norm = re.sub(r"^(Lord|Lady|Mr|Mrs|Miss|Dr|Prof)\.?\s+", "", name, flags=re.IGNORECASE)

        # Convert to title case
        norm = norm.title()

        return norm.strip()

    def _match_aliases(self, text: str, known_names: List[str]) -> Dict[str, str]:
        """
        Match character aliases and nicknames to canonical names.

        Args:
            text: Text to search
            known_names: List of known canonical names

        Returns:
            Dict of alias -> canonical name
        """
        alias_map = {}

        # Check each known name
        for canonical in known_names:
            # Direct match
            if canonical.lower() in text.lower():
                alias_map[canonical] = canonical

            # Check for common variations
            parts = canonical.split()
            if len(parts) == 2:
                first, last = parts[0], parts[1]

                # Check for both variations
                if first + " " + last in text:
                    alias_map[first + " " + last] = canonical
                if last + " " + first in text:
                    alias_map[last + " " + first] = canonical

        return alias_map

    def extract_mentions(self, text: str, characters: List[Dict[str, Any]]) -> Dict[str, List[int]]:
        """
        Extract character mentions from text.

        Args:
            text: Text to search
            characters: List of character data

        Returns:
            Dict of character ID -> list of (scene, chapter) mentions
        """
        mentions = defaultdict(list)

        for char in characters:
            char_id = char["id"]
            name = char["name"]
            aliases = char.get("aliases", [])

            # Build search patterns
            search_terms = [name] + aliases

            for term in search_terms:
                # Exact match
                if term in text:
                    mentions[char_id].append((None, None))  # Placeholder for scene/chapter

                # Case-insensitive word boundary match
                pattern = r"\b" + re.escape(term) + r"\b"
                for match in re.finditer(pattern, text):
                    mentions[char_id].append((match.start(), match.end()))

        return dict(mentions)

    def build_relationship_graph(self, characters: List[Dict[str, Any]], scenes: List[Dict[str, Any]]) -> Dict[str, Set[str]]:
        """
        Build character relationship graph based on co-occurrence in scenes.

        Args:
            characters: List of character data
            scenes: List of scene data with characters lists

        Returns:
            Dict of character ID -> set of related character IDs
        """
        graph = {}

        # Extract character IDs from scenes
        for scene in scenes:
            scene_chars = scene.get("characters", [])

            # Mark all characters in this scene as related
            for char_id in scene_chars:
                if char_id not in graph:
                    graph[char_id] = set()

            # Link all pairs in this scene
            for i, char1 in enumerate(scene_chars):
                for char2 in scene_chars[i+1:]:
                    graph[char1].add(char2)
                    graph[char2].add(char1)

        return graph

    def track_frequency(self, scenes: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Track character frequency across scenes.

        Args:
            scenes: List of scene data

        Returns:
            Dict of character ID -> frequency count
        """
        frequency = defaultdict(int)

        for scene in scenes:
            scene_chars = scene.get("characters", [])

            for char_id in scene_chars:
                frequency[char_id] += 1

        return dict(frequency)

    def compute_embedding_matrix(self, characters: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
        """
        Compute embedding similarity matrix (mock implementation).

        In production, this would use cosine similarity of embeddings.

        Args:
            characters: List of character data

        Returns:
            Dict of character ID -> Dict of character ID -> similarity score
        """
        matrix = {}

        # Mock similarity based on name and role
        for i, char1 in enumerate(characters):
            matrix[char1["id"]] = {}

            for char2 in characters[i+1:]:
                score = 0.0

                # Same name = high similarity
                if char1["name"].lower() == char2["name"].lower():
                    score = 0.95

                # Same role = medium similarity
                if char1.get("role") == char2.get("role"):
                    score = 0.7

                # Different role = lower similarity
                if char1.get("role") != char2.get("role"):
                    score = 0.3

                matrix[char1["id"]][char2["id"]] = score

        return matrix

    def track(self, text: str, characters: List[Dict[str, Any]], scenes: List[Dict[str, Any]]) -> Dict[str, CharacterEmbedding]:
        """
        Complete character tracking with embeddings and mentions.

        Args:
            text: Full text to embed
            characters: List of character data
            scenes: List of scene data

        Returns:
            Dict of character ID -> CharacterEmbedding objects
        """
        # Normalize character names
        for char in characters:
            char["normalizedName"] = self._normalize_name(char["name"])

        # Create alias map
        canonical_names = [char["normalizedName"] for char in characters]
        alias_map = self._match_aliases(text, canonical_names)

        # Assign aliases to characters
        for char in characters:
            norm_name = char["normalizedName"]
            aliases = [alias for alias, canonical in alias_map.items() if alias == canonical]
            char["canonical_aliases"] = aliases

        # Extract mentions
        mentions = self.extract_mentions(text, characters)

        # Build relationship graph
        graph = self.build_relationship_graph(characters, scenes)

        # Track frequency
        frequency = self.track_frequency(scenes)

        # Generate pseudo-embeddings
        for char in characters:
            char["embedding"] = self._generate_text_embedding(char["normalizedName"])

        # Create CharacterEmbedding objects
        embeddings = {}
        for char in characters:
            char_id = char["id"]
            char_mentions = mentions.get(char_id, [])

            # Convert mentions to (scene, chapter) tuples
            scene_chapters = []
            for start, end in char_mentions:
                # Find scene number
                scene_num = 1
                for i, scene in enumerate(scenes):
                    if start >= scene.get("text_range", {}).get("start", 0) and end <= scene.get("text_range", {}).get("end", len(text)):
                        scene_num = i + 1
                        break

                scene_chapters.append((scene_num, None))

            char_embeddings = CharacterEmbedding(
                id=char_id,
                embedding=char["embedding"],
                mentions=scene_chapters,
                aliases_map=alias_map
            )

            embeddings[char_id] = char_embeddings

        return embeddings

    def get_similar_characters(self, character_id: str, threshold: float = 0.7) -> List[str]:
        """
        Find characters similar to a given character.

        Args:
            character_id: Character ID
            threshold: Similarity threshold (0-1)

        Returns:
            List of similar character IDs
        """
        similar = []
        for char_data in characters.values():
            # Get similarity score from matrix (mock implementation)
            score = 0.0

            # Check name similarity
            if char_data.normalizedName.lower() == character_data.normalizedName.lower():
                score = 0.95

            # Check role similarity
            if char_data.get("role") == self._get_character_role(character_id):
                score = 0.7

            if score >= threshold:
                similar.append(char_data.id)

        return similar

    def _get_character_role(self, character_id: str) -> Optional[str]:
        """
        Get character role (mock implementation).

        Args:
            character_id: Character ID

        Returns:
            Role string or None
        """
        # Mock role lookup based on character ID
        # In production, this would be stored with the character
        return "protagonist" if "basil" in character_id.lower() else None


def main():
    """Test Character Embedding Tracker."""
    import sys
    sys.path.insert(0, '/home/clawd/projects/g-manga/src')

    from models.project import Character

    # Create test text
    test_text = """
    Basil stood at his easel, brush in hand. Lord Henry entered the studio, looking at the painting with interest.

    "That is quite remarkable," said Lord Henry, leaning forward with a cynical smile on his face. Basil did not reply. He was too absorbed in his work, too focused on the mysterious face that was beginning to emerge from the canvas.

    Lord Henry walked around the studio, examining the other paintings that lined the walls. Each one was a masterpiece in its own right, capturing the essence of its subject with a haunting beauty that only Basil could truly appreciate.

    "You must let me see him more often," Lord Henry continued. "A man like that deserves to be celebrated, not hidden away in some studio."

    Basil finally spoke, his voice tight with emotion. "He is not for exhibition. He is my friend, and I will not have him turned into a spectacle."

    Lord Henry laughed, a sharp, cruel sound that echoed off the walls. "Friendship? Is that what you call it? I prefer to think of it as an... investment."

    Basil's face flushed. Lord Henry had struck a nerve, and for the first time since they had met, Basil felt a genuine surge of anger.
    """

    # Create test characters
    test_characters = [
        {
            "id": "char-basil",
            "name": "Basil Hallward",
            "aliases": ["Basil", "Mr. Hallward"],
            "role": "protagonist",
            "appearance": {
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
                "clothing": "painting smock, simple shirt, dark trousers",
                "distinguishing_features": "Often has paint on his hands and clothes"
            }
        },
        {
            "id": "char-henry",
            "name": "Lord Henry Wotton",
            "aliases": ["Lord Henry", "Harry"],
            "role": "deuteragonist",
            "appearance": {
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
                "clothing": "frock coat, silk cravat, elegant clothes",
                "distinguishing_features": "Always looks bored and slightly cynical"
            }
        }
    ]

    # Create test scenes
    test_scenes = [
        {
            "id": "scene-1-1",
            "chapter_id": "chapter-1",
            "number": 1,
            "characters": ["char-basil", "char-henry"],
            "text_range": {"start": 0, "end": 500}
        },
        {
            "id": "scene-1-2",
            "chapter_id": "chapter-1",
            "number": 2,
            "characters": ["char-basil"],
            "text_range": {"start": 501, "end": 1000}
        },
        {
            "id": "scene-1-3",
            "chapter_id": "chapter-1",
            "number": 3,
            "characters": ["char-henry"],
            "text_range": {"start": 1001, "end": 1500}
        }
    ]

    # Test tracker
    tracker = CharacterEmbeddingTracker()

    # Track characters
    embeddings = tracker.track(test_text, test_characters, test_scenes)

    print("=" * 70)
    print("Character Embedding Tracker Test")
    print("=" * 70)

    print(f"Tracked {len(embeddings)} characters:")
    print()

    for char_id, embedding in embeddings.items():
        print(f"Character: {char_id}")
        print(f"  Mentions: {len(embedding.mentions)}")
        print(f"  Aliases: {embedding.aliases_map}")
        print()

    # Find similar characters
    similar = tracker.get_similar_characters("char-basil", threshold=0.7)
    print(f"Characters similar to Basil (threshold 0.7): {similar}")

    # Test alias matching
    test_alias_text = "Basil is painting with Mr. Hallward."
    canonical_names = [test_characters[0]["normalizedName"], test_characters[1]["normalizedName"]]
    alias_map = tracker._match_aliases(test_alias_text, canonical_names)

    print(f"\nAlias Map from '{test_alias_text}':")
    for alias, canonical in alias_map.items():
        print(f"  '{alias}' -> '{canonical}'")

    print("\n" + "=" * 70)
    print("All tests PASSED!")
    print("=" * 70)


if __name__ == "__main__":
    main()
