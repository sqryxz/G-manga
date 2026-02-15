import json, sys, time
sys.path.insert(0, 'src')
from common.llm_factory import create_llm_client
from stage4_character_design.character_extractor import CharacterExtractor

llm = create_llm_client(provider='openrouter', model='openai/gpt-4o-mini')
extractor = CharacterExtractor(llm_client=llm)

with open('output/projects/picture-of-dorian-gray-20260213-20260213/intermediate/scenes.json') as f:
    scenes = json.load(f).get('scenes', [])

# Filter first 10 chapters
scenes_10 = [s for s in scenes if s.get('chapter_id', '').replace('chapter-', '').isdigit() and int(s.get('chapter_id', '').replace('chapter-', '')) <= 10]

print(f"Processing {len(scenes_10)} scenes from first 10 chapters...", flush=True)

all_chars = []
for i, scene in enumerate(scenes_10):
    text = scene.get('text', '')[:1500]
    if text:
        try:
            chars = extractor.extract_characters(text, scene.get('id', ''), scene.get('number', 1))
            all_chars.extend(chars)
        except Exception as e:
            print(f"Error on scene {i}: {e}", flush=True)
        if (i+1) % 5 == 0:
            print(f"Progress: {i+1}/{len(scenes_10)} scenes", flush=True)
        time.sleep(0.5)  # Rate limiting

# Deduplicate by name
seen = {}
unique_chars = []
for c in all_chars:
    name = c.get('name', '').strip()
    if name:
        name_lower = name.lower()
        if name_lower not in seen:
            seen[name_lower] = c
            unique_chars.append(c)

# Save to output file
output_path = 'output/projects/picture-of-dorian-gray-20260213-20260213/intermediate/characters.json'
with open(output_path, 'w') as f:
    json.dump(unique_chars, f, indent=2)

print(f"Done! Saved {len(unique_chars)} unique characters to {output_path}", flush=True)
