#!/usr/bin/env python3
"""
Test OpenRouter image generation with a single character
"""
import json
import os
import requests
import base64
from pathlib import Path

# Configuration
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OUTPUT_DIR = Path("/home/clawd/projects/g-manga/output/projects/picture-of-dorian-gray-20260213-20260213/output/character_refs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Get API key
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    print("ERROR: OPENROUTER_API_KEY not set")
    exit(1)

# Test with a simple prompt
headers = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://github.com/g-manga",
    "X-Title": "Character Reference Test"
}

payload = {
    "model": "google/gemini-2.5-flash-image",
    "messages": [
        {
            "role": "user",
            "content": "Simple manga character reference sheet for Dorian Gray: young man, black hair, blue eyes, Victorian clothing, front view, side view, 3/4 view, turnaround sheet"
        }
    ],
    "modalities": ["image", "text"],
    "image_config": {
        "aspect_ratio": "1:1"
    }
}

print("Testing OpenRouter API with google/gemini-2.5-flash-image...")
print(f"URL: {OPENROUTER_API_URL}")
print(f"API Key: {OPENROUTER_API_KEY[:15]}...")

try:
    response = requests.post(
        OPENROUTER_API_URL,
        headers=headers,
        json=payload,
        timeout=60
    )
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✓ Success!")
        print(f"Response: {json.dumps(data, indent=2)[:1000]}")
        
        # Try to extract image
        if 'choices' in data and len(data['choices']) > 0:
            message = data['choices'][0].get('message', {})
            images = message.get('images', [])
            if images:
                print(f"\n✓ Images found: {len(images)}")
    else:
        print(f"\n✗ Error: {response.text[:500]}")
        
except Exception as e:
    print(f"\n✗ Exception: {e}")
