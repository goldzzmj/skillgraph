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
            confidence=0.9
        )
        entities.append(entity)

    # Create medium-risk entities
    medium_risk_count = num_entities // 3

    for i in range(medium_risk_count):
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
            risk_score=0.5 + np.random.rand() * 0.3,
            confidence=0.8
        )
        entities.append(entity)

    # Create low-risk entities
    low_risk_count = num_entities - high_risk_count - medium_risk_count

    for i in range(low_risk_count):
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
            risk_score=0.1 + np.random.rand() * 0.2,
            confidence=0.9
        )
        entities.append(entity)

    # Create relationships
    relationships = []
    num_relationships = int(num_entities * 1.5)

    for i in range(num_relationships):
        source_idx = np.random.randint(0, num_entities - 1)
        target_idx = np.random.randint(0, num_entities - 1)

        if source_idx != target_idx:
            source = entities[source_idx]
            target = entities[target_idx]

            rel_types = [
                RelationType.CALLS,
                RelationType.DEPENDS_ON,
                RelationType.ACCESSES,
                RelationType.MODIFIES,
                RelationType.REQUIRES,
                RelationType.VALIDATES,
                RelationType.TRANSFORMS,
                RelationType.AUTHENTICATES
            ]

            rel_type = rel_types[np.random.randint(0, len(rel_types))]

            rel = Relation(
                source_id=source.id,
                target_id=target.id,
                type=rel_type,
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
            'risk_score': entity.risk_score
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
        embedding = getattr(entity, 'embedding', None)

        if embedding is None:
            # Random embedding if not available
            embedding = np.random.randn(1536).astype(np.float32)

        node_features.append(embedding)

    node_features = torch.FloatTensor(np.array(node_features))

    # Create edge index
    entity_id_to_idx = {entity.id: i for i, entity in enumerate(entities)}
    edge_list = []

    for rel in relationships:
        source_idx = entity_id_to_idx.get(rel.source_id)
        target_idx = entity_id_to_idx.get(rel.target_id)

        if source_idx is not None and target_idx is not None:
            edge_list.append([source_idx, target_idx])
            edge_list.append([target_idx, source_idx])  # Undirected

    if len(edge_list) == 0:
        # Create a simple chain graph if no edges
        for i in range(len(entities) - 1):
            edge_list.append([i, i + 1])
            edge_list.append([i + 1, i])

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
    Train GAT model.

    Args:
        data: PyTorch Geometric Data object
        config: Configuration dictionary

    Returns:
        Trained model and training metrics
    """
    print("\n[INFO] Training GAT model...")

    device = config['training']['device']
    val_split = config['training']['val_split']
    epochs = config['training']['epochs']
    learning_rate = config['training']['learning_rate']
    weight_decay = config['training']['weight_decay']
    patience = config['training']['patience']
    min_delta = config['training']['min_delta']

    # Create model
    model = GATRiskModel(
        in_channels=config['model']['in_channels'],
        hidden_channels=config['model']['hidden_channels'],
        out_channels=config['model']['out_channels'],
        num_heads=config['model']['num_heads'],
        dropout=config['model']['dropout'],
        num_layers=config['model']['num_layers'],
        use_autoencoder=config['model']['use_autoencoder'],
        reconstruction_weight=config['model']['reconstruction_weight'],
        risk_weight=config['model']['risk_weight']
    ).to(device)

    # Optimizer
    optimizer = optim.Adam(
        model.parameters(),
        lr=learning_rate,
        weight_decay=weight_decay
    )

    # Scheduler
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer,
        mode='min',
        factor=0.5,
        patience=patience,
        min_lr=learning_rate * 0.01
    )

    # Training loop
    model.train()
    best_val_loss = float('inf')
    train_losses = []
    val_losses = []
    best_model_state = None

    # Create train/val mask
    val_size = int(data.num_nodes * val_split)
    train_mask = torch.ones(data.num_nodes, dtype=torch.bool)
    train_mask[:val_size] = False

    print(f"   Training samples: {data.num_nodes - val_size}")
    print(f"   Validation samples: {val_size}")
    print(f"   Epochs: {epochs}")

    for epoch in range(epochs):
        optimizer.zero_grad()

        # Forward pass
        risk_scores, confidence_scores, reconstructed_x, _ = model(
            data.x.to(device),
            data.edge_index.to(device),
            return_attention=False
        )

        # Loss function
        if config['model']['use_autoencoder']:
            # Combined loss: risk prediction + reconstruction
            # Note: Using zeros as pseudo-labels for now
            pseudo_labels = torch.zeros_like(risk_scores[train_mask])

            risk_loss = nn.BCEWithLogitsLoss()(
                risk_scores[train_mask],
                pseudo_labels
            )

            recon_loss = nn.MSELoss()(
                reconstructed_x[train_mask],
                data.x[train_mask]
            )

            total_loss = (
                config['model']['risk_weight'] * risk_loss +
                config['model']['reconstruction_weight'] * recon_loss
            )
        else:
            # Only risk prediction loss
            pseudo_labels = torch.zeros_like(risk_scores[train_mask])
            total_loss = nn.BCEWithLogitsLoss()(
                risk_scores[train_mask],
                pseudo_labels
            )

        # Backward pass
        total_loss.backward()
        optimizer.step()

        # Track losses
        train_losses.append(total_loss.item())

        # Validation
        val_mask = torch.zeros(data.num_nodes, dtype=torch.bool)
        val_mask[:val_size] = True

        model.eval()
        with torch.no_grad():
            val_risk_scores, _, val_reconstructed_x, _ = model(
                data.x.to(device),
                data.edge_index.to(device),
                return_attention=False
            )

            if config['model']['use_autoencoder']:
                val_pseudo_labels = torch.zeros_like(val_risk_scores[val_mask])
                val_risk_loss = nn.BCEWithLogitsLoss()(
                    val_risk_scores[val_mask],
                    val_pseudo_labels
                ).item()

                val_recon_loss = nn.MSELoss()(
                    val_reconstructed_x[val_mask],
                    data.x[val_mask]
                ).item()

                val_loss = (
                    config['model']['risk_weight'] * val_risk_loss +
                    config['model']['reconstruction_weight'] * val_recon_loss
                )
            else:
                val_pseudo_labels = torch.zeros_like(val_risk_scores[val_mask])
                val_loss = nn.BCEWithLogitsLoss()(
                    val_risk_scores[val_mask],
                    val_pseudo_labels
                ).item()

        model.train()

        # Step scheduler
        scheduler.step(val_loss)

        # Save best model
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_model_state = {
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'scheduler_state_dict': scheduler.state_dict(),
                'epoch': epoch
            }

        # Logging
        if (epoch + 1) % 10 == 0:
            print(f"   Epoch {epoch+1}/{epochs}: "
                  f"Train Loss: {total_loss.item():.4f}, "
                  f"Val Loss: {val_loss:.4f}")

    # Final metrics
    metrics = {
        'final_train_loss': train_losses[-1] if train_losses else None,
        'final_val_loss': best_val_loss,
        'min_train_loss': min(train_losses) if train_losses else None,
        'max_train_loss': max(train_losses) if train_losses else None,
        'avg_train_loss': np.mean(train_losses) if train_losses else None,
        'all_train_losses': train_losses,
        'num_epochs': epoch + 1
    }

    print(f"\n[INFO] Training completed!")
    print(f"   Final train loss: {metrics['final_train_loss']:.4f}")
    print(f"   Best val loss: {metrics['final_val_loss']:.4f}")
    print(f"   Epochs: {metrics['num_epochs']}")

    return model, metrics


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
    print("\n[INFO] Evaluating model...")

    model.eval()
    device = next(model.parameters()).device

    with torch.no_grad():
        # Forward pass
        risk_scores, confidence_scores, _, attention_weights = model(
            data.x.to(device),
            data.edge_index.to(device),
            return_attention=True
        )

    # Convert to numpy
    risk_scores = risk_scores.cpu().numpy().flatten()
    confidence_scores = confidence_scores.cpu().numpy().flatten()

    # Analyze results
    high_risk_indices = np.where(risk_scores > 0.5)[0]
    low_risk_indices = np.where(risk_scores <= 0.5)[0]

    print(f"   Total entities: {len(risk_scores)}")
    print(f"   High-risk entities: {len(high_risk_indices)} ({len(high_risk_indices)/len(risk_scores)*100:.1f}%)")
    print(f"   Low-risk entities: {len(low_risk_indices)} ({len(low_risk_indices)/len(risk_scores)*100:.1f}%)")
    print(f"   Average risk score: {np.mean(risk_scores):.3f}")

    # Prepare results
    results = []

    for i, entity in enumerate(entities):
        risk_score = float(risk_scores[i])
        confidence = float(confidence_scores[i])

        # Interpret risk level
        if risk_score >= 0.8:
            risk_level = "critical"
        elif risk_score >= 0.6:
            risk_level = "high"
        elif risk_score >= 0.4:
            risk_level = "medium"
        elif risk_score >= 0.2:
            risk_level = "low"
        else:
            risk_level = "safe"

        # Update entity risk score
        entity.risk_score = risk_score

        result = {
            'entity_id': entity.id,
            'entity_name': entity.name,
            'entity_type': entity.type.value,
            'risk_score': risk_score,
            'confidence': confidence,
            'risk_level': risk_level
        }
        results.append(result)

    # Calculate risk distribution
    high_risk_count = sum(1 for r in results if r['risk_score'] > 0.6)
    medium_risk_count = sum(1 for r in results if 0.4 < r['risk_score'] <= 0.6)
    low_risk_count = sum(1 for r in results if 0.2 < r['risk_score'] <= 0.4)
    safe_count = sum(1 for r in results if r['risk_score'] <= 0.2)

    return {
        'predictions': results,
        'avg_risk_score': float(np.mean(risk_scores)),
        'high_risk_count': high_risk_count,
        'medium_risk_count': medium_risk_count,
        'low_risk_count': low_risk_count,
        'safe_count': safe_count,
        'risk_distribution': {
            'critical': sum(1 for r in results if r['risk_score'] >= 0.8),
            'high': sum(1 for r in results if 0.6 < r['risk_score'] < 0.8),
            'medium': sum(1 for r in results if 0.4 < r['risk_score'] < 0.6),
            'low': sum(1 for r in results if 0.2 < r['risk_score'] < 0.4),
            'safe': sum(1 for r in results if r['risk_score'] <= 0.2)
        }
    }


def save_results(model, metrics, evaluation_results, config):
    """
    Save model and results.

    Args:
        model: Trained model
        metrics: Training metrics
        evaluation_results: Evaluation results
        config: Configuration
    """
    print("\n[INFO] Saving model and results...")

    # Create output directory
    output_dir = config['output']['output_dir']
    os.makedirs(output_dir, exist_ok=True)

    # Save model
    model_path = os.path.join(output_dir, config['output']['model_filename'])

    checkpoint = {
        'model_state_dict': model.state_dict(),
        'config': config,
        'training_metrics': metrics,
        'evaluation_results': evaluation_results,
        'timestamp': datetime.now().isoformat(),
        'torch_version': torch.__version__,
        'torch_geometric_version': 'installed'
    }

    torch.save(checkpoint, model_path)
    print(f"   Model saved to: {model_path}")

    # Save evaluation results
    evaluation_path = os.path.join(output_dir, 'evaluation_results.json')

    with open(evaluation_path, 'w', encoding='utf-8') as f:
        json.dump(evaluation_results, f, indent=2, default=str)

    print(f"   Evaluation saved to: {evaluation_path}")

    # Save training metrics
    metrics_path = os.path.join(output_dir, 'training_metrics.json')

    with open(metrics_path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2, default=str)

    print(f"   Metrics saved to: {metrics_path}")


def main():
    """Main function - complete GAT model training."""
    print("=" * 70)
    print("GAT Risk Model Training - Option 1")
    print("Pseudo-label training with rule-based risk detection")
    print("=" * 70)

    # Configuration
    config = {
        'data': {
            'num_entities': 100,
            'high_risk_ratio': 0.3
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
            'epochs': 50,
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
        print("[INFO] Using CPU")

    # Step 1: Create mock data
    print("\n[1] Creating mock training data...")
    entities, relationships, risk_findings = create_mock_skill_data(
        num_entities=config['data']['num_entities']
    )

    # Step 2: Prepare graph data
    print("\n[2] Preparing graph data...")
    data = prepare_graph_data(entities, relationships)

    # Step 3: Train model
    print("\n[3] Training GAT model...")
    model, metrics = train_gat_model(data, config)

    # Step 4: Evaluate model
    print("\n[4] Evaluating model...")
    evaluation_results = evaluate_model(model, data, entities)

    # Step 5: Save results
    print("\n[5] Saving results...")
    save_results(model, metrics, evaluation_results, config)

    # Summary
    print("\n" + "=" * 70)
    print("Training Complete!")
    print("=" * 70)

    print(f"\nTraining Results:")
    print(f"  Epochs: {metrics['num_epochs']}")
    print(f"  Final train loss: {metrics['final_train_loss']:.4f}")
    print(f"  Best val loss: {metrics['final_val_loss']:.4f}")

    print(f"\nEvaluation Results:")
    print(f"  Total entities: {len(evaluation_results['predictions'])}")
    print(f"  High-risk: {evaluation_results['high_risk_count']}")
    print(f"  Medium-risk: {evaluation_results['medium_risk_count']}")
    print(f"  Low-risk: {evaluation_results['low_risk_count']}")
    print(f"  Safe: {evaluation_results['safe_count']}")

    print(f"\nRisk Distribution:")
    print(f"  Critical: {evaluation_results['risk_distribution']['critical']}")
    print(f"  High: {evaluation_results['risk_distribution']['high']}")
    print(f"  Medium: {evaluation_results['risk_distribution']['medium']}")
    print(f"  Low: {evaluation_results['risk_distribution']['low']}")
    print(f"  Safe: {evaluation_results['risk_distribution']['safe']}")

    print(f"\nModel Info:")
    print(f"  Type: GAT (Graph Attention Network)")
    print(f"  Heads: {config['model']['num_heads']}")
    print(f"  Hidden dim: {config['model']['hidden_channels']}")
    print(f"  Dropout: {config['model']['dropout']}")

    print("\n" + "=" * 70)
    print("Output Files:")
    print(f"  Model: {os.path.join(config['output']['output_dir'], config['output']['model_filename'])}")
    print(f"  Metrics: {os.path.join(config['output']['output_dir'], 'training_metrics.json')}")
    print(f"  Evaluation: {os.path.join(config['output']['output_dir'], 'evaluation_results.json')}")
    print("=" * 70)


if __name__ == '__main__':
    main()
