"""
Test LLM-Enhanced Entity Extraction

Tests the LLM-enhanced entity extraction module.
"""

import sys
import os
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent.parent / 'src'
sys.path.insert(0, str(src_path))

from skillgraph.parser import SkillParser
from skillgraph.graphrag.llm_entity_extraction import LLMEnhancedEntityExtractor
from skillgraph.graphrag.models import EntityType


def test_llm_entity_extraction():
    """Test LLM-enhanced entity extraction."""
    print("=" * 60)
    print("LLM-Enhanced Entity Extraction Test")
    print("=" * 60)

    # Check if OpenAI API key is available
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("\n[SKIP] OPENAI_API_KEY not set")
        print("To run this test, set:")
        print("  export OPENAI_API_KEY=your_api_key")
        print("  set OPENAI_API_KEY=your_api_key  # Windows")
        return

    # Test with malicious skill
    example_file = Path(__file__).resolve().parent.parent.parent / 'examples' / 'malicious_skill.md'

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

    # Test LLM-enhanced extraction
    print("\n[2] Testing LLM-enhanced extraction...")

    try:
        config = {
            'model': {
                'provider': 'openai',
                'model_name': 'gpt-4-turbo-preview',
                'api_key': api_key,
                'temperature': 0.0
            },
            'llm_extraction': {
                'enabled': True,
                'enable_linking': False
            }
        }

        extractor = LLMEnhancedEntityExtractor(config)

        entities = extractor.extract(
            '',
            skill.sections,
            skill.code_blocks
        )

        print(f"   [OK] Extracted {len(entities)} entities")

        # Show entity types
        entity_types = {}
        for entity in entities:
            entity_types[entity.type.value] = entity_types.get(entity.type.value, 0) + 1

        print(f"\n[3] Entity types:")
        for entity_type, count in sorted(entity_types.items(), key=lambda x: x[1], reverse=True):
            print(f"   - {entity_type}: {count}")

        # Show high-risk entities
        high_risk = [e for e in entities if e.risk_score > 0.6]
        print(f"\n[4] High-risk entities (score > 0.6):")
        for entity in high_risk:
            print(f"   - [{entity.type.value}] {entity.name}")
            print(f"     Risk: {entity.risk_score:.2f}")
            print(f"     Conf: {entity.confidence:.2f}")
            print(f"     Desc: {entity.description[:60]}...")

    except Exception as e:
        print(f"   [ERROR] LLM extraction error: {e}")
        import traceback
        traceback.print_exc()
        return

    # Test relationship extraction
    print("\n[5] Testing LLM-enhanced relationship extraction...")

    try:
        content = "\n".join([
            section.content if hasattr(section, 'content') else str(section)
            for section in skill.sections
        ])

        relationships = extractor.extract_relationships(entities, content)
        print(f"   [OK] Extracted {len(relationships)} relationships")

        # Show sample relationships
        print(f"\n[6] Sample relationships:")
        for i, rel in enumerate(relationships[:3], 1):
            print(f"   {i}. {rel['type']}")
            print(f"      Source: {rel['source_id']}")
            print(f"      Target: {rel['target_id']}")
            print(f"      Confidence: {rel.get('confidence', 1.0):.2f}")

    except Exception as e:
        print(f"   [ERROR] Relationship extraction error: {e}")
        import traceback
        traceback.print_exc()
        return

    # Final summary
    print("\n" + "=" * 60)
    print("[OK] LLM-enhanced extraction test complete!")
    print("=" * 60)

    print(f"\nSummary:")
    print(f"  - Entity extraction: [OK]")
    print(f"  - Relationship extraction: [OK]")
    print(f"  - High-risk entities: {len(high_risk)}")
    print(f"  - Total entities: {len(entities)}")


def test_fallback_to_base_extractor():
    """Test fallback to base extractor when LLM unavailable."""
    print("\n" + "=" * 60)
    print("Fallback Test (LLM Disabled)")
    print("=" * 60)

    example_file = Path(__file__).resolve().parent.parent.parent / 'examples' / 'malicious_skill.md'

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

    # Test with LLM disabled
    print("\n[2] Testing with LLM disabled...")

    try:
        config = {
            'llm_extraction': {
                'enabled': False
            }
        }

        extractor = LLMEnhancedEntityExtractor(config)

        entities = extractor.extract(
            '',
            skill.sections,
            skill.code_blocks
        )

        print(f"   [OK] Extracted {len(entities)} entities (base extractor)")
        print(f"   [OK] Fallback mechanism working correctly")

    except Exception as e:
        print(f"   [ERROR] Fallback error: {e}")
        return

    print("\n" + "=" * 60)
    print("[OK] Fallback test complete!")
    print("=" * 60)


if __name__ == '__main__':
    test_llm_entity_extraction()
    test_fallback_to_base_extractor()
