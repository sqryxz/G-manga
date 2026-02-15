#!/usr/bin/env python3
"""
Generate character reference sheet images using OpenRouter API - TEST VERSION (first 2 characters)
Uses the correct /chat/completions endpoint with modalities
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
                    print(f"  Response: {json.dumps(data, indent=2)[:500]}")
                    return None
            else:
                content = message.get('content', '')
                print(f"  ✗ No images in response. Content: {content[:200]}")
                return None
        else:
            print(f"  ✗ Invalid response structure")
            print(f"  Response: {json.dumps(data, indent=2)[:500]}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"  ✗ API error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"  Response: {e.response.text[:300]}")
        return None
    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Main function - TEST with first 2 characters only"""
    with open(INPUT_FILE, 'r') as f:
        characters = json.load(f)
    
    # TEST: Only first 2 characters
    test_characters = characters[:2]
    
    print(f"TEST MODE: Generating images for first {len(test_characters)} characters")
    print(f"Output directory: {OUTPUT_DIR}")
    print()
    
    generated_count = 0
    
    for idx, character in enumerate(test_characters, 1):
        character_name = character['character_name']
        prompt = generate_prompt(character)
        
        print(f"Character {idx}/{len(test_characters)}: {character_name}")
        
        filepath = generate_image(prompt, character_name, idx)
        
        if filepath:
            generated_count += 1
        print()
    
    print(f"\n{'='*60}")
    print(f"TEST COMPLETE: Generated {generated_count} character reference images")
    print(f"{'='*60}")
    print(f"\nPlease review the images at: {OUTPUT_DIR}")
    print("If quality is acceptable, run the full version to generate all characters.")

if __name__ == "__main__":
    main()
