# G-Manga Framework
## Complete Pipeline: Project Gutenberg → Finished Comic

---

## Overview

G-Manga is a modular, end-to-end pipeline that transforms public-domain literature from Project Gutenberg into manga-styled comics through AI-driven text processing, storyboarding, and image generation.

---

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        INPUT STAGE                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ URL Fetcher  │→ │ Text Parser  │→ │ Metadata     │          │
│  │ (Gutenberg)  │  │ (TXT/HTML)   │  │ Extractor    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                     PREPROCESSING STAGE                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Text Cleaner │→ │ Chapter      │→ │ Scene        │          │
│  │ (Unicode,    │  │ Segmenter   │  │ Breakdown    │          │
│  │  Formatting) │  │ (Regex/LLM)  │  │ (LLM)        │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    STORY PLANNING STAGE                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Visual       │→ │ Panel        │→ │ Storyboard   │          │
│  │ Adaptation   │  │ Breakdown    │  │ Generator    │          │
│  │ (LLM)        │  │ (Per Page)   │  │ (JSON/JSONL)  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   CHARACTER DESIGN STAGE                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Character    │→ │ Consistency  │→ │ Ref Sheet    │          │
│  │ Extraction  │  │ Manager      │  │ Generator    │          │
│  │ (LLM)        │  │ (Embeddings) │  │ (Reference)  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                  PANEL GENERATION STAGE                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Panel        │→ │ Prompt       │→ │ Prompt       │          │
│  │ Analyzer     │  │ Builder      │  │ Optimizer    │          │
│  │ (Per Panel)  │  │ (Style Tags) │  │ (Quality)    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   IMAGE GENERATION STAGE                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Image API    │→ │ Image        │→ │ Retry/       │          │
│  │ Interface    │  │ Validator    │  │ Fallback     │          │
│  │ (DALL-E,     │  │ (Safety,     │  │ Manager      │          │
│  │  SD, etc.)   │  │  Quality)    │  │              │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    LAYOUT & ASSEMBLY STAGE                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Page         │→ │ Panel        │→ │ Comic        │          │
│  │ Composer     │  │ Arranger     │  │ Assembler    │          │
│  │ (Grid System)│  │ (Manga Layout)│  │ (Page Comp)  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   POST-PROCESSING STAGE                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Speech       │→ │ SFX          │→ │ Quality      │          │
│  │ Bubble       │  │ Effects      │  │ Checker      │          │
│  │ Renderer     │  │ Generator    │  │ (Review)     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                       OUTPUT STAGE                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Export       │→ │ Chapter      │→ │ Metadata     │          │
│  │ Manager      │  │ Packager    │  │ Generator    │          │
│  │ (PDF, IMG,   │  │ (ZIP, CBZ)   │  │ (JSON, CSV)  │          │
│  │  Web)        │  │              │  │              │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Detailed Stage Breakdown

### 1. INPUT STAGE
**Purpose:** Fetch and parse source material from Project Gutenberg

**Components:**
- **URL Fetcher**
  - Accepts Gutenberg URLs or direct TXT downloads
  - Handles HTTP requests with retries
  - Caches downloaded content

- **Text Parser**
  - Extracts main content from Gutenberg headers/footers
  - Handles both plain TXT and HTML formats
  - Preserves chapter markers, scene breaks

- **Metadata Extractor**
  - Title, author, publication year
  - Language, genre tags
  - Character name extraction (first pass)

**Data Model:**
```json
{
  "id": "gutenberg-12345",
  "title": "The Picture of Dorian Gray",
  "author": "Oscar Wilde",
  "language": "en",
  "text": "Full cleaned text...",
  "metadata": {
    "year": 1890,
    "genre": ["Gothic fiction", "Philosophical fiction"]
  }
}
```

---

### 2. PREPROCESSING STAGE
**Purpose:** Clean text and segment into manageable units

**Components:**
- **Text Cleaner**
  - Removes Gutenberg boilerplate
  - Normalizes Unicode characters
  - Fixes formatting issues (extra whitespace, broken paragraphs)

- **Chapter Segmenter**
  - Regex-based chapter detection ("Chapter X", "CHAPTER ONE", etc.)
  - LLM fallback for ambiguous chapter markers
  - Outputs chapters with text ranges

- **Scene Breakdown**
  - LLM analyzes each chapter for natural scene breaks
  - Identifies location changes, time jumps, character entrances/exits
  - Generates scene summaries and key events

**Data Model:**
```json
{
  "chapters": [
    {
      "id": "chapter-1",
      "number": 1,
      "title": "The Studio",
      "scenes": [
        {
          "id": "scene-1-1",
          "start_line": 0,
          "end_line": 50,
          "summary": "Introduction of Basil and Lord Henry discussing art and beauty",
          "location": "Basil's studio",
          "characters": ["Basil Hallward", "Lord Henry Wotton"]
        }
      ]
    }
  ]
}
```

---

### 3. STORY PLANNING STAGE
**Purpose:** Convert prose to visual storytelling format

**Components:**
- **Visual Adaptation**
  - LLM transforms narrative into visual beats
  - Decides what to show vs. tell (visual prioritization)
  - Maintains narrative flow without dialogue density

- **Panel Breakdown**
  - Divides scenes into panels per page (typically 4-8)
  - Determines panel types: establishing shot, close-up, action, dialogue
  - Balances pacing (fewer panels for slow scenes, more for action)

- **Storyboard Generator**
  - Creates structured JSON storyboard
  - Includes panel descriptions, camera angles, mood
  - Stores dialogue and narration separately for text layer

**Data Model:**
```json
{
  "pages": [
    {
      "page_number": 1,
      "panels": [
        {
          "panel_id": "p1-1",
          "type": "establishing",
          "description": "Wide shot of Basil's art studio filled with paintings",
          "camera": "wide-angle, eye-level",
          "mood": "artistic, cluttered, warm light",
          "dialogue": [],
          "narration": "The studio was filled with the rich odor of roses..."
        },
        {
          "panel_id": "p1-2",
          "type": "medium",
          "description": "Basil standing before an easel, brush in hand",
          "camera": "medium shot, slight low angle",
          "mood": "intense, focused",
          "dialogue": [
            {"speaker": "Lord Henry", "text": "You have an absolutely beautiful face, Basil."}
          ],
          "narration": ""
        }
      ]
    }
  ]
}
```

---

### 4. CHARACTER DESIGN STAGE
**Purpose:** Ensure consistent character appearance across panels

**Components:**
- **Character Extraction**
  - LLM identifies all characters from text
  - Generates appearance descriptions (age, hair, clothing, distinguishing features)
  - Assigns unique character IDs

- **Consistency Manager**
  - Uses text embeddings to track character mentions
  - Maps aliases and nicknames to canonical IDs
  - Maintains character relationship graph

- **Ref Sheet Generator**
  - Creates character reference descriptions
  - Optional: Generates reference images via image API
  - Stores style guidelines per character

**Data Model:**
```json
{
  "characters": {
    "char-001": {
      "name": "Basil Hallward",
      "aliases": ["Basil", "the artist"],
      "appearance": {
        "age": "late 20s",
        "hair": "dark, neatly kept",
        "build": "lean, painter's frame",
        "clothing": "painter's smock, earth tones",
        "distinguishing": "paint-stained fingers, intense gaze"
      },
      "reference_prompt": "Basil Hallward, late 20s, dark hair, lean build, wearing paint-stained smock, in an art studio with paintings, manga style, black and white ink, clean lines"
    }
  }
}
```

---

### 5. PANEL GENERATION STAGE
**Purpose:** Convert storyboard panels into optimized image generation prompts

**Components:**
- **Panel Analyzer**
  - Analyzes each panel's visual requirements
  - Identifies needed elements (characters, location, props)
  - Determines complexity level

- **Prompt Builder**
  - Constructs detailed prompts with style tags
  - Includes manga-specific descriptors (panel borders, speed lines, shading)
  - Injects character consistency prompts

- **Prompt Optimizer**
  - Tests prompt variations
  - Balances detail vs. generation success rate
  - Applies quality enhancement tags

**Example Prompt:**
```
Manga style panel, black and white ink, clean lines, traditional comic art.
Scene: Wide establishing shot of an art studio filled with paintings and easels.
Lighting: Warm golden sunlight streaming through large windows.
Mood: Artistic, cluttered, inspiring.
Style: Shonen manga influence, detailed background, dynamic composition.
Panel frame: Black border with white gutters.
Quality: High detail, professional manga art, consistent line weight.
```

---

### 6. IMAGE GENERATION STAGE
**Purpose:** Generate panel images from prompts

**Components:**
- **Image API Interface**
  - Supports multiple providers (DALL-E 3, Stable Diffusion XL, Midjourney API)
  - Configurable backend selection
  - Request queuing and rate limiting

- **Image Validator**
  - Checks for safety policy violations
  - Validates content (text presence, missing elements)
  - Scores visual quality metrics

- **Retry/Fallback Manager**
  - Automatic retries on failures
  - Fallback to alternative providers
  - Prompt adjustment for stubborn failures

**Configuration:**
```json
{
  "image_generation": {
    "provider": "dall-e-3",
    "model": "dall-e-3",
    "size": "1024x1024",
    "quality": "hd",
    "fallback_providers": ["sdxl", "midjourney"],
    "max_retries": 3,
    "safety_filter": true
  }
}
```

---

### 7. LAYOUT & ASSEMBLY STAGE
**Purpose:** Compose panels into complete comic pages

**Components:**
- **Page Composer**
  - Applies manga page layout templates
  - Handles special panel shapes (insets, bleeds, splash pages)
  - Balances visual weight across page

- **Panel Arranger**
  - Implements manga reading order (right-to-left or left-to-right)
  - Adds gutters and panel borders
  - Handles panel transitions (close-up to wide, etc.)

- **Comic Assembler**
  - Composites images into page canvas
  - Applies page background colors/patterns
  - Generates page thumbnails

**Layout Templates:**
- 4-panel (grid, storytelling)
- 5-panel (action sequences)
- 6-panel (balanced)
- 8-panel (conversational)
- Dynamic (splash, double-spread, tiered)

---

### 8. POST-PROCESSING STAGE
**Purpose:** Add text elements and finalize pages

**Components:**
- **Speech Bubble Renderer**
  - Auto-sizes bubbles based on text length
  - Positions bubbles optimally
  - Handles different bubble types (speech, thought, whisper, shout)

- **SFX Effects Generator**
  - Adds sound effect text (POW, WHOOSH, etc.)
  - Stylized SFX with impact lines
  - Context-appropriate placement

- **Quality Checker**
  - Human-in-the-loop review checklist
  - Automated consistency checks
  - Generates revision notes

**Text Layer Model:**
```json
{
  "p1-2": {
    "bubble_1": {
      "text": "You have an absolutely beautiful face, Basil.",
      "speaker": "Lord Henry",
      "type": "speech",
      "position": {"x": 50, "y": 80},
      "size": "medium"
    }
  }
}
```

---

### 9. OUTPUT STAGE
**Purpose:** Export final comic in various formats

**Components:**
- **Export Manager**
  - PDF export (print-ready, web-optimized)
  - Image export (PNG, JPEG per page)
  - Web export (HTML/CSS/JS viewer)

- **Chapter Packager**
  - Bundles pages into CBZ (comic zip)
  - Generates table of contents
  - Creates chapter metadata

- **Metadata Generator**
  - JSON manifest with all story data
  - Character reference export
  - Generation statistics

**Output Formats:**
- Single images (PNG, JPG)
- PDF (single file, split by chapter)
- CBZ (archive format for comic readers)
- Web viewer (HTML/CSS)
- JSON/API (for programmatic access)

---

## Configuration & Settings

### Global Config (`config.yaml`)
```yaml
pipeline:
  stages:
    - input
    - preprocessing
    - story_planning
    - character_design
    - panel_generation
    - image_generation
    - layout_assembly
    - post_processing
    - output

  parallel_stages:
    - character_design  # Can run parallel to story_planning
    - image_generation  # Can run in parallel across panels

image_generation:
  provider: "dall-e-3"
  model: "dall-e-3"
  size: "1024x1024"
  quality: "hd"
  style: "manga"
  fallback_providers: ["sdxl", "midjourney"]

manga_style:
  line_weight: "medium"
  shading: "screen_tones"
  color: "black_and_white"
  reading_direction: "left_to_right"
  panel_style: "traditional_borders"

quality:
  min_resolution: 1024
  validate_characters: true
  validate_scene_continuity: true
  human_review_required: true

storage:
  cache_dir: "./cache"
  output_dir: "./output"
  intermediate_dir: "./intermediate"
  keep_intermediates: false
```

---

## API Interface

### CLI Entry Points
```bash
# Generate full comic from Gutenberg URL
g-manga generate --url "https://www.gutenberg.org/files/174/174-0.txt"

# Resume from specific stage
g-manga resume --project-id "dorian-gray" --from-stage "layout_assembly"

# Regenerate specific panels
g-manga regenerate --project-id "dorian-gray" --panels "p1-2,p1-5,p3-1"

# Interactive mode
g-manga interactive --project-id "dorian-gray"
```

### REST API
```python
POST /api/projects
{
  "source_url": "https://www.gutenberg.org/files/174/174-0.txt",
  "config": {
    "style": "shonen",
    "reading_direction": "left_to_right"
  }
}

GET /api/projects/{id}
{
  "status": "in_progress",
  "current_stage": "image_generation",
  "progress": 0.65,
  "pages_completed": 12,
  "pages_total": 24
}

GET /api/projects/{id}/pages/{page_num}
# Returns rendered page image
```

---

## State Management

### Project State
- `config.json` - Project configuration
- `state.json` - Current pipeline stage, checkpoints
- `storyboard.json` - Generated storyboard
- `characters.json` - Character references
- `panels.json` - Panel data with prompts
- `pages/` - Generated page images
- `output/` - Final export

### Checkpointing
- Each stage writes state before completion
- Resume capability from any stage
- Partial re-generation support
- Version tracking for prompts/results

---

## Error Handling & Retry Logic

### Failure Categories
1. **Transient Failures** - API timeouts, rate limits → Auto-retry
2. **Content Failures** - Safety violations, poor quality → Prompt adjustment + retry
3. **Validation Failures** - Missing elements, inconsistency → Human review flag
4. **System Failures** - Out of memory, disk full → Alert + pause

### Retry Strategy
- Exponential backoff for transient errors
- Prompt variation for content failures
- Fallback providers for API failures
- Human-in-the-loop for validation failures

---

## Performance Considerations

### Parallelization
- Panel generation: parallel across panels
- Image generation: parallel queue with rate limiting
- Page composition: sequential (depends on panels)

### Caching
- Text parsing: cache cleaned text
- LLM calls: cache scene breakdown, character analysis
- Image generation: cache successful prompts

### Cost Optimization
- Batch image generation requests
- Use smaller models for early stages (preprocessing)
- Reserve high-quality models for final image generation

---

## Future Enhancements

### Phase 2 (Post-MVP)
- Color manga generation option
- Animation/panel transitions
- Multi-page spreads
- Character aging over time
- Custom art style training (LoRA)

### Phase 3 (Advanced)
- Interactive comic viewer with animations
- Sound effects and background music
- Multi-language support (translation + generation)
- Collaborative editing features
- Community style marketplace

---

## Dependencies

### Core
- Python 3.10+
- Pydantic (data models)
- Typer (CLI)
- Rich (terminal output)

### LLM
- OpenAI API (GPT-4 for storyboarding)
- Anthropic API (Claude - alternative)

### Image Generation
- OpenAI DALL-E 3
- Stability AI SDXL
- Midjourney API (optional)

### Storage
- Local file system (default)
- S3-compatible storage (optional)

### Image Processing
- Pillow (image manipulation)
- OpenCV (advanced composition)
- Wand/ImageMagick (vector to raster)

---

## Development Roadmap

1. **Milestone 1:** Input → Preprocessing → Story Planning
2. **Milestone 2:** Character Design + Panel Generation
3. **Milestone 3:** Image Generation Integration
4. **Milestone 4:** Layout & Assembly
5. **Milestone 5:** Post-processing + Output
6. **Milestone 6:** CLI + Basic UI
7. **Milestone 7:** Production hardening + testing

---

*Framework Version: 1.0*
*Created: February 2, 2026*
