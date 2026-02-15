#!/usr/bin/env python3
"""
Generate character reference sheet images using OpenRouter API
Generates all characters plus a combined reference sheet
"""
import json
import os
import requests
import base64
from pathlib import Path

# Configuration
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OUTPUT_DIR = "/home/clawd/projects/g-manga/output/projects/picture-of-dorian-gray-20260213-20260213/output/character_refs"
INPUT_FILE = "/home/clawd/projects/g-manga/output/projects/picture-of-dorian-gray-20260213-20260213/intermediate/character_reference_sheets.json"

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    print("ERROR: OPENROUTER_API_KEY environment variable not set")
    exit(1)

def generate_prompt(character):
    """Generate an image prompt based on character data"""
    phys = character['physical_appearance']
    costume = character['costume_design']
    
    prompt = f"""Character reference sheet for {character['character_name']}, {phys['age']} {phys['gender']}, {phys['height']}, {phys['build']} build.
Hair: {phys['hair']['color']}, {phys['hair']['length']}, {phys['hair']['style']}, {phys['hair']['texture']} texture.
Eyes: {phys['hair']['color']} eyes, {phys['eyes']['shape']} shape, {phys['eyes']['expression']}.
Skin tone: {phys['skin_tone']}.
Distinctive features: {phys['distinctive_features']}.
Typical expressions: {phys['typical_expressions'][0]}.
Clothing: {costume['everyday_attire']}, {costume['variations'][0] if costume['variations'] else 'Victorian attire'}.
Accessories: {', '.join(costume['accessories'][:2]) if costume['accessories'] else 'None'}.
Victorian manga style, front view, side view, 3/4 view, turnaround sheet, clean line art, professional character design."""
    
    return prompt

def generate_image(prompt, character_name, idx):
    """Generate an image using OpenRouter API with correct endpoint"""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/g-manga",
        "X-Title": "Character Reference Generator"
    }
    
    payload = {
        "model": "google/gemini-2.5-flash-image",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "modalities": ["image", "text"],
        "image_config": {
            "aspect_ratio": "1:1"
        }
    }
    
    print(f"Generating image for {character_name}...")
    
    try:
        response = requests.post(
            OPENROUTER_API_URL,
            headers=headers,
            json=payload,
            timeout=120
        )
        
        response.raise_for_status()
        data = response.json()
        
        # Extract image from chat/completions response
        if 'choices' in data and len(data['choices']) > 0:
            message = data['choices'][0].get('message', {})
            images = message.get('images', [])
            
            if images:
                image_info = images[0]
                image_url = image_info.get('image_url', {})
                b64_data = image_url.get('url', '')
                
                if b64_data:
                    # Parse base64 data URL
                    if b64_data.startswith("data:image"):
                        header, b64_body = b64_data.split(",", 1)
                        image_format = header.split("/")[1].split(";")[0]
                    else:
                        b64_body = b64_data
                        image_format = "png"
                    
                    # Decode and save image
                    image_bytes = base64.b64decode(b64_body)
                    
                    filename = f"{idx:02d}_{character_name.replace(' ', '_')}_reference.png"
                    filepath = os.path.join(OUTPUT_DIR, filename)
                    
                    with open(filepath, 'wb') as f:
                        f.write(image_bytes)
                    
                    print(f"  ✓ Saved: {filename} ({len(image_bytes)} bytes)")
                    return filepath
                else:
                    print(f"  ✗ No image URL in response")
                    return None
            else:
                content = message.get('content', '')
                print(f"  ✗ No images in response. Content: {content[:200]}")
                return None
        else:
            print(f"  ✗ Invalid response structure")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"  ✗ API error: {e}")
        return None
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return None

def generate_combined_sheet(characters):
    """Generate a combined reference sheet with all characters"""
    character_names = [c['character_name'] for c in characters]
    
    prompt = f"""Victorian manga character reference sheet featuring multiple characters from The Picture of Dorian Gray: {', '.join(character_names)}. 
Grid layout showing all characters in a single image, clean presentation, consistent art style, professional manga character reference design."""
    
    print("Generating combined reference sheet...")
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/g-manga",
        "X-Title": "Character Reference Generator"
    }
    
    payload = {
        "model": "google/gemini-2.5-flash-image",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "modalities": ["image", "text"],
        "image_config": {
            "aspect_ratio": "1:1"
        }
    }
    
    try:
        response = requests.post(
            OPENROUTER_API_URL,
            headers=headers,
            json=payload,
            timeout=120
        )
        
        response.raise_for_status()
        data = response.json()
        
        if 'choices' in data and len(data['choices']) > 0:
            message = data['choices'][0].get('message', {})
            images = message.get('images', [])
            
            if images:
                image_info = images[0]
                image_url = image_info.get('image_url', {})
                b64_data = image_url.get('url', '')
                
                if b64_data:
                    if b64_data.startswith("data:image"):
                        header, b64_body = b64_data.split(",", 1)
                    else:
                        b64_body = b64_data
                    
                    image_bytes = base64.b64decode(b64_body)
                    
                    filepath = os.path.join(OUTPUT_DIR, "99_combined_reference_sheet.png")
                    
                    with open(filepath, 'wb') as f:
                        f.write(image_bytes)
                    
                    print(f"  ✓ Saved: 99_combined_reference_sheet.png ({len(image_bytes)} bytes)")
                    return filepath
                    
    except Exception as e:
        print(f"  ✗ Error generating combined sheet: {e}")
        return None
    
    return None

def main():
    """Main function to generate all character reference images"""
    with open(INPUT_FILE, 'r') as f:
        characters = json.load(f)
    
    print(f"Loaded {len(characters)} characters")
    print(f"Output directory: {OUTPUT_DIR}")
    print()
    
    generated_count = 0
    
    # Generate images for all characters
    for idx, character in enumerate(characters, 1):
        character_name = character['character_name']
        prompt = generate_prompt(character)
        
        print(f"Character {idx}/{len(characters)}: {character_name}")
        
        filepath = generate_image(prompt, character_name, idx)
        
        if filepath:
            generated_count += 1
        
        # Small delay between requests
        if idx < len(characters):
            time.sleep(2)
        print()
    
    # Generate combined reference sheet
    print("Generating combined reference sheet...")
    combined_path = generate_combined_sheet(characters)
    if combined_path:
        generated_count += 1
    print()
    
    print(f"\n{'='*60}")
    print(f"COMPLETE: Generated {generated_count} character reference images")
    print(f"  - Individual character sheets: {len(characters)}")
    print(f"  - Combined reference sheet: 1")
    print(f"{'='*60}")
    print(f"\nOutput directory: {OUTPUT_DIR}")
    
    # List generated files
    print(f"\nGenerated files:")
    for f in sorted(os.listdir(OUTPUT_DIR)):
        if f.endswith('.png'):
            filepath = os.path.join(OUTPUT_DIR, f)
            size = os.path.getsize(filepath) / 1024
            print(f"  - {f} ({size:.1f} KB)")

if __name__ == "__main__":
    import time
    main()
