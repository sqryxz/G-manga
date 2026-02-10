# G-Manga Task Breakdown
## Focused, Atomic Tasks for Implementation

---

## Project Structure

```
g-manga/
├── src/
│   ├── stage1_input/
│   ├── stage2_preprocessing/
│   ├── stage3_story_planning/
│   ├── stage4_character_design/
│   ├── stage5_panel_generation/
│   ├── stage6_image_generation/
│   ├── stage7_layout_assembly/
│   ├── stage8_post_processing/
│   ├── stage9_output/
│   ├── common/
│   └── api/
├── config/
├── tests/
└── scripts/
```

---

## Milestone 1: Input → Story Planning

### Stage 1: Input (Gutenberg Fetching)

#### 1.1.1 Implement URL Fetcher
- Create `url_fetcher.py` module
- Implement HTTP request with retries (max 3, exponential backoff)
- Add user-agent header for Gutenberg compatibility
- Cache downloaded content to `cache/downloads/`
- Return raw HTML/TXT content

#### 1.1.2 Implement Text Parser
- Create `text_parser.py` module
- Detect content type (HTML vs TXT)
- Extract main content from Gutenberg boilerplate (remove headers/footers)
- Preserve chapter markers and section breaks
- Return cleaned text string

#### 1.1.3 Implement Metadata Extractor
- Create `metadata_extractor.py` module
- Extract title, author from content or Gutenberg metadata
- Parse publication year from front matter
- Detect language from content
- Return metadata dict

#### 1.1.4 Create Project Schema (Pydantic)
- Create `models/project.py` with Project, Chapter, Metadata dataclasses
- Define validation rules
- Add JSON serialization/deserialization
- Create `tests/test_project_model.py`

#### 1.1.5 Implement Project Initializer
- Create `project.py` module
- Create project directory structure
- Initialize `config.json`, `state.json`
- Save project metadata
- Generate unique project ID

#### 1.1.6 Integration Test: Input Stage
- Create test script using real Gutenberg text (Dorian Gray)
- Fetch, parse, extract metadata
- Verify project initialization
- Save intermediate files
- Document expected outputs

---

### Stage 2: Preprocessing (Text Cleaning & Segmentation)

#### 2.1.1 Implement Text Cleaner
- Create `text_cleaner.py` module
- Remove Gutenberg boilerplate (regex patterns)
- Normalize Unicode characters (NFC normalization)
- Fix formatting (extra whitespace, broken paragraphs)
- Preserve chapter markers
- Return cleaned text

#### 2.1.2 Implement Chapter Segmenter
- Create `chapter_segmenter.py` module
- Regex patterns for chapter detection (Chapter X, CHAPTER ONE, etc.)
- Handle edge cases (roman numerals, spelled-out numbers)
- Fallback to LLM for ambiguous markers
- Extract chapter titles
- Return chapter list with text ranges

#### 2.1.3 Implement Scene Breakdown (LLM)
- Create `scene_breakdown.py` module
- Design LLM prompt for scene detection
- Process each chapter (batch 2-3 chapters per call for efficiency)
- Identify scene boundaries (location changes, time jumps, character entrances)
- Generate scene summaries
- Extract characters present per scene
- Return scene list

#### 2.1.4 Create Scene Schema
- Add Scene dataclass to `models/project.py`
- Define scene structure (id, summary, location, characters, text_range)
- Add validation (location not empty, characters list)

#### 2.1.5 Implement State Persistence
- Update `state.py` module
- Save chapter segmentation to `intermediate/chapters.json`
- Save scene breakdown to `intermediate/scenes.json`
- Implement load_from_checkpoint function
- Add resume capability flag

#### 2.1.6 Integration Test: Preprocessing
- Create test script using pre-fetched text
- Clean, segment chapters, breakdown scenes
- Verify scene boundaries align with text
- Check state persistence (save/load)
- Compare LLM scene breakdown with manual review for 1 chapter

---

### Stage 3: Story Planning (Visual Adaptation & Storyboarding)

#### 3.1.1 Implement Visual Adaptation (LLM)
- Create `visual_adaptation.py` module
- Design LLM prompt for visual beat extraction
- Convert prose narration to visual moments
- Decide show vs. tell for each beat
- Process each scene independently
- Return visual beats list per scene

#### 3.1.2 Implement Panel Breakdown (LLM)
- Create `panel_breakdown.py` module
- Design LLM prompt for panel planning
- Determine panel count per scene (4-8 panels typical)
- Assign panel types (establishing, wide, medium, close-up, extreme close-up)
- Plan camera angles and movement
- Calculate pacing (action = more panels, dialogue = fewer)
- Return panel breakdown per scene

#### 3.1.3 Implement Storyboard Generator (LLM)
- Create `storyboard_generator.py` module
- Design LLM prompt for panel description
- Generate detailed panel descriptions per panel
- Specify mood, lighting, camera details
- Extract dialogue and narration separately
- Batch 3-4 panels per LLM call for efficiency
- Return storyboard JSON

#### 3.1.4 Create Storyboard Schema
- Add Page, Panel, VisualBeat dataclasses to `models/storyboard.py`
- Define panel structure (id, type, description, camera, mood, dialogue, narration)
- Add validation (description not empty, camera format valid)

#### 3.1.5 Implement Page Calculator
- Create `page_calculator.py` module
- Calculate page count from panel breakdown
- Implement layout rules (4-6 panels per page typical)
- Handle special cases (splash pages, double spreads)
- Return page list with panel assignments

#### 3.1.6 Implement Storyboard Validator
- Create `storyboard_validator.py` module
- Check panel descriptions are complete
- Verify dialogue matches source text
- Validate camera angles are valid
- Check panel pacing consistency
- Return validation report with errors/warnings

#### 3.1.7 Integration Test: Story Planning
- Create test script using preprocessed scenes
- Run visual adaptation → panel breakdown → storyboard
- Validate storyboard output
- Check panel count matches expected range
- Verify dialogue is preserved accurately
- Manual review of 1 full scene storyboard

---

## Milestone 2: Character Design + Panel Generation

### Stage 4: Character Design

#### 4.1.1 Implement Character Extractor (LLM)
- Create `character_extractor.py` module
- Design LLM prompt for character identification
- Process full text or chapter-by-chapter
- Extract character names and aliases
- Generate appearance descriptions (age, hair, build, clothing)
- Identify distinguishing features
- Return character dict

#### 4.1.2 Implement Character Embedding Tracker
- Create `character_tracker.py` module
- Generate text embeddings for character mentions
- Map aliases and nicknames to canonical IDs
- Build character relationship graph
- Track character frequency across scenes
- Return character mapping

#### 4.1.3 Create Character Schema
- Add Character dataclass to `models/characters.py`
- Define character structure (id, name, aliases, appearance, reference_prompt)
- Add validation (name not empty, appearance required fields present)

#### 4.1.4 Implement Ref Sheet Generator (Optional)
- Create `ref_sheet_generator.py` module
- Design template for reference image prompts
- Generate manga-style character reference prompts
- Include style tags and consistent descriptors
- Return reference prompts per character

#### 4.1.5 Implement Character State Persistence
- Save character data to `intermediate/characters.json`
- Save embedding mappings to `cache/embeddings/`
- Add character loading to resume workflow

#### 4.1.6 Integration Test: Character Design
- Create test script using full book text
- Extract all characters
- Verify alias mapping works
- Check appearance descriptions are complete
- Generate reference sheets (optional)
- Manual review of top 5 characters

---

### Stage 5: Panel Generation (Prompt Building)

#### 5.1.1 Create Prompt Template Library
- Create `templates/prompts/` directory
- Design panel prompt templates by type (establishing, close-up, action, dialogue)
- Include manga-specific tags (screen tones, speed lines, shading)
- Add style modifiers (shonen, shojo, seinen, gekiga)
- Document template variables

#### 5.1.2 Implement Panel Analyzer
- Create `panel_analyzer.py` module
- Parse panel description for key elements
- Extract characters, location, props
- Identify action or static pose
- Determine complexity level
- Return analysis dict

#### 5.1.3 Implement Prompt Builder
- Create `prompt_builder.py` module
- Match panel to appropriate template
- Inject panel description elements
- Add character consistency prompts (from character refs)
- Include manga style tags
- Return generated prompt

#### 5.1.4 Implement Prompt Optimizer (LLM - Optional)
- Create `prompt_optimizer.py` module
- Design LLM prompt for prompt improvement
- Rewrite prompts for clarity and detail
- Add style-specific enhancements
- Run on-demand (manual trigger or low-quality threshold)
- Return optimized prompt

#### 5.1.5 Implement Prompt Validator
- Create `prompt_validator.py` module
- Check prompt length limits (for API constraints)
- Verify required elements present (character, scene, mood)
- Validate style tags are consistent
- Return validation report

#### 5.1.6 Integration Test: Panel Generation
- Create test script using storyboard panels
- Generate prompts for all panel types
- Validate prompt quality
- Compare optimized vs unoptimized prompts
- Test character consistency injection

---

## Milestone 3: Image Generation

### Stage 6: Image Generation

#### 6.1.1 Create Image Provider Interface
- Create `providers/base.py` module
- Define ImageProvider abstract base class
- Specify interface methods: `generate()`, `batch_generate()`, `validate()`
- Define ProviderConfig dataclass

#### 6.1.2 Implement DALL-E 3 Provider
- Create `providers/dalle.py` module
- Integrate OpenAI API for image generation
- Handle DALL-E 3 size/quality parameters
- Implement rate limiting and retry logic
- Return generated image bytes + metadata

#### 6.1.3 Implement SDXL Provider
- Create `providers/sdxl.py` module
- Integrate Stability AI API
- Handle SDXL-specific parameters (negative prompts, steps, CFG)
- Implement rate limiting and retry logic
- Return generated image bytes + metadata

#### 6.1.4 Implement Image Validator
- Create `image_validator.py` module
- Check for safety policy violations
- Validate image resolution
- Detect missing elements (basic OCR if needed)
- Score visual quality metrics
- Return validation result

#### 6.1.5 Implement Retry/Fallback Manager
- Create `retry_manager.py` module
- Track failed generations
- Implement exponential backoff
- Fallback to alternative providers
- Trigger prompt optimizer on repeated failures
- Return success or error with reason

#### 6.1.6 Implement Image Queue Manager
- Create `queue_manager.py` module
- Queue panel generation requests
- Implement concurrent generation (max N concurrent)
- Rate limit per provider
- Track costs per provider
- Return completed images

#### 6.1.7 Implement Image Storage
- Create `image_storage.py` module
- Save images to `output/{project_id}/panels/`
- Generate panel filenames (e.g., `p1-2.png`)
- Store metadata in `output/{project_id}/panels/metadata.json`
- Implement compression if needed

#### 6.1.8 Integration Test: Image Generation
- Create test script using generated prompts
- Generate images for 10-20 panels
- Test provider fallback (simulate failures)
- Validate image quality
- Verify storage and metadata
- Estimate costs per panel

---

## Milestone 4: Layout & Assembly

### Stage 7: Layout & Assembly

#### 7.1.1 Create Layout Template Library
- Create `templates/layouts/` directory
- Define panel grid templates (4, 5, 6, 8 panel layouts)
- Define special layouts (splash, tiered, diagonal)
- Define manga reading order (left-to-right or right-to-left)
- Document template parameters

#### 7.1.2 Implement Page Composer
- Create `page_composer.py` module
- Match panels to layout template
- Handle panel fitting (resize, crop)
- Add gutters and panel borders
- Calculate page dimensions
- Return page composition plan

#### 7.1.3 Implement Panel Arranger
- Create `panel_arranger.py` module
- Arrange panels in reading order
- Handle panel transitions (close-up to wide)
- Add visual flow guides
- Return arrangement order

#### 7.1.4 Implement Comic Assembler
- Create `comic_assembler.py` module
- Use PIL/Pillow for image composition
- Composite panels onto page canvas
- Apply page background (white/off-white)
- Add panel borders (black, 2-3px)
- Save as `output/{project_id}/pages/page_001.png`

#### 7.1.5 Implement Page Thumbnial Generator
- Create `thumbnailer.py` module
- Generate thumbnails for quick preview
- Save as `output/{project_id}/thumbnails/`
- Include in metadata

#### 7.1.6 Integration Test: Layout & Assembly
- Create test script using generated panels
- Compose pages for 3-5 pages
- Verify panel order matches reading direction
- Check borders and gutters are consistent
- Manual review of composed pages

---

## Milestone 5: Post-Processing + Output

### Stage 8: Post-Processing

#### 8.1.1 Implement Speech Bubble Renderer
- Create `speech_bubble.py` module
- Calculate bubble size based on text length
- Position bubbles optimally (avoid faces, key art)
- Support bubble types (speech, thought, whisper, shout)
- Render using PIL (rounded rectangles, tails)
- Return bubble coordinates

#### 8.1.2 Implement SFX Generator
- Create `sfx_generator.py` module
- Generate SFX text placement positions
- Style SFX with impact lines and motion blur
- Context-aware positioning (action panels)
- Return SFX coordinates

#### 8.1.3 Implement Quality Checker
- Create `quality_checker.py` module
- Generate review checklist (human-readable)
- Check for missing elements (bubbles, panels)
- Validate text readability
- Export review notes to `intermediate/review_notes.md`

#### 8.1.4 Integration Test: Post-Processing
- Create test script using composed pages
- Add speech bubbles to 5-10 panels
- Add SFX to action panels
- Verify bubble placement is appropriate
- Check quality checklist generation

---

### Stage 9: Output

#### 9.1.1 Implement PDF Exporter
- Create `exporters/pdf.py` module
- Use reportlab or fpdf for PDF generation
- Include all pages
- Add metadata (title, author)
- Save as `output/{project_id}/comic.pdf`

#### 9.1.2 Implement Image Exporter
- Create `exporters/images.py` module
- Export individual pages as PNG/JPG
- Option to export panels separately
- Save to `output/{project_id}/images/`

#### 9.1.3 Implement CBZ Exporter
- Create `exporters/cbz.py` module
- Package pages into ZIP with comic info
- Generate ComicInfo.xml metadata
- Save as `output/{project_id}/comic.cbz`

#### 9.1.4 Implement Metadata Exporter
- Create `exporters/metadata.py` module
- Export JSON manifest of all data
- Include storyboard, characters, panels
- Save as `output/{project_id}/metadata.json`

#### 9.1.5 Integration Test: Output
- Create test script using composed pages
- Export to PDF, CBZ, images
- Verify all formats are valid
- Check metadata is complete
- Test file sizes

---

## Milestone 6: CLI + Basic UI

### CLI Development

#### 11.1.1 Implement CLI Entry Point
- Create `main.py` with Typer CLI
- Define commands: `generate`, `resume`, `interactive`, `status`
- Add global options (verbose, config path)
- Implement command routing

#### 11.1.2 Implement Generate Command
- Implement `generate` subcommand
- Accept `--url` (Gutenberg URL)
- Accept `--config` (custom config)
- Accept `--output` (output directory)
- Run full pipeline end-to-end
- Display progress bar

#### 11.1.3 Implement Resume Command
- Implement `resume` subcommand
- Accept `--project-id` (resume project)
- Accept `--from-stage` (specific stage)
- Load project state
- Continue from checkpoint
- Display progress bar

#### 11.1.4 Implement Interactive Command
- Implement `interactive` subcommand
- Accept `--project-id` (load project)
- Display current state
- Allow manual stage triggers
- Allow panel regeneration
- Review and approve options

#### 11.1.5 Implement Status Command
- Implement `status` subcommand
- Accept `--project-id`
- Display project status
- Show current stage
- Show progress percentage
- Show costs accumulated

#### 11.1.6 Implement Progress Display
- Create `progress.py` module
- Use Rich for terminal progress bars
- Show stage-by-stage progress
- Display estimated time remaining
- Show current costs

---

## Milestone 7: Production Hardening

### Testing

#### 12.1.1 Write Unit Tests
- Create `tests/` directory structure
- Write unit tests for each module (80%+ coverage)
- Mock external API calls (LLM, image generation)
- Test edge cases and error conditions

#### 12.1.2 Write Integration Tests
- Create end-to-end test pipeline
- Use sample Gutenberg text (short story)
- Verify all stages execute correctly
- Validate outputs at each stage

#### 12.1.3 Write Performance Tests
- Test large books (100+ pages)
- Measure LLM token usage
- Measure image generation time
- Identify bottlenecks

---

### Error Handling

#### 12.2.1 Implement Comprehensive Error Handling
- Wrap all external API calls in try-except
- Define custom exception types
- Implement graceful degradation
- Log all errors with context

#### 12.2.2 Implement Retry Logic
- Define retry policies per API
- Exponential backoff for transient errors
- Circuit breaker for repeated failures
- User notifications for failures

#### 12.2.3 Implement Configuration Validation
- Validate config on load
- Check API keys are present
- Validate directory permissions
- Early error on invalid setup

---

### Documentation

#### 12.3.1 Write API Documentation
- Document REST API endpoints
- Provide request/response examples
- Document authentication
- Document error codes

#### 12.3.2 Write CLI Documentation
- Document all CLI commands
- Provide usage examples
- Document configuration options
- Create man pages

#### 12.3.3 Write Development Guide
- Document project structure
- Explain design decisions
- Provide contribution guidelines
- Document testing approach

---

### Deployment

#### 12.4.1 Create Installation Script
- Create `install.sh` script
- Install Python dependencies
- Set up directory structure
- Validate installation

#### 12.4.2 Create Docker Image
- Create `Dockerfile`
- Define runtime environment
- Bundle dependencies
- Test container execution

#### 12.4.3 Create CI/CD Pipeline
- Set up GitHub Actions
- Run tests on push
- Build and publish Docker images
- Automate releases

---

## Task Dependencies

```
Milestone 1:
  Stage 1 (1.1.1 → 1.1.6) → Stage 2 (2.1.1 → 2.1.6) → Stage 3 (3.1.1 → 3.1.7)

Milestone 2:
  Stage 4 (4.1.1 → 4.1.6) || Stage 5 (5.1.1 → 5.1.6)
  (Can run parallel to Milestone 1)

Milestone 3:
  Stage 6 (6.1.1 → 6.1.8)
  Depends on: Milestone 2 complete

Milestone 4:
  Stage 7 (7.1.1 → 7.1.6)
  Depends on: Milestone 3 complete

Milestone 5:
  Stage 8 (8.1.1 → 8.1.4) → Stage 9 (9.1.1 → 9.1.4)
  Depends on: Milestone 4 complete

Milestone 6:
  CLI (11.1.1 → 11.1.6)
  Can start parallel to Milestone 5

Milestone 7:
  Testing (12.1.1 → 12.1.3) → Error Handling (12.2.1 → 12.2.3) →
  Documentation (12.3.1 → 12.3.3) → Deployment (12.4.1 → 12.4.3)
  Depends on: Milestone 6 complete
```

---

## Summary

**Total Tasks:** ~90 focused, atomic tasks
**Estimated Effort:**
- Milestone 1: ~15 tasks, 3-4 weeks
- Milestone 2: ~12 tasks, 2-3 weeks (parallel with M1)
- Milestone 3: ~8 tasks, 2-3 weeks
- Milestone 4: ~6 tasks, 1-2 weeks
- Milestone 5: ~10 tasks, 2-3 weeks
- Milestone 6: ~6 tasks, 2 weeks (parallel with M5)
- Milestone 7: ~15 tasks, 3-4 weeks

**Total Time Estimate:** 15-21 weeks (3.5-5 months)

---

*Task Breakdown Version: 1.0*
*Created: February 2, 2026*
