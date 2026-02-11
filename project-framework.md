# G-Manga Project Framework
## Complete Technical Guide to the Comic Creation Pipeline

---

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Stage 1: Input Processing](#stage-1-input-processing)
4. [Stage 2: Preprocessing](#stage-2-preprocessing)
5. [Stage 3: Story Planning](#stage-3-story-planning)
6. [Stage 4: Character Design](#stage-4-character-design)
7. [Stage 5: Panel Generation](#stage-5-panel-generation)
8. [Stage 6: Image Generation](#stage-6-image-generation)
9. [Stage 7: Layout & Assembly](#stage-7-layout--assembly)
10. [Stage 8: Post-Processing](#stage-8-post-processing)
11. [Stage 9: Output](#stage-9-output)
12. [Data Models](#data-models)
13. [Configuration System](#configuration-system)
14. [State Management & Checkpointing](#state-management--checkpointing)
15. [Error Handling & Retry Logic](#error-handling--retry-logic)
16. [CLI Commands](#cli-commands)

---

## Overview

G-Manga is a comprehensive pipeline that transforms Project Gutenberg literature into manga-style comics using AI. The system takes raw text input and outputs fully-formed comic pages with panels, illustrations, speech bubbles, and sound effects.

### Key Features

- **Modular 9-Stage Pipeline**: Each stage is independent and resumable
- **Multiple Image Providers**: DALL-E 3, SDXL, OpenRouter (Gemini, Flux models)
- **Character Consistency**: Embedding-based character tracking across panels
- **Manga-First Design**: Native support for right-to-left/left-to-right reading, panel layouts, and manga styling
- **Configurable LLM Models**: Different models per stage for cost/quality optimization
- **Checkpointing**: Resume from any stage without losing progress

---

## System Architecture

### Pipeline Flow

```
Gutenberg Text / Local File
    ↓
[Stage 1] Input Processing (URL Fetch, Parse, Metadata)
    ↓
[Stage 2] Preprocessing (Clean, Segment, Scene Breakdown)
    ↓
[Stage 3] Story Planning (Visual Adaptation, Panel Breakdown, Storyboard)
    ↓
[Stage 4] Character Design (Extraction, Tracking, Reference Sheets)
    ↓
[Stage 5] Panel Generation (Prompt Building, Optimization)
    ↓
[Stage 6] Image Generation (API Calls, Queue Management, Validation)
    ↓
[Stage 7] Layout & Assembly (Page Composition, Panel Arrangement)
    ↓
[Stage 8] Post-Processing (Speech Bubbles, SFX, Quality Check)
    ↓
[Stage 9] Output (Export to PDF, CBZ, Images, JSON)
```

### Directory Structure

```
G-manga/
├── src/                           # Source code
│   ├── __main__.py               # Entry point for `python -m g_manga`
│   ├── cli.py                    # Command-line interface (630 lines)
│   ├── main.py                   # Orchestrator with wizard (960 lines)
│   ├── config.py                 # Settings management (496 lines)
│   ├── models/                   # Data models (Project, Character, etc.)
│   ├── common/                   # Shared utilities (mocking, logging)
│   ├── stage1_input/             # Stage 1: Input Processing
│   │   ├── url_fetcher.py       # HTTP fetcher with caching
│   │   ├── text_parser.py       # Gutenberg text parser
│   │   ├── metadata_extractor.py # Title/author extraction
│   │   └── project.py           # Project initialization
│   ├── stage2_preprocessing/     # Stage 2: Preprocessing
│   │   ├── text_cleaner.py      # Text normalization
│   │   ├── chapter_segmenter.py # Chapter detection
│   │   ├── scene_breakdown.py   # Scene analysis via LLM
│   │   └── state.py             # State persistence
│   ├── stage3_story_planning/    # Stage 3: Story Planning
│   │   ├── visual_adaptation.py # Prose-to-visual conversion
│   │   ├── panel_breakdown.py   # Panel planning per scene
│   │   ├── storyboard_generator.py # Detailed panel descriptions
│   │   ├── storyboard_review.py # Review and validation system
│   │   ├── storyboard_storage.py # Storyboard persistence
│   │   └── page_calculator.py   # Page numbering
│   ├── stage4_character_design/  # Stage 4: Character Design
│   │   ├── character_extractor.py # Character identification
│   │   ├── character_tracker.py # Embedding-based tracking
│   │   ├── character_state.py   # Character state management
│   │   └── ref_sheet_generator.py # Reference sheet creation
│   ├── stage5_panel_generation/  # Stage 5: Panel Generation
│   │   ├── panel_builder.py     # Prompt construction
│   │   ├── panel_optimizer.py   # Prompt optimization
│   │   ├── panel_state.py       # Panel state persistence
│   │   └── panel_type_prompts.py # Panel type templates
│   ├── stage6_image_generation/  # Stage 6: Image Generation
│   │   ├── providers/           # Image provider implementations
│   │   │   ├── base.py         # Base provider interface
│   │   │   ├── factory.py      # Provider factory
│   │   │   ├── dalle.py        # DALL-E 3 provider
│   │   │   ├── sdxl.py         # Stability AI SDXL
│   │   │   └── openrouter.py   # OpenRouter (Gemini/Flux)
│   │   ├── queue_manager.py    # Batch processing queue
│   │   ├── retry_manager.py    # Retry/fallback logic
│   │   └── image_storage.py    # Image file management
│   ├── stage7_layout/            # Stage 7: Layout & Assembly
│   │   ├── panel_arranger.py   # Reading order management
│   │   ├── layout_templates.py # Layout templates (4-panel, 6-panel, etc.)
│   │   ├── page_composer.py    # Page composition
│   │   └── comic_assembler.py  # Final assembly
│   ├── stage8_postprocessing/    # Stage 8: Post-Processing
│   │   ├── speech_bubble.py    # Speech bubble rendering
│   │   ├── sfx_generator.py    # Sound effect generation
│   │   └── quality_checker.py  # Quality validation
│   └── stage9_output/            # Stage 9: Output
│       └── exporters/           # Export format handlers
├── config.yaml                   # User configuration
├── requirements.txt              # Python dependencies
├── pyproject.toml               # Project metadata
└── tests/                        # Test suite
```

---

## Stage 1: Input Processing

**Location:** `src/stage1_input/`

### Purpose
Fetch and parse source material from Project Gutenberg URLs or local files.

### Components

#### 1.1.1 URL Fetcher (`url_fetcher.py`)

Fetches content from URLs with retry logic and caching.

**Key Features:**
- HTTP requests with exponential backoff retry
- MD5-based caching system
- Gutenberg-compatible user agent
- Configurable timeout and retry limits

**Data Flow:**
```
URL Input → Check Cache → HTTP GET (with retries) → Cache Result → Return Content
```

**Code Example:**
```python
from stage1_input.url_fetcher import URLFetcher

fetcher = URLFetcher(cache_dir="./cache/downloads")
content = fetcher.fetch("https://www.gutenberg.org/files/174/174-0.txt")
# Returns: Raw text content (cached for subsequent calls)
```

**Cache Strategy:**
- Cache key: MD5 hash of URL
- Cache location: `./cache/downloads/{hash}.txt`
- Default cache enabled on all fetches

#### 1.1.2 Text Parser (`text_parser.py`)

Extracts main content from Gutenberg headers/footers.

**Processing Steps:**
1. Detect content type (TXT, HTML)
2. Remove Gutenberg license header/footer
3. Normalize line endings
4. Preserve chapter markers and scene breaks

**Input/Output:**
```
Input: Raw Gutenberg text with headers/footers
Output: Cleaned text content only
```

#### 1.1.3 Metadata Extractor (`metadata_extractor.py`)

Extracts title, author, publication year, language, genre.

**Extracted Fields:**
- `title`: Book title
- `author`: Author name
- `year`: Publication year
- `language`: ISO language code
- `gutenberg_id`: Project Gutenberg ID
- `genre`: Genre tags (from keywords)

#### 1.1.4 Project Initializer (`project.py`)

Creates project directory structure and initial state.

**Creates:**
```
projects/{project-id}/
├── config.json          # Project configuration
├── state.json          # Current pipeline state
├── storyboard.json     # Generated storyboard
├── characters.json     # Character references
├── panels.json         # Panel data
└── pages/              # Generated images
```

---

## Stage 2: Preprocessing

**Location:** `src/stage2_preprocessing/`

### Purpose
Clean text and segment into manageable units (chapters, scenes).

### Components

#### 2.1.1 Text Cleaner (`text_cleaner.py`)

Removes Gutenberg boilerplate and normalizes formatting.

**Operations:**
- Unicode normalization (NFKC)
- Remove extra whitespace
- Fix broken paragraphs
- Standardize punctuation
- Remove HTML tags if present

**Input/Output:**
```
Input:  "The Project Gutenberg EBook of...\n\nChapter I\n\nIt was a dark..."
Output: "Chapter I\n\nIt was a dark..."
```

#### 2.1.2 Chapter Segmenter (`chapter_segmenter.py`)

Detects and segments chapters using regex patterns.

**Detection Patterns:**
- "Chapter X" / "CHAPTER X"
- "Chapter One" / "CHAPTER ONE"
- Roman numerals ("Chapter I", "Chapter II")
- Custom patterns via config

**Output Data Model:**
```json
{
  "chapters": [
    {
      "id": "chapter-1",
      "number": 1,
      "title": "The Studio",
      "start_line": 45,
      "end_line": 892
    }
  ]
}
```

#### 2.1.3 Scene Breakdown (`scene_breakdown.py`)

Uses LLM to analyze chapters and identify natural scene breaks.

**LLM Prompt:**
```
Analyze this chapter text and identify natural scene breaks.
A scene break occurs when:
- Location changes
- Time jumps forward/backward
- New characters enter/exit
- Major action shifts

For each scene, provide:
- Scene summary (2-3 sentences)
- Characters present
- Location
- Time of day
- Emotional tone
```

**Output:**
```json
{
  "scenes": [
    {
      "id": "scene-1-1",
      "chapter_id": "chapter-1",
      "number": 1,
      "summary": "Basil and Lord Henry discuss art in the studio",
      "location": "Basil's art studio",
      "characters": ["Basil Hallward", "Lord Henry Wotton"],
      "time": "afternoon",
      "tone": "contemplative"
    }
  ]
}
```

#### 2.1.4 State Persistence (`state.py`)

Manages project state across stages.

**State Structure:**
```json
{
  "current_stage": "preprocessing",
  "stages_completed": ["input", "preprocessing"],
  "updated_at": "2026-02-11T12:00:00Z",
  "use_mock": true,
  "progress": {
    "preprocessing": {
      "status": "completed",
      "progress": 100
    }
  }
}
```

---

## Stage 3: Story Planning

**Location:** `src/stage3_story_planning/`

### Purpose
Convert prose narrative into visual storytelling format with detailed storyboards.

### Components

#### 3.1.1 Visual Adaptation (`visual_adaptation.py`)

Transforms narrative prose into visual beats using LLM.

**Function:**
- Identifies what to show vs. what to tell
- Creates visual summaries of narrative sections
- Maintains narrative flow in visual terms

**Process:**
```
Scene Text → LLM Analysis → Visual Beats
```

**Example:**
```
Input: "The studio was filled with the rich odour of roses..."
Output Visual Beat: "Wide shot: Art studio interior, natural light through windows,
Basil at easel, Lord Henry entering from right"
```

#### 3.1.2 Panel Breakdown (`panel_breakdown.py`)

Divides scenes into panels per page (typically 4-8 panels).

**Considerations:**
- Scene pacing (fewer panels for slow scenes)
- Dialogue density
- Action sequences (more panels)
- Panel types: establishing, medium, close-up, dialogue, action

**Output:**
```json
{
  "panel_plan": {
    "panel_count": 6,
    "panel_types": ["establishing", "medium", "dialogue", "close-up", "medium", "wide"],
    "pacing": "normal",
    "camera_plan": ["wide", "eye-level", "eye-level", "close-up", "medium", "wide"]
  }
}
```

#### 3.1.3 Storyboard Generator (`storyboard_generator.py`)

Generates detailed panel descriptions using LLM.

**Prompt Structure:**
```
SCENE CONTEXT: [Full scene text]
VISUAL BEATS: [Visual beat descriptions]
PANEL PLAN: [Panel breakdown]

Generate detailed descriptions for each panel including:
- Description (what's visible)
- Camera angle
- Mood/emotional tone
- Lighting
- Composition
- Dialogue
- Characters present
- Props/objects
```

**Output Model (`PanelDescription`):**
```python
@dataclass
class PanelDescription:
    id: str                    # "p1-1", "p1-2", etc.
    page_number: int
    panel_number: int
    type: str                  # "establishing", "medium", "close-up", "dialogue"
    description: str           # Detailed visual description
    camera: str               # "wide", "medium", "close-up", "eye-level"
    mood: str                 # Emotional tone
    lighting: str             # Lighting description
    composition: str          # "rule-of-thirds", "central", "dynamic"
    dialogue: List[Dict]      # [{"speaker": "Name", "text": "Quote"}]
    narration: str            # Narration text
    characters: List[str]     # Characters visible
    props: List[str]          # Objects/props
```

#### 3.1.4 Storyboard Review (`storyboard_review.py`)

Review and validation system for generated storyboards.

**Features:**
- Visual continuity checks
- Character consistency validation
- Pacing analysis
- Manual review interface

#### 3.1.5 Storyboard Storage (`storyboard_storage.py`)

Persistent storage for storyboard data.

**Storage Format:**
```json
{
  "id": "sb-scene-1-1",
  "scene_id": "scene-1-1",
  "scene_number": 1,
  "panels": [
    {
      "panel_id": "p1-1",
      "type": "establishing",
      "description": "Wide shot of studio...",
      ...
    }
  ],
  "created_at": "2026-02-11T12:00:00Z"
}
```

#### 3.1.6 Page Calculator (`page_calculator.py`)

Assigns panels to pages based on layout templates.

**Logic:**
- Groups panels into pages (typically 4-8 panels per page)
- Handles page breaks at scene boundaries
- Calculates total page count

---

## Stage 4: Character Design

**Location:** `src/stage4_character_design/`

### Purpose
Ensure consistent character appearance across all panels.

### Components

#### 4.1.1 Character Extractor (`character_extractor.py`)

Uses LLM to identify all characters from text with descriptions.

**Extraction:**
- Character names
- Physical appearance (age, hair, clothing)
- Distinguishing features
- Personality traits

**Output:**
```json
{
  "characters": [
    {
      "id": "char-001",
      "name": "Basil Hallward",
      "aliases": ["Basil", "the artist"],
      "appearance": {
        "age": "late 20s",
        "hair": "dark, neatly kept",
        "build": "lean, painter's frame",
        "clothing": "paint-stained smock",
        "distinguishing": "paint-stained fingers, intense gaze"
      },
      "personality": "introspective, dedicated to art"
    }
  ]
}
```

#### 4.1.2 Character Tracker (`character_tracker.py`)

Embedding-based character tracking for consistency.

**Features:**
- Text embeddings for character mentions
- Alias resolution (maps nicknames to canonical IDs)
- Character relationship graph
- Appearance consistency across scenes

**Tracking Data:**
```json
{
  "char-001": {
    "mentions": [
      {"scene": "scene-1-1", "context": "Basil stood at his easel..."},
      {"scene": "scene-1-2", "context": "The artist looked up..."}
    ],
    "embedding": [0.23, -0.15, 0.89, ...],
    "consistency_score": 0.95
  }
}
```

#### 4.1.3 Reference Sheet Generator (`ref_sheet_generator.py`)

Creates character reference descriptions for image generation.

**Generates:**
- Detailed appearance prompts
- Pose variations
- Expression guidelines
- Clothing details

**Example Reference Prompt:**
```
Basil Hallward, late 20s, dark hair, lean build, wearing paint-stained 
smock in earth tones, paint-stained fingers, intense artistic gaze, 
manga style, black and white ink, clean lines, consistent character design
```

---

## Stage 5: Panel Generation

**Location:** `src/stage5_panel_generation/`

### Purpose
Convert storyboard panels into optimized image generation prompts.

### Components

#### 5.1.1 Panel Type Prompts (`panel_type_prompts.py`)

Template library for different panel types.

**Panel Types:**
- `establishing`: Wide shots, scene setting
- `medium`: Character interactions
- `close-up`: Emotional moments
- `dialogue`: Conversation scenes
- `action`: Movement and action
- `insert`: Detail shots

**Template Structure:**
```python
PANEL_TYPE_PROMPTS = {
    "establishing": {
        "prefix": "Wide establishing shot,",
        "style_tags": ["detailed background", "environment focus"],
        "camera": "wide-angle"
    },
    "close-up": {
        "prefix": "Close-up portrait,",
        "style_tags": ["emotional expression", "facial detail"],
        "camera": "close-up"
    }
}
```

#### 5.1.2 Panel Builder (`panel_builder.py`)

Constructs detailed prompts from storyboard data.

**Build Process:**
```python
def build_panel_prompt(
    scene_id: str,
    scene_number: int,
    visual_beat: Dict,
    storyboard_data: Dict
) -> PanelTemplate:
    # 1. Get base template for panel type
    # 2. Inject character consistency prompts
    # 3. Add style tags (manga, B&W, etc.)
    # 4. Include lighting and mood descriptors
    # 5. Add negative prompts
```

**Example Output Prompt:**
```
Manga style panel, black and white ink, clean lines, traditional comic art.
Wide establishing shot of an art studio filled with paintings and easels.
Basil Hallward (late 20s, dark hair, paint-stained smock) stands at easel.
Lord Henry Wotton (middle-aged, aristocratic, elegant suit) enters from right.
Warm golden sunlight streaming through large windows.
Detailed background with paintings on walls.
Professional manga art, high detail, consistent character design.
```

#### 5.1.3 Panel Optimizer (`panel_optimizer.py`)

Optimizes prompts for consistency and quality.

**Optimization Techniques:**
- Token limit management (max 1000 tokens for DALL-E)
- Priority ranking (characters > setting > props)
- Consistency injection across sequential panels
- Style coherence enforcement

**Optimization Process:**
```python
def optimize_prompt(
    prompt: str,
    panel_type: str,
    characters_in_panel: List[str],
    previous_panels: List[PanelTemplate]
) -> str:
    # 1. Ensure character consistency
    # 2. Manage token count
    # 3. Add quality enhancement tags
    # 4. Remove redundant descriptors
```

#### 5.1.4 Panel State Manager (`panel_state.py`)

Manages panel data persistence and retrieval.

**Stored Data:**
```json
{
  "panel_id": "p1-1",
  "scene_id": "scene-1-1",
  "panel_number": 1,
  "panel_type": "establishing",
  "description": "Wide shot of studio...",
  "panel_prompt": "Manga style panel...",
  "optimized_prompt": "Optimized version...",
  "image_path": "pages/p1-1.png",
  "status": "generated",
  "consistency_score": 0.94
}
```

---

## Stage 6: Image Generation

**Location:** `src/stage6_image_generation/`

### Purpose
Generate panel images from prompts using AI image APIs.

### Supported Providers

#### 6.1.1 DALL-E 3 (`providers/dalle.py`)

OpenAI's DALL-E 3 integration.

**Configuration:**
```yaml
image:
  dalle:
    model: "dall-e-3"
    size: "1024x1024"  # Options: 1024x1024, 1792x1024, 1024x1792
    quality: "hd"      # Options: standard, hd
    style: "vivid"     # Options: vivid, natural
    cost_per_image: 0.04
```

**Features:**
- High-quality image generation
- Built-in content filtering
- Standardized aspect ratios

#### 6.1.2 SDXL (`providers/sdxl.py`)

Stability AI's Stable Diffusion XL.

**Configuration:**
```yaml
image:
  sdxl:
    model: "stable-diffusion-xl-1024-v1-0"
    size: "1024x1024"
    steps: 30
    cfg_scale: 7.5
    cost_per_image: 0.04
```

**Features:**
- More control via steps/CFG parameters
- Lower cost per image
- Style flexibility

#### 6.1.3 OpenRouter (`providers/openrouter.py`)

Multi-model provider supporting Gemini, Flux, and SDXL.

**Configuration:**
```yaml
image:
  openrouter:
    default_model: "google/gemini-2.5-flash-image"
    available_models:
      - "google/gemini-2.5-flash-image"
      - "black-forest-labs/flux.2-klein-4b"
      - "black-forest-labs/flux.2-pro"
      - "stabilityai/stable-diffusion-xl-base-1.0"
    cost_per_image: 0.02
```

**Features:**
- Multiple model options
- Cost-effective (Gemini ~$0.02/image)
- Fallback between models

#### 6.1.4 Provider Factory (`providers/factory.py`)

Factory pattern for provider instantiation.

```python
from stage6_image_generation.providers.factory import ImageProviderFactory

provider = ImageProviderFactory.create_provider(
    provider_type="openrouter",
    config={
        "api_key": "your-api-key",
        "default_model": "google/gemini-2.5-flash-image"
    }
)
```

### Components

#### 6.1.5 Image Queue Manager (`queue_manager.py`)

Manages batch processing of image generation requests.

**Features:**
- Queue with priority levels
- Parallel processing with rate limiting
- Progress tracking
- Failed request retry queue

**Queue Status:**
```json
{
  "queue_size": 50,
  "pending": 20,
  "in_progress": 5,
  "completed": 25,
  "failed": 0
}
```

#### 6.1.6 Retry Manager (`retry_manager.py`)

Handles retries and fallback between providers.

**Retry Strategies:**
- `EXPONENTIAL_BACKOFF`: Double delay each retry
- `LINEAR_BACKOFF`: Fixed delay increment
- `IMMEDIATE`: No delay

**Fallback Strategies:**
- `NEXT_PROVIDER`: Try next configured provider
- `SAME_PROVIDER`: Retry same provider
- `ABORT`: Stop on failure

**Configuration:**
```python
retry_config = RetryConfig(
    max_retries=3,
    backoff_factor=2.0,
    initial_delay=1.0
)
```

#### 6.1.7 Image Storage (`image_storage.py`)

Manages generated image files.

**Storage Structure:**
```
projects/{project-id}/
├── pages/
│   ├── p1-1.png
│   ├── p1-2.png
│   └── ...
└── images/
    ├── characters/
    └── refs/
```

---

## Stage 7: Layout & Assembly

**Location:** `src/stage7_layout/`

### Purpose
Compose panels into complete comic pages with proper manga layout.

### Components

#### 7.1.1 Panel Arranger (`panel_arranger.py`)

Manages reading order and panel sequencing.

**Reading Directions:**
- `left_to_right`: Western comics (default)
- `right_to_left`: Japanese manga style

**Arrangement Logic:**
```python
arrangement = arranger.arrange_panels(
    panels=panel_images,
    panel_types=panel_type_map,
    reading_direction="right_to_left"
)
```

#### 7.1.2 Layout Templates (`layout_templates.py`)

Pre-defined page layout templates.

**Available Templates:**
- `4-panel-grid`: Classic 2x2 grid
- `5-panel-action`: Dynamic action layout
- `6-panel-balanced`: Standard 3x2 grid
- `8-panel-conversational`: 4x2 for dialogue-heavy pages
- `dynamic`: Custom layouts with insets and bleeds

**Template Structure:**
```json
{
  "name": "4-panel-grid",
  "panels": [
    {"x": 0, "y": 0, "width": 0.5, "height": 0.5},
    {"x": 0.5, "y": 0, "width": 0.5, "height": 0.5},
    {"x": 0, "y": 0.5, "width": 0.5, "height": 0.5},
    {"x": 0.5, "y": 0.5, "width": 0.5, "height": 0.5}
  ],
  "gutters": {"horizontal": 0.02, "vertical": 0.02}
}
```

#### 7.1.3 Page Composer (`page_composer.py`)

Composites panels into a complete page.

**Process:**
1. Select layout template
2. Resize panels to fit layout
3. Add gutters between panels
4. Add panel borders
5. Composite onto page canvas
6. Apply background if needed

**Output:**
- Page image (PNG/JPEG)
- Page metadata JSON

#### 7.1.4 Comic Assembler (`comic_assembler.py`)

Final assembly of all pages into a complete comic.

**Functions:**
- Sequential page assembly
- Chapter breaks
- Table of contents generation
- Page numbering

---

## Stage 8: Post-Processing

**Location:** `src/stage8_postprocessing/`

### Purpose
Add text elements (speech bubbles, SFX) and final quality checks.

### Components

#### 8.1.1 Speech Bubble Renderer (`speech_bubble.py`)

Renders dialogue and narration text in manga-style speech bubbles.

**Bubble Types:**
- `speech`: Standard oval bubble
- `thought`: Cloud-shaped bubble
- `whisper`: Dotted line border
- `shout`: Spiky border
- `narration`: Rectangular box

**Features:**
- Auto-sizing based on text length
- Optimal positioning to avoid covering important elements
- Text wrapping and font selection
- Tail direction based on speaker position

**Rendering:**
```python
bubble_renderer.render_bubble(
    text="That's a remarkable piece of work.",
    speaker="Lord Henry",
    bubble_type="speech",
    position=(x, y),
    panel_image=panel_img
)
```

#### 8.1.2 SFX Generator (`sfx_generator.py`)

Generates sound effect text (onomatopoeia) with stylized rendering.

**SFX Types:**
- `impact`: POW, BAM, CRASH
- `movement`: WHOOSH, SWOOSH
- `ambient`: TICK-TOCK, DRIP
- `emotional`: GASP, SIGH

**Styling:**
- Impact lines
- Dynamic fonts
- Rotation and scaling
- Context-aware placement

#### 8.1.3 Quality Checker (`quality_checker.py`)

Validates final pages for quality issues.

**Checks:**
- Text legibility (contrast, size)
- Image resolution
- Panel border consistency
- Character consistency across pages
- Missing elements

**Output:**
```json
{
  "passed": true,
  "issues": [],
  "warnings": [
    {
      "page": 5,
      "panel": "p5-2",
      "type": "text_size",
      "message": "Text may be too small for readability"
    }
  ]
}
```

---

## Stage 9: Output

**Location:** `src/stage9_output/`

### Purpose
Export the final comic in various formats.

### Export Formats

#### 9.1.1 PDF Export

Print-ready PDF with proper page sizing.

**Features:**
- Single-page or double-page spread
- Chapter breaks
- Table of contents
- Page numbers
- Metadata embedding

#### 9.1.2 CBZ Export

Comic Book Archive format (ZIP with images).

**Structure:**
```
comic.cbz
├── 001.png
├── 002.png
├── ...
└── ComicInfo.xml
```

#### 9.1.3 Image Export

Individual page images (PNG/JPEG).

#### 9.1.4 JSON Export

Complete project data export.

**Includes:**
- All storyboard data
- Character references
- Generation statistics
- Metadata

#### 9.1.5 Metadata Exporter (`exporters/metadata.py`)

Exports project metadata in various formats.

**Formats:**
- JSON (structured data)
- CSV (spreadsheet)
- XML (metadata standard)

---

## Data Models

### Project Model (`src/models/project.py`)

```python
class Project:
    id: str                    # Unique project ID
    name: str                  # Project name
    directory: str             # Project directory path
    metadata: Metadata         # Book metadata
    created_at: datetime
    updated_at: datetime
    raw_text: str             # Original downloaded text
    cleaned_text: str         # Cleaned text
    chapters: List[Chapter]   # Chapter data
    scenes: List[Scene]       # Scene data

class Metadata:
    title: str
    author: str
    year: Optional[int]
    language: str
    gutenberg_id: Optional[str]
    genre: List[str]
    source_url: str

class Chapter:
    id: str
    number: int
    title: Optional[str]
    text_range: TextRange
    scenes: List[Scene]

class Scene:
    id: str
    chapter_id: str
    number: int
    summary: str
    characters: List[str]
    location: str
    time: str
    tone: str
```

### Character Model

```python
class Character:
    id: str
    name: str
    aliases: List[str]
    appearance: CharacterAppearance
    personality: str
    reference_prompt: str

class CharacterAppearance:
    age: str
    hair: str
    build: str
    clothing: str
    distinguishing: str
```

---

## Configuration System

### Main Config (`config.yaml`)

```yaml
# LLM Configuration
llm:
  provider: "openrouter"  # or "openai"
  api_key: ""  # Set via OPENROUTER_API_KEY env var
  
  # Stage-specific models
  scene_breakdown_model: "openai/gpt-4o"
  character_extraction_model: "openai/gpt-4o"
  visual_adaptation_model: "anthropic/claude-sonnet-4-20250514"
  panel_breakdown_model: "openai/gpt-4o-mini"
  storyboard_generation_model: "openai/gpt-4o"
  
  # Fallback chain
  fallback_models:
    - "openai/gpt-4o"
    - "anthropic/claude-sonnet-4-20250514"
    - "google/gemini-2.5-pro"

# Image Generation Configuration
image:
  default_provider: "openrouter"  # dall-e-3, sdxl, openrouter
  
  dalle:
    enabled: true
    model: "dall-e-3"
    size: "1024x1024"
    quality: "hd"
    style: "vivid"
    cost_per_image: 0.04
  
  sdxl:
    enabled: true
    model: "stable-diffusion-xl-1024-v1-0"
    size: "1024x1024"
    steps: 30
    cfg_scale: 7.5
    cost_per_image: 0.04
  
  openrouter:
    enabled: true
    default_model: "google/gemini-2.5-flash-image"
    cost_per_image: 0.02

# Manga Styling
manga:
  reading_direction: "left_to_right"  # or "right_to_left"
  color_mode: "black_and_white"       # or "grayscale", "color"
  line_weight: "medium"
  shading_style: "screen_tones"
  panel_style: "traditional_borders"

# Storage
storage:
  projects_dir: "./projects"
  output_dir: "./output"
  cache_dir: "./cache"
  keep_intermediates: false

# Global Settings
debug_mode: false
log_level: "INFO"
```

### Settings Management (`src/config.py`)

```python
from config import get_settings

settings = get_settings()

# Get LLM model for a stage
model = settings.get_llm_model("scene_breakdown")
# Returns: "openai/gpt-4o"

# Get image provider
provider = settings.get_image_provider()
# Returns: "openrouter"

# Access nested settings
manga_style = settings.manga.reading_direction
```

---

## State Management & Checkpointing

### State Persistence

Each stage writes state before completion, enabling resume capability.

**State File (`state.json`):**
```json
{
  "current_stage": "story_planning",
  "stages_completed": ["input", "preprocessing"],
  "updated_at": "2026-02-11T12:00:00Z",
  "use_mock": true,
  "progress": {
    "input": {"status": "completed", "progress": 100},
    "preprocessing": {"status": "completed", "progress": 100},
    "story_planning": {"status": "in_progress", "progress": 45}
  }
}
```

### Resume Flow

```bash
# Resume from current stage
g-manga resume dorian-gray-20260210

# Resume from specific stage
g-manga resume dorian-gray-20260210 --from preprocessing

# Continue full pipeline
g-manga resume dorian-gray-20260210 --all
```

### Checkpoint Files

- `config.json`: Project configuration
- `state.json`: Current pipeline state
- `chapters.json`: Segmented chapter data
- `scenes.json`: Scene breakdown data
- `storyboard.json`: Generated storyboard
- `characters.json`: Character references
- `panels.json`: Panel data with prompts
- `images/queue.json`: Image generation queue

---

## Error Handling & Retry Logic

### Error Categories

1. **Transient Failures**
   - API timeouts
   - Rate limits
   - Network issues
   - **Action**: Exponential backoff retry

2. **Content Failures**
   - Safety policy violations
   - Poor quality output
   - Missing elements
   - **Action**: Prompt adjustment + retry

3. **Validation Failures**
   - Inconsistency detected
   - Missing characters
   - Quality threshold not met
   - **Action**: Human review flag

4. **System Failures**
   - Out of memory
   - Disk full
   - **Action**: Alert + pause

### Retry Configuration

```python
from stage6_image_generation.retry_manager import RetryConfig

retry_config = RetryConfig(
    max_retries=3,
    backoff_factor=2.0,
    initial_delay=1.0,
    max_delay=30.0
)
```

### Fallback Chain

```python
providers = [
    ImageProviderFactory.create_provider("openrouter"),
    ImageProviderFactory.create_provider("dalle"),
    ImageProviderFactory.create_provider("sdxl")
]

retry_mgr = RetryFallbackManager(
    providers=providers,
    fallback_strategy=FallbackStrategy.NEXT_PROVIDER
)
```

---

## CLI Commands

### Basic Commands

```bash
# Generate new comic from URL
python -m g_manga generate --url "https://www.gutenberg.org/files/174/174-0.txt"

# Generate with all stages
python main.py --url "https://www.gutenberg.org/files/174/174-0.txt"

# Generate from local file
python main.py --file ./book.txt

# Resume existing project
g-manga resume dorian-gray-20260210

# Check project status
g-manga status dorian-gray-20260210

# List all projects
g-manga list

# Export completed project
g-manga export dorian-gray-20260210 --format pdf

# Show system info
g-manga info
```

### CLI Options

```bash
# Stage 1 only (for testing)
g-manga generate --url "..." --mock

# Full pipeline with real LLM/Images
python main.py --url "..." --no-mock

# Verbose logging
python main.py --url "..." --verbose
```

---

## Cost Estimation

### Per-Stage Costs (Approximate)

| Stage | Operation | Cost Range |
|-------|-----------|------------|
| 1 | URL Fetch + Parse | Free (CPU only) |
| 2 | Text Cleaning + Segmentation | Free (CPU only) |
| 2 | Scene Breakdown (LLM) | $0.01-0.05/chapter |
| 3 | Visual Adaptation | $0.02-0.10/scene |
| 3 | Storyboard Generation | $0.05-0.20/scene |
| 4 | Character Extraction | $0.02-0.05/chapter |
| 5 | Prompt Building | Free (CPU only) |
| 6 | Image Generation (DALL-E 3) | $0.04/image |
| 6 | Image Generation (Gemini) | $0.02/image |
| 6 | Image Generation (SDXL) | $0.04/image |
| 7-9 | Layout + Post-processing | Free (CPU only) |

### Example Comic (20 pages, 80 panels)

| Component | Count | Unit Cost | Total |
|-----------|-------|-----------|-------|
| Scene Breakdown | 20 scenes | $0.03 | $0.60 |
| Storyboard Generation | 20 scenes | $0.10 | $2.00 |
| Character Extraction | 10 chapters | $0.03 | $0.30 |
| Image Generation (Gemini) | 80 images | $0.02 | $1.60 |
| **Total** | | | **~$4.50** |

---

## Performance Considerations

### Parallelization

- **Stage 6 (Image Generation)**: Parallel across panels with rate limiting
- **Stage 2-5**: Sequential (text analysis depends on previous results)
- **Stage 7**: Sequential (page composition depends on all panels)

### Caching Strategy

1. **URL Fetch**: Cache downloaded text by URL hash
2. **LLM Calls**: Cache scene breakdown, character analysis
3. **Image Generation**: Cache successful prompts and results

### Optimization Tips

1. Use `--mock` flag for development/testing
2. Process shorter chapters first for testing
3. Use Gemini via OpenRouter for cost-effective image generation
4. Enable caching to avoid redundant API calls
5. Batch process chapters for better throughput

---

## Development Guidelines

### Adding a New Stage

1. Create directory: `src/stageN_name/`
2. Implement stage modules
3. Add to `main.py` orchestrator
4. Update state management
5. Add tests in `tests/test_stageN_*.py`

### Adding a New Image Provider

1. Create provider class in `src/stage6_image_generation/providers/`
2. Inherit from `ImageProvider` base class
3. Implement `generate()` method
4. Register in `providers/factory.py`
5. Add configuration in `config.yaml`

### Testing

```bash
# Run all tests
pytest

# Run specific stage tests
pytest tests/test_stage6_integration.py -v

# Run with coverage
pytest --cov=src --cov-report=html
```

---

## Troubleshooting

### Common Issues

**Issue**: "No module named 'g_manga'"
**Solution**: Run from project root or install: `pip install -e .`

**Issue**: API rate limit errors
**Solution**: Increase retry delay or reduce parallel requests in config

**Issue**: Images not generating
**Solution**: Check API key configuration, verify provider enabled in config

**Issue**: Characters inconsistent across panels
**Solution**: Ensure character reference sheets are generated and used

### Debug Mode

Enable debug logging:
```yaml
debug_mode: true
log_level: "DEBUG"
```

Or via CLI:
```bash
python main.py --url "..." --verbose
```

---

## License

MIT License - See LICENSE file for details.

---

*G-Manga Framework v1.0*
*Last Updated: February 2026*
