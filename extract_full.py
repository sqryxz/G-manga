import json, sys
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
        chars = extractor.extract_characters(text, scene.get('id', ''), scene.get('number', 1))
        all_chars.extend(chars)
        if (i+1) % 5 == 0:
            print(f"Processed {i+1}/{len(scenes_10)} scenes...", flush=True)

# Deduplicate by name
seen = set()
unique_chars = []
for c in all_chars:
    name = c.get('name', '').strip().lower()
    if name and name not in seen:
        seen.add(name)
        unique_chars.append(c)

# Save to output file
output_path = 'output/projects/picture-of-dorian-gray-20260213-20260213/intermediate/characters.json'
with open(output_path, 'w') as f:
    json.dump(unique_chars, f, indent=2)

print(f"Saved {len(unique_chars)} unique characters to {output_path}", flush=True)
