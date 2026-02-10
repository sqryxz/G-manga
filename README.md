# G-Manga

Transform Project Gutenberg literature into manga-styled comics.

## Quick Start

```bash
# Generate a comic from a Gutenberg text
g-manga generate --url "https://www.gutenberg.org/files/174/174-0.txt"

# Resume a project
g-manga resume --project-id "dorian-gray"

# Interactive mode
g-manga interactive --project-id "dorian-gray"
```

## Pipeline Overview

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

## Project Structure

```
g-manga/
├── config/           # Configuration files
├── cache/            # Cached LLM responses, prompts
├── intermediate/     # Stage outputs (storyboards, panels)
├── output/           # Final exported comics
└── projects/         # Per-project state
    └── {project-id}/
        ├── config.json
        ├── state.json
        ├── storyboard.json
        ├── characters.json
        └── pages/
```

## Key Features

- **Modular Architecture** - Each stage is independent and resumable
- **Multiple Image Providers** - DALL-E 3, SDXL, Midjourney
- **Character Consistency** - Embedding-based character tracking
- **Checkpointing** - Resume from any stage
- **Batch Parallelization** - Efficient image generation
- **Manga-First Design** - Native panel layouts, reading order, styling

## Documentation

- [FRAMEWORK.md](./FRAMEWORK.md) - Detailed pipeline specification
- [API.md](./API.md) - REST API documentation (coming soon)
- [DEV.md](./DEV.md) - Development guide (coming soon)

## Status

🚧 **Framework Design Phase**

- [x] Framework specification
- [ ] Implementation planning
- [ ] Milestone 1: Input → Story Planning
- [ ] Milestone 2: Character + Panel Generation
- [ ] Milestone 3: Image Generation
- [ ] Milestone 4: Layout & Assembly
- [ ] Milestone 5: Post-processing + Output
- [ ] Milestone 6: CLI + UI
- [ ] Milestone 7: Production hardening

---

*G-Manga v0.1 — Framework Complete*
