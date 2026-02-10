"""
Integration Test - Stage 9: Output
Tests all output exporters (PDF, CBZ, Image, Metadata).
"""

import sys
sys.path.insert(0, '/home/clawd/projects/g-manga/src')
sys.path.insert(0, '/home/clawd/projects/g-manga/src/stage9_output')
sys.path.insert(0, '/home/clawd/projects/g-manga/src/stage9_output/exporters')

import os
import json
import tempfile
import shutil
from typing import Dict, Any
from PIL import Image


# Import exporters
from exporters.images import ImageExporter, create_image_exporter
from exporters.metadata import MetadataExporter, create_metadata_exporter


def create_test_project(test_dir: str) -> str:
    """Create a test project structure."""
    os.makedirs(os.path.join(test_dir, "output"), exist_ok=True)
    os.makedirs(os.path.join(test_dir, "intermediate"), exist_ok=True)

    # Create test config
    config = {
        "project_id": "test-output-project",
        "project_name": "Test Output Project",
        "metadata": {
            "title": "The Picture of Dorian Gray",
            "author": "Oscar Wilde",
            "source_url": "https://www.gutenberg.org/files/174/174-0.txt",
            "year": 1890,
            "language": "en",
            "gutenberg_id": 174
        },
        "style": {
            "reading_direction": "left_to_right",
            "line_weight": "medium",
            "shading": "screen_tones"
        },
        "created_at": "2026-02-06T10:00:00Z"
    }

    with open(os.path.join(test_dir, "config.json"), 'w') as f:
        json.dump(config, f)

    # Create test state
    state = {
        "stages_completed": [
            "input",
            "preprocessing",
            "story_planning",
            "character_design",
            "panel_generation",
            "image_generation",
            "layout_assembly",
            "post_processing",
            "output"
        ],
        "current_stage": "output",
        "progress": 1.0
    }

    with open(os.path.join(test_dir, "state.json"), 'w') as f:
        json.dump(state, f)

    # Create test chapters
    chapters = [
        {
            "id": "chapter-1",
            "chapter_number": 1,
            "title": "The Studio",
            "start_line": 0,
            "end_line": 100
        },
        {
            "id": "chapter-2",
            "chapter_number": 2,
            "title": "The Portrait",
            "start_line": 100,
            "end_line": 200
        }
    ]

    with open(os.path.join(test_dir, "intermediate", "chapters.json"), 'w') as f:
        json.dump(chapters, f)

    # Create test characters
    characters = [
        {
            "id": "char-001",
            "name": "Basil Hallward",
            "aliases": ["Basil", "the artist"],
            "appearance": {
                "age": "late 20s",
                "hair": "dark, neatly kept",
                "build": "lean",
                "clothing": "painter's smock"
            }
        },
        {
            "id": "char-002",
            "name": "Lord Henry Wotton",
            "aliases": ["Lord Henry", "Henry"],
            "appearance": {
                "age": "early 30s",
                "hair": "auburn",
                "build": "tall",
                "clothing": "elegant suit"
            }
        }
    ]

    with open(os.path.join(test_dir, "intermediate", "characters.json"), 'w') as f:
        json.dump(characters, f)

    # Create test storyboard
    storyboard = {
        "pages": [
            {
                "page_number": 1,
                "panels": [
                    {
                        "panel_id": "p1-1",
                        "type": "establishing",
                        "description": "Wide shot of art studio"
                    },
                    {
                        "panel_id": "p1-2",
                        "type": "medium",
                        "description": "Basil at his easel"
                    }
                ]
            },
            {
                "page_number": 2,
                "panels": [
                    {
                        "panel_id": "p2-1",
                        "type": "close_up",
                        "description": "Portrait of Dorian"
                    }
                ]
            }
        ]
    }

    with open(os.path.join(test_dir, "intermediate", "storyboard.json"), 'w') as f:
        json.dump(storyboard, f)

    return test_dir


def create_test_pages(test_dir: str, num_pages: int = 3) -> list:
    """Create test page images."""
    pages_dir = os.path.join(test_dir, "output", "pages")
    os.makedirs(pages_dir, exist_ok=True)

    page_paths = []

    for i in range(1, num_pages + 1):
        # Create a simple colored image as test page
        img = Image.new('RGB', (2480, 3508), color=(255 - i * 30, 200, 150 + i * 20))
        
        # Add some text
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        draw.text((100, 100), f"Test Page {i}", fill=(0, 0, 0))
        
        page_path = os.path.join(pages_dir, f"page_{i:03d}.png")
        img.save(page_path)
        page_paths.append(page_path)

    return page_paths


def test_image_exporter():
    """Test Image Exporter."""
    print("\n" + "=" * 70)
    print("TEST: Image Exporter")
    print("=" * 70)

    test_dir = tempfile.mkdtemp(prefix="g-manga-image-test-")
    output_dir = os.path.join(test_dir, "output")

    try:
        # Create test project
        create_test_project(test_dir)
        test_pages = create_test_pages(test_dir, num_pages=3)

        # Create exporter
        print("[Test] Creating image exporter...")
        exporter = create_image_exporter(
            format="png",
            quality=85,
            optimize=True
        )
        print(f"✓ Image exporter created")
        print(f"  Format: {exporter.config.format.value}")
        print(f"  Quality: {exporter.config.quality.name}")

        # Get export info
        print("\n[Test] Getting image export info...")
        info = exporter.get_export_info()
        print(f"✓ Export info:")
        print(f"  Image format: {info['image_format']}")
        print(f"  Optimize: {info['optimize']}")

        # Test single page export
        print("\n[Test] Exporting single page...")
        single_output = exporter.export_page(
            page_path=test_pages[0],
            output_dir=output_dir,
            filename="exported_page_01.png"
        )
        print(f"✓ Single page exported to: {single_output}")

        # Test multiple pages export
        print("\n[Test] Exporting multiple pages...")
        exported = exporter.export_pages(
            page_paths=test_pages,
            output_dir=output_dir,
            filename_prefix="exported"
        )
        print(f"✓ Exported {len(exported)} pages")

        # Verify files
        print("\n[Test] Verifying exported files...")
        for path in exported:
            if os.path.exists(path):
                size = os.path.getsize(path)
                print(f"  ✓ {os.path.basename(path)}: {size:,} bytes")
            else:
                print(f"  ✗ {os.path.basename(path)}: NOT FOUND")

        # Test config update
        print("\n[Test] Testing config update...")
        exporter.update_config(format="jpg", thumbnail_size=(300, 425))
        info = exporter.get_export_info()
        print(f"✓ Updated config:")
        print(f"  Image format: {info['image_format']}")
        print(f"  Thumbnail size: {info['thumbnail_size']}")

        print("\n✅ Image Exporter - PASSED")
        return True

    except Exception as e:
        print(f"\n❌ Image Exporter FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        shutil.rmtree(test_dir)


def test_metadata_exporter():
    """Test Metadata Exporter."""
    print("\n" + "=" * 70)
    print("TEST: Metadata Exporter")
    print("=" * 70)

    test_dir = tempfile.mkdtemp(prefix="g-manga-metadata-test-")
    output_dir = os.path.join(test_dir, "output")

    try:
        # Create test project
        create_test_project(test_dir)

        # Create exporter
        print("[Test] Creating metadata exporter...")
        exporter = create_metadata_exporter(test_dir)
        print(f"✓ Metadata exporter created")

        # Get export info
        print("\n[Test] Getting export info...")
        info = exporter.get_export_info()
        print(f"✓ Export info:")
        print(f"  Project ID: {info['project_id']}")
        print(f"  Total chapters: {info['total_chapters']}")
        print(f"  Total characters: {info['total_characters']}")

        # Test JSON export
        print("\n[Test] Exporting metadata as JSON...")
        json_path = exporter.export_metadata(
            output_dir=output_dir,
            format_type="json"
        )
        print(f"✓ JSON exported to: {json_path}")

        # Test CSV export
        print("\n[Test] Exporting metadata as CSV...")
        csv_path = exporter.export_metadata(
            output_dir=output_dir,
            format_type="csv"
        )
        print(f"✓ CSV exported to: {csv_path}")

        # Test character sheet export
        print("\n[Test] Exporting character sheet...")
        char_path = exporter.export_character_sheet()
        print(f"✓ Character sheet exported to: {char_path}")

        # Test story summary export
        print("\n[Test] Exporting story summary...")
        summary_path = exporter.export_story_summary()
        print(f"✓ Story summary exported to: {summary_path}")

        # Verify exports
        print("\n[Test] Verifying exports...")
        for path in [json_path, csv_path, char_path, summary_path]:
            if os.path.exists(path):
                size = os.path.getsize(path)
                print(f"  ✓ {os.path.basename(path)}: {size:,} bytes")
            else:
                print(f"  ✗ {os.path.basename(path)}: NOT FOUND")

        # Read and verify JSON
        print("\n[Test] Verifying JSON content...")
        with open(json_path, 'r') as f:
            data = json.load(f)

        print(f"✓ JSON verified:")
        print(f"  Project title: {data['project_info']['title']}")
        print(f"  Statistics: {data['statistics']}")
        print(f"  Characters: {len(data['characters'])}")

        print("\n✅ Metadata Exporter - PASSED")
        return True

    except Exception as e:
        print(f"\n❌ Metadata Exporter FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        shutil.rmtree(test_dir)


def test_pdf_structure():
    """Test PDF exporter structure (without actual PDF generation)."""
    print("\n" + "=" * 70)
    print("TEST: PDF Exporter (Structure)")
    print("=" * 70)

    test_dir = tempfile.mkdtemp(prefix="g-manga-pdf-test-")

    try:
        from exporters.pdf import PDFExporter

        print("[Test] Creating PDF exporter...")
        exporter = PDFExporter()
        print(f"✓ PDF exporter created")
        print(f"  Has export_pdf: {hasattr(exporter, 'export_pdf')}")
        print(f"  Has config: {hasattr(exporter, 'config')}")

        print("\n✅ PDF Exporter Structure - PASSED")
        return True

    except Exception as e:
        print(f"\n❌ PDF Exporter Structure FAILED: {e}")
        return False

    finally:
        shutil.rmtree(test_dir)


def test_cbz_structure():
    """Test CBZ exporter structure (without actual CBZ generation)."""
    print("\n" + "=" * 70)
    print("TEST: CBZ Exporter (Structure)")
    print("=" * 70)

    test_dir = tempfile.mkdtemp(prefix="g-manga-cbz-test-")

    try:
        from exporters.cbz import CBZExporter

        print("[Test] Creating CBZ exporter...")
        exporter = CBZExporter()
        print(f"✓ CBZ exporter created")
        print(f"  Has export_cbz: {hasattr(exporter, 'export_cbz')}")
        print(f"  Has config: {hasattr(exporter, 'config')}")

        print("\n✅ CBZ Exporter Structure - PASSED")
        return True

    except Exception as e:
        print(f"\n❌ CBZ Exporter Structure FAILED: {e}")
        return False

    finally:
        shutil.rmtree(test_dir)


def main():
    """Run all output stage tests."""
    print("=" * 70)
    print("G-MANGA STAGE 9: OUTPUT - INTEGRATION TESTS")
    print("=" * 70)

    results = {}

    # Run tests
    results['Image Exporter'] = test_image_exporter()
    results['Metadata Exporter'] = test_metadata_exporter()
    results['PDF Exporter Structure'] = test_pdf_structure()
    results['CBZ Exporter Structure'] = test_cbz_structure()

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {name}: {status}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All Stage 9 Output tests PASSED!")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed")

    print("=" * 70)

    return passed == total


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
