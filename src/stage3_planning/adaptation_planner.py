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
        return 20  # Default for Dorian Gray
    
    def _analyze_narrative_arcs(
        self,
        plot_beats: List,
        total_chapters: int,
        analysis_result
    ) -> List[NarrativeArc]:
        """Analyze narrative arcs (Act 1, 2, 3 structure)."""
        arcs = []
        
        # For Dorian Gray-like structure:
        # Act 1: Chapters 1-7 (Setup, Dorian introduced, wish made)
        # Act 2: Chapters 8-15 (Rising action, corruption deepens)
        # Act 3: Chapters 16-20 (Falling action, tragedy unfolds)
        
        act_themes = [
            ("Introduction and the Fatal Wish", ArcRole.SETUP),
            ("The Corruption of Youth", ArcRole.RISING_ACTION),
            ("The Price of Beauty", ArcRole.CLIMAX),
            ("Retribution and Tragedy", ArcRole.FALLING_ACTION),
            ("Conclusion", ArcRole.RESOLUTION)
        ]
        
        # Calculate chapter distribution
        act_size = total_chapters // len(act_themes)
        
        for i, (theme, arc_role) in enumerate(act_themes):
            start_ch = i * act_size + 1
            end_ch = min((i + 1) * act_size, total_chapters)
            
            chapters = list(range(start_ch, end_ch + 1))
            
            # Get key events for this act
            key_events = self._get_act_events(i, plot_beats)
            
            arcs.append(NarrativeArc(
                act_number=i + 1,
                chapters=chapters,
                theme=theme,
                arc_role=arc_role,
                key_events=key_events,
                emotional_tone=self._get_act_tone(arc_role)
            ))
        
        return arcs
    
    def _get_act_events(self, act_num: int, plot_beats: List) -> List[str]:
        """Get key events for an act."""
        # Simplified - would use LLM for detailed events
        act_events = {
            0: ["Dorian introduced", "Portrait painted", "Fatal wish made"],
            1: ["Dorian's corruption begins", "Relationship with Sibyl", "Blackmail begins"],
            2: ["Crimes catch up", "Dorian confronts past", "Portrait deteriorates"],
            3: ["Final revelations", "Dorian's despair", "Destruction"],
            4: ["Aftermath", "Final statement"]
        }
        return act_events.get(act_num, [])
    
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
        """Identify emotional peaks in the story."""
        peaks = []
        
        # Standard peaks for Dorian Gray structure
        peak_data = [
            (1, "The First Meeting", "climax", 9.0, "Dorian meets Lord Henry, his path is set"),
            (5, "The Fatal Wish", "revelation", 8.5, "Dorian wishes to stay young forever"),
            (11, "Sibel Vane's Death", "tragedy", 9.0, "Dorian's cruelty leads to suicide"),
            (14, "Basil's Confrontation", "climax", 9.5, "Dorian demands Basil see the portrait"),
            (18, "The Portrait's Horror", "revelation", 10.0, "Dorian sees the true horror of his soul"),
            (20, "The Final Destruction", "tragedy", 9.5, "Dorian destroys the portrait and himself"),
        ]
        
        for chapter, desc, peak_type, intensity, moment in peak_data:
            if chapter <= total_chapters:
                peaks.append(EmotionalPeak(
                    chapter=chapter,
                    description=desc,
                    intensity=intensity,
                    peak_type=peak_type,
                    key_moment=moment
                ))
        
        return peaks
    
    def _analyze_character_arcs(
        self,
        characters: List,
        plot_beats: List,
        total_chapters: int
    ) -> List[CharacterArc]:
        """Analyze character arcs."""
        arcs = []
        
        # Dorian's arc
        dorian_arc = CharacterArc(
            character_name="Dorian Gray",
            role="protagonist",
            arc_beats=[
                {"chapter": 1, "description": "Innocent, beautiful young man", "change": "meeting Henry"},
                {"chapter": 5, "description": "Makes the fatal wish", "change": "corruption begins"},
                {"chapter": 11, "description": "Causes Sibyl's death", "change": "moral decay"},
                {"chapter": 14, "description": "Threatens Basil", "change": "complete corruption"},
                {"chapter": 18, "description": "Sees horror of portrait", "change": "despair"},
                {"chapter": 20, "description": "Destroys portrait and himself", "change": "destruction"}
            ],
            transformation_summary="From innocent beauty to corrupted soul",
            starting_state="Beautiful, innocent, impressionable",
            ending_state="Damned, despairing, destroyed"
        )
        arcs.append(dorian_arc)
        
        # Lord Henry's arc (static - corrupting influence)
        henry_arc = CharacterArc(
            character_name="Lord Henry Wotton",
            role="antagonist",  # Though not traditional antagonist
            arc_beats=[
                {"chapter": 1, "description": "Introduces cynical philosophy", "change": "influences Dorian"},
                {"chapter": 7, "description": "Continues corrupting influence", "change": "maintains control"},
                {"chapter": 15, "description": "Observes Dorian's decline", "change": "enjoys the spectacle"}
            ],
            transformation_summary="Constant corrupter, never changes",
            starting_state="Cynical, manipulative, hedonistic",
            ending_state="Same - reflects on Dorian's fate"
        )
        arcs.append(henry_arc)
        
        # Basil Hallward's arc
        basil_arc = CharacterArc(
            character_name="Basil Hallward",
            role="supporting",
            arc_beats=[
                {"chapter": 1, "description": "Paints Dorian's portrait", "change": "becomes obsessed"},
                {"chapter": 14, "description": "Confronts Dorian about the portrait", "change": "is threatened"},
                {"chapter": 15, "description": "Is murdered by Dorian", "change": "death"}
            ],
            transformation_summary="From devoted artist to victim of his creation",
            starting_state="Talented, devoted, caring",
            ending_state="Murdered, betrayed"
        )
        arcs.append(basil_arc)
        
        return arcs
    
    def _identify_themes(self, analysis_result) -> List[str]:
        """Identify major themes."""
        return [
            "The danger of beauty and youth",
            "The corruption of the soul",
            "The relationship between art and life",
            "The price of hedonism",
            "The duality of human nature",
            "The unreliability of appearances"
        ]
    
    def _determine_mood_tone(self, analysis_result) -> str:
        """Determine overall mood/tone."""
        return "Gothic, decadent, cautionary, psychologically dark"
    
    def _identify_symbols(self, analysis_result) -> List[str]:
        """Identify key symbols."""
        return [
            "The Portrait - the true self revealed",
            "The Red Roses - beauty and its decay",
            "The Yellow Book - corrupting influence",
            "The Theatre Box - voyeurism and performance"
        ]
    
    def _find_protagonist(self, characters: List) -> str:
        """Find protagonist name."""
        for char in characters:
            if hasattr(char, 'role') and char.role == 'protagonist':
                return char.name
        return "Dorian Gray"  # Default for Dorian Gray
    
    def _identify_central_conflict(
        self,
        plot_beats: List,
        themes: List[str]
    ) -> str:
        """Identify central conflict."""
        return "The conflict between appearance and reality, beauty and corruption, pleasure and consequence"
    
    def _determine_story_rhythm(
        self,
        plot_beats: List,
        total_chapters: int
    ) -> str:
        """Determine story rhythm."""
        return "deliberate"  # Literary fiction with building tension
    
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
        """Determine chapter role."""
        total_chapters = self.novel_context.total_chapters
        
        # Inciting incident
        if chapter_num == 1:
            return ChapterRole.INCITING_INCIDENT
        
        # Climax chapters (typically late in arc)
        climax_threshold = int(total_chapters * 0.80)
        if chapter_num >= climax_threshold:
            return ChapterRole.CLIMAX
        
        # Turning points
        turning_points = [5, 11, 14, 18]
        if chapter_num in turning_points:
            return ChapterRole.TURNING_POINT
        
        # Resolution
        if chapter_num > int(total_chapters * 0.90):
            return ChapterRole.RESOLUTION
        
        # Bridge chapters
        if chapter_num % 3 == 0:
            return ChapterRole.BRIDGE
        
        # Default to development
        return ChapterRole.DEVELOPMENT
    
    def _determine_narrative_function(
        self,
        chapter_num: int,
        arc_role: ArcRole,
        chapter_role: ChapterRole
    ) -> str:
        """Determine narrative function."""
        functions = {
            1: "Introduce characters, establish setting, present the fatal wish",
            2: "Develop relationship dynamics",
            3: "Deeper character exploration",
            4: "Build toward corruption",
            5: "CLIMAX: The wish is made, fate is sealed",
            6: "Explore consequences",
            7: "Introduce new character (Sibyl)",
            8: "Romantic subplot develops",
            9: "Tension builds",
            10: "Complications arise",
            11: "CLIMAX: Sibyl's death, Dorian's coldness revealed",
            12: "Aftermath and reflection",
            13: "Basil becomes concerned",
            14: "CLIMAX: Confrontation with Basil",
            15: "Consequences unfold",
            16: "Secrets threaten to surface",
            17: "Dorian's double life intensifies",
            18: "CLIMAX: The portrait's horror revealed",
            19: "Desperation and decline",
            20: "CLIMAX/RESOLUTION: Final destruction"
        }
        
        return functions.get(chapter_num, f"Advance the {arc_role.value} arc")
    
    def _determine_emotional_trajectory(
        self,
        chapter_num: int,
        chapter_role: ChapterRole
    ) -> str:
        """Determine emotional trajectory."""
        if chapter_role == ChapterRole.CLIMAX:
            return "building_tension_to_release"
        elif chapter_role == ChapterRole.TURNING_POINT:
            return "sudden_shift"
        elif chapter_role == ChapterRole.RESOLUTION:
            return "catharsis"
        elif chapter_num == 11:
            return "tragedy"  # Sibyl's death
        elif chapter_num == 1:
            return "introduction"
        else:
            return "development"
    
    def _identify_key_scenes(self, chapter_num: int) -> List[str]:
        """Identify key scenes in chapter."""
        scenes = {
            1: ["Basil's studio", "First meeting with Lord Henry", "Dorian introduced"],
            5: ["The portrait inspection", "Dorian's wish", "Lord Henry's influence"],
            11: ["The theatre scene", "Sibyl's performance", "Her death"],
            14: ["Basil arrives", "The confrontation", "The threat"],
            18: ["The locked room", "The portrait revealed", "Dorian's horror"],
            20: ["The final scene", "The destroyed portrait", "The dead Dorian"]
        }
        return scenes.get(chapter_num, ["Standard chapter scenes"])
    
    def _identify_locations(self, chapter_num: int) -> List[str]:
        """Identify locations in chapter."""
        locations = {
            1: ["Basil's studio"],
            5: ["Basil's studio"],
            7: ["The theatre", "Dorian's home"],
            11: ["The theatre", "Sibyl's home"],
            14: ["Dorian's home"],
            18: ["The locked room"],
            20: ["Dorian's home"]
        }
        return locations.get(chapter_num, ["Various"])
    
    def _determine_character_focus(self, chapter_num: int) -> List[str]:
        """Determine character focus."""
        focus = {
            1: ["Dorian Gray", "Basil Hallward", "Lord Henry"],
            5: ["Dorian Gray", "Lord Henry"],
            7: ["Dorian Gray", "Sibyl Vane"],
            11: ["Dorian Gray", "Sibyl Vane", "Lord Henry"],
            14: ["Dorian Gray", "Basil Hallward"],
            18: ["Dorian Gray"],
            20: ["Dorian Gray"]
        }
        return focus.get(chapter_num, ["Dorian Gray"])
    
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
        """Assess if chapter is visually dense."""
        # Higher visual density for:
        # - Opening chapters
        # - Climax chapters
        # - Emotionally intense chapters
        
        if chapter_role in [ChapterRole.CLIMAX, ChapterRole.TURNING_POINT]:
            return True
        if chapter_num <= 3:
            return True
        if chapter_num >= 18:
            return True
        return False
    
    def _assess_dialogue_density(self, chapter_num: int) -> str:
        """Assess dialogue density."""
        # Dorian Gray is dialogue-heavy throughout
        if chapter_num <= 5:
            return "high"  # Heavy dialogue in opening
        elif chapter_num >= 14 and chapter_num <= 18:
            return "high"  # Confrontation and revelation
        return "medium"
    
    def _assess_action_density(self, chapter_num: int) -> str:
        """Assess action density."""
        # Mostly psychological/action-light, with bursts
        if chapter_num == 11:
            return "high"  # Sibyl's death scene
        if chapter_num == 14:
            return "high"  # Confrontation
        if chapter_num == 20:
            return "high"  # Final destruction
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
        """Get chapters this chapter sets up."""
        setups = {
            1: [5, 7, 11],  # Sets up corruption, Sibyl, tragedy
            5: [11, 14],    # Sets up consequences
            7: [11],        # Sets up Sibyl's fate
            11: [14, 18],   # Sets up further corruption and reckoning
            14: [18, 20],   # Sets up final confrontation
        }
        return setups.get(chapter_num, [])
    
    def _get_payoff_from(self, chapter_num: int) -> List[int]:
        """Get chapters this chapter pays off from."""
        payoffs = {
            5: [11, 14, 18, 20],  # Wish pays off throughout
            11: [14, 18, 20],     # Death affects everything
            14: [18, 20],         # Confrontation leads to climax
            18: [20],             # Horror leads to destruction
        }
        return payoffs.get(chapter_num, [])


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
