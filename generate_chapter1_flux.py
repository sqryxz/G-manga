#!/usr/bin/env python3
"""
Generate FLUX manga images for Chapter 1 of Dorian Gray.
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from stage2_preprocessing.chapter_segmenter import ChapterSegmenter
from stage2_preprocessing.state import StatePersistence
from stage1_input.text_parser import TextParser
from models.project import Chapter, Scene, TextRange
from stage3_story_planning.panel_breakdown import PanelBreakdown
from stage6_image_generation.providers.openrouter import OpenRouterImageProvider
from stage6_image_generation.providers.base import (
    ProviderConfig, 
    ImageSize,
    ImageQuality,
    ProviderType
)
from stage7_layout.comic_assembler import ComicAssembler

def setup_chapter_1_content():
    """Set up Chapter 1 content in the project."""
    project_id = "picture-of-dorian-gray-20260211"
    project_dir = Path(f"/home/clawd/projects/g-manga/output/projects/{project_id}")
    
    # Read cached text
    cache_path = Path("/home/clawd/projects/g-manga/cache/downloads/abac0c091ac9399b223221e1ba974664.txt")
    with open(cache_path, 'r', encoding='utf-8') as f:
        raw_text = f.read()
    
    # Parse text
    parser = TextParser()
    cleaned_text, metadata = parser.parse(raw_text)
    
    # Find chapters
    segmenter = ChapterSegmenter()
    segments = segmenter.segment(cleaned_text)
    
    # Extract text for Chapter 1
    lines = cleaned_text.split('\n')
    
    # Find Chapter 1 segment
    chapter_1_seg = None
    for seg in segments:
        if seg.chapter_number == 1:
            chapter_1_seg = seg
            break
    
    if not chapter_1_seg:
        print("Could not find Chapter 1")
        return None
    
    chapter_1_text = '\n'.join(lines[chapter_1_seg.start_line:chapter_1_seg.end_line])
    
    # Create Chapter object
    chapter = Chapter(
        id=f"chapter-{chapter_1_seg.chapter_number}",
        number=chapter_1_seg.chapter_number,
        title=chapter_1_seg.title,
        text_range=TextRange(
            start=chapter_1_seg.start_line,
            end=chapter_1_seg.end_line
        ),
        content=chapter_1_text
    )
    
    # Save to state
    state = StatePersistence(project_dir)
    state.save_chapters([chapter])
    
    print(f"✓ Chapter 1 saved with {len(chapter_1_text):,} characters")
    return chapter, cleaned_text

def create_scenes(chapter, full_text):
    """Create scenes from Chapter 1."""
    project_id = "picture-of-dorian-gray-20260211"
    project_dir = Path(f"/home/clawd/projects/g-manga/output/projects/{project_id}")
    state = StatePersistence(project_dir)
    
    # For simplicity, create one scene for now (the whole chapter)
    scene = Scene(
        id=f"chapter-{chapter.number}-scene-1",
        chapter_id=chapter.id,
        number=1,
        summary=f"Chapter 1: Introduction of Basil's studio and the portrait",
        location="Basil's Art Studio",
        characters=["Basil Hallward", "Lord Henry Wotton"],
        text_range=TextRange(start=0, end=len(chapter.content)),
        text=chapter.content
    )
    
    scenes = [scene]
    state.save_scenes(scenes)
    print(f"✓ Created {len(scenes)} scene(s)")
    return scenes

def generate_panels_and_images(scenes):
    """Generate panels and FLUX images for scenes."""
    project_id = "picture-of-dorian-gray-20260211"
    project_dir = Path(f"/home/clawd/projects/g-manga/output/projects/{project_id}")
    state = StatePersistence(project_dir)
    
    panels = []
    
    for scene in scenes:
        print(f"\nProcessing Scene {scene.number}: {scene.summary}")
        
        # Create visual beats for this scene
        visual_beats = [
            {
                "number": 1,
                "description": "Establishing shot of Basil's art studio filled with roses, summer wind stirring the garden",
                "show_vs_tell": "show",
                "priority": 2,
                "visual_focus": "environment"
            },
            {
                "number": 2,
                "description": "Lord Henry Wotton lounging on Persian divan, smoking cigarettes, looking at the garden",
                "show_vs_tell": "show",
                "priority": 1,
                "visual_focus": "character"
            },
            {
                "number": 3,
                "description": "The full-length portrait of Dorian Gray on an easel in the center of the room",
                "show_vs_tell": "show",
                "priority": 1,
                "visual_focus": "object"
            },
            {
                "number": 4,
                "description": "Basil Hallward standing near his easel, looking at the portrait with a smile",
                "show_vs_tell": "show",
                "priority": 1,
                "visual_focus": "character"
            },
            {
                "number": 5,
                "description": "Lord Henry examining the portrait closely, intrigued by the young man's beauty",
                "show_vs_tell": "show",
                "priority": 1,
                "visual_focus": "character"
            },
            {
                "number": 6,
                "description": "Conversation between Basil and Lord Henry about why Basil won't exhibit the portrait",
                "show_vs_tell": "show",
                "priority": 1,
                "visual_focus": "character"
            },
            {
                "number": 7,
                "description": "Basil revealing he has put too much of himself into the portrait",
                "show_vs_tell": "show",
                "priority": 1,
                "visual_focus": "character"
            },
            {
                "number": 8,
                "description": "Lord Henry curious about the subject's name - Dorian Gray",
                "show_vs_tell": "show",
                "priority": 1,
                "visual_focus": "character"
            }
        ]
        
        # Use mock LLM for panel breakdown (simplified)
        class MockPanelBreakdown:
            class PanelInfo:
                def __init__(self, panel_num, p_type, desc, cam, mood, lighting, comp, chars):
                    self.panel_number = panel_num
                    self.type = p_type
                    self.description = desc
                    self.camera = cam
                    self.mood = mood
                    self.lighting = lighting
                    self.composition = comp
                    self.characters = chars
            
            def __init__(self, *args, **kwargs):
                pass
            
            def breakdown_scene(self, visual_beats, scene_summary, scene_id):
                class Result:
                    panel_count = len(visual_beats)
                    panels = [self.PanelInfo(
                        vb['number'],
                        'medium' if vb['priority'] > 1 else 'medium',
                        vb['description'],
                        'wide' if vb['visual_focus'] == 'environment' else 'medium_shot',
                        vb.get('mood', 'contemplative'),
                        'natural' if vb['visual_focus'] == 'environment' else 'indoor',
                        'centered',
                        []
                    ) for vb in visual_beats]
                return Result()
        
        panel_breakdown = MockPanelBreakdown()
        panel_plan = panel_breakdown.breakdown_scene(
            visual_beats=visual_beats,
            scene_summary=scene.summary,
            scene_id=scene.id
        )
        
        print(f"  Panel plan: {panel_plan.panel_count} panels")
        
        # Create panel descriptions
        for panel_info in panel_plan.panels:
            panel_id = f"panel-{scene.number}-{panel_info.panel_number}"
            panel = {
                "panel_id": panel_id,
                "scene_id": scene.id,
                "panel_number": panel_info.panel_number,
                "panel_type": panel_info.type,
                "description": panel_info.description,
                "camera": panel_info.camera,
                "mood": panel_info.mood,
                "lighting": panel_info.lighting,
                "composition": panel_info.composition,
                "characters": panel_info.characters,
                "dialogue": None,
                "narration": None,
                "text_range": [0, 100],
                "prompt": f"Manga illustration: {panel_info.description}. Style: Japanese manga, detailed linework, dramatic lighting.",
                "optimized_prompt": f"Manga style illustration showing {panel_info.description}. Victorian era art studio setting, elegant characters in period costumes, dramatic chiaroscuro lighting, detailed ink work.",
                "consistency_score": 1.0,
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat()
            }
            panels.append(panel)
            print(f"    Panel {panel_info.panel_number}: {panel_info.description[:60]}...")
    
    # Save panels
    panel_dir = project_dir / "output" / "panels"
    panel_dir.mkdir(parents=True, exist_ok=True)
    
    for panel in panels:
        panel_path = panel_dir / f"{panel['panel_id']}.json"
        with open(panel_path, 'w', encoding='utf-8') as f:
            json.dump(panel, f, indent=2)
    
    print(f"\n✓ Saved {len(panels)} panels")
    return panels

def generate_flux_images(panels):
    """Generate FLUX images for panels using OpenRouter."""
    project_id = "picture-of-dorian-gray-20260211"
    project_dir = Path(f"/home/clawd/projects/g-manga/output/projects/{project_id}")
    
    # Get API key
    api_key = os.environ.get("OPENROUTER_API_KEY", "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")
    
    # Create provider config - use string for openrouter
    config = ProviderConfig(
        provider_type="openrouter",
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        cost_per_image=0.02,
        rate_limit=20,
        default_size=ImageSize.SQUARE_1024,
        quality=ImageQuality.STANDARD
    )
    
    # Create FLUX provider - try different models
    # Model options that support image generation on OpenRouter:
    # - black-forest-labs/flux.2-klein-4b
    # - black-forest-labs/flux.2-schnell  
    # - google/gemini-2.5-flash-image
    model_options = [
        "black-forest-labs/flux.2-klein-4b",
        "google/gemini-2.5-flash-image", 
        "black-forest-labs/flux.2-schnell"
    ]
    
    for model in model_options:
        print(f"Trying model: {model}")
        try:
            provider = OpenRouterImageProvider(
                config=config,
                model=model
            )
            # Test with a simple prompt
            test_result = provider.generate("A simple test image", size=ImageSize.SQUARE_1024)
            if test_result.success:
                print(f"✓ Model {model} works!")
                return provider
            else:
                print(f"✗ Model {model} failed: {test_result.error}")
        except Exception as e:
            print(f"✗ Model {model} error: {e}")
            continue
    
def generate_flux_images(panels):
    """Generate FLUX images for panels using OpenRouter."""
    project_id = "picture-of-dorian-gray-20260211"
    project_dir = Path(f"/home/clawd/projects/g-manga/output/projects/{project_id}")
    
    # Get API key
    api_key = os.environ.get("OPENROUTER_API_KEY", "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")
    
    # Create provider config - use string for openrouter
    config = ProviderConfig(
        provider_type="openrouter",
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        cost_per_image=0.02,
        rate_limit=20,
        default_size=ImageSize.SQUARE_1024,
        quality=ImageQuality.STANDARD
    )
    
    # Create FLUX provider - try different models
    # Model options that support image generation on OpenRouter:
    # - black-forest-labs/flux.2-klein-4b
    # - black-forest-labs/flux.2-schnell  
    # - google/gemini-2.5-flash-image
    model_options = [
        "black-forest-labs/flux.2-klein-4b",
        "google/gemini-2.5-flash-image", 
        "black-forest-labs/flux.2-schnell"
    ]
    
    provider = None
    working_model = None
    for model in model_options:
        print(f"Trying model: {model}")
        try:
            test_provider = OpenRouterImageProvider(config, model=model)
            test_result = test_provider.generate("A simple test image of a rose", size=ImageSize.SQUARE_1024)
            if test_result.success:
                print(f"✓ Model {model} works!")
                provider = test_provider
                working_model = model
                break
            else:
                print(f"✗ Model {model} failed: {test_result.error}")
        except Exception as e:
            print(f"✗ Model {model} error: {e}")
            continue
    
    if provider is None:
        print("\n⚠ No working image generation model found")
        print("Generating placeholder images instead...")
        return generate_placeholder_images(panels), 0.0
    
    print(f"\nUsing model: {working_model}")
    
    image_dir = project_dir / "output" / "images"
    image_dir.mkdir(parents=True, exist_ok=True)
    
    generated_images = []
    total_cost = 0.0
    errors = []
    
    print(f"\nGenerating {len(panels)} images...")
    print(f"Cost per image: ~$0.02")
    print(f"Estimated total cost: ${len(panels) * 0.02:.2f}")
    print()
    
    for i, panel in enumerate(panels):
        print(f"[{i+1}/{len(panels)}] Generating image for {panel['panel_id']}...")
        print(f"  Prompt: {panel['optimized_prompt'][:80]}...")
        
        try:
            result = provider.generate(
                prompt=panel['optimized_prompt'],
                size=ImageSize.SQUARE_1024
            )
            
            if result.success and result.image_bytes:
                # Save image
                image_path = image_dir / f"{panel['panel_id']}.png"
                with open(image_path, 'wb') as f:
                    f.write(result.image_bytes)
                
                print(f"  ✓ Image saved: {image_path}")
                generated_images.append({
                    'panel_id': panel['panel_id'],
                    'image_path': str(image_path),
                    'cost': result.cost or 0.02
                })
                total_cost += result.cost or 0.02
            else:
                error_msg = result.error or "Unknown error"
                print(f"  ✗ Failed: {error_msg}")
                errors.append({'panel_id': panel['panel_id'], 'error': error_msg})
                
        except Exception as e:
            error_msg = str(e)
            print(f"  ✗ Error: {error_msg}")
            errors.append({'panel_id': panel['panel_id'], 'error': error_msg})
    
    print(f"\n✓ Generated {len(generated_images)}/{len(panels)} images")
    print(f"✓ Total cost: ${total_cost:.2f}")
    
    if errors:
        print(f"✗ Errors: {len(errors)}")
        for err in errors[:3]:
            print(f"  - {err['panel_id']}: {err['error']}")
    
    return generated_images, total_cost

def generate_placeholder_images(panels):
    """Generate placeholder manga-style images when API fails."""
    from PIL import Image, ImageDraw, ImageFont
    
    project_id = "picture-of-dorian-gray-20260211"
    project_dir = Path(f"/home/clawd/projects/g-manga/output/projects/{project_id}")
    
    image_dir = project_dir / "output" / "images"
    image_dir.mkdir(parents=True, exist_ok=True)
    
    generated_images = []
    
    for panel in panels:
        # Create placeholder image
        width, height = 1024, 1024
        img = Image.new('RGB', (width, height), color='#F5F5DC')
        draw = ImageDraw.Draw(img)
        
        # Draw border
        draw.rectangle([20, 20, width-20, height-20], outline='#333333', width=5)
        
        # Add panel description
        description = panel['description'][:60] + "..." if len(panel['description']) > 60 else panel['description']
        
        # Draw text
        draw.text((100, 400), f"Panel: {panel['panel_id']}", fill='#333333')
        draw.text((100, 500), description, fill='#666666')
        
        # Save image
        image_path = image_dir / f"{panel['panel_id']}.png"
        img.save(image_path)
        
        print(f"  ✓ Placeholder saved: {image_path}")
        generated_images.append({
            'panel_id': panel['panel_id'],
            'image_path': str(image_path),
            'cost': 0.0
        })
    
    print(f"\n✓ Generated {len(generated_images)} placeholder images")
    return generated_images

def assemble_pages(panels, images):
    """Assemble comic pages from panels and images."""
    project_id = "picture-of-dorian-gray-20260211"
    project_dir = Path(f"/home/clawd/projects/g-manga/output/projects/{project_id}")
    
    # Create simple page assembly
    pages = []
    panels_per_page = 4
    
    for i in range(0, len(panels), panels_per_page):
        page_panels = panels[i:i + panels_per_page]
        page_num = len(pages) + 1
        
        page = {
            'page_number': page_num,
            'panels': [p['panel_id'] for p in page_panels],
            'images': [p['image_path'] for p in page_panels if any(img['panel_id'] == p['panel_id'] for img in images)]
        }
        pages.append(page)
    
    # Save pages info
    pages_dir = project_dir / "output" / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    
    with open(pages_dir / "pages.json", 'w') as f:
        json.dump(pages, f, indent=2)
    
    print(f"\n✓ Assembled {len(pages)} comic pages")
    return pages

def main():
    """Main function to generate manga."""
    print("=" * 60)
    print("G-Manga Chapter 1 Generator - FLUX Edition")
    print("=" * 60)
    
    project_id = "picture-of-dorian-gray-20260211"
    project_dir = Path(f"/home/clawd/projects/g-manga/output/projects/{project_id}")
    
    # Step 1: Setup Chapter 1 content
    print("\n[1/5] Setting up Chapter 1 content...")
    result = setup_chapter_1_content()
    if not result:
        print("Failed to setup Chapter 1")
        return
    chapter, full_text = result
    
    # Step 2: Create scenes
    print("\n[2/5] Creating scenes...")
    scenes = create_scenes(chapter, full_text)
    
    # Step 3: Generate panels
    print("\n[3/5] Generating panels...")
    panels = generate_panels_and_images(scenes)
    
    # Step 4: Generate FLUX images (requires API call)
    print("\n[4/5] Generating FLUX images...")
    images, cost = generate_flux_images(panels)
    
    # Step 5: Assemble pages
    print("\n[5/5] Assembling pages...")
    pages = assemble_pages(panels, images)
    
    # Summary
    print("\n" + "=" * 60)
    print("GENERATION COMPLETE")
    print("=" * 60)
    print(f"Project: {project_id}")
    print(f"Chapter: 1")
    print(f"Scenes: {len(scenes)}")
    print(f"Panels: {len(panels)}")
    print(f"Images: {len(images)}")
    print(f"Pages: {len(pages)}")
    print(f"Total cost: ${cost:.2f}")
    print(f"Output: {project_dir / 'output'}")
    print("=" * 60)

if __name__ == "__main__":
    main()
