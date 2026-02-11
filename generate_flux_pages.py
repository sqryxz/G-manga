#!/usr/bin/env python3
"""
Generate Manga Pages with FLUX.2-Klein-4B (or mock fallback)
Generates real images via OpenRouter API or creates placeholder manga panels.
"""

import sys
import os
import json
import base64
import time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, List, Optional, Tuple

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from stage6_image_generation.providers.openrouter import OpenRouterImageProvider
from stage6_image_generation.providers.base import ProviderConfig, ProviderType, ImageSize, ImageQuality
from stage7_layout.comic_assembler import ComicAssembler


def load_api_key() -> Optional[str]:
    """Load OpenRouter API key from environment."""
    return os.environ.get("OPENROUTER_API_KEY", "")


def create_flux_provider(api_key: str) -> Optional[OpenRouterImageProvider]:
    """Create OpenRouter provider with FLUX.2-Klein-4B model."""
    try:
        config = ProviderConfig(
            provider_type=ProviderType.SDXL,
            api_key=api_key,
            default_size=ImageSize.SQUARE_1024,
            quality=ImageQuality.STANDARD,
            rate_limit=20,
            cost_per_image=0.02,
            max_retries=3,
            timeout=60
        )
        
        return OpenRouterImageProvider(
            config=config,
            model="black-forest-labs/flux.2-klein-4b"
        )
    except Exception as e:
        print(f"Error creating provider: {e}")
        return None


def generate_manga_panel_image(
    width: int = 1024,
    height: int = 768,
    panel_type: str = "action",
    mood: str = "neutral",
    description: str = "Manga panel"
) -> Image:
    """
    Generate a manga-style placeholder panel image.
    Creates stylized placeholder images that look like manga panels.
    """
    # Create base image
    img = Image.new('RGB', (width, height), color='#F8F8F8')
    draw = ImageDraw.Draw(img)
    
    # Color scheme based on mood
    mood_colors = {
        'neutral': ('#E8E8E8', '#666666', '#4A90D9'),
        'dramatic': ('#2C2C2C', '#CCCCCC', '#D94A4A'),
        'happy': ('#FFF8E8', '#886644', '#D9A04A'),
        'sad': ('#E8E8F0', '#666688', '#4A6DD9'),
        'action': ('#FFF0F0', '#884444', '#D94A4A'),
    }
    
    bg_color, text_color, accent_color = mood_colors.get(mood, mood_colors['neutral'])
    
    # Fill background with subtle gradient effect
    for y in range(height):
        ratio = y / height
        r = int(int(bg_color[1:3], 16) * (1 - ratio * 0.1))
        g = int(int(bg_color[3:5], 16) * (1 - ratio * 0.1))
        b = int(int(bg_color[5:7], 16) * (1 - ratio * 0.1))
        color = f'#{r:02x}{g:02x}{b:02x}'
        draw.line([(0, y), (width, y)], fill=color)
    
    # Draw panel border (manga style - irregular border)
    border_style = "action" if panel_type == "action" else "establishing"
    
    if border_style == "action":
        # Jagged action border
        points = []
        for x in range(0, width, 20):
            offset = 5 if x % 40 == 0 else 0
            points.extend([(x, offset), (x + 10, height - offset)])
        draw.polygon(
            [(0, 0), (width - 10, 0), (width, 0), (width, height), 
             (10, height), (0, height), (0, 0)],
            outline=accent_color, width=4
        )
    else:
        # Clean establishing shot border
        draw.rectangle([15, 15, width - 15, height - 15], outline=accent_color, width=3)
    
    # Add panel type label
    label_font_size = 28
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", label_font_size)
        small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
    except:
        font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    # Panel type badge
    draw.rectangle([30, 30, 180, 70], fill=accent_color, outline=text_color)
    draw.text([50, 35], panel_type.upper(), fill='white', font=font)
    
    # Description text
    desc_lines = []
    words = description.split()
    line = ""
    for word in words:
        if len(line + word) < 40:
            line += " " + word if line else word
        else:
            desc_lines.append(line)
            line = word
    if line:
        desc_lines.append(line)
    
    y_offset = 120
    for line in desc_lines:
        draw.text([50, y_offset], line, fill=text_color, font=small_font)
        y_offset += 30
    
    # Add manga-style visual elements
    # Speed lines for action panels
    if panel_type == "action":
        for i in range(8):
            x = width - 50 - (i * 40)
            draw.line([(x, 80), (x - 20, height - 80)], fill='#CCCCCC', width=2)
    
    # Character silhouette placeholder
    char_x = width // 2
    char_y = height // 2 + 50
    
    # Draw character silhouette
    draw.ellipse(
        [char_x - 80, char_y - 150, char_x + 80, char_y - 50],
        fill=text_color, outline=text_color
    )
    # Body
    draw.polygon(
        [(char_x - 100, char_y - 50), (char_x + 100, char_y - 50), 
         (char_x + 80, char_y + 100), (char_x - 80, char_y + 100)],
        fill=text_color
    )
    
    # Add mood indicator
    draw.text([width - 150, height - 60], f"Mood: {mood}", fill=text_color, font=small_font)
    
    # Add FLUX.2-Klein-4B label
    draw.text([width - 250, 30], "FLUX.2-Klein-4B", fill=accent_color, font=font)
    
    return img


def generate_panel_image_api(
    provider: OpenRouterImageProvider,
    prompt: str,
    panel_id: str,
    output_dir: str,
    size: Tuple[int, int] = (1024, 768)
) -> Optional[str]:
    """Generate a panel image using FLUX API."""
    print(f"\n  Generating: {panel_id}")
    print(f"  Prompt: {prompt[:100]}...")
    
    # Map size tuple to ImageSize enum
    if size == (1024, 1024):
        image_size = ImageSize.SQUARE_1024
    elif size == (1024, 768):
        image_size = ImageSize.LANDSCAPE_1024
    else:
        image_size = ImageSize.SQUARE_1024
    
    result = provider.generate(
        prompt=prompt,
        size=image_size,
        quality=ImageQuality.STANDARD
    )
    
    if result.success:
        panel_output_dir = os.path.join(output_dir, "panels")
        os.makedirs(panel_output_dir, exist_ok=True)
        
        output_path = os.path.join(panel_output_dir, f"{panel_id}.png")
        
        with open(output_path, "wb") as f:
            f.write(result.image_bytes)
        
        print(f"  ✓ Saved: {output_path}")
        print(f"  Cost: ${result.cost:.4f}")
        
        return output_path
    else:
        print(f"  ✗ Failed: {result.error}")
        return None


def generate_panel_image_mock(
    panel_data: dict,
    panel_id: str,
    output_dir: str,
    width: int = 1024,
    height: int = 768
) -> str:
    """Generate a mock manga panel image."""
    panel_type = panel_data.get("panel_type", "action")
    mood = panel_data.get("mood", "neutral")
    description = panel_data.get("description", panel_data.get("panel_prompt", "Manga panel"))
    
    img = generate_manga_panel_image(
        width=width,
        height=height,
        panel_type=panel_type,
        mood=mood,
        description=description
    )
    
    panel_output_dir = os.path.join(output_dir, "panels")
    os.makedirs(panel_output_dir, exist_ok=True)
    
    output_path = os.path.join(panel_output_dir, f"{panel_id}.png")
    img.save(output_path, 'PNG', optimize=True)
    
    print(f"  ✓ Generated mock: {output_path}")
    
    return output_path


def create_manga_prompt(panel_data: dict) -> str:
    """Create an enhanced manga-style prompt for FLUX."""
    description = panel_data.get("description", panel_data.get("panel_prompt", ""))
    panel_type = panel_data.get("panel_type", "action")
    mood = panel_data.get("mood", "neutral")
    lighting = panel_data.get("lighting", "natural")
    
    enhanced_prompt = f"""Manga panel, {panel_type} shot, {mood} mood, {lighting} lighting. {description}

Style: Japanese manga, clean linework, dramatic shading, professional comic art. 
Composition: Well-framed panel with clear focal point.
Quality: High detail, sharp lines, professional manga illustration."""
    
    return enhanced_prompt


def assemble_comic_page(
    panel_images: Dict[str, str],
    output_dir: str,
    page_number: int = 1
) -> str:
    """Assemble panel images into a comic page."""
    print(f"\n  Assembling page {page_number}...")
    
    # Create comic assembler (A4 size at 300 DPI)
    assembler = ComicAssembler(
        page_width=2480,
        page_height=3508,
        background_color="#FFFFFF",
        border_color="#000000",
        border_thickness=3
    )
    
    # Create blank page
    page_image = Image.new("RGB", (2480, 3508), "#FFFFFF")
    draw = ImageDraw.Draw(page_image)
    
    panel_ids = list(panel_images.keys())
    panel_count = len(panel_ids)
    
    # Page layout
    margin = 80
    gap = 25
    
    # Calculate panel sizes based on count
    if panel_count <= 1:
        panel_width = 2480 - 2 * margin
        panel_height = 3508 - 2 * margin
        positions = [(margin, margin)]
    elif panel_count == 2:
        panel_width = (2480 - 2 * margin - gap) // 2
        panel_height = 2800
        positions = [(margin, margin), (margin + panel_width + gap, margin)]
    elif panel_count <= 4:
        panel_width = (2480 - 2 * margin - gap) // 2
        panel_height = (3508 - 2 * margin - gap) // 2
        positions = []
        for i in range(panel_count):
            row = i // 2
            col = i % 2
            x = margin + col * (panel_width + gap)
            y = margin + row * (panel_height + gap)
            positions.append((x, y))
    else:
        # 6 panel grid
        panel_width = (2480 - 2 * margin - gap) // 3
        panel_height = (3508 - 2 * margin - 2 * gap) // 3
        positions = []
        for i in range(min(panel_count, 6)):
            row = i // 3
            col = i % 3
            x = margin + col * (panel_width + gap)
            y = margin + row * (panel_height + gap)
            positions.append((x, y))
    
    # Load and place panels
    for i, panel_id in enumerate(panel_images):
        if i >= len(positions):
            break
            
        image_path = panel_images[panel_id]
        x, y = positions[i]
        
        try:
            panel_img = Image.open(image_path).convert("RGB")
            
            # Resize to fit slot
            panel_img.thumbnail((panel_width, panel_height), Image.LANCZOS)
            
            # Center in slot
            paste_x = x + (panel_width - panel_img.width) // 2
            paste_y = y + (panel_height - panel_img.height) // 2
            
            # Paste onto page
            page_image.paste(panel_img, (paste_x, paste_y))
            
            # Draw panel border
            draw.rectangle(
                [x, y, x + panel_width, y + panel_height],
                outline="#000000",
                width=3
            )
            
            print(f"  ✓ Placed {panel_id} at ({paste_x}, {paste_y})")
            
        except Exception as e:
            print(f"  ✗ Error loading {panel_id}: {e}")
    
    # Add page header
    draw.text(
        (1240, 40),
        "G-Manga Demo - The Picture of Dorian Gray",
        fill="#333333",
        anchor="mm",
        font_size=24
    )
    
    # Add page number
    draw.text(
        (1240, 3460),
        "Page 1",
        fill="#666666",
        anchor="mm"
    )
    
    # Save page
    pages_dir = os.path.join(output_dir, "pages")
    os.makedirs(pages_dir, exist_ok=True)
    
    output_path = os.path.join(pages_dir, f"page_{page_number:03d}.png")
    page_image.save(output_path, "PNG", optimize=True)
    
    print(f"  ✓ Saved page: {output_path}")
    
    return output_path


def create_thumbnail(page_path: str, output_dir: str, max_width: int = 400) -> str:
    """Create thumbnail for a page."""
    page_img = Image.open(page_path)
    
    aspect = page_img.height / page_img.width
    new_height = int(max_width * aspect)
    
    thumbnail = page_img.resize((max_width, new_height), Image.LANCZOS)
    
    thumb_dir = os.path.join(output_dir, "thumbnails")
    os.makedirs(thumb_dir, exist_ok=True)
    
    base_name = os.path.basename(page_path)
    thumb_path = os.path.join(thumb_dir, f"thumb_{base_name}")
    thumbnail.save(thumb_path, "PNG", optimize=True)
    
    return thumb_path


def main():
    """Main function to generate manga pages."""
    print("=" * 70)
    print("G-Manga FLUX.2-Klein-4B Generator")
    print("=" * 70)
    
    # Configuration
    api_key = load_api_key()
    project_dir = "/home/clawd/projects/g-manga/projects/demo-dorian-gray-20260211"
    panels_path = os.path.join(project_dir, "panels", "panels.json")
    output_dir = os.path.join(project_dir, "output")
    
    use_api = bool(api_key)
    
    if use_api:
        print("\n✓ OpenRouter API key found")
    else:
        print("\n⚠ OpenRouter API key not found")
        print("  Generating manga-style placeholder images...")
        print("  (Set OPENROUTER_API_KEY to generate real images with FLUX)")
    
    # Load panels
    print("\n[1/5] Loading panels...")
    with open(panels_path, 'r') as f:
        panels_data = json.load(f)
    
    panels = panels_data.get('panels', {})
    panel_ids = list(panels.keys())
    print(f"✓ Loaded {len(panel_ids)} panels")
    
    # Create provider if API key available
    provider = None
    if use_api:
        print("\n[2/5] Creating FLUX.2-Klein-4B provider...")
        provider = create_flux_provider(api_key)
        if provider:
            print(f"✓ Provider created with model: black-forest-labs/flux.2-klein-4b")
        else:
            use_api = False
            print("⚠ Provider creation failed, using mock images")
    
    # Generate panel images
    print("\n[3/5] Generating panel images...")
    generated_paths = {}
    
    for panel_id in panel_ids:
        panel = panels[panel_id]
        
        if use_api:
            prompt = create_manga_prompt(panel)
            path = generate_panel_image_api(
                provider=provider,
                prompt=prompt,
                panel_id=panel_id,
                output_dir=output_dir
            )
        else:
            path = generate_panel_image_mock(
                panel_data=panel,
                panel_id=panel_id,
                output_dir=output_dir
            )
        
        if path:
            generated_paths[panel_id] = path
        
        # Rate limiting for API
        if use_api:
            time.sleep(1)
    
    if not generated_paths:
        print("\n✗ No panels were generated successfully")
        return 1
    
    print(f"\n✓ Generated {len(generated_paths)}/{len(panel_ids)} panels")
    
    # Assemble comic page
    print("\n[4/5] Assembling comic page...")
    page_path = assemble_comic_page(
        panel_images=generated_paths,
        output_dir=output_dir,
        page_number=1
    )
    
    # Create thumbnail
    print("\n[5/5] Creating thumbnail...")
    thumb_path = create_thumbnail(page_path, output_dir)
    print(f"✓ Thumbnail: {thumb_path}")
    
    # Summary
    mode = "FLUX.2-Klein-4B API" if use_api else "Manga-style Mock"
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"""
✅ Manga Page Generated Successfully!

📊 Statistics:
   - Panels generated: {len(generated_paths)}
   - Page assembled: Yes
   - Generation mode: {mode}
   - Model: black-forest-labs/flux.2-klein-4b

📂 Output Files:
   - Generated panels: {output_dir}/panels/
   - Assembled page: {page_path}
   - Thumbnail: {thumb_path}

🎨 Page Details:
   - Dimensions: 2480 x 3508 pixels (A4 at 300 DPI)
   - Panels: {len(generated_paths)} on 1 page
   - Format: PNG

🚀 To generate REAL images:
   export OPENROUTER_API_KEY="sk-or-v1-..."
   python3 generate_flux_pages.py

✅ Done!
""")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
