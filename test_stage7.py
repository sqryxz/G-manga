#!/usr/bin/env python3
"""Test script to run Stage 7 with existing panels."""
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, '/home/clawd/projects/g-manga/src')

from stage7_layout.panel_arranger import PanelArranger
from stage7_layout.page_composer import PageComposer, PanelFitting
from stage7_layout.layout_templates import LayoutTemplateLibrary
from stage7_layout.comic_assembler import ComicAssembler
import json

# Use the existing project
project_id = "picture-of-dorian-gray-20260212-20260212"
project_dir = f"/home/clawd/projects/g-manga/output/projects/{project_id}"
panels_dir = os.path.join(project_dir, "output", "panels")
comic_pages_dir = os.path.join(project_dir, "output", "comic_pages")

# Get panel files
panel_files = sorted([f for f in os.listdir(panels_dir) if f.endswith('.png')])
panel_ids = [f.replace('.png', '') for f in panel_files]

print(f"Found {len(panel_ids)} panels")
print(f"Project dir: {project_dir}")
print(f"Panels dir: {panels_dir}")
print(f"Output dir: {comic_pages_dir}")

# Create output directory
os.makedirs(comic_pages_dir, exist_ok=True)

# Create components
arranger = PanelArranger()
composer = PageComposer()
assembler = ComicAssembler(project_dir=project_dir)

# Create mock panel types (all "medium" for now)
panel_types = {pid: "medium" for pid in panel_ids}

# Create panel fittings for arrangement
library = LayoutTemplateLibrary()

# Since we have 60 panels and max template is 8 panels, we need multiple pages
# Use 6-panel comic as template
template = library.get_template("6-panel-comic")
print(f"Using template: {template.name} (max 6 panels per page)")

# Create multiple pages - distribute panels across pages
PANELS_PER_PAGE = 6
pages_composed = 0
all_metadata = []

for page_num, i in enumerate(range(0, len(panel_ids), PANELS_PER_PAGE), start=1):
    page_panel_ids = panel_ids[i:i + PANELS_PER_PAGE]
    print(f"\n[Page {page_num}] Composing with {len(page_panel_ids)} panels: {page_panel_ids[0]}...")
    
    # Create mock fittings for this page
    mock_fittings = []
    for j, slot in enumerate(sorted(template.slots, key=lambda s: s.order)):
        if j < len(page_panel_ids):
            fitting = PanelFitting(
                panel_id=page_panel_ids[j],
                slot_id=slot.slot_id,
                slot=slot,
                panel_aspect_ratio=1.0,
                slot_aspect_ratio=slot.width / slot.height,
                gutter_size=template.gutter_size,
                fit_mode="fit",
                scale_factor=1.0
            )
            mock_fittings.append(fitting)

    # Arrange panels for this page
    arrangement = arranger.arrange_panels(mock_fittings, panel_types)
    
    # Compose page
    page_layout = composer.compose_page(page_panel_ids, preferred_template="6-panel-comic")
    
    # Load panel images for this page
    page_panel_images = assembler.load_all_panel_images(page_panel_ids)
    
    # Assemble page
    comic_page = assembler.assemble_page(
        panel_images=page_panel_images,
        composition=page_layout,
        arrangement=arrangement,
        panel_fittings=page_layout.panel_fittings
    )
    
    # Save page
    saved_path = assembler.save_page(comic_page, comic_pages_dir, page_number=page_num)
    print(f"   Saved: {saved_path}")
    
    # Save individual metadata
    metadata = {
        "page_number": comic_page.page_number,
        "width": comic_page.width,
        "height": comic_page.height,
        "panel_count": comic_page.panel_count,
        "reading_order": comic_page.reading_order,
        "panel_positions": {k: list(v) for k, v in comic_page.panel_positions.items()},
        "saved_path": saved_path
    }
    metadata_path = os.path.join(comic_pages_dir, f"page_{page_num:03d}_metadata.json")
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    all_metadata.append(metadata)
    pages_composed += 1

# Save overall metadata
overall_metadata = {
    "total_panels": len(panel_ids),
    "panels_per_page": PANELS_PER_PAGE,
    "total_pages": pages_composed,
    "pages": all_metadata
}
overall_path = os.path.join(comic_pages_dir, "comic_metadata.json")
with open(overall_path, 'w') as f:
    json.dump(overall_metadata, f, indent=2)

print("\n" + "="*50)
print(f"SUCCESS: {pages_composed} pages saved to {comic_pages_dir}")
print("="*50)
