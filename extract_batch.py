import json, sys
sys.path.insert(0, 'src')
from common.llm_factory import create_llm_client

llm = create_llm_client(provider='openrouter', model='openai/gpt-4o-mini')

with open('output/projects/picture-of-dorian-gray-20260213-20260213/intermediate/scenes.json') as f:
    scenes = json.load(f).get('scenes', [])

scenes_10 = [s for s in scenes if s.get('chapter_id', '').replace('chapter-', '').isdigit() and int(s.get('chapter_id', '').replace('chapter-', '')) <= 10]

print(f"Processing {len(scenes_10)} scenes...", flush=True)

all_chars = []
for i, scene in enumerate(scenes_10):
    text = scene.get('text', '')[:1500]
    if not text:
        continue
        
    prompt = f"""Extract all character names from this text. Return as JSON array with format:
[{{"name": "Character Name", "role": "protagonist|deuteragonist|supporting|minor|background"}}]

Text:
{text[:1200]}"""

    try:
        response = llm.complete(prompt, max_tokens=200)
        content = response.content if hasattr(response, 'content') else str(response)
        
        # Parse JSON from response
        import re
        json_match = re.search(r'\[.*\]', content, re.DOTALL)
        if json_match:
            chars = json.loads(json_match.group())
            for c in chars:
                c['scene_id'] = scene.get('id')
            all_chars.extend(chars)
            print(f"Scene {i+1}: Found {len(chars)} characters", flush=True)
        else:
            print(f"Scene {i+1}: No JSON found", flush=True)
    except Exception as e:
        print(f"Scene {i+1} error: {e}", flush=True)

# Deduplicate
seen = {}
unique_chars = []
for c in all_chars:
    name = c.get('name', '').strip()
    if name:
        name_lower = name.lower()
        if name_lower not in seen:
            seen[name_lower] = c
            unique_chars.append(c)

# Save
output_path = 'output/projects/picture-of-dorian-gray-20260213-20260213/intermediate/characters.json'
with open(output_path, 'w') as f:
    json.dump(unique_chars, f, indent=2)

print(f"Done! Saved {len(unique_chars)} unique characters", flush=True)
