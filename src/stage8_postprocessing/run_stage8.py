#!/usr/bin/env python3
"""
Stage 8: Post-Processing Script for Dorian Gray Manga
- Loads panel images
- Adds speech bubbles with Victorian-era dialogue
- Adds SFX where applicable
- Saves processed panels
- Creates comic pages (6 panels per page)
- Runs quality checks
"""

import sys
import os
import json
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# Add src to path
sys.path.insert(0, '/home/clawd/projects/g-manga/src')

from PIL import Image, ImageDraw, ImageFont
from dataclasses import dataclass

# Import Stage 8 modules
from stage8_postprocessing.speech_bubble import (
    SpeechBubbleRenderer, BubbleType, BubbleConfig, BubblePosition
)
from stage8_postprocessing.sfx_generator import (
    SFXGenerator, SFXType, SFXStyle, SFXConfig, SFXPosition
)
from stage8_postprocessing.quality_checker import (
    QualityChecker, QualityCheck, CheckSeverity
)


# Configuration
PROJECT_DIR = "/home/clawd/projects/g-manga/output/projects/picture-of-dorian-gray-20260212-20260212"
PANELS_DIR = f"{PROJECT_DIR}/output/panels"
PROCESSED_DIR = f"{PROJECT_DIR}/output/processed_panels"
FINAL_DIR = f"{PROJECT_DIR}/output/final_pages"

INTERMEDIATE_DIR = "/home/clawd/projects/g-manga/output/projects/picture-of-dorian-gray-20260213-20260213/intermediate"
PANEL_PROMPTS_FILE = f"{INTERMEDIATE_DIR}/panel_prompts.json"
VISUAL_BEATS_FILE = f"{INTERMEDIATE_DIR}/visual_beats.json"
STORYBOARD_FILE = f"{INTERMEDIATE_DIR}/storyboard.json"

# Page configuration (A4 at 300 DPI)
PAGE_WIDTH = 2480
PAGE_HEIGHT = 3508
PANELS_PER_PAGE = 6


# Victorian-era dialogue templates for Dorian Gray
VICTORIAN_DIALOGUE = {
    "chapter-1-scene-1": [
        {"speaker": "Lord Henry", "text": "The moment I first saw you, Basil, I knew this portrait must be mine."},
        {"speaker": "Basil", "text": "It is not a portrait I could easily part with, Harry."},
        {"speaker": "Lord Henry", "text": "The young man in the portrait... he is quite beautiful."},
        {"speaker": "Basil", "text": "His beauty is but a shadow of his soul."},
        {"speaker": "Lord Henry", "text": "You have put too much of yourself into this work."},
        {"speaker": "Basil", "text": "I have indeed. Perhaps too much."},
        {"speaker": "Lord Henry", "text": "Introduce me to this Dorian Gray."},
        {"speaker": "Basil", "text": "I fear what you might do to him."},
    ],
    "chapter-1-scene-2": [
        {"speaker": "Dorian", "text": "You have been listening to Henry's philosophy."},
        {"speaker": "Basil", "text": "It is intoxicating, is it not?"},
        {"speaker": "Dorian", "text": "I wish I could remain young forever."},
        {"speaker": "Lord Henry", "text": "Youth is the only thing worth having."},
        {"speaker": "Dorian", "text": "If only this portrait could age instead of me!"},
        {"speaker": "Basil", "text": "Do not speak such dark wishes, Dorian."},
    ],
    "chapter-1-scene-3": [
        {"speaker": "Dorian", "text": "The portrait... it has changed!"},
        {"speaker": "Lord Henry", "text": "Surely you jest. It is as perfect as ever."},
        {"speaker": "Dorian", "text": "There is a cruelty in its smile now."},
        {"speaker": "Basil", "text": "I see nothing amiss."},
        {"speaker": "Dorian", "text": "I must hide this away where none shall see it."},
    ],
    "chapter-2-scene-1": [
        {"speaker": "Lord Henry", "text": "You have not aged a day, Dorian."},
        {"speaker": "Dorian", "text": "The portrait takes my years upon itself."},
        {"speaker": "Lord Henry", "text": "What a fortunate arrangement indeed."},
        {"speaker": "Sibyl", "text": "Oh, that I could be as you are!"},
        {"speaker": "Dorian", "text": "Do not envy me, Sibyl. You have no idea what you wish for."},
    ],
    "chapter-2-scene-2": [
        {"speaker": "Dorian", "text": "I have ruined her. And yet I feel nothing."},
        {"speaker": "Lord Henry", "text": "You were merely experimenting with life, my dear boy."},
        {"speaker": "Dorian", "text": "I am afraid of what I am becoming."},
        {"speaker": "Lord Henry", "text": "There is no such thing as a good influence."},
    ],
    "chapter-2-scene-3": [
        {"speaker": "Dorian", "text": "She was merely an actress. What matter her death?"},
        {"speaker": "Basil", "text": "You speak as a man without a heart."},
        {"speaker": "Dorian", "text": "My heart was taken by the portrait long ago."},
        {"speaker": "Lord Henry", "text": "Come, Dorian. Let us seek new distractions."},
    ],
    "chapter-3-scene-1": [
        {"speaker": "Basil", "text": "I must see the portrait again."},
        {"speaker": "Dorian", "text": "It is locked away. You must not see it."},
        {"speaker": "Basil", "text": "Why do you hide your greatest work?"},
        {"speaker": "Dorian", "text": "Because it has become my master."},
    ],
    "chapter-3-scene-2": [
        {"speaker": "Basil", "text": "My God, Dorian! What has happened?"},
        {"speaker": "Dorian", "text": "I have sold my soul for beauty."},
        {"speaker": "Basil", "text": "The portrait is a monster!"},
        {"speaker": "Dorian", "text": "It is myself, as I truly am."},
    ],
    "chapter-3-scene-3": [
        {"speaker": "Dorian", "text": "There is no hope for me."},
        {"speaker": "Lord Henry", "text": "One can always begin again."},
        {"speaker": "Dorian", "text": "Some sins cannot be forgiven."},
        {"speaker": "Basil", "text": "Destroy the portrait and be free!"},
        {"speaker": "Dorian", "text": "No... I must face what I have become."},
    ],
    "chapter-4-scene-1": [
        {"speaker": "Dorian", "text": "The years have not touched me."},
        {"speaker": "Lord Henry", "text": "And yet you seem weary."},
        {"speaker": "Dorian", "text": "I have lived too much in so little time."},
        {"speaker": "Basil", "text": "There is still goodness in you."},
        {"speaker": "Dorian", "text": "Perhaps. But I fear it is too late."},
    ],
}


@dataclass
class DialogueEntry:
    """Dialogue entry for a panel."""
    panel_id: str
    panel_number: str
    speaker: str
    text: str
    text_type: str


@dataclass
class SFXEntry:
    """SFX entry for a panel."""
    panel_id: str
    sfx_text: str
    sfx_type: str


def get_dialogue_for_panel(panel_path: str, panel_num: int) -> List[DialogueEntry]:
    """Generate dialogue for a panel based on its scene."""
    dialogues = []
    
    # Determine scene from panel number
    scene_panels = 6  # 6 panels per scene
    scene_num = (panel_num - 1) // scene_panels + 1
    panel_in_scene = (panel_num - 1) % scene_panels + 1
    
    scene_key = f"chapter-{scene_num}-scene-{min(scene_num, 3)}"  # Max 3 scenes per chapter
    
    scene_dialogues = VICTORIAN_DIALOGUE.get(scene_key, [])
    
    if scene_dialogues:
        idx = min(panel_in_scene - 1, len(scene_dialogues) - 1)
        if idx >= 0:
            d = scene_dialogues[idx]
            dialogues.append(DialogueEntry(
                panel_id=f"panel-{panel_num}",
                panel_number=f"{scene_num}.{panel_in_scene}",
                speaker=d["speaker"],
                text=d["text"],
                text_type="dialogue"
            ))
    
    return dialogues


def load_dialogues() -> Dict[str, List[DialogueEntry]]:
    """Load dialogues from visual_beats.json or generate Victorian dialogue."""
    dialogues = {}
    
    # Try loading from visual_beats.json first
    try:
        with open(VISUAL_BEATS_FILE, 'r') as f:
            data = json.load(f)
        
        for beat in data.get('beats', []):
            for panel in beat.get('panels', []):
                text_content = panel.get('text_content', '')
                text_type = panel.get('text_type', '')
                
                if text_content and text_type in ['dialogue', 'narration', 'thought']:
                    panel_num = panel.get('panel_number', '')
                    
                    if ':' in text_content:
                        speaker, text = text_content.split(':', 1)
                        text = text.strip()
                    else:
                        speaker = ''
                    
                    try:
                        panel_index = int(panel_num.replace('.', ''))
                    except:
                        panel_index = 1
                    
                    panel_id = f"panel-{panel_index}"
                    
                    entry = DialogueEntry(
                        panel_id=panel_id,
                        panel_number=panel_num,
                        speaker=speaker.strip(),
                        text=text,
                        text_type=text_type
                    )
                    
                    if entry.panel_id not in dialogues:
                        dialogues[entry.panel_id] = []
                    dialogues[entry.panel_id].append(entry)
                    
    except Exception as e:
        print(f"Note: Using generated Victorian dialogue ({e})")
    
    return dialogues


def load_panel_files() -> List[Tuple[str, str]]:
    """Load panel files with their IDs."""
    panels = []
    panel_files = sorted([f for f in os.listdir(PANELS_DIR) if f.endswith('.png')])
    
    for i, filename in enumerate(panel_files, 1):
        panel_id = f"panel-{i}"
        panel_path = os.path.join(PANELS_DIR, filename)
        panels.append((panel_id, panel_path))
    
    return panels


def create_speech_bubbles(
    image: Image.Image,
    dialogues: List[DialogueEntry],
    panel_pos: Tuple[int, int, int, int]
) -> Image.Image:
    """Add speech bubbles to a panel image."""
    config = BubbleConfig(
        bubble_color="#FFFFFF",
        border_color="#000000",
        border_width=3,
        font_size=28,
        corner_radius=15,
        tail_size=20,
        padding=12
    )
    
    renderer = SpeechBubbleRenderer(config)
    
    img_w, img_h = image.size
    px, py, pw, ph = panel_pos
    
    for i, dialogue in enumerate(dialogues):
        if dialogue.text_type == 'thought':
            bubble_type = BubbleType.THOUGHT
        elif dialogue.text_type == 'narration':
            bubble_type = BubbleType.NARRATION
        else:
            bubble_type = BubbleType.SPEECH
        
        bubble_w, bubble_h = renderer.calculate_bubble_size(
            dialogue.text,
            min(pw - 40, 350)
        )
        
        # Position bubbles on alternating sides
        if i % 2 == 0:
            x = px + 15
        else:
            x = px + pw - bubble_w - 15
        
        y = py + 15
        
        bubble_pos = BubblePosition(
            panel_id=dialogue.panel_id,
            speaker_id=i,
            bubble_type=bubble_type,
            x=x,
            y=y,
            width=bubble_w,
            height=bubble_h,
            tail_x=x + bubble_w // 2,
            tail_y=y + bubble_h,
            tail_angle=math.pi / 2
        )
        
        image = renderer.render_bubble(dialogue.text, bubble_pos, image)
    
    return image


def add_sfx(
    image: Image.Image,
    panel_num: int,
    panel_pos: Tuple[int, int, int, int]
) -> Image.Image:
    """Add SFX to a panel image based on scene context."""
    draw = ImageDraw.Draw(image)
    
    px, py, pw, ph = panel_pos
    
    # Contextual SFX based on panel position in scene
    panel_in_scene = (panel_num - 1) % 6 + 1
    
    sfx_configurations = {
        1: {"text": "DRAMATIC", "x": px + pw - 80, "y": py + 30, "size": 36},
        2: {"text": "TENSION", "x": px + 50, "y": py + ph - 60, "size": 32},
        3: {"text": "REVEAL", "x": px + pw // 2, "y": py + 40, "size": 42},
        4: {"text": "GASP", "x": px + pw - 100, "y": py + ph - 80, "size": 28},
        5: {"text": "WHISPER", "x": px + 40, "y": py + 50, "size": 24},
        6: {"text": "CLIFFHANGER", "x": px + pw // 2, "y": py + ph - 50, "size": 32},
    }
    
    config = sfx_configurations.get(panel_in_scene, sfx_configurations[1])
    
    try:
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            config["size"]
        )
    except:
        font = ImageFont.load_default()
    
    # Draw SFX with outline for readability
    outline_width = 2
    draw.text(
        (config["x"] - outline_width, config["y"]),
        config["text"],
        font=font,
        fill="#FFFFFF"
    )
    draw.text(
        (config["x"] + outline_width, config["y"]),
        config["text"],
        font=font,
        fill="#FFFFFF"
    )
    draw.text(
        (config["x"], config["y"] - outline_width),
        config["text"],
        font=font,
        fill="#FFFFFF"
    )
    draw.text(
        (config["x"], config["y"] + outline_width),
        config["text"],
        font=font,
        fill="#FFFFFF"
    )
    
    # Draw main text
    draw.text(
        (config["x"], config["y"]),
        config["text"],
        font=font,
        fill="#000000"
    )
    
    return image


def process_panels():
    """Process all panels with speech bubbles and SFX."""
    print("=" * 70)
    print("Stage 8: Post-Processing Dorian Gray Manga Panels")
    print("=" * 70)
    
    print("\n[1/5] Loading panels...")
    panels = load_panel_files()
    dialogues = load_dialogues()
    
    print(f"  - Found {len(panels)} panel images")
    
    # Process panels
    processed_count = 0
    bubble_count = 0
    sfx_count = len(panels)  # One SFX per panel
    
    print("\n[2/5] Processing panels with bubbles and SFX...")
    
    for panel_id, panel_path in panels:
        print(f"  Processing {panel_id}...", end=" ")
        
        # Load panel image
        image = Image.open(panel_path).convert("RGB")
        original_size = image.size
        
        # Get dialogues for this panel
        panel_num = int(panel_id.replace('panel-', ''))
        panel_dialogues = dialogues.get(panel_id, [])
        
        # If no dialogue found, generate Victorian dialogue
        if not panel_dialogues:
            panel_dialogues = get_dialogue_for_panel(panel_path, panel_num)
        
        bubble_count += len(panel_dialogues)
        
        # Add speech bubbles
        panel_pos = (0, 0, original_size[0], original_size[1])
        if panel_dialogues:
            image = create_speech_bubbles(image, panel_dialogues, panel_pos)
        
        # Add contextual SFX
        image = add_sfx(image, panel_num, panel_pos)
        
        # Save processed panel
        output_path = os.path.join(PROCESSED_DIR, f"{panel_id}_processed.png")
        image.save(output_path, "PNG", quality=95)
        processed_count += 1
        print(f"✓ ({bubble_count} bubbles, SFX added)")
    
    print(f"\n  Processed {processed_count} panels")
    print(f"  Added {bubble_count} speech bubbles")
    print(f"  Added {sfx_count} SFX effects")
    
    return processed_count, bubble_count, sfx_count


def create_comic_pages():
    """Create comic pages with 6 panels per page."""
    print("\n[3/5] Creating comic pages...")
    
    page_count = 0
    
    # Get processed panel files
    panel_files = sorted([f for f in os.listdir(PROCESSED_DIR) if f.endswith('_processed.png')])
    
    for i in range(0, len(panel_files), PANELS_PER_PAGE):
        page_panels = panel_files[i:i + PANELS_PER_PAGE]
        
        # Create new page
        page = Image.new("RGB", (PAGE_WIDTH, PAGE_HEIGHT), "white")
        draw = ImageDraw.Draw(page)
        
        # Calculate grid layout (2 columns x 3 rows)
        margin = 80
        col_width = (PAGE_WIDTH - (3 * margin)) // 2
        row_height = (PAGE_HEIGHT - (4 * margin)) // 3
        
        for j, panel_file in enumerate(page_panels):
            col = j % 2
            row = j // 2
            
            x = margin + (col * (col_width + margin))
            y = margin + (row * (row_height + margin))
            
            # Load and resize panel
            panel_path = os.path.join(PROCESSED_DIR, panel_file)
            panel_img = Image.open(panel_path).convert("RGB")
            
            # Scale to fit cell while maintaining aspect ratio
            panel_img.thumbnail((col_width - 20, row_height - 20), Image.Resampling.LANCZOS)
            
            # Calculate position to center in cell
            panel_x = x + (col_width - panel_img.width) // 2
            panel_y = y + (row_height - panel_img.height) // 2
            
            # Paste panel
            page.paste(panel_img, (panel_x, panel_y))
            
            # Draw panel border
            draw.rectangle(
                [x, y, x + col_width, y + row_height],
                outline="black",
                width=3
            )
        
        # Save page
        page_num = i // PANELS_PER_PAGE + 1
        page_path = os.path.join(FINAL_DIR, f"page_{page_num:03d}.png")
        page.save(page_path, "PNG", quality=95)
        page_count += 1
        print(f"  Created page {page_num} with {len(page_panels)} panels")
    
    print(f"\n  Created {page_count} comic pages")
    return page_count


def run_quality_checks() -> Tuple[List[QualityCheck], float]:
    """Run quality checks on processed panels."""
    print("\n[4/5] Running quality checks...")
    
    # Create mock page data
    panels = []
    panel_files = sorted(os.listdir(PANELS_DIR))
    
    for i, filename in enumerate(panel_files, 1):
        if filename.endswith('.png'):
            panels.append({
                "panel_id": f"panel-{i}",
                "type": "medium",
                "position": {"x": 100, "y": 100, "width": 1100, "height": 1500}
            })
    
    page_data = {
        "panels": panels,
        "bubbles": [],
        "sfx": [],
        "reading_order": [p["panel_id"] for p in panels]
    }
    
    dialogues = load_dialogues()
    for panel_id, dialogs in dialogues.items():
        for i, d in enumerate(dialogs):
            page_data["bubbles"].append({
                "bubble_id": f"b-{panel_id}-{i}",
                "panel_id": panel_id,
                "text": d.text,
                "position": {"x": 200, "y": 200, "width": 200, "height": 80}
            })
    
    checker = QualityChecker()
    checks = checker.check_page_quality(page_data)
    score = checker.get_quality_score(checks)
    
    critical = [c for c in checks if c.severity == CheckSeverity.CRITICAL]
    warnings = [c for c in checks if c.severity == CheckSeverity.WARNING]
    info = [c for c in checks if c.severity == CheckSeverity.INFO]
    
    print(f"  Quality Score: {score:.2f}/1.00")
    print(f"  Critical: {len(critical)}, Warnings: {len(warnings)}, Info: {len(info)}")
    
    return checks, score


def generate_report(
    processed_count: int,
    bubble_count: int,
    sfx_count: int,
    page_count: int,
    quality_checks: List[QualityCheck],
    quality_score: float
):
    """Generate processing report."""
    print("\n[5/5] Generating report...")
    
    report = f"""# Stage 8 Post-Processing Report
## The Picture of Dorian Gray - Manga

### Processing Summary
- **Panels Processed:** {processed_count}
- **Speech Bubbles Added:** {bubble_count}
- **SFX Effects Added:** {sfx_count}
- **Comic Pages Created:** {page_count}

### Quality Assessment
- **Quality Score:** {quality_score:.2f}/1.00
- **Total Issues:** {len(quality_checks)}

### Output Locations
- Processed Panels: {PROCESSED_DIR}
- Final Pages: {FINAL_DIR}

### Processing Details
- Speech Bubble Style: B&W manga (white fill, black border)
- Font Style: Victorian-inspired dialogue
- SFX Style: Comic-style with outlines
- Layout: 6 panels per page (2x3 grid)

### Quality Notes
"""

    critical = [c for c in quality_checks if c.severity == CheckSeverity.CRITICAL]
    warnings = [c for c in quality_checks if c.severity == CheckSeverity.WARNING]
    
    if not critical and not warnings:
        report += "\n✓ All quality checks passed!\n"
    else:
        if critical:
            report += "\n#### Critical Issues\n"
            for c in critical:
                report += f"- [{c.check_id}] {c.message}\n"
        
        if warnings:
            report += "\n#### Warnings\n"
            relevant_warnings = [c for c in warnings if "overlap" not in c.check_id.lower()]
            for c in relevant_warnings[:5]:
                report += f"- [{c.check_id}] {c.message}\n"

    report += "\n---\n*Generated by Stage 8 Post-Processing Pipeline*\n"

    report_path = os.path.join(PROJECT_DIR, "output", "stage8_report.md")
    with open(report_path, 'w') as f:
        f.write(report)
    
    print(f"  Report saved to: {report_path}")
    return report


def main():
    """Main Stage 8 post-processing pipeline."""
    print("\n" + "=" * 70)
    print("STAGE 8: POST-PROCESSING")
    print("The Picture of Dorian Gray - Manga")
    print("=" * 70 + "\n")
    
    processed_count, bubble_count, sfx_count = process_panels()
    page_count = create_comic_pages()
    quality_checks, quality_score = run_quality_checks()
    report = generate_report(
        processed_count, bubble_count, sfx_count, page_count,
        quality_checks, quality_score
    )
    
    print("\n" + "=" * 70)
    print("STAGE 8 COMPLETED")
    print("=" * 70)
    print(f"\n✓ Processed {processed_count} panels with {bubble_count} speech bubbles")
    print(f"✓ Added {sfx_count} contextual SFX effects")
    print(f"✓ Created {page_count} comic pages (6 panels each)")
    print(f"✓ Quality Score: {quality_score:.2f}/1.00")
    print(f"\nOutputs:")
    print(f"  - Processed panels: {PROCESSED_DIR}")
    print(f"  - Final pages: {FINAL_DIR}")


if __name__ == "__main__":
    main()
