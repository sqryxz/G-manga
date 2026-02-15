#!/usr/bin/env python3
"""
Character Reference Sheet Generator for Manga/Comic Projects
Generates detailed character reference sheets based on character data.
"""

import json
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent
CHARACTERS_INPUT_PATH = BASE_DIR / "output/projects/picture-of-dorian-gray-20260213-20260213/intermediate/characters.json"
OUTPUT_PATH = BASE_DIR / "output/projects/picture-of-dorian-gray-20260213-20260213/intermediate/character_reference_sheets.json"


def generate_reference_sheet(character):
    """Generate a detailed character reference sheet from character data."""
    
    name = character.get("name", "Unknown")
    hair = character.get("hair", {})
    eyes = character.get("eyes", {})
    personality = character.get("personality", [])
    
    # Build reference sheet based on character
    ref_sheet = {
        "character_name": name,
        "physical_appearance": {
            "age": character.get("age", "unknown"),
            "gender": character.get("gender", "unknown"),
            "height": character.get("height", "average"),
            "build": character.get("build", "average"),
            "skin_tone": character.get("skin_tone", "fair"),
            "hair": {
                "color": hair.get("color", "brown"),
                "style": hair.get("style", "short"),
                "length": hair.get("length", "short"),
                "texture": "straight" if hair.get("color") != "red" else "wavy"
            },
            "eyes": {
                "color": eyes.get("color", "brown"),
                "shape": eyes.get("shape", "round"),
                "expression": get_eye_expression(personality)
            },
            "distinctive_features": character.get("distinguishing_features", []),
            "typical_expressions": get_expressions(name, personality),
            "posture_and_bearing": get_posture(name)
        },
        "costume_design": {
            "everyday_attire": character.get("clothing", "typical Victorian attire"),
            "variations": get_costume_variations(name),
            "accessories": get_accessories(name),
            "footwear": get_footwear(name),
            "props": get_props(name)
        },
        "color_palette": {
            "hair": [hair.get("color", "brown")],
            "skin": [character.get("skin_tone", "fair")],
            "eyes": [eyes.get("color", "brown")],
            "primary_clothing": get_clothing_colors(name),
            "accessories_colors": get_accessory_colors(name)
        },
        "turnaround_views": {
            "front_view": f"Full frontal view showing {name}'s face with characteristic expression, symmetrical features",
            "side_view": f"Profile view showing hair texture, ear shape, and posture characteristic of {name}",
            "back_view": f"Back view showing hair from behind, clothing silhouette, and overall silhouette",
            "three_quarter_view": f"3/4 view - most characteristic angle, shows depth of features and expression"
        },
        "signature_gestures": get_gestures(name, personality),
        "emotional_range": get_emotional_range(name, personality),
        "consistency_notes": get_consistency_notes(name)
    }
    
    return ref_sheet


def get_eye_expression(personality):
    """Determine eye expression based on personality."""
    expressions = []
    if "charming" in personality or "cynical" in personality:
        expressions.append("penetrating, captivating gaze")
    if "sincere" in personality or "humble" in personality:
        expressions.append("honest, warm eyes")
    if "manipulative" in personality:
        expressions.append("calculating, knowing look")
    if "dramatic" in personality:
        expressions.append("large, expressive eyes")
    return expressions[0] if expressions else "typical Victorian gentle expression"


def get_expressions(name, personality):
    """Get typical expressions for character."""
    expressions = []
    
    if name == "Dorian Gray":
        expressions = [
            "Innocent, angelic smile when first introduced",
            "Charming, slightly mysterious smile",
            "Haunted expression as corruption sets in",
            "Cold, distant gaze in later chapters",
            "Self-satisfied smirk when admiring portrait"
        ]
    elif name == "Lord Henry Wotton":
        expressions = [
            "Sardonic, knowing smirk",
            "Raised eyebrow of amusement",
            "Contemplative, philosophical expression",
            "Predatory smile when manipulating others"
        ]
    elif name == "Basil Hallward":
        expressions = [
            "Sincere, devoted expression when looking at Dorian",
            "Concerned frown when worried",
            "Passionate expression when discussing art"
        ]
    elif name == "Sibyl Vane":
        expressions = [
            "Dramatic, theatrical expressions",
                    "Romantic, dreamy gaze",
                    "Heartbroken despair",
                    "Innocent wonder"
        ]
    else:
        expressions = [
            "Neutral, composed expression",
            "Occasional smile in social situations",
            "Contemplative when alone"
        ]
    
    return expressions


def get_posture(name):
    """Get posture and bearing description."""
    postures = {
        "Dorian Gray": "Erect, graceful, almost ethereal posture; moves with unnatural elegance",
        "Lord Henry Wotton": "Elegant slouch of aristocracy; leisurely, controlled movements",
        "Basil Hallward": "Lean forward in artistic enthusiasm; hands often gesturing",
        "Sibyl Vane": "Dramatic poses from acting training; expressive body language",
        "James Vane": "Sailor's rigid posture; sturdy, determined stance"
    }
    return postures.get(name, "Typical Victorian upright posture")


def get_costume_variations(name):
    """Get costume variations for character."""
    variations = {
        "Dorian Gray": [
            "Formal evening wear - black tailcoat, white waistcoat",
            "Day suit - fashionable morning coat",
            "Italian costume for opera (Chapter 8)",
            "Dark, mysterious attire as corruption grows",
            "Working clothes when visiting opium dens"
        ],
        "Lord Henry Wotton": [
            "Morning suit for social calls",
            "Formal evening attire with elaborate cravat",
            "Country casual - shooting clothes",
            "Comfortable house coat for private moments"
        ],
        "Basil Hallward": [
            "Artist smock with paint stains",
            "Gentleman's suit for social occasions",
            "Casual creative attire in studio"
        ],
        "Sibyl Vane": [
            "Theatrical costumes for stage roles",
            "Simple cotton dresses for everyday",
            "White dress for romantic scenes"
        ],
        "default": [
            "Formal Victorian attire",
            "Casual day clothes",
            "Evening social wear"
        ]
    }
    return variations.get(name, variations["default"])


def get_accessories(name):
    """Get accessories for character."""
    accessories = {
        "Lord Henry Wotton": ["Monocle", "Fine cravats", "Pocket watch", "Diamond ring"],
        "Dorian Gray": ["Occasional flowers in buttonhole", "Jeweled rings (later)", "Walking cane"],
        "Basil Hallward": ["Paintbrushes behind ear", "Sketchbook", "Artist's palette"],
        "Sibyl Vane": ["Dramatic costume jewelry for theater", "Simple hair ribbons"]
    }
    return accessories.get(name, ["Typical Victorian accessories"])


def get_footwear(name):
    """Get footwear for character."""
    footwear = {
        "Dorian Gray": "Polished black boots, fashionable leather shoes",
        "Lord Henry Wotton": "Fine leather boots, patent leather shoes for evenings",
        "James Vane": "Heavy sailor boots",
        "Basil Hallward": "Comfortable walking shoes, occasionally paint-stained"
    }
    return footwear.get(name, "Typical Victorian leather shoes")


def get_props(name):
    """Get props for character."""
    props = {
        "Dorian Gray": ["Portrait (central prop)", "Novels and books", "Opium pipe (later)"],
        "Lord Henry Wotton": [" cigarette holder", "Fine wines", "Books of philosophy"],
        "Basil Hallward": ["Sketchbook", "Paintbrushes", "Canvases"],
        "Sibyl Vane": ["Theater props for performances", "Letters from Dorian"]
    }
    return props.get(name, [])


def get_clothing_colors(name):
    """Get clothing color palette."""
    colors = {
        "Dorian Gray": ["Black", "White", "Cream", "Deep red (later)", "Dark colors (corruption)"],
        "Lord Henry Wotton": ["Black", "Gray", "White", "Burgundy"],
        "Basil Hallward": ["Earth tones", "Brown", "Gray", "Practical colors"],
        "Sibyl Vane": ["White", "Pastels", "Dramatic reds for theater"]
    }
    return colors.get(name, ["Black", "White", "Gray", "Earth tones"])


def get_accessory_colors(name):
    """Get accessory color palette."""
    colors = {
        "Lord Henry Wotton": ["Gold", "Diamond", "Emerald"],
        "Dorian Gray": ["Gold (later)", "Black onyx", "Ruby (later)"],
        "Sibyl Vane": ["Costume jewelry - gold and ruby"]
    }
    return colors.get(name, ["Gold", "Silver", "Black"])


def get_gestures(name, personality):
    """Get signature gestures for character."""
    gestures = {
        "Dorian Gray": [
            "Touching face when anxious",
            "Admiring reflection in mirrors",
            "Graceful, flowing hand movements",
            "Cold, distant gestures in later chapters"
        ],
        "Lord Henry Wotton": [
            "Tapping cigarette holder",
            "Raised eyebrow",
            "Leisure wave of hand",
            "Finger tapped against glass while speaking"
        ],
        "Basil Hallward": [
            "Gesturing passionately when discussing art",
            "Sketching motion with fingers",
            "Touching Dorian's shoulder affectionately"
        ],
        "Sibyl Vane": [
            "Dramatic hand gestures from acting",
            "Touching heart when emotional",
            "Large, theatrical movements"
        ],
        "James Vane": [
            "Clenched fists when angry",
            "Suspicious squinting",
            "Standing with arms crossed"
        ]
    }
    return gestures.get(name, ["Typical Victorian restrained gestures"])


def get_emotional_range(name, personality):
    """Get emotional range description."""
    if name == "Dorian Gray":
        return {
            "happy": "Radiant, almost supernatural beauty; infectious joy",
            "sad": "Melancholic, tragic beauty; withdrawn despair",
            "angry": "Rare cold fury, controlled and terrifying",
            "contemplative": "Deep introspection, staring at mirrors or portrait",
            "romantic": "Passionate but increasingly hollow romantic gestures",
            "corrupted": "Harsh, cynical expressions; hard eyes; cruel smile"
        }
    elif name == "Lord Henry Wotton":
        return {
            "happy": "Amused smirk, intellectual satisfaction",
            "sad": "Bored disdain, weary world-weariness",
            "angry": "Rare, controlled irritation behind smooth facade",
            "contemplative": "Philosophical musing, ironic observations",
            "romantic": "Cynical take on romance, views it as amusement",
            "corrupted": "Predatory satisfaction, manipulative pleasure"
        }
    elif name == "Basil Hallward":
        return {
            "happy": "Warm, genuine smile; artistic satisfaction",
            "sad": "Deep sorrow for Dorian's path; grief",
            "angry": "Righteous indignation defending art/morals",
            "contemplative": "Artist's eye analyzing beauty",
            "romantic": "Devoted, unspoken love for Dorian",
            "corrupted": "Confusion, horror at what Dorian becomes"
        }
    elif name == "Sibyl Vane":
        return {
            "happy": "Bubbly theatrical joy, romantic happiness",
            "sad": "Dramatic despair, broken-hearted tears",
            "angry": "Theatrical outrage, wounded pride",
            "contemplative": "Daydreaming romantic visions",
            "romantic": "All-consuming romantic passion",
            "corrupted": "Tragic, devastated by Dorian's rejection"
        }
    else:
        return {
            "happy": "Reserved Victorian happiness",
            "sad": "Composed melancholy",
            "angry": "Controlled Victorian restraint",
            "contemplative": "Thoughtful expression",
            "romantic": "Appropriate romantic interest",
            "corrupted": "Varies by character arc"
        }


def get_consistency_notes(name):
    """Get consistency notes for character."""
    notes = {
        "Dorian Gray": "CRITICAL: Dorian must maintain his extraordinary, almost supernatural beauty throughout. The contrast between his external beauty and internal corruption should be subtle. His appearance should subtly deteriorate only when comparing to earlier drawings - the portrait shows his true state. Hair should remain black, eyes blue, skin pale. Clothing becomes darker and more elaborate over time.",
        "Lord Henry Wotton": "Maintain the sardonic, knowing expression. Always elegant and well-dressed. Green eyes should convey intelligence and manipulation. The monocle is optional but distinctive when present.",
        "Basil Hallward": "Honest, sincere eyes should always convey genuine emotion. Hands should show artistic work (sometimes stained with paint). Lean, artistic build. Changes from hopeful to devastated in later chapters.",
        "Sibyl Vane": "Large, expressive eyes essential. Theatrical training evident in dramatic poses. Transforms from innocent romantic to tragic figure. Should look fragile and delicate.",
        "James Vane": "Weathered, sailor appearance. Suspicious blue eyes. Muscular build from seafaring. Protective posture toward sister, then vengeful."
    }
    return notes.get(name, f"Maintain consistent Victorian aesthetic. Age {name} appropriately. Ensure clothing and accessories reflect social status and era.")


def main():
    """Main function to generate character reference sheets."""
    
    print("=" * 60)
    print("Character Reference Sheet Generator (Manual Mode)")
    print("=" * 60)
    
    # Load characters
    print(f"\nLoading characters from: {CHARACTERS_INPUT_PATH}")
    if not CHARACTERS_INPUT_PATH.exists():
        print(f"Error: Characters file not found at {CHARACTERS_INPUT_PATH}")
        return 0
    
    with open(CHARACTERS_INPUT_PATH, 'r', encoding='utf-8') as f:
        characters = json.load(f)
    
    print(f"Loaded {len(characters)} characters.")
    
    # Generate reference sheets
    reference_sheets = []
    
    print("\nGenerating reference sheets...")
    print("-" * 40)
    
    for i, character in enumerate(characters, 1):
        char_name = character.get("name", "Unknown")
        print(f"\n[{i}/{len(characters)}] Processing: {char_name}")
        
        result = generate_reference_sheet(character)
        result["source_character"] = char_name
        reference_sheets.append(result)
        print(f"  ✓ Generated reference sheet")
    
    print("-" * 40)
    
    # Save results
    print(f"\nSaving {len(reference_sheets)} reference sheets to: {OUTPUT_PATH}")
    
    # Create output directory if needed
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(reference_sheets, f, indent=2, ensure_ascii=False)
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total characters: {len(characters)}")
    print(f"Reference sheets generated: {len(reference_sheets)}")
    print(f"Output saved to: {OUTPUT_PATH}")
    print("=" * 60)
    
    return len(reference_sheets)


if __name__ == "__main__":
    main()
