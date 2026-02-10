# LLM Call Points
## G-Manga Pipeline

---

## LLM Call Points (8 Primary Stages)

### 1. Preprocessing → Scene Breakdown

**Purpose:** Identify natural scene breaks within chapters

- **Input:** Chapter text
- **Output:** Scene boundaries, summaries, locations, characters present
- **Frequency:** Once per scene (~5-20 scenes per chapter)

### 2. Story Planning → Visual Adaptation

**Purpose:** Transform prose into visual storytelling beats

- **Input:** Scene text
- **Output:** Key visual moments to depict (show vs. tell decisions)
- **Frequency:** Once per scene

### 3. Story Planning → Panel Breakdown

**Purpose:** Determine panel types, pacing, and camera angles

- **Input:** Visual adaptation beats
- **Output:** Panel count per page, panel types (establishing/medium/close-up/action)
- **Frequency:** Once per scene (covers multiple pages)

### 4. Story Planning → Storyboard Generator

**Purpose:** Generate detailed panel descriptions

- **Input:** Panel breakdown + scene text
- **Output:** Panel descriptions, mood, camera, dialogue narration
- **Frequency:** Once per panel (4-8 panels per page)

### 5. Character Design → Character Extraction

**Purpose:** Identify all characters and generate appearance descriptions

- **Input:** Full text or chapter-by-chapter
- **Output:** Character names, aliases, appearance, distinguishing features
- **Frequency:** Once per character (can batch across chapters)

### 6. Character Design → Ref Sheet Generator (Optional)

**Purpose:** Create image generation prompts for reference images

- **Input:** Character data
- **Output:** Detailed reference prompts
- **Frequency:** Once per character (optional feature)

### 7. Panel Generation → Prompt Optimizer (Optional)

**Purpose:** Improve prompt quality/variations for image generation

- **Input:** Initial panel prompts
- **Output:** Refined prompts with style tags
- **Frequency:** On demand (not always needed)

### 8. Image Generation → Retry/Fallback Manager (Conditional)

**Purpose:** Rewrite failed prompts when generation errors occur

- **Input:** Failed prompt + error reason
- **Output:** Adjusted prompt
- **Frequency:** Only on failures (5-15% of prompts typically)

---

## Summary by Stage

| Stage | LLM Calls | Total Calls (Est.) |
|-------|-----------|-------------------|
| Preprocessing | Scene breakdown | ~15-50 per book |
| Story Planning | Visual adaptation + Panel breakdown + Storyboard | ~50-200 per book |
| Character Design | Extraction + Ref sheet (optional) | ~5-20 per book |
| Panel Generation | Prompt optimizer (optional) | 0-50 per book |
| Image Generation | Retry/fallback (conditional) | ~10-30 per book |
| **Total** | | **~80-300 LLM calls per book** |

---

## Cost Optimization Opportunities

1. **Batch Scene Breakdown** — Process multiple scenes in one LLM call
2. **Batch Panel Storyboarding** — Generate multiple panels together
3. **Cache Character Extraction** — Characters identified once, reused
4. **Smaller Models** — Use cheaper models (GPT-4o-mini, Claude Haiku) for lower-stakes tasks
5. **Prompt Templates** — Panel generation can be template-based, only LLM for complex scenes

---

## Recommended Model Allocation

| Task | Recommended Model | Why |
|------|------------------|-----|
| Scene Breakdown | GPT-4o-mini | Pattern matching, lower complexity |
| Visual Adaptation | GPT-4o | Creative, requires understanding of visual storytelling |
| Panel Breakdown | GPT-4o-mini | Structured decision-making |
| Storyboard Generation | GPT-4o | Descriptive, needs nuance |
| Character Extraction | GPT-4o | One-time, high quality needed |
| Prompt Optimization | GPT-4o-mini | Iterative, cost-sensitive |

---

*Document Version: 1.0*
*Created: February 2, 2026*
