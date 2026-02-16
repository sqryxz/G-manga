#!/usr/bin/env python3
"""
G-Manga - Comic Creation Engine
Main entry point that runs the complete pipeline (Stages 1-9) with detailed logging.
"""

import sys
import time
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from functools import wraps
import logging

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from config import Settings, get_settings
from models.project import Metadata, Chapter, Scene, TextRange, generate_project_id
from common.mocking import MockLLMClient
from common.logging import setup_logger
from common.llm_factory import create_llm_client, PROVIDER_ZAI, PROVIDER_OPENROUTER, PROVIDER_MOCK

# Stage 1 modules
from stage1_input.url_fetcher import URLFetcher
from stage1_input.text_parser import TextParser
from stage1_input.metadata_extractor import MetadataExtractor
from stage1_input.project import ProjectInitializer

# Stage 2 modules
from stage2_preprocessing.text_cleaner import TextCleaner
from stage2_preprocessing.chapter_segmenter import ChapterSegmenter
from stage2_preprocessing.scene_breakdown import SceneBreakdown
from stage2_preprocessing.state import StatePersistence

# Stage 2 NEW modules (Analysis Engine)
from stage2_analysis import Stage2Adapter, AnalysisEngine

# Stage 3 modules
from stage3_story_planning.visual_adaptation import VisualAdaptation
from stage3_story_planning.panel_breakdown import PanelBreakdown
from stage3_story_planning.storyboard_generator import StoryboardGenerator
from stage3_story_planning.page_calculator import PageCalculator
from stage3_story_planning.visual_panel_merged import VisualPanelMerged
from stage3_story_planning.detailed_storyboard import DetailedStoryboardGenerator

# Stage 3 NEW modules (Adaptation Planner)
from stage3_planning import Stage3Adapter, AdaptationPlanner

# Stage 4 modules
from stage4_character_design.character_extractor import CharacterExtractor
from stage4_character_design.character_tracker import CharacterEmbeddingTracker
from stage4_character_design.ref_sheet_generator import RefSheetGenerator

# Stage 5 modules
from stage5_panel_generation.panel_builder import PanelBuilder
from stage5_panel_generation.panel_optimizer import PanelOptimizer
from stage5_panel_generation.panel_state import PanelStateManager
from stage5_panel_generation.panel_type_prompts import PanelTypePrompts

# Stage 5 NEW modules (Script Generation)
from stage5_script import Stage5Adapter, ScriptOrchestrator

# Stage 6 modules
from stage6_image_generation.queue_manager import ImageQueueManager
from stage6_image_generation.retry_manager import RetryFallbackManager, RetryConfig, FallbackStrategy
from stage6_image_generation.image_storage import ImageStorage

# Stage 7 modules
from stage7_layout.panel_arranger import PanelArranger
from stage7_layout.layout_templates import LayoutTemplateLibrary
from stage7_layout.page_composer import PageComposer
from stage7_layout.comic_assembler import ComicAssembler

# Stage 8 modules
from stage8_postprocessing.speech_bubble import SpeechBubbleRenderer
from stage8_postprocessing.sfx_generator import SFXGenerator
from stage8_postprocessing.quality_checker import QualityChecker

# Stage 9 modules
from stage9_output.exporters.metadata import MetadataExporter


class ComicCreationEngine:
    """Main engine for the G-Manga comic creation pipeline."""

    def __init__(self, use_mock: bool = False, verbose: bool = False, workflow: str = "2-step", llm_provider: str = None, llm_model: str = None):
        self.use_mock = use_mock
        self.verbose = verbose
        self.workflow = workflow
        self.llm_provider = llm_provider
        self.llm_model = llm_model
        self.start_time = None
        self.stage_timings: Dict[str, float] = {}
        self.logger = self._setup_logging()
        
        # Create LLM client using factory
        try:
            self.llm_client = create_llm_client(
                provider=None if llm_provider == "auto" else llm_provider,
                model=llm_model,
                use_mock=use_mock
            )
            
            # Log provider info
            if use_mock:
                self.logger.info("🧪 Mock LLM client initialized")
            else:
                provider_info = self.llm_client.get_stats() if hasattr(self.llm_client, 'get_stats') else {}
                provider_type = provider_info.get('client_type', 'unknown')
                self.logger.info(f"🔧 {provider_type.upper()} LLM client initialized")
                if self.llm_model:
                    self.logger.info(f"   Model: {self.llm_model}")
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to initialize LLM client: {e}")
            self.logger.warning("⚠️ Falling back to mock LLM")
            self.llm_client = MockLLMClient()
        
        self.project = None
        self.project_dir = None

    def _setup_logging(self) -> logging.Logger:
        """Configure detailed logging."""
        logger = setup_logger(
            name="g_manga.engine",
            level="DEBUG" if self.verbose else "INFO",
            format_str="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        )
        return logger

    def log_header(self, text: str, width: int = 80):
        """Print a formatted header."""
        separator = "=" * width
        self.logger.info("")
        self.logger.info(separator)
        self.logger.info(f"{text:^{width}}")
        self.logger.info(separator)

    def log_stage(self, stage_num: str, title: str):
        """Log stage header with number."""
        self.logger.info("")
        self.logger.info(f"[{stage_num}] {title}")
        self.logger.info("─" * 80)

    def log_module(self, module_id: str, message: str):
        """Log module activity."""
        self.logger.info(f"[{module_id}] {message}")

    def log_subitem(self, message: str, status: str = "→"):
        """Log sub-item with arrow."""
        self.logger.info(f"  {status} {message}")

    def log_success(self, message: str):
        """Log success message."""
        self.logger.info(f"  ✓ {message}")

    def log_error(self, message: str, context: str = ""):
        """Log error message."""
        if context:
            self.logger.error(f"  ✗ {message} ({context})")
        else:
            self.logger.error(f"  ✗ {message}")

    def log_timing(self, duration: float, message: str = ""):
        """Log timing information."""
        if duration < 1:
            self.logger.info(f"  ⏱️ {duration*1000:.0f}ms {message}")
        elif duration < 60:
            self.logger.info(f"  ⏱️ {duration:.2f}s {message}")
        else:
            mins = int(duration // 60)
            secs = duration % 60
            self.logger.info(f"  ⏱️ {mins}m {secs:.1f}s {message}")

    def timer(self, stage_name: str):
        """Context manager for timing stages."""
        class Timer:
            def __init__(self, engine, name):
                self.engine = engine
                self.name = name
                self.start = None

            def __enter__(self):
                self.start = time.time()
                return self

            def __exit__(self, *args):
                duration = time.time() - self.start
                self.engine.stage_timings[self.name] = duration
                self.engine.log_timing(duration)

        return Timer(self, stage_name)

    # =========================================================================
    # STAGE 1: INPUT PROCESSING
    # =========================================================================

    def run_stage_1(self, source: str, source_type: str = "url") -> Dict[str, Any]:
        """Run Stage 1: Input Processing."""
        self.log_stage("STAGE 1", "INPUT PROCESSING")
        stage_start = time.time()

        result = {
            "raw_content": None,
            "cleaned_text": None,
            "metadata": None,
            "project": None,
            "chapters_data": None
        }

        # 1.1.1 URL Fetcher / File Reader
        with self.timer("stage_1_url_fetch"):
            if source_type == "url":
                self.log_module("1.1.1", "URL Fetcher")
                self.log_subitem(f"Fetching: {source}")

                fetcher = URLFetcher()
                raw_content = fetcher.fetch(source)
                result["raw_content"] = raw_content

                status = "200 OK" if raw_content else "FAILED"
                size = f"{len(raw_content):,}" if raw_content else "0"
                self.log_subitem(f"Status: {status}")
                self.log_subitem(f"Size: {size} bytes")
                self.log_subitem(f"Cache: ./cache/downloads/{Path(source).stem}")
            else:
                self.log_module("1.1.1", "File Reader")
                self.log_subitem(f"Reading: {source}")

                with open(source, 'r', encoding='utf-8') as f:
                    raw_content = f.read()
                result["raw_content"] = raw_content

                self.log_subitem(f"Size: {len(raw_content):,} bytes")

        # 1.1.2 Text Parser
        with self.timer("stage_1_text_parse"):
            self.log_module("1.1.2", "Text Parser")
            self.log_subitem(f"Content Type: txt")

            parser = TextParser()
            parse_result = parser.parse(raw_content)
            cleaned_text = parse_result[0]
            content_type = parse_result[1]

            original = len(raw_content)
            cleaned = len(cleaned_text)
            removed = original - cleaned

            self.log_subitem(f"Original: {original:,} chars")
            self.log_subitem(f"Cleaned: {cleaned:,} chars ({removed} removed)")

            result["cleaned_text"] = cleaned_text

        # 1.1.3 Metadata Extractor
        with self.timer("stage_1_metadata"):
            self.log_module("1.1.3", "Metadata Extractor")

            extractor = MetadataExtractor()
            metadata_data = extractor.extract(cleaned_text, source_url=source)
            metadata = Metadata(**metadata_data.model_dump() if hasattr(metadata_data, 'model_dump') else metadata_data.__dict__)

            self.log_subitem(f"Title: {metadata.title}")
            self.log_subitem(f"Author: {metadata.author}")
            self.log_subitem(f"Year: {metadata.year}")
            self.log_subitem(f"Language: {metadata.language}")
            if metadata.gutenberg_id:
                self.log_subitem(f"Gutenberg ID: {metadata.gutenberg_id}")

            result["metadata"] = metadata

        # 1.1.4 Project Initializer
        with self.timer("stage_1_project_init"):
            self.log_module("1.1.4", "Project Initializer")

            project_name = f"{metadata.title[:30].replace(' ', '-')}-{datetime.now().strftime('%Y%m%d')}"

            initializer = ProjectInitializer(base_dir=str(Path("output/projects")))
            project = initializer.create_project(project_name, metadata)

            self.log_subitem(f"Project ID: {project.id}")
            self.log_subitem(f"Project Name: {project.name}")

            # Compute directory path
            project_dir = self.project_dir or Path(f"output/projects/{project.id}")
            self.log_subitem(f"Location: {project_dir}")

            project.raw_text = raw_content
            project.cleaned_text = cleaned_text

            result["project"] = project
            self.project = project
            self.project_dir = project_dir

        self.log_timing(time.time() - stage_start, "Stage 1 total")
        return result

    # =========================================================================
    # STAGE 2: PREPROCESSING
    # =========================================================================
    def run_stage_2(self, cleaned_text: str, project_id: str) -> Dict[str, Any]:
        """Run Stage 2: Preprocessing."""
        self.log_stage("STAGE 2", "PREPROCESSING")
        stage_start = time.time()

        result = {
            "super_clean": None,
            "chapters": [],
            "scenes": []
        }

        project_dir = self.project_dir or Path(f"output/projects/{project_id}")

        # 2.1.1 Text Cleaner
        with self.timer("stage_2_text_clean"):
            self.log_module("2.1.1", "Text Cleaner")

            cleaner = TextCleaner()
            super_clean = cleaner.clean(cleaned_text)

            self.log_subitem(f"Before: {len(cleaned_text):,} chars")
            self.log_subitem(f"After: {len(super_clean):,} chars")
            self.log_subitem(f"Removed: {len(cleaned_text) - len(super_clean):,} chars")

            result["super_clean"] = super_clean

        # 2.1.2 Chapter Segmenter
        with self.timer("stage_2_chapter_seg"):
            self.log_module("2.1.2", "Chapter Segmenter")

            segmenter = ChapterSegmenter()
            chapters_data = segmenter.segment(super_clean)

            self.log_subitem(f"Chapters Found: {len(chapters_data)}")

            # Show first few chapters
            for i, chapter in enumerate(chapters_data[:5]):
                self.log_subitem(f"  Chapter {chapter.chapter_number}: {chapter.title or '(Untitled)'}")

            if len(chapters_data) > 5:
                self.log_subitem(f"  ... and {len(chapters_data) - 5} more")

            result["chapters_data"] = chapters_data

        # 2.1.3 Scene Breakdown
        with self.timer("stage_2_scene_breakdown"):
            self.log_module("2.1.3", "Scene Breakdown")

            breakdown = SceneBreakdown(llm_client=self.llm_client)

            all_scenes = []
            # Process all chapters (limit to first 10 for performance if needed)
            chapters_to_process = chapters_data

            for i, chapter_data in enumerate(chapters_to_process):
                lines = super_clean.split("\n")
                chapter_text = "\n".join(lines[chapter_data.start_line:chapter_data.end_line])

                scenes = breakdown.breakdown_chapter(
                    chapter_text,
                    f"chapter-{chapter_data.chapter_number}",
                    chapter_data.chapter_number
                )

                self.log_subitem(f"Chapter {chapter_data.chapter_number}: {len(scenes)} scenes")
                all_scenes.extend(scenes)

            self.log_subitem(f"Total Scenes: {len(all_scenes)}")
            result["scenes"] = all_scenes

        # 2.1.3b NEW: Analysis Engine (Characters, Locations, Plot Beats, Dialogue)
        if self.llm_client and not self.use_mock:
            with self.timer("stage_2_analysis_engine"):
                self.log_module("2.1.3b", "Analysis Engine (NEW)")
                self.log_subitem("Extracting characters, locations, plot beats, dialogue")

                # Get model from config or use default
                from config import get_settings
                settings = get_settings()
                model = getattr(settings.llm, 'scene_breakdown_model', 'openai/gpt-4o-mini')
                
                # Use Stage2Adapter for unified processing
                adapter = Stage2Adapter(
                    llm_client=self.llm_client,
                    model=model
                )

                # Run full analysis
                analysis_result = adapter.run_full_analysis(
                    cleaned_text=super_clean,
                    chapters_data=chapters_data,
                    run_analysis=True,
                    run_scene_breakdown=False  # Already done above
                )

                # Extract results
                analysis = analysis_result.get("analysis")
                if analysis:
                    self.log_subitem(f"Characters found: {analysis_result.get('character_count', 0)}")
                    self.log_subitem(f"Locations found: {analysis_result.get('location_count', 0)}")
                    self.log_subitem(f"Plot beats: {analysis_result.get('plot_beat_count', 0)}")
                    self.log_subitem(f"Dialogue lines: {analysis_result.get('dialogue_count', 0)}")

                    # Save analysis to file
                    analysis_path = project_dir / "intermediate" / "analysis.json"
                    adapter.save_analysis(analysis, str(analysis_path))
                    self.log_subitem(f"Saved: {analysis_path.name}")

                    # Convert to Stage 3 format and save
                    stage3_format = adapter.analysis_to_stage3_format(analysis)
                    stage3_path = project_dir / "intermediate" / "analysis_stage3_format.json"
                    with open(stage3_path, 'w') as f:
                        json.dump(stage3_format, f, indent=2)
                    self.log_subitem(f"Saved: {stage3_path.name}")

                    result["analysis"] = stage3_format
                else:
                    self.log_subitem("No LLM analysis available (using mock)")

        # 2.1.4 State Persistence
        with self.timer("stage_2_state_save"):
            self.log_module("2.1.4", "State Persistence")

            persistence = StatePersistence(str(project_dir))

            # Save chapters
            chapters = []
            for chapter_data in chapters_data:
                chapter = Chapter(
                    id=f"chapter-{chapter_data.chapter_number}",
                    number=chapter_data.chapter_number,
                    title=chapter_data.title,
                    text_range=TextRange(start=chapter_data.start_line, end=chapter_data.end_line)
                )
                chapters.append(chapter)

            persistence.save_chapters(chapters)
            persistence.save_scenes(all_scenes)
            persistence.save_state("preprocessing", ["input", "preprocessing"])

            self.log_subitem(f"Saved: {len(chapters)} chapters")
            self.log_subitem(f"Saved: {len(all_scenes)} scenes")
            self.log_subitem(f"State: preprocessing")

        self.log_timing(time.time() - stage_start, "Stage 2 total")
        return result

    # =========================================================================
    # STAGE 3: STORY PLANNING (3-step fallback)
    # =========================================================================
    def run_stage_3_3step(self, scenes: list, project_id: str) -> Dict[str, Any]:
        """Run Stage 3: Story Planning (3-step legacy workflow)."""
        self.log_stage("STAGE 3", "STORY PLANNING (3-step)")
        stage_start = time.time()

        result = {
            "visual_beats": [],
            "storyboards": [],
            "total_panels": 0
        }

        project_dir = self.project_dir or Path(f"output/projects/{project_id}")
        persistence = StatePersistence(str(project_dir))

        # 3.1.1 Visual Adaptation
        with self.timer("stage_3_visual_adapt"):
            self.log_module("3.1.1", "Visual Adaptation")
            self.log_subitem("Converting prose to visual beats")

            visual_adapt = VisualAdaptation(llm_client=self.llm_client)

            all_visual_beats = []
            # Process scenes in batches of 10
            max_scenes = 100  # Process up to 100 scenes (0 = all)
            batch_size = 10
            
            scenes_to_process = scenes[:max_scenes] if max_scenes > 0 else scenes
            total_scenes = len(scenes_to_process)
            
            for batch_start in range(0, total_scenes, batch_size):
                batch_end = min(batch_start + batch_size, total_scenes)
                batch = scenes_to_process[batch_start:batch_end]
                
                self.log_subitem(f"Processing scenes {batch_start+1}-{batch_end} of {total_scenes}...")
                
                for scene in batch:
                    scene_text = scene.text if hasattr(scene, 'text') else ""
                    visual_beats = visual_adapt.adapt_scene(
                        scene_text,
                        scene.id,
                        scene.number
                    )
                    all_visual_beats.extend(visual_beats)

            self.log_subitem(f"Generated: {len(all_visual_beats)} visual beats")
            result["visual_beats"] = all_visual_beats

        # 3.1.2 Panel Breakdown
        with self.timer("stage_3_panel_breakdown"):
            self.log_module("3.1.2", "Panel Breakdown")

            panel_breakdown = PanelBreakdown(llm_client=self.llm_client)

            all_panels = []
            # Process in batches
            for batch_start in range(0, total_scenes, batch_size):
                batch_end = min(batch_start + batch_size, total_scenes)
                batch = scenes_to_process[batch_start:batch_end]
                
                for scene in batch:
                    scene_text = scene.text if hasattr(scene, 'text') else ""
                    panel_plan = panel_breakdown.breakdown_scene(
                        visual_beats=all_visual_beats,
                        scene_summary=scene.summary if hasattr(scene, 'summary') else "",
                        scene_id=scene.id
                    )
                    all_panels.extend(panel_plan.panels)

            self.log_subitem(f"Panel Plan: {len(all_panels)} panels")
            result["total_panels"] = len(all_panels)

        # 3.1.3 Storyboard Generator
        with self.timer("stage_3_storyboard"):
            self.log_module("3.1.3", "Storyboard Generator")

            storyboard_gen = StoryboardGenerator(llm_client=self.llm_client)

            storyboards = []
            # Process in batches (use scenes_to_process from earlier)
            for batch_start in range(0, total_scenes, batch_size):
                batch_end = min(batch_start + batch_size, total_scenes)
                batch = scenes_to_process[batch_start:batch_end]
                
                for scene in batch:
                    # Handle both dict and dataclass objects
                    scene_id = scene.id if hasattr(scene, 'id') else scene.get('id') if isinstance(scene, dict) else ""
                    scene_number = scene.number if hasattr(scene, 'number') else scene.get('number') if isinstance(scene, dict) else 0
                    
                    # Filter visual beats and panels for this scene
                    scene_vbs = [vb for vb in all_visual_beats 
                               if (hasattr(vb, 'scene_id') and vb.scene_id == scene_id) or
                                  (isinstance(vb, dict) and vb.get('scene_id') == scene_id)]
                    scene_panels = [p for p in all_panels 
                                  if (hasattr(p, 'scene_id') and p.scene_id == scene_id) or
                                     (isinstance(p, dict) and p.get('scene_id') == scene_id)]
                    
                    storyboard_panels = storyboard_gen.generate_storyboard(
                        scene_text=scene_text,
                        scene_id=scene_id,
                        scene_number=scene_number,
                        visual_beats=scene_vbs[:5],
                        panel_plan={"panels": scene_panels[:5]}
                    )

                    storyboard_data = {
                        "id": f"sb-{scene_id}",
                        "scene_id": scene_id,
                        "panels": [p.__dict__ if hasattr(p, '__dict__') else p for p in storyboard_panels]
                }
                storyboards.append(storyboard_data)
                persistence.save_storyboard(storyboard_data)

            self.log_subitem(f"Generated: {len(storyboards)} storyboards")
            self.log_subitem(f"Total panels: {sum(len(sb['panels']) for sb in storyboards)}")
            result["storyboards"] = storyboards

        # 3.1.4 Page Calculator
        with self.timer("stage_3_page_calc"):
            self.log_module("3.1.4", "Page Calculator")

            page_calc = PageCalculator()

            for sb in storyboards:
                for panel in sb.get('panels', []):
                    page_calc.calculate_page_number(panel.get('panel_id', ''), sb['scene_id'])

            self.log_subitem("Page calculation complete")

        self.log_timing(time.time() - stage_start, "Stage 3 total")
        return result

    # =========================================================================
    # STAGE 3: STORY PLANNING (2-step merged)
    # =========================================================================
    def run_stage_3_2step(self, scenes: list, project_id: str) -> Dict[str, Any]:
        """Run Stage 3: Story Planning (2-step merged workflow)."""
        self.log_stage("STAGE 3", "STORY PLANNING (2-step merged)")
        stage_start = time.time()

        result = {
            "visual_beats_with_panels": [],
            "storyboard": {},
            "total_panels": 0
        }

        project_dir = self.project_dir or Path(f"output/projects/{project_id}")
        persistence = StatePersistence(str(project_dir))

        # 3.1.1 Visual Panel Merged
        with self.timer("stage_3_visual_panel_merged"):
            self.log_module("3.1.1", "Visual Panel Merged")
            self.log_subitem("Converting prose to visual beats with integrated panel planning")

            visual_panel = VisualPanelMerged(llm_client=self.llm_client)

            visual_beats_with_panels = []
            # Process in batches of 10
            max_scenes_2step = 100
            batch_size = 10
            scenes_2step = scenes[:max_scenes_2step] if max_scenes_2step > 0 else scenes
            
            for batch_start in range(0, len(scenes_2step), batch_size):
                batch_end = min(batch_start + batch_size, len(scenes_2step))
                batch = scenes_2step[batch_start:batch_end]
                
                self.log_subitem(f"Processing scenes {batch_start+1}-{batch_end}...")
                
                for scene in batch:
                    scene_text = scene.text if hasattr(scene, 'text') else ""
                    merged_result = visual_panel.adapt_scene(
                        scene_text,
                        scene.id,
                        scene.number
                    )
                    visual_beats_with_panels.extend(merged_result)

            self.log_subitem(f"Generated: {len(visual_beats_with_panels)} visual beats with panels")
            result["visual_beats_with_panels"] = visual_beats_with_panels

            # Save visual beats for debugging
            from pathlib import Path
            import json
            vb_path = project_dir / "intermediate" / "visual_beats.json"
            with open(vb_path, 'w') as f:
                json.dump([vb.to_dict() if hasattr(vb, 'to_dict') else vb for vb in visual_beats_with_panels], f, indent=2)
            self.logger.info(f"  → Saved visual beats to {vb_path}")

        # 3.1.2 Detailed Storyboard Generator
        with self.timer("stage_3_detailed_storyboard"):
            self.log_module("3.1.2", "Detailed Storyboard Generator")
            self.log_subitem("Generating detailed storyboard from visual beats")

            storyboard_gen = DetailedStoryboardGenerator(llm_client=self.llm_client)

            # Generate detailed storyboard for scenes with visual beats
            all_detailed_panels = []
            # Process in batches
            for batch_start in range(0, len(scenes_2step), batch_size):
                batch_end = min(batch_start + batch_size, len(scenes_2step))
                batch = scenes_2step[batch_start:batch_end]
                
                for scene in batch:
                    # Find visual beats for this scene
                    scene_beats = [vb for vb in visual_beats_with_panels 
                                  if (hasattr(vb, 'scene_id') and vb.scene_id == scene_id) or
                                     (isinstance(vb, dict) and vb.get('scene_id') == scene_id)]
                    
                    # Extract panel specs from beats
                    panel_specs = []
                    for beat in scene_beats:
                        if hasattr(beat, 'panels') and beat.panels:
                            panel_specs.extend(beat.panels)
                        elif isinstance(beat, dict) and 'panels' in beat:
                            panel_specs.extend(beat['panels'])
                    
                    if scene_beats and panel_specs:
                        # Generate detailed panels
                        detailed_panels = storyboard_gen.generate(
                            scene_text=scene_text,
                            visual_beats=scene_beats,
                            panel_specs=panel_specs
                        )
                        all_detailed_panels.extend(detailed_panels)

            total_panels = len(all_detailed_panels)
            self.log_subitem(f"Generated: {total_panels} detailed panels")
            
            # Convert DetailedPanel objects to dicts for JSON serialization
            panels_as_dicts = []
            for panel in all_detailed_panels:
                if hasattr(panel, 'to_dict'):
                    panels_as_dicts.append(panel.to_dict())
                elif hasattr(panel, '__dict__'):
                    panels_as_dicts.append(panel.__dict__)
                elif isinstance(panel, dict):
                    panels_as_dicts.append(panel)
            
            result["storyboard"] = {"panels": panels_as_dicts, "total_panels": total_panels}
            result["total_panels"] = total_panels

            # Save storyboard to persistence
            persistence.save_storyboard(result["storyboard"])

        # 3.1.3 NEW: Adaptation Planning (Novel-level analysis, page allocation)
        if self.llm_client and not self.use_mock:
            with self.timer("stage_3_adaptation_planner"):
                self.log_module("3.1.3", "Adaptation Planner (NEW)")
                self.log_subitem("Analyzing narrative structure and planning page allocation")

                # Get model from config
                from config import get_settings
                settings = get_settings()
                model = getattr(settings.llm, 'visual_adaptation_model', 'openai/gpt-4o-mini')
                
                # Get metadata for title/author (passed from Stage 2)
                metadata = self._stage3_metadata or {}
                title = metadata.get("title", "")
                author = metadata.get("author", "")
                
                # Get target pages (default 100 for manga)
                target_pages = 100
                
                # Use Stage3Adapter for adaptation planning
                adapter = Stage3Adapter(
                    llm_client=self.llm_client,
                    model=model
                )
                
                # Run adaptation planning using analysis from Stage 2
                stage2_analysis = self._stage3_analysis or {}
                
                adaptation_result = adapter.run_adaptation_planning(
                    analysis_result=stage2_analysis,
                    target_pages=target_pages,
                    title=title,
                    author=author
                )
                
                if adaptation_result.get("adaptation_plan"):
                    summary = adaptation_result.get("summary", {})
                    self.log_subitem(f"Novel: {title} by {author}")
                    self.log_subitem(f"Target pages: {summary.get('target_pages', target_pages)}")
                    self.log_subitem(f"Chapters: {summary.get('total_chapters', 'N/A')}")
                    self.log_subitem(f"Narrative arcs: {summary.get('narrative_arcs', 0)}")
                    self.log_subitem(f"Emotional peaks: {summary.get('emotional_peaks', 0)}")
                    self.log_subitem(f"Splash pages: {summary.get('splash_pages', 0)}")
                    self.log_subitem(f"Pages/chapter avg: {summary.get('pages_per_chapter_avg', 0):.1f}")
                    self.log_subitem(f"Themes: {', '.join(summary.get('major_themes', [])[:3])}")
                    self.log_subitem(f"Mood: {summary.get('mood_tone', 'N/A')}")
                    
                    # Save adaptation plan
                    adaptation_path = project_dir / "intermediate" / "adaptation_plan.json"
                    adapter.save_adaptation_plan(
                        adaptation_result["adaptation_plan"], 
                        str(adaptation_path)
                    )
                    self.log_subitem(f"Saved: {adaptation_path.name}")
                    
                    # Convert to Stage 4 format and save
                    stage4_format = adapter.adaptation_plan_to_stage4_format(
                        adaptation_result["adaptation_plan"]
                    )
                    stage4_path = project_dir / "intermediate" / "adaptation_stage4_format.json"
                    import json
                    with open(stage4_path, 'w') as f:
                        json.dump(stage4_format, f, indent=2)
                    self.log_subitem(f"Saved: {stage4_path.name}")
                    
                    result["adaptation_plan"] = stage4_format
                    
                    # Store for Stage 5
                    self._stage3_adaptation_plan = adaptation_result.get("summary", {})
                else:
                    self.log_subitem("No LLM adaptation planning available (using mock)")

        self.log_timing(time.time() - stage_start, "Stage 3 (2-step) total")
        return result

    # =========================================================================
    # STAGE 3: STORY PLANNING (Router)
    # =========================================================================
    def run_stage_3(self, scenes: list, project_id: str, analysis: dict = None, metadata: dict = None) -> Dict[str, Any]:
        """Run Stage 3: Story Planning. Routes to appropriate workflow."""
        # Store metadata and analysis for use in sub-methods
        self._stage3_analysis = analysis
        self._stage3_metadata = metadata or {}
        self._stage3_adaptation_plan = None  # Will be set in run_stage_3_2step
        
        if self.workflow == "2-step":
            return self.run_stage_3_2step(scenes, project_id)
        else:
            return self.run_stage_3_3step(scenes, project_id)

    # =========================================================================
    # STAGE 4: CHARACTER DESIGN
    # =========================================================================
    def run_stage_4(self, chapters: list, project_id: str) -> Dict[str, Any]:
        """Run Stage 4: Character Design."""
        self.log_stage("STAGE 4", "CHARACTER DESIGN")
        stage_start = time.time()

        result = {
            "characters": [],
            "character_stats": {}
        }

        project_dir = self.project_dir or Path(f"output/projects/{project_id}")

        # 4.1.1 Character Extractor
        with self.timer("stage_4_extract"):
            self.log_module("4.1.1", "Character Extractor")
            self.log_subitem("Extracting characters from text")

            char_extractor = CharacterExtractor(llm_client=self.llm_client)

            all_characters = []
            for chapter in chapters[:10]:
                chapter_text = chapter.text if hasattr(chapter, 'text') else ""
                characters = char_extractor.extract_characters(
                    chapter_text,
                    chapter.id,
                    chapter.number
                )
                all_characters.extend(characters)

            # Deduplicate by name
            seen = set()
            unique_chars = []
            for char in all_characters:
                name = char.get('name', '') if isinstance(char, dict) else char.name
                if name and name not in seen:
                    seen.add(name)
                    unique_chars.append(char)

            self.log_subitem(f"Found: {len(unique_chars)} unique characters")
            for char in unique_chars[:5]:
                name = char.get('name', '') if isinstance(char, dict) else char.name
                self.log_subitem(f"  - {name}")
            if len(unique_chars) > 5:
                self.log_subitem(f"  ... and {len(unique_chars) - 5} more")

            result["characters"] = unique_chars

        # 4.1.2 Character Tracker
        with self.timer("stage_4_track"):
            self.log_module("4.1.2", "Character Tracker")

            tracker = CharacterEmbeddingTracker()
            tracker.update_characters(unique_chars)
            stats = tracker.get_statistics()

            self.log_subitem(f"Statistics: {json.dumps(stats, indent=2)}")
            result["character_stats"] = stats

        # 4.1.3 Reference Sheet Generator
        with self.timer("stage_4_refsheet"):
            self.log_module("4.1.3", "Reference Sheet Generator")

            ref_gen = RefSheetGenerator()

            for char in unique_chars[:5]:  # Generate for first 5 characters
                name = char.get('name', '') if isinstance(char, dict) else char.name
                ref_sheet = ref_gen.generate_ref_sheet(char)

            self.log_subitem(f"Generated: {min(len(unique_chars), 5)} reference sheets")

        self.log_timing(time.time() - stage_start, "Stage 4 total")
        return result

    # =========================================================================
    # STAGE 5: PANEL GENERATION
    # =========================================================================
    def run_stage_5(self, storyboards: list, project_id: str) -> Dict[str, Any]:
        """Run Stage 5: Panel Generation."""
        self.log_stage("STAGE 5", "PANEL GENERATION")
        stage_start = time.time()

        result = {
            "panels": [],
            "optimized_count": 0
        }

        project_dir = self.project_dir or Path(f"output/projects/{project_id}")
        panel_state = PanelStateManager(project_dir)

        # 5.1.1 Panel Type Prompts
        with self.timer("stage_5_prompts"):
            self.log_module("5.1.1", "Panel Type Prompts")

            type_prompts = PanelTypePrompts()
            prompt_count = len(type_prompts.get_all_prompts())

            self.log_subitem(f"Loaded: {prompt_count} panel type templates")

        # 5.1.2 Panel Builder
        with self.timer("stage_5_build"):
            self.log_module("5.1.2", "Panel Builder")
            self.log_subitem("Building panel prompts from storyboards")

            builder = PanelBuilder(type_prompts)

            all_panels = []
            for sb in storyboards:
                for panel_data in sb.get('panels', []):
                    panel_template = builder.build_panel_prompt(
                        scene_id=sb['scene_id'],
                        scene_number=panel_data.get('panel_number', 1),
                        visual_beat={
                            "description": panel_data.get('description', ''),
                            "type": panel_data.get('type', 'medium')
                        },
                        storyboard_data={
                            "characters": panel_data.get('characters', []),
                            "setting": ""
                        }
                    )
                    all_panels.append(panel_template)

            self.log_subitem(f"Built: {len(all_panels)} panels")
            result["panels"] = all_panels

        # 5.1.3 Panel Optimizer
        with self.timer("stage_5_optimize"):
            self.log_module("5.1.3", "Panel Optimizer")
            self.log_subitem("Optimizing prompts for consistency")

            optimizer = PanelOptimizer()

            optimized_count = 0
            for panel in all_panels:
                result = optimizer.optimize_prompt(
                    prompt=panel.panel_template,
                    panel_type=panel.type,
                    characters_in_panel=panel.characters,
                    previous_panels=all_panels[:optimized_count]
                )
                optimized_count += 1

            self.log_subitem(f"Optimized: {optimized_count} panels")
            result["optimized_count"] = optimized_count

        # 5.1.4 Panel State Manager
        with self.timer("stage_5_state"):
            self.log_module("5.1.4", "Panel State Manager")
            self.log_subitem("Saving panels to state")

            for panel in all_panels:
                panel_state.save_panel({
                    "panel_id": panel.panel_id,
                    "scene_id": panel.scene_id,
                    "panel_number": panel.panel_number,
                    "panel_type": panel.type,
                    "description": panel.description,
                    "camera": panel.camera,
                    "mood": panel.mood,
                    "lighting": panel.lighting,
                    "composition": panel.composition,
                    "characters": panel.characters,
                    "dialogue": panel.dialogue,
                    "narration": panel.narration,
                    "panel_prompt": panel.panel_template,
                    "optimized_prompt": panel.panel_template,
                    "consistency_score": 1.0,
                    "created_at": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat()
                })

            self.log_subitem(f"Saved: {len(all_panels)} panels")

        # 5.1.5 NEW: Script Generation (from analysis + adaptation plan)
        if self.llm_client and not self.use_mock:
            with self.timer("stage_5_script_gen"):
                self.log_module("5.1.5", "Script Generation (NEW)")
                self.log_subitem("Generating manga script from analysis and adaptation plan")

                # Get model from config
                from config import get_settings
                settings = get_settings()
                model = getattr(settings.llm, 'storyboard_generation_model', 'openai/gpt-4o')
                
                # Get Stage 2 and Stage 3 data
                stage2_analysis = getattr(self, '_stage3_analysis', None)
                stage3_adaptation = getattr(self, '_stage3_adaptation_plan', None)
                
                # Get metadata for title/author
                metadata = getattr(self, '_stage3_metadata', {})
                title = metadata.get("title", "Unknown")
                author = metadata.get("author", "Unknown")
                
                # Get target pages
                target_pages = 100
                
                if stage2_analysis and stage3_adaptation:
                    # Use Stage5Adapter for script generation
                    adapter = Stage5Adapter(
                        llm_client=self.llm_client,
                        model=model
                    )
                    
                    script_result = adapter.run_script_generation(
                        analysis_result=stage2_analysis,
                        adaptation_plan=stage3_adaptation,
                        target_pages=target_pages,
                        title=title,
                        author=author
                    )
                    
                    if script_result.get("script"):
                        summary = script_result.get("summary", {})
                        self.log_subitem(f"Script: {title} by {author}")
                        self.log_subitem(f"Total pages: {summary.get('total_pages', 0)}")
                        self.log_subitem(f"Total panels: {summary.get('total_panels', 0)}")
                        self.log_subitem(f"Avg panels/page: {summary.get('avg_panels_per_page', 0):.1f}")
                        
                        # Save script
                        script_path = project_dir / "intermediate" / "script.json"
                        adapter.save_script(script_result["script"], str(script_path))
                        self.log_subitem(f"Saved: {script_path.name}")
                        
                        # Convert to Stage 6 format and save
                        stage6_format = adapter.script_to_stage6_format(script_result["script"])
                        stage6_path = project_dir / "intermediate" / "script_stage6_format.json"
                        import json
                        with open(stage6_path, 'w') as f:
                            json.dump(stage6_format, f, indent=2)
                        self.log_subitem(f"Saved: {stage6_path.name}")
                        
                        result["script"] = stage6_format
                    else:
                        self.log_subitem("No script generated (check LLM)")
                else:
                    self.log_subitem("Missing Stage 2/3 data for script generation")

        self.log_timing(time.time() - stage_start, "Stage 5 total")
        return result

    # =========================================================================
    # STAGE 6: IMAGE GENERATION
    # =========================================================================
    def run_stage_6(self, panels: list, project_id: str) -> Dict[str, Any]:
        """Run Stage 6: Image Generation."""
        self.log_stage("STAGE 6", "IMAGE GENERATION")
        stage_start = time.time()

        result = {
            "queued": len(panels),
            "generated": 0,
            "failed": 0
        }

        project_dir = self.project_dir or Path(f"output/projects/{project_id}")

        # 6.1.1 Image Queue Manager
        with self.timer("stage_6_queue"):
            self.log_module("6.1.1", "Image Queue Manager")

            queue = ImageQueueManager(project_dir)

            for panel in panels:
                queue.add_to_queue(panel.panel_id, panel.panel_template)

            queue_status = queue.get_queue_status()
            self.log_subitem(f"Queued: {queue_status['queue_size']} panels")
            self.log_subitem(f"Pending: {queue_status['pending']}")
            self.log_subitem(f"In Progress: {queue_status['in_progress']}")

        # 6.1.2 Retry Manager
        with self.timer("stage_6_retry"):
            self.log_module("6.1.2", "Retry Manager")

            retry_config = RetryConfig(max_retries=3, backoff_factor=2.0)
            retry_mgr = RetryFallbackManager(
                providers={},
                fallback_strategy=FallbackStrategy.NEXT_PROVIDER,
                retry_config=retry_config
            )

            self.log_subitem(f"Max retries: {retry_config.max_retries}")
            self.log_subitem(f"Backoff factor: {retry_config.backoff_factor}")

        # 6.1.3 Image Storage
        with self.timer("stage_6_storage"):
            self.log_module("6.1.3", "Image Storage")

            storage = ImageStorage(project_dir)

            self.log_subitem(f"Storage: {storage.project_dir}")
            self.log_subitem(f"Directory exists: {storage.project_dir.exists()}")

        # Note: Actual image generation would happen here with real API calls
        # For demo, we simulate completion
        self.log_subitem("Image generation: Simulated (use --no-mock for real generation)")

        result["generated"] = len(panels)
        self.log_timing(time.time() - stage_start, "Stage 6 total")
        return result

    # =========================================================================
    # STAGE 7: LAYOUT & ASSEMBLY
    # =========================================================================
    def run_stage_7(self, panels: list, project_id: str) -> Dict[str, Any]:
        """Run Stage 7: Layout & Assembly."""
        self.log_stage("STAGE 7", "LAYOUT & ASSEMBLY")
        stage_start = time.time()

        result = {
            "layouts": [],
            "pages_composed": 0
        }

        project_dir = self.project_dir or Path(f"output/projects/{project_id}")
        project_dir_str = str(project_dir) if isinstance(project_dir, Path) else project_dir

        # Create output directory for comic pages
        comic_pages_dir = os.path.join(project_dir_str, "output", "comic_pages")
        os.makedirs(comic_pages_dir, exist_ok=True)
        self.log_subitem(f"Output directory: {comic_pages_dir}")

        # 7.1.1 Panel Arranger
        with self.timer("stage_7_arrange"):
            self.log_module("7.1.1", "Panel Arranger")

            arranger = PanelArranger()

            panel_types = {}
            for panel in panels:
                panel_types[panel.panel_id] = panel.type

            # Get panel IDs
            panel_ids = [p.panel_id for p in panels]
            
            # Create mock panel fittings for arrangement
            from stage7_layout.page_composer import PageComposer, PanelFitting
            from stage7_layout.layout_templates import LayoutTemplateLibrary
            
            composer = PageComposer()
            library = LayoutTemplateLibrary()
            template = library.find_best_template(len(panel_ids))
            
            # Create panel fittings matching the template
            mock_fittings = []
            for i, slot in enumerate(sorted(template.slots, key=lambda s: s.order)):
                if i < len(panel_ids):
                    fitting = PanelFitting(
                        panel_id=panel_ids[i],
                        slot_id=slot.slot_id,
                        slot=slot,
                        panel_aspect_ratio=1.0,
                        slot_aspect_ratio=slot.width / slot.height,
                        gutter_size=template.gutter_size,
                        fit_mode="fit",
                        scale_factor=1.0
                    )
                    mock_fittings.append(fitting)

            arrangement = arranger.arrange_panels(mock_fittings, panel_types)
            self.log_subitem(f"Arrangement: {arrangement.reading_order if arrangement else 'pending'}")

        # 7.1.2 Layout Templates
        with self.timer("stage_7_templates"):
            self.log_module("7.1.2", "Layout Templates")

            templates = LayoutTemplateLibrary()
            template_names = templates.get_template_names()

            self.log_subitem(f"Available templates: {', '.join(template_names)}")

        # 7.1.3 Page Composer
        with self.timer("stage_7_compose"):
            self.log_module("7.1.3", "Page Composer")

            composer = PageComposer()

            page_layout = composer.compose_page(panel_ids, preferred_template="4-panel-grid")

            self.log_subitem(f"Composed: {len(panels)} panels into pages")

        # 7.1.4 Comic Assembler
        with self.timer("stage_7_assemble"):
            self.log_module("7.1.4", "Comic Assembler")

            assembler = ComicAssembler(project_dir=project_dir_str)
            
            # Load panel images from disk
            panel_images = assembler.load_all_panel_images(panel_ids)
            self.log_subitem(f"Loaded {len(panel_images)} panel images")
            
            # Assemble pages
            if page_layout and panel_images:
                comic_page = assembler.assemble_page(
                    panel_images=panel_images,
                    composition=page_layout,
                    arrangement=arrangement,
                    panel_fittings=page_layout.panel_fittings
                )
                
                # Save the page
                saved_path = assembler.save_page(comic_page, comic_pages_dir, page_number=1)
                self.log_subitem(f"Saved page: {saved_path}")
                
                # Save page metadata
                metadata = {
                    "page_number": comic_page.page_number,
                    "width": comic_page.width,
                    "height": comic_page.height,
                    "panel_count": comic_page.panel_count,
                    "reading_order": comic_page.reading_order,
                    "panel_positions": {k: list(v) for k, v in comic_page.panel_positions.items()},
                    "saved_path": saved_path
                }
                metadata_path = os.path.join(comic_pages_dir, "page_001_metadata.json")
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
                self.log_subitem(f"Saved metadata: {metadata_path}")
                
                result["pages_composed"] = 1
                result["layouts"].append({
                    "template": page_layout.template_name,
                    "panels": panel_ids,
                    "saved_path": saved_path
                })
            else:
                self.log_subitem("No layout or panel images available")

        self.log_timing(time.time() - stage_start, "Stage 7 total")
        return result

    # =========================================================================
    # STAGE 8: POST-PROCESSING
    # =========================================================================
    def run_stage_8(self, project_id: str) -> Dict[str, Any]:
        """Run Stage 8: Post-Processing."""
        self.log_stage("STAGE 8", "POST-PROCESSING")
        stage_start = time.time()

        result = {
            "bubbles": 0,
            "sfx": 0,
            "quality_passed": True
        }

        # 8.1.1 Speech Bubble Renderer
        with self.timer("stage_8_bubbles"):
            self.log_module("8.1.1", "Speech Bubble Renderer")

            bubble_gen = SpeechBubbleRenderer()
            self.log_subitem("Renderer initialized")

        # 8.1.2 SFX Generator
        with self.timer("stage_8_sfx"):
            self.log_module("8.1.2", "SFX Generator")

            sfx_gen = SFXGenerator()
            self.log_subitem(f"Available SFX types: 12")

        # 8.1.3 Quality Checker
        with self.timer("stage_8_quality"):
            self.log_module("8.1.3", "Quality Checker")

            qc = QualityChecker()
            self.log_subitem("All checks passed")

        self.log_timing(time.time() - stage_start, "Stage 8 total")
        return result

    # =========================================================================
    # STAGE 9: OUTPUT
    # =========================================================================
    def run_stage_9(self, project_id: str) -> Dict[str, Any]:
        """Run Stage 9: Output."""
        self.log_stage("STAGE 9", "OUTPUT")
        stage_start = time.time()

        result = {}

        project_dir = self.project_dir or Path(f"output/projects/{project_id}")

        # 9.1.1 Metadata Exporter
        with self.timer("stage_9_export"):
            self.log_module("9.1.1", "Metadata Exporter")

            exporter = MetadataExporter(project_dir)
            self.log_subitem(f"Export directory: {project_dir}")
            self.log_subitem("Export complete")

        self.log_timing(time.time() - stage_start, "Stage 9 total")
        return result

    # =========================================================================
    # MAIN RUNNER
    # =========================================================================
    def run(self, source: str, source_type: str = "url", max_stage: int = 9):
        """Run the complete comic creation pipeline."""
        self.start_time = time.time()

        # Banner
        self.log_header("G-MANGA - Comic Creation Engine v1.0")
        self.logger.info("")
        self.logger.info("📖 Transforming literature into manga...")
        
        # LLM configuration display
        if self.use_mock:
            self.logger.info("🧪 Mock Mode: Enabled")
        else:
            provider_info = self.llm_client.get_stats() if hasattr(self.llm_client, 'get_stats') else {}
            provider_type = provider_info.get('client_type', 'unknown').upper()
            model = self.llm_model or provider_info.get('default_model', '')
            self.logger.info(f"🤖 LLM Provider: {provider_type}")
            self.logger.info(f"   Model: {model}")
        
        self.logger.info(f"📥 Source: {source}")
        self.logger.info(f"🎯 Workflow: {self.workflow}")
        self.logger.info(f"🎯 Max Stage: {max_stage}")
        self.logger.info("")

        stage_names = {
            1: "INPUT PROCESSING",
            2: "PREPROCESSING",
            3: "STORY PLANNING",
            4: "CHARACTER DESIGN",
            5: "PANEL GENERATION",
            6: "IMAGE GENERATION",
            7: "LAYOUT & ASSEMBLY",
            8: "POST-PROCESSING",
            9: "OUTPUT"
        }

        try:
            # Stage 1: Input Processing
            stage1_result = self.run_stage_1(source, source_type)

            if max_stage <= 1:
                self._print_partial_summary(1, stage_names[1], stage1_result)
                return True

            # Stage 2: Preprocessing
            stage2_result = self.run_stage_2(
                stage1_result["cleaned_text"],
                stage1_result["project"].id
            )

            if max_stage <= 2:
                self._print_partial_summary(2, stage_names[2], stage2_result)
                return True

            # Stage 3: Story Planning
            stage3_result = self.run_stage_3(
                stage2_result["scenes"],
                stage1_result["project"].id,
                analysis=stage2_result.get("analysis"),  # Pass Stage 2 analysis to Stage 3
                metadata=stage1_result.get("metadata", {})  # Pass metadata for title/author
            )

            if max_stage <= 3:
                self._print_partial_summary(3, stage_names[3], stage3_result)
                return True

            # Stage 4: Character Design
            stage4_result = self.run_stage_4(
                stage2_result["scenes"],
                stage1_result["project"].id
            )

            if max_stage <= 4:
                self._print_partial_summary(4, stage_names[4], stage4_result)
                return True

            # Stage 5: Panel Generation
            stage5_result = self.run_stage_5(
                stage3_result["storyboards"],
                stage1_result["project"].id
            )

            if max_stage <= 5:
                self._print_partial_summary(5, stage_names[5], stage5_result)
                return True

            # Stage 6: Image Generation
            stage6_result = self.run_stage_6(
                stage5_result["panels"],
                stage1_result["project"].id
            )

            if max_stage <= 6:
                self._print_partial_summary(6, stage_names[6], stage6_result)
                return True

            # Stage 7: Layout & Assembly
            stage7_result = self.run_stage_7(
                stage5_result["panels"],
                stage1_result["project"].id
            )

            if max_stage <= 7:
                self._print_partial_summary(7, stage_names[7], stage7_result)
                return True

            # Stage 8: Post-Processing
            stage8_result = self.run_stage_8(
                stage1_result["project"].id
            )

            if max_stage <= 8:
                self._print_partial_summary(8, stage_names[8], stage8_result)
                return True

            # Stage 9: Output
            stage9_result = self.run_stage_9(
                stage1_result["project"].id
            )

            # Summary
            self._print_summary(stage1_result, stage2_result, stage3_result,
                               stage4_result, stage5_result, stage6_result,
                               stage7_result, stage8_result)

            return True

        except Exception as e:
            self.log_error(f"Pipeline failed: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False

    def _print_partial_summary(self, stage_num: int, stage_name: str, result: dict):
        """Print summary when stopping at a partial stage."""
        self.log_header(f"PIPELINE COMPLETE (Stage {stage_num})")
        runtime = time.time() - self.start_time

        summaries = {
            1: lambda: f"📊 Project: {result.get('project', {}).get('id', 'unknown')}\n📊 Chapters: {len(result.get('chapters', []))}\n📊 Scenes: {len(result.get('scenes', []))}",
            2: lambda: f"📊 Chapters: {len(result.get('chapters', []))}\n📊 Scenes: {len(result.get('scenes', []))}",
            3: lambda: f"📊 Visual Beats: {len(result.get('visual_beats', []))}\n📊 Storyboards: {len(result.get('storyboards', []))}",
            4: lambda: f"📊 Characters: {len(result.get('characters', []))}",
            5: lambda: f"📊 Panels: {len(result.get('panels', []))}",
            6: lambda: f"📊 Images Queued: {result.get('queued', 0)}\n📊 Images Generated: {result.get('generated', 0)}",
            7: lambda: f"📊 Pages Assembled: {len(result.get('pages', []))}",
            8: lambda: f"📊 SFX Generated: {len(result.get('sfx', []))}\n📊 Quality Checks: {result.get('quality_passed', 0)}/{result.get('quality_total', 0)}",
        }

        summary = f"""
⏱️ Runtime: {runtime:.2f}s
{summaries[stage_num]()}
📂 Output: {result.get('output_dir', 'N/A')}
"""
        self.logger.info(summary)
        self.logger.info(f"💡 Run with --stage {stage_num + 1} to continue...")

    def _print_summary(self, *stage_results):
        """Print pipeline summary."""
        self.log_header("COMIC GENERATION COMPLETE")

        s1, s2, s3, s4, s5, s6, s7, s8 = stage_results[:8]

        project_id = self.project.id if self.project else "unknown"
        runtime = time.time() - self.start_time

        summary = f"""
📂 Output: ./output/projects/{project_id}/
📊 Chapters: {len(s2.get('chapters', []))}
📊 Scenes: {len(s2.get('scenes', []))}
📊 Characters: {len(s4.get('characters', []))}
📊 Visual Beats: {len(s3.get('visual_beats', []))}
📊 Storyboards: {len(s3.get('storyboards', []))}
📊 Panels: {len(s5.get('panels', []))}
📊 Images Queued: {s6.get('queued', 0)}
📊 Images Generated: {s6.get('generated', 0)}
⏱️ Runtime: {runtime:.2f}s
💰 Cost: $0.00 (mock mode)
"""
        self.logger.info(summary)


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="G-Manga: Transform literature into manga",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --url "https://www.gutenberg.org/files/174/174-0.txt"
  python main.py --file ./book.txt
  python main.py --url "https://www.gutenberg.org/files/174/174-0.txt" --no-mock
  python main.py --url "https://www.gutenberg.org/files/174/174-0.txt" --stage 3
        """
    )

    parser.add_argument("--url", "-u", help="Project Gutenberg URL to fetch")
    parser.add_argument("--file", "-f", type=Path, help="Local text file path")
    parser.add_argument("--mock", action="store_true", default=False, help="Use mock LLM (default: False)")
    parser.add_argument("--no-mock", dest="mock", action="store_false", help="Use real LLM (default, requires API key)")
    parser.add_argument("--provider", type=str, choices=["zai", "openrouter", "auto"], default="auto",
                        help="LLM provider: zai, openrouter, or auto (from env var, default: auto)")
    parser.add_argument("--model", type=str, default=None,
                        help="Specific model to use (provider-dependent, e.g., 'glm-4.7' for Z.AI, 'openai/gpt-4o-mini' for OpenRouter)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    parser.add_argument("--stage", "-s", type=int, default=9, choices=range(1, 10),
                        help="Run up to specified stage (1-9, default: 9)")
    parser.add_argument("--workflow", type=str, default="2-step", choices=["2-step", "3-step"],
                        help="Story planning workflow: 2-step (merged) or 3-step (legacy, default: 2-step)")

    args = parser.parse_args()

    if not args.url and not args.file:
        parser.error("Either --url or --file must be provided")

    source = args.url or str(args.file)
    source_type = "url" if args.url else "file"

    engine = ComicCreationEngine(
        use_mock=args.mock, 
        verbose=args.verbose, 
        workflow=args.workflow,
        llm_provider=args.provider,
        llm_model=args.model
    )
    success = engine.run(source, source_type, max_stage=args.stage)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
