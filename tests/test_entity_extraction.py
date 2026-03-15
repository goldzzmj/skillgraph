"""
Test entity extraction functionality
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent.parent / 'src'
sys.path.insert(0, str(src_path))

from skillgraph.parser import SkillParser
from skillgraph.graphrag import EntityExtractor
from skillgraph.graphrag.models import EntityType


def test_entity_types():
    """Test extraction of different entity types."""
    print("="*60)
    print("Entity Extraction Test")
    print("="*60)

    # Test with malicious skill
    example_file = Path(__file__).parent.parent.parent / 'examples' / 'malicious_skill.md'

    # Alternative: use Path.cwd() / 'examples' / 'malicious_skill.md'
    if not example_file.exists():
        example_file = Path.cwd() / 'examples' / 'malicious_skill.md'

    if not example_file.exists():
        print(f"\n[X] Example file not found: {example_file}")
        print(f"    Current directory: {Path.cwd()}")
        return

    print(f"\n[1] Parsing skill file...")

    try:
        parser = SkillParser()
        skill = parser.parse_file(str(example_file))
        print(f"   [OK] Parsed skill: {skill.name}")
        print(f"   - Sections: {len(skill.sections)}")
        print(f"   - Code blocks: {len(skill.code_blocks)}")
    except Exception as e:
        print(f"   [ERROR] Parse error: {e}")
        return

    # Test entity extraction
    print("\n[2] Testing entity extraction...")

    try:
        extractor = EntityExtractor()

        entities = extractor.extract(
            '',
            skill.sections,
            skill.code_blocks
        )

        print(f"   [OK] Extracted {len(entities)} entities")

        # Check entity types
        entity_types = set(e.type.value for e in entities)

        print(f"\n[3] Entity types found:")
        for entity_type in sorted(entity_types):
            count = sum(1 for e in entities if e.type.value == entity_type)
            print(f"   - {entity_type}: {count}")

        # Validate expected types are present
        expected_types = ['network', 'file', 'permission', 'api']

        print(f"\n[4] Validating expected entity types:")

        for expected_type in expected_types:
            if expected_type in entity_types:
                print(f"   [OK] {expected_type}: found")
            else:
                print(f"   [WARN] {expected_type}: not found")

        # Show sample entities
        print(f"\n[5] Sample entities:")

        for i, entity in enumerate(entities[:5], 1):
            print(f"   {i}. [{entity.type.value}] {entity.name}")
            print(f"      Risk: {entity.risk_score:.2f}")
            print(f"      Desc: {entity.description[:60]}...")

    except Exception as e:
        print(f"   [ERROR] Extraction error: {e}")
        import traceback
        traceback.print_exc()
        return

    # Test relationship extraction
    print("\n[6] Testing relationship extraction...")

    try:
        # Combine sections into content string
        content = "\n".join([
            section.content if hasattr(section, 'content') else str(section)
            for section in skill.sections
        ])

        relationships = extractor.extract_relationships(
            entities,
            content
        )

        print(f"   [OK] Extracted {len(relationships)} relationships")

        # Show sample relationships
        print(f"\n[7] Sample relationships:")

        for i, rel_dict in enumerate(relationships[:3], 1):
            print(f"   {i}. {rel_dict['type']}")
            print(f"      Source: {rel_dict['source_id']}")
            print(f"      Target: {rel_dict['target_id']}")
            print(f"      Confidence: {rel_dict.get('confidence', 1.0):.2f}")

    except Exception as e:
        print(f"   [ERROR] Relationship extraction error: {e}")
        import traceback
        traceback.print_exc()
        return

    # Final summary
    print("\n" + "="*60)
    print("[OK] Entity extraction test complete!")
    print("="*60)


def test_edge_cases():
    """Test edge cases for entity extraction."""
    print("\n" + "="*60)
    print("Edge Cases Test")
    print("="*60)

    # Test with minimal content
    print("\n[1] Testing with minimal content...")

    try:
        extractor = EntityExtractor()
        entities = extractor.extract("", [], [])

        print(f"   [OK] Extracted {len(entities)} entities from minimal content")

        if len(entities) == 0:
            print(f"   [OK] Correctly handled empty content")
        else:
            print(f"   [INFO] Found {len(entities)} entities in minimal content")

    except Exception as e:
        print(f"   [WARN] Edge case error: {e}")


if __name__ == '__main__':
    test_entity_types()
    test_edge_cases()
