"""Stage 3: Adaptation Planner - Main Orchestrator

Orchestrates the complete adaptation planning process:
1. Novel-level analysis (run ONCE on full book)
2. Chapter-level analysis (uses novel context)
3. Page allocation
4. Splash page identification
5. Scene compression decisions

Usage:
    planner = AdaptationPlanner()
    plan = planner.plan(analysis_result, target_pages=100)
"""

import json
from typing import List, Optional, Dict, Any
from dataclasses import asdict

from .schemas import (
    NovelLevelAnalysis, ChapterLevelAnalysis, AdaptationPlan,
    PageAllocation, SplashPage, EmotionalPeak, CharacterArc,
    NarrativeArc, PacingStructure, ArcRole, ChapterRole, PageType
)
from .page_allocator import PageAllocator, PageAllocationConfig
from .compression_decider import CompressionDecider
from .splash_page_id import SplashPageIdentifier


class NovelLevelAnalyzer:
    """Analyzes novel structure at the narrative level."""
    
    def __init__(self, llm_client=None, model: str = "aurora-alpha"):
        self.llm_client = llm_client
        self.model = model
    
    def analyze(self, analysis_result, title: str = "", author: str = "") -> NovelLevelAnalysis:
        """
        Perform novel-level analysis using Stage 2 analysis results.
        
        Args:
            analysis_result: Result from Stage 2 analysis engine
            title: Book title
            author: Book author
        
        Returns:
            NovelLevelAnalysis with narrative structure
        """
        # Extract information from analysis result
        characters = self._extract_characters(analysis_result)
        plot_beats = self._extract_plot_beats(analysis_result)
        locations = self._extract_locations(analysis_result)
        dialogue = self._extract_dialogue(analysis_result)
        
        # Determine chapter count
        total_chapters = self._count_chapters(analysis_result)
        
        # Analyze narrative arcs
        narrative_arcs = self._analyze_narrative_arcs(
            plot_beats, total_chapters, analysis_result
        )
        
        # Analyze pacing structure
        pacing_structure = self._analyze_pacing_structure(
            plot_beats, total_chapters, narrative_arcs
        )
        
        # Identify emotional peaks
        emotional_peaks = self._identify_emotional_peaks(
            plot_beats, dialogue, total_chapters
        )
        
        # Analyze character arcs
        character_arcs = self._analyze_character_arcs(
            characters, plot_beats, total_chapters
        )
        
        # Identify major themes
        major_themes = self._identify_themes(analysis_result)
        
        # Determine mood/tone
        mood_tone = self._determine_mood_tone(analysis_result)
        
        # Identify key symbols
        key_symbols = self._identify_symbols(analysis_result)
        
        return NovelLevelAnalysis(
            title=title or "Unknown Title",
            author=author or "Unknown Author",
            total_chapters=total_chapters,
            narrative_arcs=narrative_arcs,
            pacing_structure=pacing_structure,
            major_themes=major_themes,
            mood_tone=mood_tone,
            character_arcs=character_arcs,
            emotional_peaks=emotional_peaks,
            protagonist=self._find_protagonist(characters),
            central_conflict=self._identify_central_conflict(plot_beats, major_themes),
            thematic_statements=major_themes,
            story_rhythm=self._determine_story_rhythm(plot_beats, total_chapters),
            key_symbols=key_symbols
        )
    
    def _extract_characters(self, analysis_result) -> List:
        """Extract characters from analysis result."""
        if hasattr(analysis_result, 'characters'):
            return analysis_result.characters
        elif isinstance(analysis_result, dict) and 'characters' in analysis_result:
            return analysis_result['characters']
        return []
    
    def _extract_plot_beats(self, analysis_result) -> List:
        """Extract plot beats from analysis result."""
        if hasattr(analysis_result, 'plot_beats'):
            return analysis_result.plot_beats
        elif isinstance(analysis_result, dict) and 'plot_beats' in analysis_result:
            return analysis_result['plot_beats']
        return []
    
    def _extract_locations(self, analysis_result) -> List:
        """Extract locations from analysis result."""
        if hasattr(analysis_result, 'locations'):
            return analysis_result.locations
        elif isinstance(analysis_result, dict) and 'locations' in analysis_result:
            return analysis_result['locations']
        return []
    
    def _extract_dialogue(self, analysis_result) -> List:
        """Extract dialogue from analysis result."""
        if hasattr(analysis_result, 'dialogue'):
            return analysis_result.dialogue
        elif isinstance(analysis_result, dict) and 'dialogue' in analysis_result:
            return analysis_result['dialogue']
        return []
    
    def _count_chapters(self, analysis_result) -> int:
        """Count total chapters."""
        if hasattr(analysis_result, 'chapters'):
            return len(analysis_result.chapters)
        elif hasattr(analysis_result, 'total_chapters'):
            return analysis_result.total_chapters
        elif hasattr(analysis_result, 'plot_beats') and analysis_result.plot_beats:
            chapters = set()
            for beat in analysis_result.plot_beats:
                if hasattr(beat, 'chapter'):
                    chapters.add(beat.chapter)
            if chapters:
                return max(chapters)
        return 10
    
    def _analyze_narrative_arcs(
        self,
        plot_beats: List,
        total_chapters: int,
        analysis_result
    ) -> List[NarrativeArc]:
        """Analyze narrative arcs (Act 1, 2, 3 structure) from plot beats."""
        arcs = []
        
        # If we have actual plot beats, derive arcs from them
        if plot_beats and len(plot_beats) > 0:
            arcs = self._derive_arcs_from_beats(plot_beats, total_chapters)
        
        # If no arcs derived or not enough data, create generic arc structure
        if not arcs:
            arcs = self._create_generic_arcs(total_chapters)
        
        return arcs
    
    def _derive_arcs_from_beats(
        self,
        plot_beats: List,
        total_chapters: int
    ) -> List[NarrativeArc]:
        """Derive narrative arcs from actual plot beats."""
        arcs = []
        
        # Group beats by chapter to find act boundaries
        beats_by_chapter = {}
        for beat in plot_beats:
            chapter = getattr(beat, 'chapter', 1)
            if chapter not in beats_by_chapter:
                beats_by_chapter[chapter] = []
            beats_by_chapter[chapter].append(beat)
        
        # Determine act boundaries based on chapter distribution
        # Standard 3-act structure: 25%, 50%, 25%
        act_boundaries = [
            (1, int(total_chapters * 0.25), ArcRole.SETUP, "Setup"),
            (int(total_chapters * 0.25) + 1, int(total_chapters * 0.75), ArcRole.RISING_ACTION, "Rising Action"),
            (int(total_chapters * 0.75) + 1, total_chapters, ArcRole.CLIMAX, "Climax")
        ]
        
        # Add falling action and resolution for longer works
        if total_chapters > 10:
            act_boundaries = [
                (1, int(total_chapters * 0.20), ArcRole.SETUP, "Setup"),
                (int(total_chapters * 0.20) + 1, int(total_chapters * 0.50), ArcRole.RISING_ACTION, "Rising Action"),
                (int(total_chapters * 0.50) + 1, int(total_chapters * 0.75), ArcRole.RISING_ACTION, "Escalation"),
                (int(total_chapters * 0.75) + 1, int(total_chapters * 0.90), ArcRole.CLIMAX, "Climax"),
                (int(total_chapters * 0.90) + 1, total_chapters, ArcRole.FALLING_ACTION, "Falling Action"),
                (total_chapters, total_chapters, ArcRole.RESOLUTION, "Resolution")
            ]
        
        # Filter valid boundaries
        act_boundaries = [(s, e, r, t) for s, e, r, t in act_boundaries if s <= total_chapters]
        
        for i, (start, end, arc_role, theme_base) in enumerate(act_boundaries):
            # Get beats in this act
            act_beats = []
            for ch in range(start, min(end + 1, total_chapters + 1)):
                if ch in beats_by_chapter:
                    for beat in beats_by_chapter[ch]:
                        desc = getattr(beat, 'description', str(beat))
                        if desc:
                            act_beats.append(desc[:100])  # Truncate for storage
            
            # Unique events only
            key_events = list(dict.fromkeys(act_beats))[:5]  # Max 5 key events per act
            
            # Generate theme from beats if available
            theme = self._generate_theme_from_beats(key_events, arc_role, theme_base)
            
            arcs.append(NarrativeArc(
                act_number=i + 1,
                chapters=list(range(start, min(end + 1, total_chapters + 1))),
                theme=theme,
                arc_role=arc_role,
                key_events=key_events,
                emotional_tone=self._get_act_tone(arc_role)
            ))
        
        return arcs
    
    def _generate_theme_from_beats(
        self,
        key_events: List[str],
        arc_role: ArcRole,
        default_theme: str
    ) -> str:
        """Generate a theme description from key events."""
        if not key_events:
            return default_theme
        
        # Use first significant event as theme anchor
        first_event = key_events[0] if key_events else default_theme
        
        # Map arc role to appropriate theme framing
        role_themes = {
            ArcRole.SETUP: f"Introduction: {first_event}",
            ArcRole.RISING_ACTION: f"Development: {first_event}",
            ArcRole.CLIMAX: f"Crisis: {first_event}",
            ArcRole.FALLING_ACTION: f"Resolution: {first_event}",
            ArcRole.RESOLUTION: f"Conclusion: {first_event}"
        }
        
        return role_themes.get(arc_role, default_theme)
    
    def _create_generic_arcs(self, total_chapters: int) -> List[NarrativeArc]:
        """Create generic arc structure when no plot beats available."""
        arcs = []
        
        # Standard 5-act structure
        act_configs = [
            (1, int(total_chapters * 0.20), ArcRole.SETUP, "Setup and Introduction"),
            (int(total_chapters * 0.20) + 1, int(total_chapters * 0.50), ArcRole.RISING_ACTION, "Rising Action"),
            (int(total_chapters * 0.50) + 1, int(total_chapters * 0.75), ArcRole.CLIMAX, "Climax"),
            (int(total_chapters * 0.75) + 1, int(total_chapters * 0.90), ArcRole.FALLING_ACTION, "Falling Action"),
            (int(total_chapters * 0.90) + 1, total_chapters, ArcRole.RESOLUTION, "Resolution")
        ]
        
        for i, (start, end, role, theme) in enumerate(act_configs):
            if start > total_chapters:
                break
            end = min(end, total_chapters)
            
            arcs.append(NarrativeArc(
                act_number=i + 1,
                chapters=list(range(start, end + 1)),
                theme=theme,
                arc_role=role,
                key_events=[],
                emotional_tone=self._get_act_tone(role)
            ))
        
        return arcs
    
    def _get_act_tone(self, arc_role: ArcRole) -> str:
        """Get emotional tone for arc role."""
        tones = {
            ArcRole.SETUP: "hopeful, curious, beautiful",
            ArcRole.RISING_ACTION: "intensifying, hedonistic, tense",
            ArcRole.CLIMAX: "dark, desperate, tragic",
            ArcRole.FALLING_ACTION: "despairing, inevitable",
            ArcRole.RESOLUTION: "reflective, cautionary"
        }
        return tones.get(arc_role, "neutral")
    
    def _analyze_pacing_structure(
        self,
        plot_beats: List,
        total_chapters: int,
        narrative_arcs: List[NarrativeArc]
    ) -> PacingStructure:
        """Analyze pacing structure."""
        # Calculate chapter ranges for each phase
        setup_end = int(total_chapters * 0.20)
        rising_end = int(total_chapters * 0.60)
        climax_end = int(total_chapters * 0.80)
        falling_end = int(total_chapters * 0.92)
        
        return PacingStructure(
            setup_chapters=list(range(1, setup_end + 1)),
            rising_action_chapters=list(range(setup_end + 1, rising_end + 1)),
            climax_chapters=list(range(rising_end + 1, climax_end + 1)),
            falling_action_chapters=list(range(climax_end + 1, falling_end + 1)),
            resolution_chapters=list(range(falling_end + 1, total_chapters + 1)),
            setup_ratio=0.20,
            rising_ratio=0.40,
            climax_ratio=0.20,
            falling_ratio=0.12,
            resolution_ratio=0.08
        )
    
    def _identify_emotional_peaks(
        self,
        plot_beats: List,
        dialogue: List,
        total_chapters: int
    ) -> List[EmotionalPeak]:
        """Identify emotional peaks in the story from plot beats and dialogue."""
        peaks = []
        
        # Derive peaks from plot beats if available
        if plot_beats and len(plot_beats) > 0:
            peaks = self._derive_peaks_from_beats(plot_beats, total_chapters)
        
        # Also check dialogue for emotional intensity
        if dialogue and len(dialogue) > 0:
            dialogue_peaks = self._derive_peaks_from_dialogue(dialogue, total_chapters)
            # Merge with beat-derived peaks
            existing_chapters = {p.chapter for p in peaks}
            for peak in dialogue_peaks:
                if peak.chapter not in existing_chapters:
                    peaks.append(peak)
        
        # Sort by chapter
        peaks.sort(key=lambda p: p.chapter)
        
        # If still no peaks, generate based on structural positions
        if not peaks:
            peaks = self._generate_structural_peaks(total_chapters)
        
        return peaks
    
    def _derive_peaks_from_beats(
        self,
        plot_beats: List,
        total_chapters: int
    ) -> List[EmotionalPeak]:
        """Derive emotional peaks from plot beats."""
        peaks = []
        
        # Find major beats (is_major=True) or emotional/decision types
        major_beats = [
            b for b in plot_beats
            if (getattr(b, 'is_major', False) or 
                getattr(b, 'beat_type', '') in ['emotional', 'decision', 'revelation'])
        ]
        
        # Group by chapter and score by intensity
        chapter_scores = {}
        for beat in major_beats:
            chapter = getattr(beat, 'chapter', 1)
            beat_type = getattr(beat, 'beat_type', 'action')
            
            # Score based on beat type
            type_scores = {
                'revelation': 8.5,
                'decision': 8.0,
                'emotional': 9.0,
                'action': 6.0
            }
            score = type_scores.get(beat_type, 6.0)
            
            if chapter not in chapter_scores:
                chapter_scores[chapter] = {'score': 0, 'beats': [], 'type': beat_type}
            
            if score > chapter_scores[chapter]['score']:
                chapter_scores[chapter]['score'] = score
                chapter_scores[chapter]['beats'] = [getattr(beat, 'description', 'Key moment')]
                chapter_scores[chapter]['type'] = beat_type
        
        # Convert to EmotionalPeak objects
        for chapter, data in chapter_scores.items():
            if chapter <= total_chapters:
                peak_type_map = {
                    'revelation': 'revelation',
                    'decision': 'tension',
                    'emotional': 'climax',
                    'action': 'action'
                }
                
                peaks.append(EmotionalPeak(
                    chapter=chapter,
                    description=data['beats'][0] if data['beats'] else f"Chapter {chapter} peak",
                    intensity=data['score'],
                    peak_type=peak_type_map.get(data['type'], 'tension'),
                    key_moment=data['beats'][0] if data['beats'] else ""
                ))
        
        return peaks
    
    def _derive_peaks_from_dialogue(
        self,
        dialogue: List,
        total_chapters: int
    ) -> List[EmotionalPeak]:
        """Derive emotional peaks from dialogue intensity."""
        peaks = []
        
        # Find chapters with high emotional dialogue
        emotional_tones = {'angry', 'sad', 'intense', 'dramatic', 'desperate', 'joyful'}
        
        chapter_emotions = {}
        for dial in dialogue:
            chapter = getattr(dial, 'chapter', 0)
            if chapter == 0:
                continue
            tone = getattr(dial, 'tone', 'neutral').lower()
            
            if tone in emotional_tones:
                if chapter not in chapter_emotions:
                    chapter_emotions[chapter] = {'count': 0, 'tones': set()}
                chapter_emotions[chapter]['count'] += 1
                chapter_emotions[chapter]['tones'].add(tone)
        
        # Convert to peaks
        for chapter, data in chapter_emotions.items():
            if chapter <= total_chapters and data['count'] >= 2:
                peaks.append(EmotionalPeak(
                    chapter=chapter,
                    description=f"Emotional dialogue scene",
                    intensity=7.0 + (data['count'] * 0.5),
                    peak_type='emotional',
                    key_moment=f"Tone: {', '.join(data['tones'])}"
                ))
        
        return peaks
    
    def _generate_structural_peaks(self, total_chapters: int) -> List[EmotionalPeak]:
        """Generate peaks at structural positions when no data available."""
        peaks = []
        
        # Standard structural peak positions
        if total_chapters >= 3:
            peaks.append(EmotionalPeak(
                chapter=1,
                description="Opening incident",
                intensity=7.0,
                peak_type='setup',
                key_moment="Story begins"
            ))
        
        if total_chapters >= 5:
            peaks.append(EmotionalPeak(
                chapter=max(1, int(total_chapters * 0.25)),
                description="First turning point",
                intensity=7.5,
                peak_type='turning_point',
                key_moment="Major plot development"
            ))
        
        if total_chapters >= 10:
            peaks.append(EmotionalPeak(
                chapter=max(1, int(total_chapters * 0.50)),
                description="Midpoint",
                intensity=8.0,
                peak_type='revelation',
                key_moment="Mid-story revelation"
            ))
        
        if total_chapters >= 15:
            peaks.append(EmotionalPeak(
                chapter=max(1, int(total_chapters * 0.75)),
                description="Pre-climax",
                intensity=8.5,
                peak_type='tension',
                key_moment="Building to climax"
            ))
        
        if total_chapters >= 3:
            peaks.append(EmotionalPeak(
                chapter=total_chapters,
                description="Final confrontation",
                intensity=9.0,
                peak_type='climax',
                key_moment="Story climax"
            ))
        
        return peaks
    
    def _analyze_character_arcs(
        self,
        characters: List,
        plot_beats: List,
        total_chapters: int
    ) -> List[CharacterArc]:
        """Analyze character arcs from character data and plot beats."""
        arcs = []
        
        # If we have characters from Stage 2, derive arcs from them
        if characters and len(characters) > 0:
            arcs = self._derive_arcs_from_characters(characters, plot_beats, total_chapters)
        
        # If no arcs derived, try to infer from plot beats
        if not arcs and plot_beats and len(plot_beats) > 0:
            arcs = self._infer_arcs_from_beats(plot_beats, total_chapters)
        
        return arcs
    
    def _derive_arcs_from_characters(
        self,
        characters: List,
        plot_beats: List,
        total_chapters: int
    ) -> List[CharacterArc]:
        """Derive character arcs from Stage 2 character data."""
        arcs = []
        
        # Group plot beats by character mentions
        character_beats = {c.name: [] for c in characters}
        
        # Use character relationships and first appearances
        
        for char in characters:
            name = char.name
            role = getattr(char, 'role', 'supporting')
            relationships = getattr(char, 'relationships', {})
            first_chapter = getattr(char, 'chapter_first_appeared', 1)
            
            # Determine transformation based on role
            if role == 'protagonist':
                starting_state = "Beginning of story"
                ending_state = "End of story"
                transformation_summary = f"{name}'s journey throughout the story"
            elif role == 'antagonist':
                starting_state = "Initial opposition"
                ending_state = "Final confrontation"
                transformation_summary = f"{name}'s conflict with protagonist"
            else:
                starting_state = "Introduction"
                ending_state = "Conclusion"
                transformation_summary = f"{name}'s role in the story"
            
            # Create arc beats from relationships
            arc_beats = []
            if first_chapter > 0:
                arc_beats.append({
                    "chapter": first_chapter,
                    "description": f"{name} introduced",
                    "change": "First appearance"
                })
            
            # Add beats from relationships
            for other, rel in list(relationships.items())[:3]:
                arc_beats.append({
                    "chapter": min(first_chapter + 5, total_chapters),
                    "description": f"{name} and {other}: {rel}",
                    "change": "Relationship established"
                })
            
            arcs.append(CharacterArc(
                character_name=name,
                role=role,
                arc_beats=arc_beats,
                transformation_summary=transformation_summary,
                starting_state=starting_state,
                ending_state=ending_state
            ))
        
        return arcs
    
    def _infer_arcs_from_beats(
        self,
        plot_beats: List,
        total_chapters: int
    ) -> List[CharacterArc]:
        """Infer character arcs when no character data available."""
        arcs = []
        
        # Find unique "characters" mentioned in plot beats
        # This is a heuristic - would be better with actual character data
        unique_mentions = {}
        
        for beat in plot_beats[:20]:  # Sample first 20 beats
            desc = getattr(beat, 'description', '')
            if not desc:
                continue
            # Very basic extraction - first capitalized phrase
            words = desc.split()
            for i, word in enumerate(words):
                if word and word[0].isupper() and len(word) > 2:
                    if word not in unique_mentions:
                        unique_mentions[word] = getattr(beat, 'chapter', 1)
        
        # Create arcs for first 3 "characters" found
        for i, (name, chapter) in enumerate(list(unique_mentions.items())[:3]):
            role = 'protagonist' if i == 0 else 'supporting'
            
            arcs.append(CharacterArc(
                character_name=name,
                role=role,
                arc_beats=[
                    {"chapter": chapter, "description": f"{name} appears", "change": "Introduction"}
                ],
                transformation_summary=f"The journey of {name}",
                starting_state="Beginning",
                ending_state="Conclusion"
            ))
        
        return arcs
    
    def _identify_themes(self, analysis_result) -> List[str]:
        """Identify major themes from analysis result or key quotes."""
        themes = []
        
        # Try to extract from key quotes if available
        if hasattr(analysis_result, 'key_quotes') and analysis_result.key_quotes:
            for quote in analysis_result.key_quotes[:5]:
                significance = getattr(quote, 'significance', '')
                if significance:
                    themes.append(significance)
        
        # If still no themes, derive from plot beats
        if not themes:
            plot_beats = self._extract_plot_beats(analysis_result)
            if plot_beats:
                themes = self._derive_themes_from_beats(plot_beats)
        
        # Final fallback
        if not themes:
            themes = ["Central conflict and character development"]
        
        return themes[:6]  # Return max 6 themes
    
    def _derive_themes_from_beats(self, plot_beats: List) -> List[str]:
        """Derive themes from plot beats."""
        # Simple heuristic - look for recurring concepts
        theme_indicators = {
            'love': ['love', 'heart', 'affection', 'romance'],
            'conflict': ['fight', 'battle', 'war', 'conflict', 'struggle'],
            'death': ['death', 'die', 'kill', 'murder', 'dead'],
            'power': ['power', 'control', 'rule', 'authority'],
            'identity': ['self', 'identity', 'who am I', 'become'],
            'transformation': ['change', 'transform', 'become', 'grow'],
            'truth': ['truth', 'real', 'reveal', 'secret'],
            ' sacrifice': ['sacrifice', 'give up', 'price', 'cost']
        }
        
        # Count occurrences
        theme_counts = {t: 0 for t in theme_indicators}
        
        for beat in plot_beats:
            desc = getattr(beat, 'description', '').lower()
            for theme, keywords in theme_indicators.items():
                if any(kw in desc for kw in keywords):
                    theme_counts[theme] += 1
        
        # Return themes with highest counts
        sorted_themes = sorted(theme_counts.items(), key=lambda x: x[1], reverse=True)
        return [t for t, count in sorted_themes if count > 0][:6]
    
    def _determine_mood_tone(self, analysis_result) -> str:
        """Determine overall mood/tone from analysis data."""
        # Try dialogue tones first
        if hasattr(analysis_result, 'dialogue') and analysis_result.dialogue:
            tone_counts = {}
            for dial in analysis_result.dialogue[:50]:  # Sample
                tone = getattr(dial, 'tone', 'neutral')
                tone_counts[tone] = tone_counts.get(tone, 0) + 1
            
            if tone_counts:
                dominant_tone = max(tone_counts.items(), key=lambda x: x[1])[0]
                return f"Primarily {dominant_tone} with variations"
        
        # Check plot beat types
        plot_beats = self._extract_plot_beats(analysis_result)
        if plot_beats:
            beat_types = [getattr(b, 'beat_type', 'action') for b in plot_beats[:20]]
            action_count = beat_types.count('action')
            emotional_count = beat_types.count('emotional')
            revelation_count = beat_types.count('revelation')
            
            if emotional_count > action_count:
                return "Emotionally intense, character-driven narrative"
            elif revelation_count > 2:
                return "Mystery-driven with revelations throughout"
            else:
                return "Action-oriented plot-driven narrative"
        
        return "Balanced narrative with character and plot development"
    
    def _identify_symbols(self, analysis_result) -> List[str]:
        """Identify key symbols from analysis data."""
        symbols = []
        
        # Try to extract from key quotes
        if hasattr(analysis_result, 'key_quotes') and analysis_result.key_quotes:
            for quote in analysis_result.key_quotes[:3]:
                context = getattr(quote, 'context', '')
                if context and len(context) > 10:
                    symbols.append(f"Symbolic element in: {context[:50]}")
        
        # Try locations as symbolic settings
        locations = self._extract_locations(analysis_result)
        if locations and len(locations) > 0:
            for loc in locations[:3]:
                name = getattr(loc, 'name', '')
                if name:
                    symbols.append(f"Key location: {name}")
        
        # Fallback
        if not symbols:
            symbols = ["Recurring motifs and symbolic elements"]
        
        return symbols[:4]
    
    def _find_protagonist(self, characters: List) -> str:
        """Find protagonist name from character list."""
        # First, look for explicit protagonist role
        for char in characters:
            if hasattr(char, 'role') and char.role == 'protagonist':
                return char.name
        
        # Second, look for main/main_character role
        for char in characters:
            if hasattr(char, 'role') and char.role in ('main', 'main_character'):
                return char.name
        
        # Third, try first appearance as proxy for protagonist
        if characters:
            first_char = min(characters, key=lambda c: getattr(c, 'chapter_first_appeared', 999))
            return first_char.name
        
        # Fallback
        return "Unknown Protagonist"
    
    def _identify_central_conflict(
        self,
        plot_beats: List,
        themes: List[str]
    ) -> str:
        """Identify central conflict from plot beats and themes."""
        if themes and len(themes) > 0:
            return f"Central conflict: {themes[0]}"
        
        if plot_beats and len(plot_beats) > 0:
            # Use first major beat as conflict indicator
            major_beats = [b for b in plot_beats if getattr(b, 'is_major', False)]
            if major_beats:
                return f"Conflict: {getattr(major_beats[0], 'description', 'unknown')[:100]}"
        
        return "Primary narrative conflict"
    
    def _determine_story_rhythm(
        self,
        plot_beats: List,
        total_chapters: int
    ) -> str:
        """Determine story rhythm based on beat density."""
        if not plot_beats or total_chapters == 0:
            return "moderate"
        
        beats_per_chapter = len(plot_beats) / total_chapters
        
        if beats_per_chapter > 3:
            return "fast-paced"
        elif beats_per_chapter > 1.5:
            return "moderate"
        else:
            return "deliberate"
    
    def analyze_with_llm(
        self,
        text: str,
        title: str,
        author: str
    ) -> NovelLevelAnalysis:
        """Perform novel-level analysis using LLM for deeper insights."""
        if not self.llm_client:
            # Fallback to rule-based analysis
            return self._rule_based_analysis(title, author)
        
        # LLM-based analysis
        prompt = f"""Analyze the narrative structure of "{title}" by {author}.

Provide a comprehensive analysis in JSON format:
{{
    "narrative_arcs": [
        {{"act": 1, "chapters": [1-7], "theme": "...", "role": "setup"}}
    ],
    "emotional_peaks": [
        {{"chapter": 5, "description": "...", "intensity": 8.5, "type": "climax"}}
    ],
    "character_arcs": [
        {{"name": "...", "role": "protagonist", "beats": [...]}}
    ],
    "major_themes": [...],
    "story_rhythm": "...",
    "key_symbols": [...],
    "central_conflict": "..."
}}

Analyze the full narrative and provide detailed structural insights."""

        try:
            response = self.llm_client.generate(prompt, model=self.model)
            response_text = response.text if hasattr(response, 'text') else str(response)
            return self._parse_llm_response(response_text, title, author)
        except Exception as e:
            print(f"LLM analysis error: {e}")
            return self._rule_based_analysis(title, author)
    
    def _parse_llm_response(
        self,
        response_text: str,
        title: str,
        author: str
    ) -> NovelLevelAnalysis:
        """Parse LLM response into NovelLevelAnalysis."""
        # Simplified - would need proper JSON parsing
        return self._rule_based_analysis(title, author)
    
    def _rule_based_analysis(
        self,
        title: str,
        author: str
    ) -> NovelLevelAnalysis:
        """Fallback rule-based analysis."""
        # Default structure for The Picture of Dorian Gray
        return self.analyze(AnalysisResult(), title, author)


class ChapterLevelPlanner:
    """Plans chapter-level adaptation decisions."""
    
    def __init__(self, novel_context: NovelLevelAnalysis):
        self.novel_context = novel_context
    
    def plan_chapter(
        self,
        chapter_num: int,
        chapter_title: str,
        word_count: int,
        chapter_text: str
    ) -> ChapterLevelAnalysis:
        """Plan a single chapter's adaptation."""
        
        # Determine arc role
        arc_role = self._determine_arc_role(chapter_num)
        
        # Determine chapter role
        chapter_role = self._determine_chapter_role(chapter_num, arc_role)
        
        # Determine narrative function
        narrative_function = self._determine_narrative_function(
            chapter_num, arc_role, chapter_role
        )
        
        # Determine emotional trajectory
        emotional_trajectory = self._determine_emotional_trajectory(
            chapter_num, chapter_role
        )
        
        # Identify key scenes
        key_scenes = self._identify_key_scenes(chapter_num)
        
        # Determine location changes
        location_changes = self._identify_locations(chapter_num)
        
        # Determine character focus
        character_focus = self._determine_character_focus(chapter_num)
        
        # Check splash page candidacy
        is_splash, splash_reason = self._check_splash_page_candidate(
            chapter_num, chapter_role, arc_role
        )
        
        # Assess visual density
        is_visual_heavy = self._assess_visual_density(chapter_num, chapter_role)
        
        return ChapterLevelAnalysis(
            chapter_number=chapter_num,
            chapter_title=chapter_title,
            word_count=word_count,
            arc_role=chapter_role,
            act_number=self._get_act_number(chapter_num),
            narrative_function=narrative_function,
            emotional_trajectory=emotional_trajectory,
            key_scenes=key_scenes,
            location_changes=location_changes,
            character_focus=character_focus,
            is_splash_page_candidate=is_splash,
            splash_page_reason=splash_reason,
            is_visual_heavy=is_visual_heavy,
            dialogue_density=self._assess_dialogue_density(chapter_num),
            action_density=self._assess_action_density(chapter_num),
            setup_for=self._get_setup_for(chapter_num),
            payoff_from=self._get_payoff_from(chapter_num)
        )
    
    def _determine_arc_role(self, chapter_num: int) -> ArcRole:
        """Determine arc role for chapter."""
        pacing = self.novel_context.pacing_structure
        if not pacing:
            return ArcRole.RISING_ACTION
        
        if chapter_num in pacing.setup_chapters:
            return ArcRole.SETUP
        elif chapter_num in pacing.rising_action_chapters:
            return ArcRole.RISING_ACTION
        elif chapter_num in pacing.climax_chapters:
            return ArcRole.CLIMAX
        elif chapter_num in pacing.falling_action_chapters:
            return ArcRole.FALLING_ACTION
        else:
            return ArcRole.RESOLUTION
    
    def _determine_chapter_role(
        self,
        chapter_num: int,
        arc_role: ArcRole
    ) -> ChapterRole:
        """Determine chapter role based on structural position."""
        total_chapters = self.novel_context.total_chapters
        
        if chapter_num == 1:
            return ChapterRole.INCITING_INCIDENT
        
        climax_threshold = int(total_chapters * 0.80)
        if chapter_num >= climax_threshold:
            return ChapterRole.CLIMAX
        
        turning_point_chapters = self._get_structural_turning_points(total_chapters)
        if chapter_num in turning_point_chapters:
            return ChapterRole.TURNING_POINT
        
        if chapter_num > int(total_chapters * 0.90):
            return ChapterRole.RESOLUTION
        
        if chapter_num % 3 == 0:
            return ChapterRole.BRIDGE
        
        return ChapterRole.DEVELOPMENT
    
    def _get_structural_turning_points(self, total_chapters: int) -> List[int]:
        """Get turning point chapters based on story structure."""
        if total_chapters <= 5:
            return [max(1, total_chapters - 1)]
        elif total_chapters <= 10:
            return [max(1, int(total_chapters * 0.25)), max(1, int(total_chapters * 0.50))]
        elif total_chapters <= 20:
            return [
                max(1, int(total_chapters * 0.20)),
                max(1, int(total_chapters * 0.40)),
                max(1, int(total_chapters * 0.60)),
                max(1, int(total_chapters * 0.80))
            ]
        else:
            return [
                max(1, int(total_chapters * 0.15)),
                max(1, int(total_chapters * 0.30)),
                max(1, int(total_chapters * 0.50)),
                max(1, int(total_chapters * 0.70)),
                max(1, int(total_chapters * 0.85))
            ]
    
    def _determine_narrative_function(
        self,
        chapter_num: int,
        arc_role: ArcRole,
        chapter_role: ChapterRole
    ) -> str:
        """Determine narrative function from novel context."""
        total = self.novel_context.total_chapters
        
        if chapter_role == ChapterRole.INCITING_INCIDENT:
            return f"Chapter {chapter_num}: Introduce characters and establish setting"
        
        if chapter_role == ChapterRole.CLIMAX:
            return f"Chapter {chapter_num}: Climax of the story arc"
        
        if chapter_role == ChapterRole.TURNING_POINT:
            return f"Chapter {chapter_num}: Major turning point in the narrative"
        
        if chapter_role == ChapterRole.RESOLUTION:
            return f"Chapter {chapter_num}: Resolve story threads"
        
        arc_name = arc_role.value.replace('_', ' ')
        return f"Chapter {chapter_num}: Develop {arc_name} thread"
    
    def _determine_emotional_trajectory(
        self,
        chapter_num: int,
        chapter_role: ChapterRole
    ) -> str:
        """Determine emotional trajectory from chapter role."""
        if chapter_role == ChapterRole.CLIMAX:
            return "building_tension_to_release"
        if chapter_role == ChapterRole.TURNING_POINT:
            return "sudden_shift"
        if chapter_role == ChapterRole.RESOLUTION:
            return "catharsis"
        if chapter_role == ChapterRole.INCITING_INCIDENT:
            return "introduction"
        
        peaks = self.novel_context.emotional_peaks
        for peak in peaks:
            if peak.chapter == chapter_num:
                if peak.peak_type in ['tragedy', 'climax']:
                    return "intense"
                elif peak.peak_type == 'revelation':
                    return "revelation"
        
        return "development"
    
    def _identify_key_scenes(self, chapter_num: int) -> List[str]:
        """Identify key scenes from novel context."""
        scenes = []
        
        for arc in self.novel_context.narrative_arcs:
            if chapter_num in arc.chapters:
                scenes.extend(arc.key_events[:3])
        
        peaks = [p for p in self.novel_context.emotional_peaks if p.chapter == chapter_num]
        for peak in peaks:
            if peak.key_moment and peak.key_moment not in scenes:
                scenes.append(peak.key_moment)
        
        if not scenes:
            scenes = [f"Chapter {chapter_num} development"]
        
        return scenes[:5]
    
    def _identify_locations(self, chapter_num: int) -> List[str]:
        """Identify locations from novel context."""
        locations = []
        
        if hasattr(self.novel_context, 'character_arcs'):
            for arc in self.novel_context.character_arcs:
                for beat in arc.arc_beats:
                    if beat.get('chapter') == chapter_num:
                        desc = beat.get('description', '')
                        if desc and desc not in locations:
                            locations.append(desc)
        
        if not locations:
            total = self.novel_context.total_chapters
            position = "early" if chapter_num <= total * 0.33 else "middle" if chapter_num <= total * 0.66 else "late"
            locations = [f"Chapter {chapter_num} ({position})"]
        
        return locations[:3]
    
    def _determine_character_focus(self, chapter_num: int) -> List[str]:
        """Determine character focus from novel context."""
        characters = []
        
        for arc in self.novel_context.character_arcs:
            for beat in arc.arc_beats:
                if beat.get('chapter') == chapter_num:
                    name = arc.character_name
                    if name not in characters:
                        characters.append(name)
        
        protagonist = self.novel_context.protagonist
        if protagonist and protagonist not in characters and chapter_num <= 3:
            characters.insert(0, protagonist)
        
        if not characters:
            characters = [self.novel_context.protagonist or "Main Character"]
        
        return characters[:4]
    
    def _check_splash_page_candidate(
        self,
        chapter_num: int,
        chapter_role: ChapterRole,
        arc_role: ArcRole
    ) -> tuple:
        """Check if chapter is splash page candidate."""
        # Chapter 1 always splash
        if chapter_num == 1:
            return True, "Series opening - establish tone"
        
        # Climax chapters
        if chapter_role == ChapterRole.CLIMAX:
            return True, "Climactic moment - high impact"
        
        # Major turning points
        if chapter_role == ChapterRole.TURNING_POINT:
            return True, "Turning point - narrative shift"
        
        # Emotional peaks
        for peak in self.novel_context.emotional_peaks:
            if peak.chapter == chapter_num and peak.intensity >= 8.0:
                return True, f"Emotional peak: {peak.description}"
        
        return False, ""
    
    def _assess_visual_density(
        self,
        chapter_num: int,
        chapter_role: ChapterRole
    ) -> bool:
        """Assess if chapter is visually dense based on role and position."""
        if chapter_role in [ChapterRole.CLIMAX, ChapterRole.TURNING_POINT]:
            return True
        
        total = self.novel_context.total_chapters
        if chapter_num <= int(total * 0.15):
            return True
        if chapter_num >= int(total * 0.85):
            return True
        
        peaks = self.novel_context.emotional_peaks
        for peak in peaks:
            if peak.chapter == chapter_num and peak.intensity >= 8.0:
                return True
        
        return False
    
    def _assess_dialogue_density(self, chapter_num: int) -> str:
        """Assess dialogue density from emotional peaks and chapter role."""
        peaks = self.novel_context.emotional_peaks
        
        for peak in peaks:
            if peak.chapter == chapter_num:
                if peak.peak_type in ['revelation', 'decision']:
                    return "high"
                if peak.intensity >= 8.0:
                    return "medium"
        
        total = self.novel_context.total_chapters
        if chapter_num <= int(total * 0.20):
            return "high"
        
        arc_role = self._determine_arc_role(chapter_num)
        if arc_role == ArcRole.CLIMAX:
            return "high"
        
        return "medium"
    
    def _assess_action_density(self, chapter_num: int) -> str:
        """Assess action density from emotional peaks and pacing."""
        peaks = self.novel_context.emotional_peaks
        
        for peak in peaks:
            if peak.chapter == chapter_num:
                if peak.peak_type in ['action', 'climax', 'tragedy']:
                    return "high"
                if peak.intensity >= 9.0:
                    return "high"
        
        arc_role = self._determine_arc_role(chapter_num)
        if arc_role == ArcRole.CLIMAX:
            return "high"
        
        return "low"
    
    def _get_act_number(self, chapter_num: int) -> int:
        """Get act number for chapter."""
        total = self.novel_context.total_chapters
        if chapter_num <= total * 0.35:
            return 1
        elif chapter_num <= total * 0.70:
            return 2
        elif chapter_num <= total * 0.90:
            return 3
        return 4
    
    def _get_setup_for(self, chapter_num: int) -> List[int]:
        """Get chapters this chapter sets up based on narrative structure."""
        setups = []
        total = self.novel_context.total_chapters
        
        if chapter_num == 1:
            setups = [max(1, int(total * 0.25)), max(1, int(total * 0.50))]
        
        turning_points = self._get_structural_turning_points(total)
        for tp in turning_points:
            if tp > chapter_num:
                setups.append(tp)
        
        return list(dict.fromkeys(setups))[:3]
    
    def _get_payoff_from(self, chapter_num: int) -> List[int]:
        """Get chapters this chapter pays off from based on narrative structure."""
        payoffs = []
        total = self.novel_context.total_chapters
        
        turning_points = self._get_structural_turning_points(total)
        for tp in turning_points:
            if tp < chapter_num:
                payoffs.append(tp)
        
        return list(dict.fromkeys(payoffs))[-3:]


class AdaptationPlanner:
    """Main orchestrator for adaptation planning."""
    
    def __init__(self, llm_client=None, model: str = "aurora-alpha"):
        self.novel_analyzer = NovelLevelAnalyzer(llm_client, model)
        self.page_allocator = PageAllocator()
        self.compression_decider = CompressionDecider()
        self.llm_client = llm_client
        self.model = model
    
    def plan(
        self,
        analysis_result,
        target_pages: int = 100,
        title: str = "",
        author: str = ""
    ) -> AdaptationPlan:
        """
        Create complete adaptation plan.
        
        Phase 1: Novel-level analysis (run ONCE)
        Phase 2: Chapter-level analysis (uses novel context)
        
        Args:
            analysis_result: Stage 2 analysis result
            target_pages: Total target pages for adaptation
            title: Book title
            author: Book author
        
        Returns:
            Complete AdaptationPlan
        """
        # Phase 1: Novel-level analysis
        print("Phase 1: Performing novel-level analysis...")
        novel_context = self.novel_analyzer.analyze(
            analysis_result, title, author
        )
        print(f"  - Identified {novel_context.act_count} narrative arcs")
        print(f"  - Found {novel_context.peak_count} emotional peaks")
        print(f"  - {len(novel_context.character_arcs)} character arcs")
        
        # Phase 2: Chapter-level planning
        print("Phase 2: Planning chapter-level adaptation...")
        chapter_analyses = self._plan_all_chapters(novel_context)
        
        # Phase 3: Page allocation
        print("Phase 3: Allocating pages...")
        page_allocations = self.page_allocator.allocate_all_chapters(
            chapter_analyses, novel_context, target_pages
        )
        
        # Phase 4: Splash page identification
        print("Phase 4: Identifying splash pages...")
        splash_identifier = SplashPageIdentifier(target_pages)
        splash_pages = splash_identifier.identify_splash_pages(
            novel_context, chapter_analyses
        )
        
        # Validate splash distribution
        is_valid, notes = splash_identifier.validate_splash_distribution(
            splash_pages, novel_context.total_chapters
        )
        
        # Create adaptation plan
        plan = AdaptationPlan(
            novel_level_analysis=novel_context,
            page_allocation=page_allocations,
            splash_pages=splash_pages,
            total_target_pages=target_pages,
            pages_per_chapter_avg=target_pages / len(page_allocations) if page_allocations else 0,
            is_valid=is_valid,
            validation_notes=notes
        )
        
        return plan
    
    def _plan_all_chapters(
        self,
        novel_context: NovelLevelAnalysis
    ) -> List[ChapterLevelAnalysis]:
        """Plan all chapters."""
        chapter_planner = ChapterLevelPlanner(novel_context)
        analyses = []
        
        for chapter_num in range(1, novel_context.total_chapters + 1):
            chapter = chapter_planner.plan_chapter(
                chapter_num=chapter_num,
                chapter_title=f"Chapter {chapter_num}",
                word_count=self._estimate_word_count(chapter_num, novel_context),
                chapter_text=""  # Would use actual text in full implementation
            )
            analyses.append(chapter)
        
        return analyses
    
    def _estimate_word_count(
        self,
        chapter_num: int,
        novel_context: NovelLevelAnalysis
    ) -> int:
        """Estimate word count for chapter (simplified)."""
        # Average ~4000 words per chapter in Dorian Gray
        return 4000
    
    def plan_with_text(
        self,
        chapters: List,
        target_pages: int = 100,
        title: str = "",
        author: str = ""
    ) -> AdaptationPlan:
        """
        Create plan with chapter texts (for more detailed planning).
        
        Args:
            chapters: List of chapter objects with 'number', 'title', 'text'
            target_pages: Total target pages
            title: Book title
            author: Book author
        """
        # Create combined analysis result
        from .schemas import AnalysisResult
        
        combined_result = AnalysisResult()
        
        # Phase 1: Novel-level analysis
        novel_context = self.novel_analyzer.analyze(
            combined_result, title, author
        )
        
        # Phase 2: Chapter-level with actual text
        chapter_planner = ChapterLevelPlanner(novel_context)
        chapter_analyses = []
        
        for chapter in chapters:
            chapter_analysis = chapter_planner.plan_chapter(
                chapter_num=chapter.number if hasattr(chapter, 'number') else chapter.get('number'),
                chapter_title=chapter.title if hasattr(chapter, 'title') else chapter.get('title', ''),
                word_count=chapter.word_count if hasattr(chapter, 'word_count') else len(chapter.text),
                chapter_text=chapter.text if hasattr(chapter, 'text') else ''
            )
            chapter_analyses.append(chapter_analysis)
        
        # Rest same as plan()
        page_allocations = self.page_allocator.allocate_all_chapters(
            chapter_analyses, novel_context, target_pages
        )
        
        splash_identifier = SplashPageIdentifier(target_pages)
        splash_pages = splash_identifier.identify_splash_pages(
            novel_context, chapter_analyses
        )
        
        is_valid, notes = splash_identifier.validate_splash_distribution(
            splash_pages, novel_context.total_chapters
        )
        
        return AdaptationPlan(
            novel_level_analysis=novel_context,
            page_allocation=page_allocations,
            splash_pages=splash_pages,
            total_target_pages=target_pages,
            pages_per_chapter_avg=target_pages / len(page_allocations) if page_allocations else 0,
            is_valid=is_valid,
            validation_notes=notes
        )
    
    def save_plan(self, plan: AdaptationPlan, output_path: str):
        """Save adaptation plan to JSON."""
        import json
        from pathlib import Path
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        plan_dict = {
            'novel_analysis': {
                'title': plan.novel_level_analysis.title,
                'author': plan.novel_level_analysis.author,
                'total_chapters': plan.novel_level_analysis.total_chapters,
                'major_themes': plan.novel_level_analysis.major_themes,
                'protagonist': plan.novel_level_analysis.protagonist,
                'story_rhythm': plan.novel_level_analysis.story_rhythm,
                'emotional_peaks': [
                    {'chapter': p.chapter, 'description': p.description, 'intensity': p.intensity}
                    for p in plan.novel_level_analysis.emotional_peaks
                ],
                'character_arcs': [
                    {'name': c.character_name, 'role': c.role, 'summary': c.transformation_summary}
                    for c in plan.novel_level_analysis.character_arcs
                ]
            },
            'page_allocations': [
                {
                    'chapter': a.chapter_number,
                    'total_pages': a.total_pages,
                    'splash_pages': a.splash_pages,
                    'reasoning': a.allocation_reasoning
                }
                for a in plan.page_allocation
            ],
            'splash_pages': [
                {
                    'id': s.splash_id,
                    'chapter': s.chapter,
                    'description': s.description,
                    'type': s.scene_type
                }
                for s in plan.splash_pages
            ],
            'summary': {
                'total_pages': plan.total_target_pages,
                'chapters': plan.chapter_count,
                'splash_pages': plan.splash_page_count,
                'is_valid': plan.is_valid
            }
        }
        
        with open(output_path, 'w') as f:
            json.dump(plan_dict, f, indent=2)
        
        print(f"Plan saved to {output_path}")


# Helper class for AnalysisResult (for compatibility)
class AnalysisResult:
    """Minimal AnalysisResult for novel-level analysis."""
    def __init__(self):
        self.characters = []
        self.plot_beats = []
        self.locations = []
        self.dialogue = []
        self.key_quotes = []
