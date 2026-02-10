# G-Manga

Transform Project Gutenberg literature into manga-styled comics using AI.

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Or with poetry
poetry install

# Generate a comic from a Gutenberg text
python -m g_manga generate --url "https://www.gutenberg.org/files/174/174-0.txt"

# Resume a project
python -m g_manga resume --project-id "dorian-gray-20260210"

# Interactive mode
python -m g_manga interactive --project-id "dorian-gray-20260210"
```

## 📁 Project Structure

```
g-manga/
├── src/                    # Source code
│   ├── __init__.py
│   ├── config.py           # Settings management
│   ├── common/            # Shared utilities
│   │   └── mocking.py     # Mock LLM client for testing
│   ├── stage1_input/      # Fetch & parse Gutenberg texts
│   ├── stage2_preprocessing/  # Clean & segment text
│   ├── stage3_story_planning/  # Visual adaptation & panels
│   ├── stage4_character_design/  # Character consistency
│   ├── stage5_panel_generation/  # Prompt building
│   ├── stage6_image_generation/  # API calls (DALL-E/SDXL)
│   ├── stage7_layout/      # Page composition
│   ├── stage8_postprocessing/  # Speech bubbles & SFX
│   └── stage9_output/      # Export (PDF/CBZ/Images)
├── tests/                  # Test suite
├── config.yaml            # Configuration file
├── pyproject.toml         # Python project config
├── requirements.txt       # Dependencies
└── README.md
```

## ⚙️ Configuration

Edit `config.yaml` to customize:

```yaml
# LLM Models for each stage
llm:
  scene_breakdown_model: "gpt-4o"
  character_extraction_model: "gpt-4o"
  visual_adaptation_model: "gpt-4o"
  panel_breakdown_model: "gpt-4o-mini"
  storyboard_generation_model: "gpt-4o"

# Image Generation
image:
  default_provider: "dall-e-3"
  dalle_size: "1024x1024"
  dalle_quality: "hd"

# Manga Styling
manga:
  reading_direction: "left_to_right"
  color_mode: "black_and_white"
```

## 📊 Pipeline Overview

```
Gutenberg Text
    ↓
[1] Input → Fetch & Parse
    ↓
[2] Preprocessing → Clean & Segment (Chapters/Scenes)
    ↓
[3] Story Planning → Visual Adaptation & Panel Breakdown
    ↓
[4] Character Design → Consistency & References
    ↓
[5] Panel Generation → Prompt Building & Optimization
    ↓
[6] Image Generation → API Calls (DALL-E/SDXL)
    ↓
[7] Layout & Assembly → Page Composition
    ↓
[8] Post-processing → Speech Bubbles & SFX
    ↓
[9] Output → Export (PDF/CBZ/Images)
```

## 🎨 Key Features

- **Modular Architecture** - Each stage is independent and resumable
- **Multiple Image Providers** - DALL-E 3, SDXL, Midjourney (via API)
- **Character Consistency** - Embedding-based character tracking
- **Checkpointing** - Resume from any stage
- **Batch Parallelization** - Efficient image generation
- **Manga-First Design** - Native panel layouts, reading order, styling
- **Configurable LLM Models** - Set different models per stage

## 📚 Documentation

- [FRAMEWORK.md](./FRAMEWORK.md) - Detailed pipeline specification
- `src/stage*/` - Stage-specific documentation in each directory

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test
pytest tests/test_stage9_output.py -v
```

## 🛠️ Development

```bash
# Format code
black src tests

# Lint
ruff check src tests

# Type checking
mypy src
```

## 📦 Dependencies

- Python 3.10+
- Requests, Pydantic, Typer, Rich, Pillow
- OpenAI API key (for LLM and image generation)
- Optional: Stability AI API key (for SDXL)

## 📄 License

MIT

---

*G-Manga v0.1 - Complete Pipeline Implementation*
