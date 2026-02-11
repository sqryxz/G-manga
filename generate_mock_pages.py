#!/usr/bin/env python3
"""
Mock Comic Page Generator for G-Manga Pipeline
Generates placeholder images for panels and assembles comic pages.
"""

import sys
import json
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, List, Tuple, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from stage7_layout.comic_assembler import ComicAssembler, ComicPage
from stage7_layout.layout_templates import LayoutTemplateLibrary


def create_mock_panel_image(
    panel_id: str,
    description: str,
    width: int = 1024,
    height: int = 768,
    output_path: str = None
) -> Image:
    """
    Create a placeholder panel image with description text.
    
    Args:
        panel_id: Panel identifier
        description: Panel description
        width: Image width
        height: Image height
        output_path: Optional path to save image
        
    Returns:
        PIL Image object
    """
    # Create background with gradient-like effect
    img = Image.new('RGB', (width, height), color='#F5F5F5')
    draw = ImageDraw.Draw(img)
    
    # Add colored border
    border_color = '#4A90D9' if 'establishing' in description.lower() else '#666666'
    draw.rectangle([10, 10, width-10, height-10], outline=border_color, width=3)
    
    # Add title text
    title_text = f"Panel: {panel_id}"
    
    # Try to use a font, fall back to default
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
        desc_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    except:
        title_font = ImageFont.load_default()
        desc_font = ImageFont.load_default()
    
    # Draw title
    draw.text((50, 50), title_text, fill='#333333', font=title_font)
    
    # Draw description (wrap text)
    desc_lines = []
    words = description.split()
    current_line = ""
    for word in words:
        test_line = current_line + (" " if current_line else "") + word
        if len(test_line) < 50:
            current_line = test_line
        else:
            if current_line:
                desc_lines.append(current_line)
            current_line = word
    if current_line:
        desc_lines.append(current_line)
    
    y_offset = 100
    for line in desc_lines:
        draw.text((50, y_offset), line, fill='#555555', font=desc_font)
        y_offset += 35
    
    # Add panel type indicator
    panel_type = "ESTABLISHING" if 'establishing' in description.lower() else "ACTION"
    draw.text((50, height - 80), f"Type: {panel_type}", fill='#888888', font=desc_font)
    
    # Save if path provided
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        img.save(output_path, 'PNG', optimize=True)
    
    return img


def create_mock_speech_bubble(
    text: str = "...",
    bubble_type: str = "speech",
    position: Tuple[int, int] = (100, 100),
    size: Tuple[int, int] = (200, 100)
) -> Image:
    """
    Create a placeholder speech bubble.
    
    Args:
        text: Bubble text
        bubble_type: Type of bubble (speech, thought, shout)
        position: Position tuple
        size: Size tuple
        
    Returns:
        PIL Image object
    """
    width, height = size
    img = Image.new('RGBA', (width, height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw bubble shape
    if bubble_type == "speech":
        # Oval speech bubble
        draw.ellipse([0, 0, width-20, height], outline='black', width=2, fill='white')
        # Tail
        draw.polygon([(width-20, height-10), (width, height), (width-30, height)], fill='white', outline='black')
    elif bubble_type == "thought":
        # Cloud-like thought bubble
        draw.ellipse([20, 0, width-20, height-40], outline='black', width=2, fill='white')
        draw.ellipse([0, height-60, 60, height], outline='black', width=2, fill='white')
        draw.ellipse([20, height-40, 50, height-10], outline='black', width=2, fill='white')
    elif bubble_type == "shout":
        # Jagged shout bubble
        points = []
        for i in range(0, width, 30):
            points.extend([(i, 0), (i + 15, 20)])
        points.extend([(width, 0), (width, height), (0, height)])
        draw.polygon(points, outline='black', width=2, fill='white')
    
    # Add text
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
    except:
        font = ImageFont.load_default()
    
    draw.text((10, 10), text[:20], fill='black', font=font)
    
    return img


def create_mock_sfx(
    text: str = "BANG!",
    style: str = "action",
    position: Tuple[int, int] = (100, 100),
    size: Tuple[int, int] = (150, 50)
) -> Image:
    """
    Create a placeholder SFX text.
    
    Args:
        text: SFX text
        style: Style (action, dramatic, subtle)
        position: Position tuple
        size: Size tuple
        
    Returns:
        PIL Image object
    """
    width, height = size
    img = Image.new('RGBA', (width, height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # Set color based on style
    colors = {
        'action': '#FF0000',
        'dramatic': '#000000',
        'subtle': '#666666'
    }
    color = colors.get(style, '#000000')
    
    # Draw text with outline
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
    except:
        font = ImageFont.load_default()
    
    # Text outline
    draw.text((position[0]-1, position[1]), text, fill='white', font=font)
    draw.text((position[0]+1, position[1]), text, fill='white', font=font)
    draw.text((position[0], position[1]-1), text, fill='white', font=font)
    draw.text((position[0], position[1]+1), text, fill='white', font=font)
    # Main text
    draw.text(position, text, fill=color, font=font)
    
    return img


def load_panels(panels_path: str) -> Dict:
    """Load panels from JSON file."""
    with open(panels_path, 'r') as f:
        return json.load(f)


def main():
    """Main function to generate mock comic pages."""
    print("=" * 70)
    print("G-Manga Mock Comic Page Generator")
    print("=" * 70)
    
    # Configuration
    project_dir = "/home/clawd/projects/g-manga/projects/demo-dorian-gray-20260211"
    panels_path = f"{project_dir}/panels/panels.json"
    output_dir = f"{project_dir}/output"
    pages_output_dir = f"{output_dir}/pages"
    mock_output_dir = f"{output_dir}/mock_output"
    
    # Load panels
    print("\n[1/5] Loading panels...")
    with open(panels_path, 'r') as f:
        panels_data = json.load(f)
    
    panels = panels_data.get('panels', {})
    panel_ids = list(panels.keys())
    print(f"✓ Loaded {len(panel_ids)} panels: {', '.join(panel_ids)}")
    
    # Step 2: Create mock panel images
    print("\n[2/5] Creating mock panel images...")
    mock_panels = {}
    
    for panel_id in panel_ids:
        panel = panels[panel_id]
        description = panel.get('description', panel.get('panel_prompt', 'Panel description'))
        output_path = f"{mock_output_dir}/panels/{panel_id}.png"
        
        # Create panel image
        panel_img = create_mock_panel_image(
            panel_id=panel_id,
            description=description,
            width=1200,
            height=900,
            output_path=output_path
        )
        mock_panels[panel_id] = panel_img
        print(f"✓ Created mock panel: {panel_id}")
    
    # Step 3: Assemble pages using layout templates
    print("\n[3/5] Assembling pages...")
    
    # Select template based on panel count
    template_lib = LayoutTemplateLibrary()
    panel_count = len(panel_ids)
    template = template_lib.find_best_template(panel_count)
    
    if template:
        print(f"✓ Selected template: {template.name} (supports {template.panel_count} panels)")
    else:
        # Fallback to splash layout
        template = template_lib.get_template("splash-full")
        print(f"✓ Using fallback template: {template.name}")
    
    # Create blank page
    page_image = Image.new('RGB', (2480, 3508), '#FFFFFF')
    draw = ImageDraw.Draw(page_image)
    
    # Place panels on page based on template slots
    for i, panel_id in enumerate(panel_ids):
        panel = mock_panels[panel_id]
        slot = template.slots[i] if i < len(template.slots) else template.slots[0]
        
        # Calculate position and size based on slot percentages
        x = int(slot.x * 2480)
        y = int(slot.y * 3508)
        w = int(slot.width * 2480)
        h = int(slot.height * 3508)
        
        # Resize and paste panel
        panel_resized = panel.copy()
        panel_resized.thumbnail((w, h), Image.LANCZOS)
        
        # Center in slot
        paste_x = x + (w - panel_resized.width) // 2
        paste_y = y + (h - panel_resized.height) // 2
        
        page_image.paste(panel_resized, (paste_x, paste_y))
        
        # Draw border
        draw.rectangle([x, y, x + w, y + h], outline='#000000', width=2)
        
        print(f"✓ Placed panel {panel_id} at ({paste_x}, {paste_y})")
    
    # Step 4: Add speech bubbles and SFX
    print("\n[4/5] Adding speech bubbles and SFX...")
    
    # Add placeholder speech bubble (simplified - draw directly on page)
    bubble_x, bubble_y = 400, 200
    bubble_w, bubble_h = 200, 100
    
    # Draw speech bubble shape on page
    draw.ellipse(
        [bubble_x, bubble_y, bubble_x + bubble_w - 20, bubble_y + bubble_h],
        outline='#000000', width=2, fill='#FFFFFF'
    )
    # Bubble tail
    draw.polygon(
        [(bubble_x + bubble_w - 20, bubble_y + bubble_h - 10),
         (bubble_x + bubble_w, bubble_y + bubble_h),
         (bubble_x + bubble_w - 30, bubble_y + bubble_h)],
        fill='#FFFFFF', outline='#000000'
    )
    
    # Draw text
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
    except:
        font = ImageFont.load_default()
    draw.text((bubble_x + 20, bubble_y + 40), "...", fill='#000000', font=font)
    print("✓ Added speech bubble placeholder")
    
    # Add placeholder SFX (simplified - draw text directly)
    sfx_x, sfx_y = 1800, 500
    
    # Draw SFX text with outline
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
    except:
        font = ImageFont.load_default()
    
    # White outline
    draw.text((sfx_x - 2, sfx_y), "POW!", fill='white', font=font)
    draw.text((sfx_x + 2, sfx_y), "POW!", fill='white', font=font)
    draw.text((sfx_x, sfx_y - 2), "POW!", fill='white', font=font)
    draw.text((sfx_x, sfx_y + 2), "POW!", fill='white', font=font)
    # Red text
    draw.text((sfx_x, sfx_y), "POW!", fill='#FF0000', font=font)
    print("✓ Added SFX placeholder")
    
    # Add page number
    draw.text((1200, 3400), "Page 1", fill='#999999', anchor='mm')
    
    # Step 5: Save output
    print("\n[5/5] Saving output...")
    
    # Save assembled page
    os.makedirs(pages_output_dir, exist_ok=True)
    page_path = f"{pages_output_dir}/page_001.png"
    page_image.save(page_path, 'PNG', optimize=True)
    print(f"✓ Saved page: {page_path}")
    
    # Create thumbnail
    thumb_width = 400
    thumb_height = int(thumb_width * 3508 / 2480)
    thumbnail = page_image.copy()
    thumbnail.thumbnail((thumb_width, thumb_height), Image.LANCZOS)
    thumb_path = f"{output_dir}/thumbnails/page_001_thumb.png"
    os.makedirs(os.path.dirname(thumb_path), exist_ok=True)
    thumbnail.save(thumb_path, 'PNG', optimize=True)
    print(f"✓ Saved thumbnail: {thumb_path}")
    
    # Generate summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"""
✅ Mock Comic Pages Generated Successfully!

📊 Statistics:
   - Panels created: {len(panel_ids)}
   - Pages assembled: 1
   - Template used: {template.name}

📂 Output Files:
   - Panel images: {mock_output_dir}/panels/
   - Assembled page: {page_path}
   - Thumbnail: {thumb_path}

📝 Generated Files:
""")
    
    # List all generated files
    for root, dirs, files in os.walk(mock_output_dir):
        for f in files:
            rel_path = os.path.relpath(os.path.join(root, f), mock_output_dir)
            print(f"   - {rel_path}")
    
    print(f"""
🎨 Preview:
   - Page dimensions: 2480 x 3508 pixels (A4 at 300 DPI)
   - Panel images: 1200 x 900 pixels
   - Speech bubbles: Placeholder added
   - SFX effects: Placeholder added

✅ Mock comic page generation complete!
""")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
