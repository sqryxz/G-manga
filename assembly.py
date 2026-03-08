#!/usr/bin/env python3
"""
G-Manga Assembly Module
Creates a 5-page manga PDF from generated panel images with speech bubbles.

Usage:
    python3 assembly.py [--pages N] [--output OUTPUT.PDF] [--with-dialogue]
"""

import sys
import json
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

PROJECT_ID = "frankenstein-20260216-20260216"
PAGE_WIDTH = 1800
PAGE_HEIGHT = 2560
PANELS_PER_PAGE = 6


def get_panel_number(pid):
    """Extract sequential panel number from panel_id."""
    parts = pid.split('-')
    if len(parts) == 2:
        return int(parts[1])
    return 0


def load_panels(project_dir):
    """Load successfully generated panels from manifest."""
    manifest_path = project_dir / "output" / "panels" / "manifest.json"
    if not manifest_path.exists():
        print(f"ERROR: No manifest found at {manifest_path}")
        return []
    
    with open(manifest_path) as f:
        manifest = json.load(f)
    
    successful = [img for img in manifest.get('images', []) if img.get('success', False)]
    successful.sort(key=lambda x: get_panel_number(x['panel_id']))
    return successful


def load_dialogue(project_dir):
    """Load dialogue from analysis.json."""
    dialogue_path = project_dir / "intermediate" / "analysis.json"
    if not dialogue_path.exists():
        print(f"Warning: No dialogue file found at {dialogue_path}")
        return []
    
    with open(dialogue_path) as f:
        data = json.load(f)
    
    return data.get('dialogue', [])


def create_page_layout(panel_count):
    """Create a simple manga page layout (3x2 grid for 6 panels)."""
    margin = 40
    gutter = 20
    
    if panel_count <= 4:
        rows, cols = 2, 2
    elif panel_count <= 6:
        rows, cols = 3, 2
    else:
        rows, cols = 4, 2
    
    cell_width = (PAGE_WIDTH - 2 * margin - (cols - 1) * gutter) // cols
    cell_height = (PAGE_HEIGHT - 2 * margin - (rows - 1) * gutter) // rows
    
    slots = []
    for row in range(rows):
        for col in range(cols):
            if len(slots) < panel_count:
                x = margin + col * (cell_width + gutter)
                y = margin + row * (cell_height + gutter)
                slots.append({
                    'x': x,
                    'y': y,
                    'width': cell_width,
                    'height': cell_height
                })
    
    return slots


def load_panel_image(panel, project_dir):
    """Load a panel image from disk."""
    filename = project_dir / "output" / "panels" / panel['filename']
    if filename.exists():
        img = Image.open(filename)
        return img.convert("RGB")
    return None


def add_page_number(draw, page_num, total_pages):
    """Add page number to page."""
    font_size = 24
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    text = f"- {page_num} -"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    x = (PAGE_WIDTH - text_width) // 2
    y = PAGE_HEIGHT - 60
    
    draw.text((x, y), text, fill="#666666", font=font)


def add_title(draw, title="Frankenstein"):
    """Add manga title."""
    font_size = 48
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    text = title
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    x = (PAGE_WIDTH - text_width) // 2
    y = 10
    
    draw.text((x, y), text, fill="#000000", font=font)


def draw_speech_bubble(draw, x, y, width, height, text, speaker):
    """Draw a speech bubble on the page."""
    padding = 15
    radius = 15
    
    # Draw rounded rectangle for bubble
    bubble_box = [x + padding, y + padding, x + width - padding, y + height - padding]
    draw.rounded_rectangle(bubble_box, radius=radius, outline="#000000", width=2, fill="#FFFFFF")
    
    # Draw tail
    tail_x = x + width // 3
    tail_points = [
        (tail_x, y + height - padding),
        (tail_x + 15, y + height),
        (tail_x + 30, y + height - padding)
    ]
    draw.polygon(tail_points, fill="#FFFFFF", outline="#000000", width=2)
    
    # Draw speaker name
    font_size = 14
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    draw.text((x + padding + 5, y + padding), speaker, fill="#000000", font=font)
    
    # Draw dialogue text (wrapped)
    font_size = 12
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    # Simple text wrapping
    max_chars = (width - 2 * padding - 10) // 7
    words = text.split()
    lines = []
    current_line = ""
    
    for word in words:
        if len(current_line) + len(word) + 1 <= max_chars:
            current_line += " " + word if current_line else word
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    
    # Limit to 3 lines
    lines = lines[:3]
    
    text_y = y + padding + 22
    for line in lines:
        draw.text((x + padding + 5, text_y), line[:max_chars], fill="#333333", font=font)
        text_y += 14


def create_page(panels, page_num, total_pages, project_dir, dialogue_list=None):
    """Create a single manga page with panels and optional dialogue."""
    page = Image.new("RGB", (PAGE_WIDTH, PAGE_HEIGHT), "#FFFFFF")
    draw = ImageDraw.Draw(page)
    
    slots = create_page_layout(len(panels))
    
    # Calculate dialogue index for this page
    dialogue_idx_start = (page_num - 1) * 2  # 2 bubbles per page
    
    for i, panel in enumerate(panels):
        if i >= len(slots):
            break
        
        slot = slots[i]
        panel_img = load_panel_image(panel, project_dir)
        
        if panel_img:
            panel_img.thumbnail((slot['width'], slot['height']), Image.LANCZOS)
            x = slot['x'] + (slot['width'] - panel_img.width) // 2
            y = slot['y'] + (slot['height'] - panel_img.height) // 2
            page.paste(panel_img, (x, y))
        
        # Draw panel border
        draw.rectangle(
            [slot['x'], slot['y'], slot['x'] + slot['width'], slot['y'] + slot['height']],
            outline="#000000",
            width=3
        )
        
        # Add speech bubble if dialogue available
        if dialogue_list and i < 2:  # Max 2 bubbles per page
            dialog_idx = dialogue_idx_start + i
            if dialog_idx < len(dialogue_list):
                d = dialogue_list[dialog_idx]
                bubble_w = slot['width'] // 2
                bubble_h = slot['height'] // 4
                bubble_x = slot['x'] + slot['width'] - bubble_w - 10
                bubble_y = slot['y'] + slot['height'] - bubble_h - 10
                
                draw_speech_bubble(
                    draw, 
                    bubble_x, bubble_y, bubble_w, bubble_h,
                    d.get('quote', '')[:80],
                    d.get('speaker', '???')
                )
    
    add_page_number(draw, page_num, total_pages)
    
    if page_num == 1:
        add_title(draw)
    
    return page


def create_pdf(pages, output_path):
    """Save pages as PDF."""
    first_page = pages[0]
    
    if first_page.mode != 'RGB':
        first_page = first_page.convert('RGB')
    
    pdf_path = Path(output_path)
    first_page.save(
        pdf_path,
        "PDF",
        resolution=100.0,
        save_all=True,
        append_images=pages[1:]
    )
    
    return pdf_path


def main():
    parser = argparse.ArgumentParser(description="G-Manga Assembly Module")
    parser.add_argument('--pages', type=int, default=5, help='Number of pages to generate')
    parser.add_argument('--output', type=str, default='output.pdf', help='Output PDF filename')
    parser.add_argument('--project', type=str, default=PROJECT_ID, help='Project ID')
    parser.add_argument('--with-dialogue', action='store_true', help='Add speech bubbles with dialogue')
    args = parser.parse_args()
    
    print("=" * 60)
    print("G-MANGA ASSEMBLY MODULE")
    print("=" * 60)
    
    # Project directory
    project_dir = Path("output/projects") / args.project
    
    # Load panels
    panels = load_panels(project_dir)
    
    if not panels:
        print("ERROR: No panels found. Run Stage 6 first.")
        return 1
    
    num_panels_needed = args.pages * PANELS_PER_PAGE
    
    if len(panels) < num_panels_needed:
        print(f"WARNING: Only {len(panels)} panels available, need {num_panels_needed}")
        print(f"Generating {len(panels) // PANELS_PER_PAGE} pages instead")
        args.pages = len(panels) // PANELS_PER_PAGE
    
    print(f"\nLoaded {len(panels)} panel images")
    
    # Load dialogue if requested
    dialogue_list = None
    if args.with_dialogue:
        dialogue_list = load_dialogue(project_dir)
        print(f"Loaded {len(dialogue_list)} dialogue entries")
    
    print(f"Generating {args.pages} pages")
    
    # Create pages
    print(f"\n[2/3] Creating {args.pages} manga pages...")
    pages = []
    
    for page_num in range(1, args.pages + 1):
        start_idx = (page_num - 1) * PANELS_PER_PAGE
        end_idx = start_idx + PANELS_PER_PAGE
        page_panels = panels[start_idx:end_idx]
        
        page = create_page(page_panels, page_num, args.pages, project_dir, dialogue_list)
        pages.append(page)
        print(f"  ✓ Page {page_num}/{args.pages} created")
    
    # Save as PDF
    print(f"\n[3/3] Saving as PDF...")
    output_path = project_dir / "output" / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf_path = create_pdf(pages, output_path)
    
    print(f"\n{'=' * 60}")
    print("ASSEMBLY COMPLETE")
    print(f"{'=' * 60}")
    print(f"PDF saved to: {pdf_path}")
    print(f"Pages: {args.pages}")
    print(f"Panels per page: {PANELS_PER_PAGE}")
    if args.with_dialogue:
        print(f"Dialogue: {len(dialogue_list)} entries loaded")
    
    return __name__ == 0


if "__main__":
    sys.exit(main())
