"""
GAT Risk Model Training Script

Complete training pipeline with multiple strategies:
1. Pseudo-label training (rule-based)
2. Self-supervised training (graph reconstruction)
3. Weak supervision (rule confidence)
4. Zero-shot inference
5. Active learning framework
"""

import os
import sys
import json
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add src to path
src_path = Path(__file__).parent.parent.parent / 'src'
sys.path.insert(0, str(src_path))

from skillgraph.parser import SkillParser
from skillgraph.graphrag import EntityExtractor
from skillgraph.graphrag.gat_risk_model import GATRiskTrainer, GATRiskModel
from skillgraph.graphrag.models import Entity, EntityType


def create_mock_entities(num_entities: int = 100) -> List[Entity]:
    """
    Create mock entities for training when real data is not available.

    Args:
        num_entities: Number of entities to create

    Returns:
        List of Entity objects
    """
    print("Creating mock entities for training...")

    entities = []
    entity_types = ['network', 'file', 'permission', 'api']

    # Create high-risk entities
    for i in range(num_entities // 3):
        entity_type = entity_types[i % len(entity_types)]

        high_risk_names = [
            '.env', 'secret_key', 'admin_access', 'sudo_command',
            'http://evil.com', 'upload_data', 'token.txt',
            'credential_file', 'root_access'
        ]

        name = high_risk_names[i % len(high_risk_names)]

        entity = Entity(
            id=f"high_risk_{i}",
            name=name,
            type=EntityType.__annotations__['type'][entity_type.upper()],
            description=f"High-risk {entity_type}: {name}",
            embedding=np.random.randn(1536).astype(np.float32),
            risk_score=0.8 + np.random.rand() * 0.2,  # 0.8-1.0
            confidence=0.9
        )
        entities.append(entity)

    # Create medium-risk entities
    for i in range(num_entities // 3, num_entities * 2 // 3):
        entity_type = entity_types[i % len(entity_types)]

        medium_risk_names = [
            'config_file', 'api_call', 'external_service', 'write_file',
            'read_database', 'execute_command', 'network_request',
            'modify_config', 'http_request'
        ]

        name = medium_risk_names[i % len(medium_risk_names)]

        entity = Entity(
            id=f"medium_risk_{i}",
            name=name,
            type=EntityType.__annotations__['type'][entity_type.upper()],
            description=f"Medium-risk {entity_type}: {name}",
            embedding=np.random.randn(1536).astype(np.float32),
            risk_score=0.5 + np.random.rand() * 0.2,  # 0.5-0.7
            confidence=0.8
        )
        entities.append(entity)

    # Create low-risk entities
    for i in range(num_entities * 2 // 3, num_entities):
        entity_type = entity_types[i % len(entity_types)]

        low_risk_names = [
            'read_only', 'log_entry', 'cache_file', 'temp_file',
            'info_display', 'safe_operation', 'validation',
            'check_permission', 'verify_user', 'local_variable'
        ]

        name = low_risk_names[i % len(low_risk_names)]

        entity = Entity(
            id=f"low_risk_{i}",
            name=name,
            type=EntityType.__annotations__['type'][entity_type.upper()],
            description=f"Low-risk {entity_type}: {name}",
            embedding=np.random.randn(1536).astype(np.float32),
            risk_score=0.1 + np.random.rand() * 0.2,  # 0.1-0.3
            confidence=0.9
        )
        entities.append(entity)

    print(f"Created {len(entities)} mock entities")
    print(f"  High-risk: {sum(1 for e in entities if e.risk_score > 0.7)}")
    print(f"  Medium-risk: {sum(1 for e in entities if 0.5 < e.risk_score <= 0.7)}")
    print(f"  Low-risk: {sum(1 for e in entities if e.risk_score <= 0.5)}")

    return entities


def create_mock_relationships(entities, density: float = 0.1) -> List[Any]:
    """
    Create mock relationships for training.

    Args:
        entities: List of entities
        density: Relationship density (0-1)

    Returns:
        List of Relationship-like objects
    """
    print("Creating mock relationships...")

    from skillgraph.graphrag.models import Relationship, RelationType

    relationships = []
    num_relationships = int(len(entities) * (len(entities) - 1) * density)

    import random

    for _ in range(num_relationships):
        source_idx = random.randint(0, len(entities) - 1)
        target_idx = random.randint(0, len(entities) - 1)

        if source_idx != target_idx:
            source = entities[source_idx]
            target = entities[target_idx]

            rel_types = [
                RelationType.CALLS,
                RelationType.DEPENDS_ON,
                RelationType.ACCESSES,
                RelationType.MODIFIES
                RelationType.REQUIRES
                RelationType.VALIDATES
            ]

            rel = Relationship(
                source_id=source.id,
                target_id=target.id,
                type=random.choice(rel_types),
                description=f"{source.name} {random.choice(['calls', 'depends on', 'accesses', 'modifies'])} {target.name}",
                weight=random.random(),
                confidence=0.9
            )
            relationships.append(rel)

    print(f"Created {len(relationships)} relationships (density: {density})")

    return relationships


def create_mock_risk_findings(entities, high_risk_ratio: float = 0.3) -> List[Dict[str, Any]]:
    """
    Create mock risk findings for pseudo-label generation.

    Args:
        entities: List of entities
        high_risk_ratio: Ratio of high-risk findings

    Returns:
        List of risk finding dictionaries
    """
    print("Creating mock risk findings...")

    risk_findings = []

    # Find high-risk entities
    high_risk_entities = [e for e in entities if e.risk_score > 0.6]

    num_findings = int(len(entities) * high_risk_ratio)

    for i in range(num_findings):
        if high_risk_entities:
            entity = random.choice(high_risk_entities)
            finding = {
                'type': 'high_risk_entity',
                'content_snippet': f"Found high-risk {entity.type.value}: {entity.name}",
                'severity': 'high' if entity.risk_score > 0.8 else 'critical',
                'confidence': 0.9,
                'risk_score': entity.risk_score
            }
            risk_findings.append(finding)

    print(f"Created {len(risk_findings)} risk findings")

    return risk_findings


def run_training_pipeline(
    entities: List[Entity],
    relationships: List[Any],
    risk_findings: List[Dict[str, Any]],
    config: Dict[str, Any],
    output_dir: str
):
    """
    Run complete training pipeline with multiple strategies.

    Args:
        entities: List of entities
        relationships: List of relationships
        risk_findings: List of risk findings
        config: Configuration dictionary
        output_dir: Output directory for results

    Returns:
        Training results
    """
    print("=" * 60)
    print("GAT Risk Model Training Pipeline")
    print("=" * 60)

    os.makedirs(output_dir, exist_ok=True)

    results = {'pipeline': 'GAT Risk Model Training', 'timestamp': datetime.now().isoformat()}

    # Initialize trainer
    trainer = GATRiskTrainer(config)

    # Prepare graph data
    print("\n[1] Preparing graph data...")

    pseudo_labels = trainer.generate_pseudo_labels(entities, risk_findings)
    data = trainer.prepare_graph_data(entities, relationships, pseudo_labels)

    print(f"   Nodes: {data.num_nodes}")
    print(f"   Edges: {data.num_edges}")
    print(f"   Labels: {'Yes' if data.y is not None else 'No'}")

    results['graph_preparation'] = {
        'num_nodes': int(data.num_nodes),
        'num_edges': int(data.num_edges),
        'has_labels': data.y is not None
    }

    # Run training strategies
    print("\n[2] Running training strategies...")

    # Strategy 1: Pseudo-label training (supervised)
    print("\n  Strategy 1: Pseudo-Label Training (Supervised)")

    if data.y is not None:
        try:
            pseudo_metrics = trainer.train_pseudo_label(data)
            results['pseudo_label_training'] = pseudo_metrics

            print(f"  [OK] Final Val Acc: {pseudo_metrics['final_val_accuracy']:.2%}")

        except Exception as e:
            print(f"  [ERROR] Pseudo-label training failed: {e}")
            results['pseudo_label_training'] = {'error': str(e)}
    else:
        print("  [SKIP] No labels available")
        results['pseudo_label_training'] = {'status': 'skipped'}

    # Strategy 2: Self-supervised training (graph reconstruction)
    print("\n  Strategy 2: Self-Supervised Training (Graph Reconstruction)")

    try:
        config_self_supervised = {**config, 'model': {**config.get('model', {}), 'training': {'learning_rate': 0.001, 'epochs': 50}}}
        trainer_self = GATRiskTrainer(config_self_supervised)

        self_metrics = trainer_self.train_self_supervised(data)

        results['self_supervised_training'] = self_metrics

        print(f"  [OK] Final Recon Loss: {self_metrics['final_train_loss']:.4f}")

    except Exception as e:
        print(f"  [ERROR] Self-supervised training failed: {e}")
        results['self_supervised_training'] = {'error': str(e)}

    # Strategy 3: Zero-shot inference
    print("\n  Strategy 3: Zero-Shot Inference")

    try:
        zero_shot_results = trainer.zero_shot_inference(data)

        results['zero_shot_inference'] = zero_shot_results

        print(f"  [OK] Avg Risk Score: {zero_shot_results['avg_risk_score']:.3f}")
        print(f"  [OK] High-Risk Entities: {zero_shot_results['num_high_risk']}")
        print(f"  [OK] Low-Risk Entities: {zero_shot_results['num_low_risk']}")

    except Exception as e:
        print(f"  [ERROR] Zero-shot inference failed: {e}")
        results['zero_shot_inference'] = {'error': str(e)}

    # Save results
    print("\n[3] Saving training results...")

    results_path = os.path.join(output_dir, "training_results.json")

    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"   [OK] Results saved to: {results_path}")

    # Save training history
    history_path = os.path.join(output_dir, "training_history.json")

    history = {
        'config': config,
        'timestamp': datetime.now().isoformat(),
        'results': results
    }

    with open(history_path, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, default=str)

    print(f"   [OK] History saved to: {history_path}")

    # Generate summary
    print("\n" + "=" * 60)
    print("Training Pipeline Summary")
    print("=" * 60)

    print(f"\n✓ Graph Preparation: {data.num_nodes} nodes, {data.num_edges} edges")

    if 'pseudo_label_training' in results:
        if 'error' not in results['pseudo_label_training']:
            acc = results['pseudo_label_training']['final_val_accuracy']
            print(f"✓ Pseudo-Label Training: {acc:.2%} accuracy")
        else:
            print(f"✗ Pseudo-Label Training: Failed")

    if 'self_supervised_training' in results:
        if 'error' not in results['self_supervised_training']:
            loss = results['self_supervised_training']['final_train_loss']
            print(f"✓ Self-Supervised Training: {loss:.4f} recon loss")
        else:
            print(f"✗ Self-Supervised Training: Failed")

    if 'zero_shot_inference' in results:
        if 'error' not in results['zero_shot_inference']:
            risk = results['zero_shot_inference']['avg_risk_score']
            print(f"✓ Zero-Shot Inference: {risk:.3f} avg risk score")
            print(f"  High-Risk: {results['zero_shot_inference']['num_high_risk']}")
            print(f"  Low-Risk: {results['zero_shot_inference']['num_low_risk']}")
        else:
            print(f"✗ Zero-Shot Inference: Failed")

    print("=" * 60)

    return results


def main():
    """Main function - run complete training pipeline."""
    print("GAT Risk Model Training Pipeline")
    print("=" * 60)

    # Check dependencies
    try:
        import torch
        import torch_geometric
        print(f"✓ PyTorch: {torch.__version__}")
        print(f"✓ PyTorch Geometric: Available")
    except ImportError as e:
        print(f"✗ Error: {e}")
        print("\nPlease install required dependencies:")
        print("  pip install torch")
        print("  pip install torch-geometric")
        return

    # Configuration
    config = {
        'model': {
            'in_channels': 1536,
            'hidden_channels': 128,
            'out_channels': 1,
            'num_heads': 4,
            'dropout': 0.6,
            'num_layers': 2,
            'use_autoencoder': True,
            'reconstruction_weight': 0.3,
            'risk_weight': 0.7
        },
        'training': {
            'learning_rate': 0.001,
            'epochs': 100,
            'batch_size': 32,
            'patience': 10,
            'min_delta': 0.001
            'val_split': 0.2
        },
        'validation': {
            'device': 'cuda' if torch.cuda.is_available() else 'cpu',
            'risk_threshold': 0.5
        }
    }

    # Create mock data
    print("\nCreating mock training data...")

    entities = create_mock_entities(num_entities=100)
    relationships = create_mock_relationships(entities, density=0.15)
    risk_findings = create_mock_risk_findings(entities)

    # Run training pipeline
    output_dir = "output/gat_training"

    results = run_training_pipeline(
        entities,
        relationships,
        risk_findings,
        config,
        output_dir
    )

    # Final summary
    print("\n" + "=" * 60)
    print("Training Pipeline Complete!")
    print("=" * 60)

    print(f"\nResults saved to: {output_dir}")
    print(f"\nNext steps:")
    print(f"  1. Review training results")
    print(f"  2. Analyze attention weights")
    print(f"  3. Evaluate risk predictions")
    print(f"  4. Integrate into SkillGraph pipeline")

    print("=" * 60)


if __name__ == '__main__':
    main()
