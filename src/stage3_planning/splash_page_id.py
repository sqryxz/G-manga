"""Stage 3: Splash Page Identification Module

Identifies optimal splash page moments based on novel context.
Strategic placement for maximum visual and narrative impact.
"""

from typing import List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from .schemas import (
    SplashPage, NovelLevelAnalysis, ChapterLevelAnalysis,
    EmotionalPeak, ChapterRole, ArcRole
)


@dataclass
class SplashPageCandidate:
    """Candidate for splash page placement."""
    chapter: int
    scene_or_moment: str
    impact_score: float  # 0.0 to 1.0
    splash_type: str  # "opening", "climax", "revelation", "emotional", "atmospheric"
    reason: str
    visual_elements: List[str]
    priority_rank: int = 0


class SplashPageIdentifier:
    """Identifies optimal splash page moments."""
    
    # Splash page distribution guidelines
    MIN_SPLASH_PAGES = 3  # Minimum for any adaptation
    MAX_SPLASH_PAGES_PERCENT = 0.15  # Max 15% of pages are splash
    
    # Impact thresholds
    HIGH_IMPACT_THRESHOLD = 0.8
    MEDIUM_IMPACT_THRESHOLD = 0.6
    
    # Strategic positions for splash pages
    STRATEGIC_POSITIONS = [
        (1, "Opening impact"),  # Chapter 1 opening
        ("middle", "Mid-point revelation"),  # Around middle of book
        ("penultimate", "Before climax"),  # Chapter before climax
        ("final", "Final emotional beat"),  # Near the end
    ]
    
    def __init__(
        self,
        target_pages: int,
        min_splash: Optional[int] = None,
        max_splash_percent: float = 0.15
    ):
        """
        Initialize splash page identifier.
        
        Args:
            target_pages: Total target pages for adaptation
            min_splash: Minimum splash pages (default: 3)
            max_splash_percent: Max percentage of pages as splash (default: 0.15)
        """
        self.target_pages = target_pages
        self.min_splash = min_splash or self.MIN_SPLASH_PAGES
        self.max_splash = int(target_pages * max_splash_percent)
    
    def identify_splash_pages(
        self,
        novel_context: NovelLevelAnalysis,
        chapter_analyses: List[ChapterLevelAnalysis]
    ) -> List[SplashPage]:
        """
        Identify all splash page moments.
        
        Args:
            novel_context: Novel-level analysis
            chapter_analyses: Chapter-level analyses
        
        Returns:
            List of SplashPage objects
        """
        candidates = self._generate_candidates(novel_context, chapter_analyses)
        selected = self._select_optimal_splash_pages(candidates, len(chapter_analyses))
        splash_pages = self._convert_to_splash_pages(selected, novel_context)
        
        return splash_pages
    
    def _generate_candidates(
        self,
        novel_context: NovelLevelAnalysis,
        chapter_analyses: List[ChapterLevelAnalysis]
    ) -> List[SplashPageCandidate]:
        """Generate all potential splash page candidates."""
        candidates = []
        
        # 1. Chapter 1 opening (always a candidate)
        candidates.append(SplashPageCandidate(
            chapter=1,
            scene_or_moment="Opening scene",
            impact_score=1.0,
            splash_type="opening",
            reason="First impression - establish tone and draw reader in",
            visual_elements=["key setting", "protagonist introduction"],
            priority_rank=1
        ))
        
        # 2. Emotional peaks
        for peak in novel_context.emotional_peaks:
            candidate = self._create_peak_candidate(peak, novel_context)
            if candidate:
                candidates.append(candidate)
        
        # 3. Chapter-level candidates
        for chapter in chapter_analyses:
            if chapter.is_splash_page_candidate:
                candidate = self._create_chapter_candidate(chapter, novel_context)
                if candidate:
                    candidates.append(candidate)
        
        # 4. Arc transitions and climaxes
        for arc in novel_context.narrative_arcs:
            candidate = self._create_arc_candidate(arc, novel_context)
            if candidate:
                candidates.append(candidate)
        
        # 5. Character transformation beats
        for character_arc in novel_context.character_arcs:
            if character_arc.role == "protagonist":
                for beat in character_arc.arc_beats:
                    if beat.get("is_transformation", False):
                        candidates.append(SplashPageCandidate(
                            chapter=beat.get("chapter", 0),
                            scene_or_moment=beat.get("description", ""),
                            impact_score=0.75,
                            splash_type="emotional",
                            reason=f"Character transformation: {character_arc.character_name}",
                            visual_elements=["character", "emotional expression"],
                            priority_rank=3
                        ))
        
        # 6. Thematic statement moments
        for i, theme in enumerate(novel_context.major_themes):
            if i < len(chapter_analyses):
                candidates.append(SplashPageCandidate(
                    chapter=i + 1,
                    scene_or_moment=f"Thematic statement: {theme}",
                    impact_score=0.65,
                    splash_type="atmospheric",
                    reason=f"Establish thematic focus: {theme}",
                    visual_elements=["symbolic imagery", "mood"],
                    priority_rank=4
                ))
        
        return candidates
    
    def _create_peak_candidate(
        self,
        peak: EmotionalPeak,
        novel_context: NovelLevelAnalysis
    ) -> Optional[SplashPageCandidate]:
        """Create candidate from emotional peak."""
        impact_score = peak.intensity / 10.0  # Normalize to 0-1
        
        # Higher impact for climax-type peaks
        if peak.peak_type == "climax":
            impact_score *= 1.2
        
        return SplashPageCandidate(
            chapter=peak.chapter,
            scene_or_moment=peak.description,
            impact_score=min(1.0, impact_score),
            splash_type=self._peak_type_to_splash_type(peak.peak_type),
            reason=f"Emotional peak: {peak.key_moment}",
            visual_elements=self._get_peak_visual_elements(peak),
            priority_rank=2  # High priority
        )
    
    def _create_chapter_candidate(
        self,
        chapter: ChapterLevelAnalysis,
        novel_context: NovelLevelAnalysis
    ) -> Optional[SplashPageCandidate]:
        """Create candidate from chapter analysis."""
        if not chapter.is_splash_page_candidate:
            return None
        
        # Calculate impact based on role
        base_impact = 0.5
        
        if chapter.arc_role == ChapterRole.CLIMAX:
            base_impact = 0.9
        elif chapter.arc_role == ChapterRole.TURNING_POINT:
            base_impact = 0.8
        elif chapter.arc_role == ChapterRole.INCITING_INCIDENT:
            base_impact = 0.7
        elif chapter.arc_role == ChapterRole.BRIDGE:
            base_impact = 0.5
        
        # Boost for visual-heavy content
        if chapter.is_visual_heavy:
            base_impact += 0.1
        
        return SplashPageCandidate(
            chapter=chapter.chapter_number,
            scene_or_moment=chapter.narrative_function,
            impact_score=min(1.0, base_impact),
            splash_type=self._chapter_role_to_splash_type(chapter.arc_role),
            reason=chapter.splash_page_reason,
            visual_elements=chapter.key_scenes[:3],
            priority_rank=3
        )
    
    def _create_arc_candidate(
        self,
        arc: ArcRole,
        novel_context: NovelLevelAnalysis
    ) -> Optional[SplashPageCandidate]:
        """Create candidate from arc structure."""
        if arc.arc_role == ArcRole.CLIMAX:
            # First chapter of climax arc
            if arc.chapters:
                return SplashPageCandidate(
                    chapter=arc.chapters[0],
                    scene_or_moment=f"Arc climax: {arc.theme}",
                    impact_score=0.95,
                    splash_type="climax",
                    reason=f"Arc climax beginning: {arc.theme}",
                    visual_elements=["dramatic tension", "key characters"],
                    priority_rank=1
                )
        
        return None
    
    def _peak_type_to_splash_type(self, peak_type: str) -> str:
        """Convert peak type to splash type."""
        mapping = {
            "climax": "climax",
            "tragedy": "emotional",
            "revelation": "revelation",
            "tension": "atmospheric",
        }
        return mapping.get(peak_type, "emotional")
    
    def _chapter_role_to_splash_type(self, role: ChapterRole) -> str:
        """Convert chapter role to splash type."""
        mapping = {
            ChapterRole.CLIMAX: "climax",
            ChapterRole.TURNING_POINT: "revelation",
            ChapterRole.INCITING_INCIDENT: "opening",
            ChapterRole.DEVELOPMENT: "atmospheric",
            ChapterRole.SETUP: "atmospheric",
            ChapterRole.RESOLUTION: "emotional",
            ChapterRole.BRIDGE: "atmospheric",
        }
        return mapping.get(role, "atmospheric")
    
    def _get_peak_visual_elements(self, peak: EmotionalPeak) -> List[str]:
        """Get visual elements for emotional peak."""
        elements = []
        
        if peak.peak_type in ["climax", "action"]:
            elements.extend(["dynamic pose", "dramatic action"])
        if peak.peak_type in ["revelation"]:
            elements.extend(["character reaction", "symbolic imagery"])
        if peak.peak_type in ["tragedy", "emotional"]:
            elements.extend(["facial expression", "atmospheric lighting"])
        
        return elements if elements else ["key moment capture"]
    
    def _select_optimal_splash_pages(
        self,
        candidates: List[SplashPageCandidate],
        total_chapters: int
    ) -> List[SplashPageCandidate]:
        """
        Select optimal splash pages from candidates.
        
        Distributes splash pages strategically across the narrative.
        """
        # Sort by impact score descending
        sorted_candidates = sorted(
            candidates,
            key=lambda c: (c.priority_rank, -c.impact_score)
        )
        
        selected = []
        chapter_coverage = set()
        
        # First pass: select highest priority
        for candidate in sorted_candidates:
            # Avoid too many splash pages in same chapter
            if candidate.chapter in chapter_coverage:
                continue
            
            if candidate.priority_rank == 1:
                selected.append(candidate)
                chapter_coverage.add(candidate.chapter)
        
        # Second pass: fill in based on impact
        for candidate in sorted_candidates:
            if candidate.chapter in chapter_coverage:
                continue
            
            # Check if we should add more
            current_count = len(selected)
            if current_count >= self.max_splash:
                break
            
            # Select if high enough impact
            if candidate.impact_score >= self.MEDIUM_IMPACT_THRESHOLD:
                selected.append(candidate)
                chapter_coverage.add(candidate.chapter)
        
        # Ensure minimum coverage
        while len(selected) < self.min_splash:
            # Add next best candidate
            for candidate in sorted_candidates:
                if candidate.chapter not in chapter_coverage:
                    selected.append(candidate)
                    chapter_coverage.add(candidate.chapter)
                    break
        
        # Sort by chapter order
        selected = sorted(selected, key=lambda c: c.chapter)
        
        # Assign sequential splash IDs
        for i, candidate in enumerate(selected):
            candidate.priority_rank = i + 1
        
        return selected
    
    def _convert_to_splash_pages(
        self,
        candidates: List[SplashPageCandidate],
        novel_context: NovelLevelAnalysis
    ) -> List[SplashPage]:
        """Convert candidates to SplashPage objects."""
        splash_pages = []
        
        for i, candidate in enumerate(candidates):
            # Determine page number (usually chapter opening)
            page_number = 1  # Typically first page of chapter
            
            splash_id = f"splash_{candidate.chapter:02d}_{i+1}"
            
            splash = SplashPage(
                chapter=candidate.chapter,
                page_number=page_number,
                splash_id=splash_id,
                description=candidate.scene_or_moment,
                reason=candidate.reason,
                scene_type=candidate.splash_type,
                visual_elements=candidate.visual_elements
            )
            
            splash_pages.append(splash)
        
        return splash_pages
    
    def validate_splash_distribution(
        self,
        splash_pages: List[SplashPage],
        total_chapters: int
    ) -> Tuple[bool, List[str]]:
        """
        Validate splash page distribution.
        
        Returns:
            Tuple of (is_valid, list of notes/warnings)
        """
        notes = []
        
        # Check minimum
        if len(splash_pages) < self.min_splash:
            notes.append(f"WARNING: Only {len(splash_pages)} splash pages (minimum: {self.min_splash})")
        
        # Check maximum
        if len(splash_pages) > self.max_splash:
            notes.append(f"WARNING: {len(splash_pages)} splash pages exceeds maximum ({self.max_splash})")
        
        # Check distribution across book
        chapters_with_splash = set(s.chapter for s in splash_pages)
        
        if len(chapters_with_splash) < 3 and total_chapters > 10:
            notes.append("NOTE: Splash pages concentrated in few chapters - consider spreading")
        
        # Check for opening splash
        has_opening = any(s.chapter == 1 for s in splash_pages)
        if not has_opening:
            notes.append("NOTE: No splash page at chapter 1 opening - consider adding")
        
        # Check for ending coverage
        final_chapters = list(range(max(1, total_chapters - 2), total_chapters + 1))
        has_ending = any(s.chapter in final_chapters for s in splash_pages)
        if not has_ending and total_chapters > 5:
            notes.append("NOTE: No splash page in final chapters - consider adding climactic moment")
        
        is_valid = len([n for n in notes if n.startswith("WARNING")]) == 0
        
        return is_valid, notes
    
    def generate_splash_page_summary(
        self,
        splash_pages: List[SplashPage],
        novel_context: NovelLevelAnalysis
    ) -> dict:
        """Generate summary of splash page decisions."""
        by_type = {}
        by_chapter = {}
        
        for splash in splash_pages:
            # By type
            if splash.scene_type not in by_type:
                by_type[splash.scene_type] = []
            by_type[splash.scene_type].append({
                'chapter': splash.chapter,
                'description': splash.description[:50]
            })
            
            # By chapter
            if splash.chapter not in by_chapter:
                by_chapter[splash.chapter] = []
            by_chapter[splash.chapter].append(splash.splash_id)
        
        return {
            'total_splash_pages': len(splash_pages),
            'by_type': by_type,
            'by_chapter': by_chapter,
            'novel_title': novel_context.title,
            'generated_at': datetime.now().isoformat()
        }
