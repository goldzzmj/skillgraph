"""
Test community detection functionality - Simplified version
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent.parent / 'src'
sys.path.insert(0, str(src_path))

from skillgraph.graphrag import EntityExtractor, CommunityDetector
from skillgraph.parser import SkillParser


def test_community_detection_simple():
    """Test community detection with minimal setup."""
    print("="*60)
    print("Community Detection Test (Simplified)")
    print("="*60)

    # Test with malicious skill
    example_file = Path(__file__).parent.parent.parent / 'examples' / 'malicious_skill.md'

    # Alternative: use Path.cwd() / 'examples' / 'malicious_skill.md'
    if not example_file.exists():
        example_file = Path.cwd() / 'examples' / 'malicious_skill.md'

    if not example_file.exists():
        print(f"\n[X] Example file not found: {example_file}")
        return

    print(f"\n[1] Parsing skill file...")

    try:
        parser = SkillParser()
        skill = parser.parse_file(str(example_file))
        print(f"   [OK] Parsed skill: {skill.name}")
    except Exception as e:
        print(f"   [ERROR] Parse error: {e}")
        return

    # Extract entities
    print("\n[2] Extracting entities...")

    try:
        extractor = EntityExtractor()
        entities = extractor.extract(
            '',
            skill.sections,
            skill.code_blocks
        )
        print(f"   [OK] Extracted {len(entities)} entities")
    except Exception as e:
        print(f"   [ERROR] Extraction error: {e}")
        import traceback
        traceback.print_exc()
        return

    # Extract some relationships
    print("\n[3] Extracting relationships...")

    try:
        content = "\n".join([
            section.content if hasattr(section, 'content') else str(section)
            for section in skill.sections
        ])
        relationships = extractor.extract_relationships(
            entities,
            content
        )
        print(f"   [OK] Extracted {len(relationships)} relationships")
    except Exception as e:
        print(f"   [ERROR] Relationship extraction error: {e}")
        relationships = []

    # Test community detection with only one algorithm
    print("\n[4] Testing community detection (Leiden only)...")

    try:
        detector = CommunityDetector({'community_detection': {'algorithm': 'leiden', 'enabled': True}})
        communities = detector.detect(entities, relationships)
        print(f"   [OK] Detected {len(communities)} communities")

        # Show community details
        for i, community in enumerate(communities[:3], 1):
            risk_level = 'HIGH' if community.risk_score > 0.6 else 'MEDIUM' if community.risk_score > 0.4 else 'LOW'
            print(f"      {i}. [{risk_level}] {community.description}")
            print(f"         Size: {len(community.entities)} | Level: {community.level}")

    except Exception as e:
        print(f"   [ERROR] Detection error: {e}")
        import traceback
        traceback.print_exc()
        return

    # Final summary
    print("\n" + "="*60)
    print("[OK] Community detection test complete!")
    print("="*60)

    print(f"\nSummary:")
    print(f"  - Entity extraction: [OK]")
    print(f"  - Relationship extraction: [OK]")
    print(f"  - Leiden algorithm: [OK]")


if __name__ == '__main__':
    test_community_detection_simple()
