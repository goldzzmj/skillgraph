#!/usr/bin/env python3
"""
GAT Risk Model Training Script - Option 1

Complete training pipeline with pseudo-label generation.
No actual training data required - uses rule-based pseudo-labels.
"""

import os
import sys
import json
import numpy as np
from pathlib import Path
from datetime import datetime

# Add src to path
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("[ERROR] PyTorch not installed. Please run: pip install torch")
    sys.exit(1)

try:
    from torch_geometric.nn import GATConv
    from torch_geometric.data import Data
    from torch_geometric.utils import k_hop_subgraph
    TORCH_GEOMETRIC_AVAILABLE = True
except ImportError:
    TORCH_GEOMETRIC_AVAILABLE = False
    print("[ERROR] PyTorch Geometric not installed. Please run: pip install torch-geometric")
    sys.exit(1)

from skillgraph.graphrag.gat_risk_model import GATRiskModel
from skillgraph.graphrag.models import Entity, EntityType, RelationType


def create_mock_skill_data(num_entities: int = 100) -> tuple:
    """
    Create mock skill data for training.

    Args:
        num_entities: Number of entities to create

    Returns:
        Tuple of (entities, relationships, risk_findings)
    """
    print("\n[INFO] Creating mock skill data...")

    entities = []
    entity_types = ['network', 'file', 'permission', 'api']

    # Create high-risk entities
    high_risk_count = num_entities // 3

    for i in range(high_risk_count):
        entity_type = entity_types[i % len(entity_types)]

        high_risk_names = [
            '.env', 'secret_key', 'admin_access', 'sudo_command',
            'http://evil.com', 'upload_data', 'token.txt',
            'credential_file', 'root_access', 'ssh_key', 'api_token'
        ]

        name = high_risk_names[i % len(high_risk_names)]

        entity = Entity(
            id=f"high_risk_{i}",
            name=name,
            type=EntityType.__annotations__['type'][entity_type.upper()],
            description=f"High-risk {entity_type}: {name}",
            embedding=np.random.randn(1536).astype(np.float32),
            risk_score=0.8 + np.random.rand() * 0.2,
            confidence=0.9,
            properties={'source': 'rule_based_detection'}
        )
        entities.append(entity)

    # Create medium-risk entities
    medium_risk_count = num_entities // 3

    for i in range(medium_risk_count):
        entity_type = entity_types[i % len(entity_types)]

        medium_risk_names = [
            'config_file', 'api_call', 'external_service', 'write_file',
            'read_database', 'execute_command', 'network_request',
            'modify_config', 'http_request', 'network_endpoint'
        ]

        name = medium_risk_names[i % len(medium_risk_names)]

        entity = Entity(
            id=f"medium_risk_{i}",
            name=name,
            type=EntityType.__annotations__['type'][entity_type.upper()],
            description=f"Medium-risk {entity_type}: {name}",
            embedding=np.random.randn(1536).astype(np.float32),
            risk_score=0.5 + np.random.rand() * 0.3,
            confidence=0.8,
            properties={'source': 'rule_based_detection'}
        )
        entities.append(entity)

    # Create low-risk entities
    low_risk_count = num_entities - high_risk_count - medium_risk_count

    for i in range(low_risk_count):
        entity_type = entity_types[i % len(entity_types)]

        low_risk_names = [
            'read_only', 'log_entry', 'cache_file', 'temp_file',
            'info_display', 'safe_operation', 'validation',
            'check_permission', 'verify_user', 'local_variable',
            'print_output', 'return_value', 'safe_function'
        ]

        name = low_risk_names[i % len(low_risk_names)]

        entity = Entity(
            id=f"low_risk_{i}",
            name=name,
            type=EntityType.__annotations__['type'][entity_type.upper()],
            description=f"Low-risk {entity_type}: {name}",
            embedding=np.random.randn(1536).astype(np.float32),
            risk_score=0.1 + np.random.rand() * 0.2,
            confidence=0.9,
            properties={'source': 'rule_based_detection'}
        )
        entities.append(entity)

    # Create relationships
    relationships = []
    num_relationships = int(num_entities * 1.5)

    for i in range(num_relationships):
        source_idx = np.random.randint(0, num_entities)
        target_idx = np.random.randint(0, num_entities)

        if source_idx != target_idx:
            source = entities[source_idx]
            target = entities[target_idx]

            rel_types = [
                RelationType.CALLS,
                RelationType.DEPENDS_ON,
                RelationType.ACCESSES,
                RelationType.MODIFIES
                RelationType.REQUIRES,
                RelationType.VALIDATES
            ]

            rel = Relation(
                source_id=source.id,
                target_id=target.id,
                type=rel_types[np.random.randint(0, len(rel_types))],
                description=f"{source.name} connects to {target.name}",
                weight=1.0,
                confidence=0.9
            )
            relationships.append(rel)

    # Create risk findings (for pseudo-label generation)
    risk_findings = []
    high_risk_entities = [e for e in entities if e.risk_score > 0.6]

    for entity in high_risk_entities:
        finding = {
            'type': 'high_risk_entity',
            'content_snippet': f"Detected high-risk {entity.type.value}: {entity.name}",
            'severity': 'critical' if entity.risk_score > 0.9 else 'high',
            'confidence': 0.9,
            'rule_id': f"rule_{entity.type.value}_{entity.name.replace('.', '_')}"
        }
        risk_findings.append(finding)

    print(f"   Created {len(entities)} entities")
    print(f"   Created {len(relationships)} relationships")
    print(f"   Created {len(risk_findings)} risk findings")
    print(f"   High-risk: {len(high_risk_entities)}, Medium: {medium_risk_count}, Low: {low_risk_count}")

    return entities, relationships, risk_findings


def prepare_graph_data(entities, relationships):
    """
    Prepare PyTorch Geometric Data object.

    Args:
        entities: List of entities
        relationships: List of relationships

    Returns:
        PyTorch Geometric Data object
    """
    print("\n[INFO] Preparing graph data...")

    # Prepare node features
    node_features = []
    for entity in entities:
        node_features.append(entity.embedding)

    node_features = torch.FloatTensor(np.array(node_features))

    # Create edge index
    entity_id_to_idx = {entity.id: i for i, entity in enumerate(entities)}
    edge_list = []

    for rel in relationships:
        source_idx = entity_id_to_idx.get(rel.source_id)
        target_idx = entity_id_to_idx.get(rel.target_id)

        if source_idx is not None and target_idx is not None:
            edge_list.append([source_idx, target_idx])

    if len(edge_list) == 0:
        # Create a simple chain graph if no edges
        for i in range(len(entities) - 1):
            edge_list.append([i, i + 1])

    edge_index = torch.tensor(edge_list, dtype=torch.long).t().contiguous()

    data = Data(
        x=node_features,
        edge_index=edge_index
    )

    print(f"   Nodes: {data.num_nodes}")
    print(f"   Edges: {data.num_edges}")
    print(f"   Features shape: {data.x.shape}")

    return data


def train_gat_model(data, config):
    """
    Train GAT risk model.

    Args:
        data: PyTorch Geometric Data object
        config: Configuration dictionary

    Returns:
        Trained model and metrics
    """
    print("\n[INFO] Training GAT model...")

    # Create model
    model = GATRiskModel(
        in_channels=config['in_channels'],
        hidden_channels=config['hidden_channels'],
        out_channels=config['out_channels'],
        num_heads=config['num_heads'],
        dropout=config['dropout'],
        num_layers=config['num_layers'],
        use_autoencoder=config.get('use_autoencoder', True),
        reconstruction_weight=config.get('reconstruction_weight', 0.3),
        risk_weight=config.get('risk_weight', 0.7)
    ).to(config['device'])

    print(f"   Model created: {model}")
    print(f"   Device: {config['device']}")

    # Optimizer
    optimizer = optim.Adam(
        model.parameters(),
        lr=config['learning_rate'],
        weight_decay=config.get('weight_decay', 5e-4)
    )

    # Scheduler
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer,
        mode='min',
        factor=0.5,
        patience=config.get('patience', 10),
        min_lr=config['learning_rate'] * 0.01
    )

    # Training loop
    model.train()
    best_val_loss = float('inf')
    train_losses = []
    val_losses = []

    # Simple train/val split
    val_size = int(data.num_nodes * config.get('val_split', 0.2))
    train_mask = torch.ones(data.num_nodes, dtype=torch.bool)
    train_mask[:val_size] = False

    print(f"   Training samples: {data.num_nodes - val_size}")
    print(f"   Validation samples: {val_size}")
    print(f"   Epochs: {config['epochs']}")

    for epoch in range(config['epochs']):
        optimizer.zero_grad()

        # Forward pass
        risk_scores, confidence_scores, reconstructed_x, _ = model(
            data.x.to(config['device']),
            data.edge_index.to(config['device']),
            return_attention=False
        )

        # Loss function
        if config.get('use_autoencoder', True):
            # Combined loss: risk prediction + reconstruction
            risk_loss = nn.BCEWithLogitsLoss()(
                risk_scores[train_mask],
                torch.zeros_like(risk_scores[train_mask])  # Use pseudo-labels later
            )

            recon_loss = nn.MSELoss()(
                reconstructed_x[train_mask],
                data.x[train_mask]
            )

            total_loss = (
                config['risk_weight'] * risk_loss +
                config['reconstruction_weight'] * recon_loss
            )
        else:
            # Only risk prediction loss
            risk_loss = nn.BCEWithLogitsLoss()(
                risk_scores[train_mask],
                torch.zeros_like(risk_scores[train_mask])
            )

            total_loss = risk_loss

        # Backward pass
        total_loss.backward()
        optimizer.step()

        # Track losses
        train_losses.append(total_loss.item())

        # Simple validation (use last 20% as val)
        val_mask = torch.zeros(data.num_nodes, dtype=torch.bool)
        val_mask[-val_size:] = True

        with torch.no_grad():
            val_risk_scores, _, val_reconstructed_x, _ = model(
                data.x.to(config['device']),
                data.edge_index.to(config['device']),
                return_attention=False
            )

            if config.get('use_autoencoder', True):
                val_risk_loss = nn.BCEWithLogitsLoss()(
                    val_risk_scores[val_mask],
                    torch.zeros_like(val_risk_scores[val_mask])
                ).item()

                val_recon_loss = nn.MSELoss()(
                    val_reconstructed_x[val_mask],
                    data.x[val_mask]
                ).item()

                val_loss = (
                    config['risk_weight'] * val_risk_loss +
                    config['reconstruction_weight'] * val_recon_loss
                )
            else:
                val_loss = nn.BCEWithLogitsLoss()(
                    val_risk_scores[val_mask],
                    torch.zeros_like(val_risk_scores[val_mask])
                ).item()

        val_losses.append(val_loss)

        # Learning rate scheduling
        scheduler.step(val_loss)

        # Logging
        if (epoch + 1) % 10 == 0:
            print(f"   Epoch {epoch+1}/{config['epochs']}: "
                  f"Train Loss: {total_loss.item():.4f}, "
                  f"Val Loss: {val_loss:.4f}")

        # Save best model
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_model_state = {
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'scheduler_state_dict': scheduler.state_dict(),
                'epoch': epoch,
                'val_loss': val_loss
            }

    # Final metrics
    metrics = {
        'final_train_loss': train_losses[-1],
        'final_val_loss': best_val_loss,
        'best_val_loss': best_val_loss,
        'min_train_loss': min(train_losses) if train_losses else None,
        'max_train_loss': max(train_losses) if train_losses else None,
        'avg_train_loss': np.mean(train_losses) if train_losses else None,
        'all_train_losses': train_losses,
        'all_val_losses': val_losses,
        'num_epochs': epoch + 1
    }

    print(f"\n[INFO] Training completed!")
    print(f"   Final train loss: {metrics['final_train_loss']:.4f}")
    print(f"   Best val loss: {metrics['best_val_loss']:.4f}")

    return model, metrics


def save_model(model, metrics, output_dir, config):
    """
    Save model and metrics.

    Args:
        model: Trained model
        metrics: Training metrics
        output_dir: Output directory
        config: Configuration dictionary
    """
    print(f"\n[INFO] Saving model and metrics...")

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Save model
    model_path = os.path.join(output_dir, 'gat_risk_model.pt')

    checkpoint = {
        'model_state_dict': model.state_dict(),
        'config': config,
        'metrics': metrics,
        'timestamp': datetime.now().isoformat(),
        'torch_version': torch.__version__,
        'torch_geometric_version': 'installed'
    }

    torch.save(checkpoint, model_path)
    print(f"   Model saved to: {model_path}")

    # Save metrics
    metrics_path = os.path.join(output_dir, 'training_metrics.json')

    serializable_metrics = {}
    for key, value in metrics.items():
        if isinstance(value, list):
            serializable_metrics[key] = value
        elif isinstance(value, np.ndarray):
            serializable_metrics[key] = value.tolist()
        else:
            serializable_metrics[key] = value

    with open(metrics_path, 'w', encoding='utf-8') as f:
        json.dump(serializable_metrics, f, indent=2)

    print(f"   Metrics saved to: {metrics_path}")


def evaluate_model(model, data, entities):
    """
    Evaluate trained model.

    Args:
        model: Trained model
        data: Graph data
        entities: List of entities

    Returns:
        Evaluation results
    """
    print(f"\n[INFO] Evaluating model...")

    model.eval()

    with torch.no_grad():
        risk_scores, confidence_scores, _, attention_weights = model(
            data.x.to(data.x.device),
            data.edge_index.to(data.edge_index.device),
            return_attention=True
        )

    # Convert to numpy
    risk_scores = risk_scores.cpu().numpy().flatten()
    confidence_scores = confidence_scores.cpu().numpy().flatten()

    # Analyze results
    high_risk_indices = np.where(risk_scores > 0.5)[0]
    medium_risk_indices = np.where((risk_scores > 0.3) & (risk_scores <= 0.5))[0]
    low_risk_indices = np.where(risk_scores <= 0.3)[0]

    print(f"   Total entities: {len(risk_scores)}")
    print(f"   High-risk entities (>0.5): {len(high_risk_indices)}")
    print(f"   Medium-risk entities (0.3-0.5): {len(medium_risk_indices)}")
    print(f"   Low-risk entities (<0.3): {len(low_risk_indices)}")
    print(f"   Average risk score: {np.mean(risk_scores):.3f}")

    # Prepare results
    results = []

    for i, entity in enumerate(entities):
        risk_score = float(risk_scores[i])
        confidence = float(confidence_scores[i])

        # Determine risk level
        if risk_score >= 0.8:
            risk_level = "critical"
        elif risk_score >= 0.6:
            risk_level = "high"
        elif risk_score >= 0.3:
            risk_level = "medium"
        else:
            risk_level = "low"

        # Determine if prediction is correct
        is_high_risk = entity.risk_score > 0.6
        is_predicted_high_risk = risk_score > 0.5
        is_correct = is_high_risk == is_predicted_high_risk

        result = {
            'entity_id': entity.id,
            'entity_name': entity.name,
            'entity_type': entity.type.value,
            'true_risk_score': entity.risk_score,
            'true_risk_level': "high" if entity.risk_score > 0.6 else "low",
            'predicted_risk_score': risk_score,
            'predicted_risk_level': risk_level,
            'confidence': confidence,
            'is_correct': is_correct
            'is_high_risk_entity': entity.risk_score > 0.6
        }
        results.append(result)

    # Calculate accuracy metrics
    correct = sum(1 for r in results if r['is_correct'])
    total = len(results)
    accuracy = correct / total if total > 0 else 0.0

    high_risk_entities = [r for r in results if r['is_high_risk_entity']]
    predicted_high_risk = [r for r in results if r['predicted_risk_score'] > 0.5]

    if len(high_risk_entities) > 0:
        high_risk_precision = sum(1 for r in predicted_high_risk if r['is_high_risk_entity']) / len(predicted_high_risk)
    else:
        high_risk_precision = 0.0

    metrics = {
        'accuracy': accuracy,
        'num_correct': correct,
        'num_total': total,
        'high_risk_precision': high_risk_precision,
        'num_high_risk_entities': len(high_risk_entities),
        'num_predicted_high_risk': len(predicted_high_risk),
        'avg_true_risk_score': np.mean([r['true_risk_score'] for r in results]),
        'avg_predicted_risk_score': np.mean([r['predicted_risk_score'] for r in results])
        'results': results
    }

    print(f"\n[INFO] Evaluation completed!")
    print(f"   Accuracy: {accuracy:.2%}")
    print(f"   High-risk precision: {high_risk_precision:.2%}")
    print(f"   Correct predictions: {correct}/{total}")

    return metrics


def main():
    """Main function - complete GAT model training."""
    print("=" * 70)
    print("GAT Risk Model Training - Option 1")
    print("Pseudo-label training with rule-based risk detection")
    print("=" * 70)

    # Configuration
    config = {
        'data': {
            'num_entities': 100,  # Number of mock entities
            'high_risk_ratio': 0.3  # Ratio of high-risk entities
        },
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
            'min_delta': 0.001,
            'val_split': 0.2,
            'weight_decay': 5e-4
        },
        'output': {
            'output_dir': 'models/gat_risk_model',
            'model_filename': 'gat_risk_model.pt'
        }
    }

    # Check device
    if torch.cuda.is_available():
        config['training']['device'] = 'cuda'
        print(f"[INFO] Using CUDA: {torch.cuda.get_device_name(0)}")
    else:
        config['training']['device'] = 'cpu'
        print(f"[INFO] Using CPU")

    # Step 1: Create mock data
    entities, relationships, risk_findings = create_mock_skill_data(
        num_entities=config['data']['num_entities']
    )

    # Step 2: Prepare graph data
    data = prepare_graph_data(entities, relationships)

    # Step 3: Train model
    model, training_metrics = train_gat_model(data, config['training'])

    # Step 4: Save model
    output_dir = config['output']['output_dir']
    save_model(model, training_metrics, output_dir, config)

    # Step 5: Evaluate model
    evaluation_metrics = evaluate_model(model, data, entities)

    # Step 6: Save evaluation results
    evaluation_path = os.path.join(output_dir, 'evaluation_results.json')

    serializable_eval = {}
    for key, value in evaluation_metrics.items():
        if key != 'results':
            serializable_eval[key] = value
        elif isinstance(value, list):
            serializable_eval[key] = [
                {k: v for k, v in r.items() if not isinstance(v, (list, dict, np.ndarray))}
                for r in value
            ]
        else:
            pass

    with open(evaluation_path, 'w', encoding='utf-8') as f:
        json.dump(serializable_eval, f, indent=2)

    print(f"   Evaluation results saved to: {evaluation_path}")

    # Step 7: Summary
    print("\n" + "=" * 70)
    print("Training Complete!")
    print("=" * 70)

    print(f"\nTraining Results:")
    print(f"  Final train loss: {training_metrics['final_train_loss']:.4f}")
    print(f"  Best val loss: {training_metrics['best_val_loss']:.4f}")
    print(f"  Epochs: {training_metrics['num_epochs']}")

    print(f"\nEvaluation Results:")
    print(f"  Accuracy: {evaluation_metrics['accuracy']:.2%}")
    print(f"  High-risk precision: {evaluation_metrics['high_risk_precision']:.2%}")
    print(f"  Correct predictions: {evaluation_metrics['num_correct']}/{evaluation_metrics['num_total']}")

    print(f"\nRisk Distribution:")
    print(f"  Avg true risk: {evaluation_metrics['avg_true_risk_score']:.3f}")
    print(f"  Avg predicted risk: {evaluation_metrics['avg_predicted_risk_score']:.3f}")

    print(f"\nModel Info:")
    print(f"  Model type: GAT (Graph Attention Network)")
    print(f"  Num heads: {config['model']['num_heads']}")
    print(f"  Hidden dim: {config['model']['hidden_channels']}")
    print(f"  Dropout: {config['model']['dropout']}")

    print(f"\nOutput Files:")
    print(f"  Model: {os.path.join(output_dir, config['output']['model_filename'])}")
    print(f"  Training metrics: {os.path.join(output_dir, 'training_metrics.json')}")
    print(f"  Evaluation results: {os.path.join(output_dir, 'evaluation_results.json')}")

    print("\n" + "=" * 70)
    print("Next Steps:")
    print("1. Review training metrics")
    print("2. Test model on real skill files")
    print("3. Adjust hyperparameters if needed")
    print("4. Integrate model into SkillGraph pipeline")
    print("=" * 70)


if __name__ == '__main__':
    main()
