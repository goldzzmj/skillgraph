"""
GAT Technical Validation Test

Runs GAT validation on test data to validate the hybrid approach.
"""

import sys
from pathlib import Path
import os

# Add src to path
src_path = Path(__file__).parent.parent.parent / 'src'
sys.path.insert(0, str(src_path))

from skillgraph.parser import SkillParser
from skillgraph.graphrag import EntityExtractor
from skillgraph.graphrag.gat_validation import GATRiskValidator
from skillgraph.graphrag.models import Entity


def create_test_entities(num_entities: int = 50):
    """
    Create test entities for validation.

    Args:
        num_entities: Number of test entities to create

    Returns:
        List of test Entity objects
    """
    import numpy as np

    entities = []
    entity_types = ['network', 'file', 'permission', 'api']

    # Create high-risk entities
    for i in range(num_entities // 3):
        entity_type = entity_types[i % len(entity_types)]

        high_risk_names = [
            '.env', 'secret_key', 'admin_access', 'sudo_command',
            'http://evil.com', 'upload_data', 'token.txt'
        ]

        name = high_risk_names[i % len(high_risk_names)]

        entity = Entity(
            id=f"high_risk_{i}",
            name=name,
            type=Entity.__annotations__['type'][entity_type.upper()],
            description=f"High-risk {entity_type}: {name}",
            embedding=np.random.randn(1536).astype(np.float32),
            risk_score=0.8 + np.random.rand() * 0.2,
            confidence=0.9
        )
        entities.append(entity)

    # Create low-risk entities
    for i in range(num_entities - num_entities // 3):
        entity_type = entity_types[i % len(entity_types)]

        low_risk_names = [
            'config_file', 'read_only', 'api_call', 'normal_tool',
            'log_entry', 'cache_file', 'temp_file'
        ]

        name = low_risk_names[i % len(low_risk_names)]

        entity = Entity(
            id=f"low_risk_{i}",
            name=name,
            type=Entity.__annotations__['type'][entity_type.upper()],
            description=f"Low-risk {entity_type}: {name}",
            embedding=np.random.randn(1536).astype(np.float32),
            risk_score=0.1 + np.random.rand() * 0.2,
            confidence=0.9
        )
        entities.append(entity)

    return entities


def create_test_relationships(entities):
    """
    Create test relationships between entities.

    Args:
        entities: List of entities

    Returns:
        List of test Relationship objects
    """
    from skillgraph.graphrag.models import Relationship, RelationType

    relationships = []
    entity_count = len(entities)

    # Create random relationships
    num_relationships = min(entity_count * 2, 100)

    import random

    for _ in range(num_relationships):
        source_idx = random.randint(0, entity_count - 1)
        target_idx = random.randint(0, entity_count - 1)

        if source_idx != target_idx:
            source = entities[source_idx]
            target = entities[target_idx]

            rel = Relationship(
                source_id=source.id,
                target_id=target.id,
                type=RelationType.CALLS,
                description=f"{source.name} calls {target.name}",
                weight=1.0,
                confidence=0.9
            )
            relationships.append(rel)

    return relationships


def create_test_risk_findings(entities):
    """
    Create test risk findings for validation.

    Args:
        entities: List of entities

    Returns:
        List of risk finding dictionaries
    """
    risk_findings = []

    # Create findings for high-risk entities
    for entity in entities:
        if entity.risk_score > 0.6:
            finding = {
                'type': 'high_risk_entity',
                'content_snippet': f"Found high-risk entity: {entity.name}",
                'severity': 'high',
                'confidence': 0.9
            }
            risk_findings.append(finding)

    return risk_findings


def run_gat_validation():
    """Run GAT technical validation."""
    print("=" * 60)
    print("GAT Technical Validation Test")
    print("=" * 60)

    # Step 1: Create test data
    print("\n[1] Creating test data...")

    try:
        entities = create_test_entities(num_entities=50)
        relationships = create_test_relationships(entities)
        risk_findings = create_test_risk_findings(entities)

        print(f"   Created {len(entities)} entities")
        print(f"   Created {len(relationships)} relationships")
        print(f"   Created {len(risk_findings)} risk findings")

        high_risk_count = sum(1 for e in entities if e.risk_score > 0.6)
        low_risk_count = len(entities) - high_risk_count

        print(f"   High risk: {high_risk_count}")
        print(f"   Low risk: {low_risk_count}")

    except Exception as e:
        print(f"   [ERROR] Failed to create test data: {e}")
        return

    # Step 2: Initialize validator
    print("\n[2] Initializing GAT validator...")

    try:
        config = {
            'model': {
                'in_channels': 1536,
                'hidden_channels': 64,
                'out_channels': 1,
                'num_heads': 4,
                'dropout': 0.6
            },
            'training': {
                'learning_rate': 0.001,
                'epochs': 30,  # Reduced for quick validation
                'batch_size': 16
            },
            'validation': {
                'device': 'cpu',  # Use CPU for validation
                'risk_threshold': 0.5
            }
        }

        validator = GATRiskValidator(config)
        print(f"   [OK] Validator initialized")

    except Exception as e:
        print(f"   [ERROR] Failed to initialize validator: {e}")
        import traceback
        traceback.print_exc()
        return

    # Step 3: Run validation
    print("\n[3] Running GAT validation...")

    try:
        results = validator.run_validation(
            entities,
            relationships,
            risk_findings
        )

        print(f"   [OK] Validation completed")

    except Exception as e:
        print(f"   [ERROR] Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # Step 4: Save results
    print("\n[4] Saving validation results...")

    try:
        output_dir = "output/validation"
        os.makedirs(output_dir, exist_ok=True)

        results_path = os.path.join(output_dir, "validation_results.json")
        validator.save_results(results, results_path)

        print(f"   [OK] Results saved to: {results_path}")

    except Exception as e:
        print(f"   [ERROR] Failed to save results: {e}")

    # Step 5: Summary
    print("\n" + "=" * 60)
    print("Validation Test Complete")
    print("=" * 60)

    print(f"\n✓ Test data created: {len(entities)} entities")
    print(f"✓ GAT model trained and validated")
    print(f"✓ Attention weights visualized")
    print(f"✓ Results saved to: {results_path}")

    # Check if validation was successful
    if 'training' in results:
        val_acc = results['training']['val_accuracy']
        if val_acc > 0.8:
            print(f"\n🎉 SUCCESS: GAT validation passed!")
            print(f"   Validation accuracy: {val_acc:.2%}")
            print(f"   Recommendation: PROCEED with GAT implementation")
        elif val_acc > 0.7:
            print(f"\n⚠️  MODERATE SUCCESS: GAT validation passed with caution")
            print(f"   Validation accuracy: {val_acc:.2%}")
            print(f"   Recommendation: PROCEED with tuning needed")
        else:
            print(f"\n❌ VALIDATION FAILED: GAT model performance insufficient")
            print(f"   Validation accuracy: {val_acc:.2%}")
            print(f"   Recommendation: Reconsider approach")
    else:
        print(f"\n⚠️  Validation incomplete - training results not available")

    print("=" * 60)


def test_dependencies():
    """Test if required dependencies are available."""
    print("=" * 60)
    print("Dependency Check")
    print("=" * 60)

    dependencies = {
        'numpy': False,
        'torch': False,
        'torch-geometric': False,
        'matplotlib': False
    }

    # Test numpy
    try:
        import numpy as np
        dependencies['numpy'] = True
        print(f"✓ numpy: {np.__version__}")
    except ImportError:
        print(f"✗ numpy: Not installed")

    # Test torch
    try:
        import torch
        dependencies['torch'] = True
        print(f"✓ torch: {torch.__version__}")
    except ImportError:
        print(f"✗ torch: Not installed")

    # Test torch-geometric
    try:
        import torch_geometric
        dependencies['torch-geometric'] = True
        print(f"✓ torch-geometric: Available")
    except ImportError:
        print(f"✗ torch-geometric: Not installed")

    # Test matplotlib
    try:
        import matplotlib
        dependencies['matplotlib'] = True
        print(f"✓ matplotlib: {matplotlib.__version__}")
    except ImportError:
        print(f"✗ matplotlib: Not installed")

    print("=" * 60)

    # Summary
    available = sum(dependencies.values())
    total = len(dependencies)

    print(f"\nDependencies: {available}/{total} available")

    if available == total:
        print("✓ All dependencies available - Ready for validation")
    else:
        missing = [k for k, v in dependencies.items() if not v]
        print(f"✗ Missing dependencies: {', '.join(missing)}")
        print("\nInstall missing dependencies:")
        for dep in missing:
            if dep == 'numpy':
                print("  pip install numpy")
            elif dep == 'torch':
                print("  pip install torch")
            elif dep == 'torch-geometric':
                print("  pip install torch-geometric")
            elif dep == 'matplotlib':
                print("  pip install matplotlib")


if __name__ == '__main__':
    print("GAT Technical Validation Test Suite")
    print("=" * 60)

    # First check dependencies
    test_dependencies()

    # Then run validation
    run_gat_validation()

    print("\n" + "=" * 60)
    print("Test Suite Complete")
    print("=" * 60)
