"""
GAT Risk Model - Complete Implementation with Multiple Training Strategies

Implements GAT-based risk detection with:
1. Pseudo-label training (rule-based)
2. Self-supervised learning (graph reconstruction)
3. Weak supervision (rule confidence as soft labels)
4. Active learning framework
5. Zero-shot inference capabilities
"""

import os
import json
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import asdict
from datetime import datetime

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    import torch.optim as optim
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("Warning: PyTorch not installed")

try:
    from torch_geometric.nn import GATConv, GCNConv
    from torch_geometric.data import Data, Batch
    from torch_geometric.utils import negative_sampling
    from torch_geometric.utils import k_hop_subgraph
    TORCH_GEOMETRIC_AVAILABLE = True
except ImportError:
    TORCH_GEOMETRIC_AVAILABLE = False
    print("Warning: PyTorch Geometric not installed")

from .models import Entity, Relationship, EntityType


class GATRiskModel(nn.Module):
    """
    Complete GAT-based risk prediction model.

    Features:
    - Multi-head attention for interpretable risk scoring
    - Graph autoencoder for self-supervised learning
    - Support for both supervised and unsupervised training
    - Attention weight extraction for interpretability
    """

    def __init__(
        self,
        in_channels: int = 1536,
        hidden_channels: int = 128,
        out_channels: int = 64,
        num_heads: int = 4,
        dropout: float = 0.6,
        num_layers: int = 2,
        use_autoencoder: bool = True
        reconstruction_weight: float = 0.3
        risk_weight: float = 0.7
    ):
        """
        Initialize GAT risk model.

        Args:
            in_channels: Input feature dimension (e.g., embedding size)
            hidden_channels: Hidden layer dimension
            out_channels: Output dimension
            num_heads: Number of attention heads
            dropout: Dropout rate
            num_layers: Number of GAT layers
            use_autoencoder: Whether to use graph autoencoder
            reconstruction_weight: Weight for autoencoder loss
            risk_weight: Weight for risk prediction loss
        """
        super().__init__()

        self.in_channels = in_channels
        self.hidden_channels = hidden_channels
        self.out_channels = out_channels
        self.num_heads = num_heads
        self.dropout = dropout
        self.num_layers = num_layers
        self.use_autoencoder = use_autoencoder
        self.reconstruction_weight = reconstruction_weight
        self.risk_weight = risk_weight

        # GAT layers
        self.gat_layers = nn.ModuleList()
        for i in range(num_layers):
            if i == 0:
                # First layer
                gat_conv = GATConv(
                    in_channels,
                    hidden_channels,
                    heads=num_heads,
                    dropout=dropout,
                    concat=True
                )
            elif i == num_layers - 1:
                # Last layer
                gat_conv = GATConv(
                    hidden_channels * num_heads,
                    out_channels,
                    heads=1,
                    dropout=dropout,
                    concat=False
                )
            else:
                # Middle layers
                gat_conv = GATConv(
                    hidden_channels * num_heads,
                    hidden_channels,
                    heads=num_heads,
                    dropout=dropout,
                    concat=True
                )

            self.gat_layers.append(gat_conv)

        # Autoencoder decoder (for self-supervised learning)
        if use_autoencoder:
            self.decoder = nn.Sequential(
                nn.Linear(out_channels, hidden_channels),
                nn.ReLU(),
                nn.Dropout(dropout),
                nn.Linear(hidden_channels, in_channels)
            )
        else:
            self.decoder = None

        # Risk prediction head
        self.risk_head = nn.Sequential(
            nn.Linear(out_channels, hidden_channels // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_channels // 2, 1),
            nn.Sigmoid()  # Risk score in [0, 1]
        )

        # Confidence prediction head (for weak supervision)
        self.confidence_head = nn.Sequential(
            nn.Linear(out_channels, hidden_channels // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_channels // 2, 1),
            nn.Sigmoid()  # Confidence in [0, 1]
        )

        # Store attention weights for interpretability
        self.attention_weights = []

    def forward(self, x, edge_index, return_attention=False):
        """
        Forward pass through GAT layers.

        Args:
            x: Node features [num_nodes, in_channels]
            edge_index: Edge indices [2, num_edges]
            return_attention: Whether to return attention weights

        Returns:
            Tuple of (risk_scores, confidence_scores, reconstructed_x, attention_weights)
        """
        self.attention_weights = []

        # Pass through GAT layers
        for i, gat_layer in enumerate(self.gat_layers):
            x = F.dropout(x, p=self.dropout, training=self.training)

            # Apply GAT layer
            if return_attention and i == 0:
                # Store attention from first layer
                x, attention = gat_layer(x, edge_index, return_attention=True)
                self.attention_weights.append(attention)
            else:
                x = gat_layer(x, edge_index)

            x = F.elu(x)

        # Risk prediction
        risk_scores = self.risk_head(x)

        # Confidence prediction
        confidence_scores = self.confidence_head(x)

        # Reconstruction (for autoencoder)
        if self.use_autoencoder:
            reconstructed_x = self.decoder(x)
        else:
            reconstructed_x = None

        return risk_scores, confidence_scores, reconstructed_x, self.attention_weights

    def get_attention_weights(self) -> List[torch.Tensor]:
        """
        Get stored attention weights.

        Returns:
            List of attention weight tensors
        """
        return self.attention_weights


class GATRiskTrainer:
    """
    GAT model trainer with multiple training strategies.

    Supports:
    1. Pseudo-label training (rule-based labels)
    2. Self-supervised training (graph reconstruction)
    3. Weak supervision (rule confidence as soft labels)
    4. Active learning framework
    5. Zero-shot inference
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize GAT risk trainer.

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}

        # Model configuration
        model_config = self.config.get('model', {})
        self.in_channels = model_config.get('in_channels', 1536)
        self.hidden_channels = model_config.get('hidden_channels', 128)
        self.out_channels = model_config.get('out_channels', 64)
        self.num_heads = model_config.get('num_heads', 4)
        self.dropout = model_config.get('dropout', 0.6)
        self.num_layers = model_config.get('num_layers', 2)
        self.use_autoencoder = model_config.get('use_autoencoder', True)
        self.reconstruction_weight = model_config.get('reconstruction_weight', 0.3)
        self.risk_weight = model_config.get('risk_weight', 0.7)

        # Training configuration
        training_config = self.config.get('training', {})
        self.learning_rate = training_config.get('learning_rate', 0.001)
        self.weight_decay = training_config.get('weight_decay', 5e-4)
        self.patience = training_config.get('patience', 10)
        self.min_delta = training_config.get('min_delta', 0.001)
        self.epochs = training_config.get('epochs', 100)
        self.batch_size = training_config.get('batch_size', 32)
        self.val_split = training_config.get('val_split', 0.2)
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        # Training mode
        self.training_mode = training_config.get('training_mode', 'pseudo_label')  # Options: pseudo_label, self_supervised, weak_supervised, zero_shot

        # Initialize model
        self.model = None
        self.optimizer = None
        self.scheduler = None

        # Training history
        self.train_losses = []
        self.val_losses = []
        self.best_val_loss = float('inf')
        self.best_model_state = None

        # Active learning state
        self.labeled_indices = []
        self.unlabeled_indices = []

    def build_model(self):
        """Build GAT risk model."""
        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch is not installed")

        self.model = GATRiskModel(
            in_channels=self.in_channels,
            hidden_channels=self.hidden_channels,
            out_channels=self.out_channels,
            num_heads=self.num_heads,
            dropout=self.dropout,
            num_layers=self.num_layers,
            use_autoencoder=self.use_autoencoder,
            reconstruction_weight=self.reconstruction_weight,
            risk_weight=self.risk_weight
        ).to(self.device)

        self.optimizer = optim.Adam(
            self.model.parameters(),
            lr=self.learning_rate,
            weight_decay=self.weight_decay
        )

        self.scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer,
            mode='min',
            factor=0.5,
            patience=self.patience,
            min_lr=self.learning_rate * 0.01
        )

        print(f"Model built: {self.model}")
        print(f"Optimizer: {self.optimizer}")
        print(f"Scheduler: {self.scheduler}")
        print(f"Device: {self.device}")

    def prepare_pseudo_labels(
        self,
        entities: List[Entity],
        risk_findings: List[Dict[str, Any]]
    ) -> np.ndarray:
        """
        Generate pseudo-labels from rule-based risk detection.

        Args:
            entities: List of entities
            risk_findings: List of risk findings

        Returns:
            Array of pseudo-labels [0, 1] for risk prediction
        """
        pseudo_labels = np.zeros(len(entities), dtype=np.float32)

        entity_name_to_idx = {entity.id: i for i, entity in enumerate(entities)}

        # Rule-based pseudo-labeling
        for finding in risk_findings:
            content = finding.get('content_snippet', '')
            severity = finding.get('severity', 'medium')
            confidence = finding.get('confidence', 0.8)

            # Find entities mentioned in findings
            for entity in entities:
                if entity.name.lower() in content.lower():
                    idx = entity_name_to_idx.get(entity.id)

                    if idx is not None:
                        # Assign pseudo-label based on severity
                        if severity == 'high':
                            pseudo_labels[idx] = 1.0  # High risk
                        elif severity == 'critical':
                            pseudo_labels[idx] = 1.0  # Critical risk
                        elif severity == 'medium':
                            pseudo_labels[idx] = 0.7  # Medium risk
                        elif severity == 'low':
                            pseudo_labels[idx] = 0.3  # Low risk
                        else:
                            pseudo_labels[idx] = 0.5  # Unknown

        # Confidence-weighted pseudo-labels
        confidences = [getattr(e, 'confidence', 0.8) for e in entities]
        pseudo_labels = pseudo_labels * np.array(confidences).reshape(-1, 1)
        pseudo_labels = np.clip(pseudo_labels, 0.0, 1.0)

        # Count high-risk entities
        high_risk_count = np.sum(pseudo_labels > 0.5)
        low_risk_count = len(pseudo_labels) - high_risk_count

        print(f"Pseudo-labels: {high_risk_count} high-risk, {low_risk_count} low-risk")

        return pseudo_labels

    def prepare_graph_data(
        self,
        entities: List[Entity],
        relationships: List[Relationship],
        pseudo_labels: Optional[np.ndarray] = None
    ) -> Data:
        """
        Prepare PyTorch Geometric Data object.

        Args:
            entities: List of entities
            relationships: List of relationships
            pseudo_labels: Pseudo-labels for supervised training

        Returns:
            PyTorch Geometric Data object
        """
        if not TORCH_GEOMETRIC_AVAILABLE:
            raise RuntimeError("PyTorch Geometric is not installed")

        # Prepare node features
        node_features = []
        for entity in entities:
            embedding = getattr(entity, 'embedding', None)

            if embedding is None:
                # Random embedding if not available
                embedding = np.random.randn(self.in_channels).astype(np.float32)

            node_features.append(embedding)

        node_features = torch.FloatTensor(np.array(node_features))

        # Prepare edge index
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

        # Prepare labels
        if pseudo_labels is not None:
            labels = torch.FloatTensor(pseudo_labels)
        else:
            labels = None

        # Create Data object
        data = Data(
            x=node_features,
            edge_index=edge_index,
            y=labels
        )

        print(f"Graph data prepared: {data.num_nodes} nodes, {data.num_edges} edges")

        return data

    def train_pseudo_label(
        self,
        data: Data,
        val_data: Optional[Data] = None
    ) -> Dict[str, Any]:
        """
        Train with pseudo-labels (supervised learning).

        Args:
            data: Training data
            val_data: Validation data

        Returns:
            Dictionary with training metrics
        """
        print("\n" + "=" * 60)
        print("Training with Pseudo-Labels (Supervised)")
        print("=" * 60)

        self.model.train()
        best_val_loss = float('inf')

        for epoch in range(self.epochs):
            # Forward pass
            self.optimizer.zero_grad()

            if val_data is not None:
                # Separate train/val for supervised
                train_mask = torch.ones(data.num_nodes, dtype=torch.bool)
                num_val = int(data.num_nodes * self.val_split)
                train_mask[-num_val:] = False
            else:
                train_mask = torch.ones(data.num_nodes, dtype=torch.bool)

            risk_scores, confidence_scores, reconstructed_x, _ = self.model(
                data.x, data.edge_index, return_attention=False
            )

            # Loss function
            if self.use_autoencoder:
                # Combined loss: risk prediction + reconstruction
                risk_loss = F.binary_cross_entropy_with_logits(
                    risk_scores[train_mask],
                    data.y[train_mask]
                )

                recon_loss = F.mse_loss(
                    reconstructed_x[train_mask],
                    data.x[train_mask]
                )

                total_loss = (
                    self.risk_weight * risk_loss +
                    self.reconstruction_weight * recon_loss
                )
            else:
                # Only risk prediction loss
                total_loss = F.binary_cross_entropy_with_logits(
                    risk_scores[train_mask],
                    data.y[train_mask]
                )

            # Backward pass
            total_loss.backward()
            self.optimizer.step()

            # Track losses
            self.train_losses.append(total_loss.item())

            # Validation
            if val_data is not None:
                self.model.eval()
                with torch.no_grad():
                    val_risk_scores, _, _, _ = self.model(
                        val_data.x, val_data.edge_index, return_attention=False
                    )

                    val_loss = F.binary_cross_entropy_with_logits(
                        val_risk_scores,
                        val_data.y
                    ).item()

                self.scheduler.step(val_loss)

                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    self.best_model_state = {
                        'model_state_dict': self.model.state_dict(),
                        'optimizer_state_dict': self.optimizer.state_dict(),
                        'epoch': epoch
                    }

                if (epoch + 1) % 10 == 0:
                    print(f"  Epoch {epoch+1}/{self.epochs}: "
                          f"Train Loss: {total_loss.item():.4f}, "
                          f"Val Loss: {val_loss:.4f}")

        # Final metrics
        metrics = {
            'mode': 'pseudo_label',
            'final_train_loss': self.train_losses[-1] if self.train_losses else None,
            'final_val_loss': best_val_loss,
            'train_losses': self.train_losses,
            'num_epochs': self.epochs
        }

        print("\n" + "=" * 60)
        print("Pseudo-Label Training Complete")
        print("=" * 60)

        return metrics

    def train_self_supervised(
        self,
        data: Data
    ) -> Dict[str, Any]:
        """
        Train with self-supervised learning (graph reconstruction).

        Args:
            data: Training data

        Returns:
            Dictionary with training metrics
        """
        print("\n" + "=" * 60)
        print("Training Self-Supervised (Graph Reconstruction)")
        print("=" * 60)

        self.model.train()
        best_val_loss = float('inf')

        for epoch in range(self.epochs):
            self.optimizer.zero_grad()

            # Forward pass (autoencoder only)
            risk_scores, _, reconstructed_x, _ = self.model(
                data.x, data.edge_index, return_attention=False
            )

            # Loss: reconstruction only
            recon_loss = F.mse_loss(
                reconstructed_x,
                data.x
            )

            # Backward pass
            recon_loss.backward()
            self.optimizer.step()

            self.train_losses.append(recon_loss.item())

            if (epoch + 1) % 10 == 0:
                print(f"  Epoch {epoch+1}/{self.epochs}: "
                      f"Recon Loss: {recon_loss.item():.4f}")

            # Simple early stopping
            if len(self.train_losses) > self.patience:
                recent_losses = self.train_losses[-self.patience:]
                if all(l > recent_losses[0] - self.min_delta for l in recent_losses):
                    print(f"  Early stopping at epoch {epoch+1}")
                    break

        metrics = {
            'mode': 'self_supervised',
            'final_train_loss': self.train_losses[-1],
            'train_losses': self.train_losses,
            'num_epochs': epoch + 1
        }

        print("\n" + "=" * 60)
        print("Self-Supervised Training Complete")
        print("=" * 60)

        return metrics

    def train_weak_supervision(
        self,
        data: Data,
        confidences: np.ndarray
    ) -> Dict[str, Any]:
        """
        Train with weak supervision (rule confidences as soft labels).

        Args:
            data: Training data
            confidences: Confidence scores from rules [0, 1]

        Returns:
            Dictionary with training metrics
        """
        print("\n" + "=" * 60)
        print("Training with Weak Supervision")
        print("=" * 60)

        self.model.train()

        # Convert confidences to tensor
        confidence_tensor = torch.FloatTensor(confidences).to(self.device)

        for epoch in range(self.epochs):
            self.optimizer.zero_grad()

            # Forward pass
            risk_scores, confidence_scores, _, _ = self.model(
                data.x, data.edge_index, return_attention=False
            )

            # Loss: risk prediction + confidence prediction
            risk_loss = F.binary_cross_entropy_with_logits(
                risk_scores,
                data.y
            )

            confidence_loss = F.mse_loss(
                confidence_scores,
                confidence_tensor
            )

            # Combined loss
            total_loss = 0.7 * risk_loss + 0.3 * confidence_loss

            # Backward pass
            total_loss.backward()
            self.optimizer.step()

            self.train_losses.append(total_loss.item())

            if (epoch + 1) % 10 == 0:
                print(f"  Epoch {epoch+1}/{self.epochs}: "
                      f"Total Loss: {total_loss.item():.4f}, "
                      f"Risk Loss: {risk_loss.item():.4f}, "
                      f"Conf Loss: {confidence_loss.item():.4f}")

        metrics = {
            'mode': 'weak_supervision',
            'final_train_loss': self.train_losses[-1] if self.train_losses else None,
            'train_losses': self.train_losses,
            'num_epochs': self.epochs
        }

        print("\n" + "=" * 60)
        print("Weak Supervision Training Complete")
        print("=" * 60)

        return metrics

    def zero_shot_inference(
        self,
        data: Data
    ) -> Dict[str, Any]:
        """
        Perform zero-shot inference without training.

        Args:
            data: Graph data

        Returns:
            Dictionary with inference results
        """
        print("\n" + "=" * 60)
        print("Zero-Shot Inference")
        print("=" * 60)

        self.model.eval()

        with torch.no_grad():
            # Forward pass
            risk_scores, confidence_scores, _, attention_weights = self.model(
                data.x,
                data.edge_index,
                return_attention=True
            )

        # Convert to numpy
            risk_scores = risk_scores.cpu().numpy().flatten()
            confidence_scores = confidence_scores.cpu().numpy().flatten()

        # Analyze results
        high_risk_indices = np.where(risk_scores > 0.5)[0]
        low_risk_indices = np.where(risk_scores <= 0.5)[0]

        print(f"  Total entities: {len(risk_scores)}")
        print(f"  High-risk entities: {len(high_risk_indices)} ({len(high_risk_indices)/len(risk_scores)*100:.1f}%)")
        print(f"  Low-risk entities: {len(low_risk_indices)} ({len(low_risk_indices)/len(risk_scores)*100:.1f}%)")
        print(f"  Average risk score: {np.mean(risk_scores):.3f}")
        print(f"  Average confidence: {np.mean(confidence_scores):.3f}")

        # Get attention weights
        attention_list = []
        for attn_weights in attention_weights:
            attn_numpy = attn_weights.cpu().numpy()
            attention_list.append(attn_numpy)

        results = {
            'risk_scores': risk_scores,
            'confidence_scores': confidence_scores,
            'high_risk_indices': high_risk_indices.tolist(),
            'low_risk_indices': low_risk_indices.tolist(),
            'avg_risk_score': float(np.mean(risk_scores)),
            'attention_weights': attention_list,
            'num_high_risk': int(len(high_risk_indices))
            'num_low_risk': int(len(low_risk_indices))
        }

        print("\n" + "=" * 60)
        print("Zero-Shot Inference Complete")
        print("=" * 60)

        return results

    def predict_risk(
        self,
        entities: List[Entity],
        relationships: List[Relationship],
        return_attention: bool = False
    ) -> Dict[str, Any]:
        """
        Predict risk scores for entities.

        Args:
            entities: List of entities
            relationships: List of relationships
            return_attention: Whether to return attention weights

        Returns:
            Dictionary with prediction results
        """
        if self.model is None:
            raise RuntimeError("Model not built. Call build_model() first.")

        # Prepare graph data
        data = self.prepare_graph_data(entities, relationships)

        # Inference
        self.model.eval()
        with torch.no_grad():
            risk_scores, confidence_scores, _, attention_weights = self.model(
                data.x.to(self.device),
                data.edge_index.to(self.device),
                return_attention=return_attention
            )

        # Convert to numpy
        risk_scores = risk_scores.cpu().numpy().flatten()
        confidence_scores = confidence_scores.cpu().numpy().flatten()

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
                'risk_score': risk_score,
                'confidence': confidence,
                'risk_level': risk_level
            }
            results.append(result)

        return {
            'predictions': results,
            'avg_risk_score': float(np.mean(risk_scores)),
            'num_high_risk': int(np.sum(risk_scores > 0.6))
            'risk_distribution': {
                'critical': int(np.sum(risk_scores >= 0.8)),
                'high': int(np.sum((risk_scores >= 0.6) & (risk_scores < 0.8))),
                'medium': int(np.sum((risk_scores >= 0.4) & (risk_scores < 0.6))),
                'low': int(np.sum((risk_scores >= 0.2) & (risk_scores < 0.4))),
                'safe': int(np.sum(risk_scores < 0.2))
            }
        }

    def save_model(self, filepath: str):
        """
        Save model checkpoint.

        Args:
            filepath: Path to save model
        """
        if self.best_model_state is None:
            print("Warning: No best model state saved during training")
            return

        import os
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        checkpoint = {
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'scheduler_state_dict': self.scheduler.state_dict(),
            'config': self.config,
            'train_losses': self.train_losses
            'best_val_loss': self.best_val_loss
        }

        torch.save(checkpoint, filepath)
        print(f"Model saved to: {filepath}")

    def load_model(self, filepath: str):
        """
        Load model checkpoint.

        Args:
            filepath: Path to load model from
        """
        import os

        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Model file not found: {filepath}")

        checkpoint = torch.load(filepath)

        # Restore model state
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.scheduler.load_state_dict(checkpoint['scheduler_state_dict'])

        self.config = checkpoint.get('config', self.config)
        self.train_losses = checkpoint.get('train_losses', [])

        print(f"Model loaded from: {filepath}")
        print(f"Restored training loss: {self.train_losses[-1] if self.train_losses else 'N/A'}")

    def get_training_summary(self) -> Dict[str, Any]:
        """
        Get training summary.

        Returns:
            Dictionary with training statistics
        """
        if not self.train_losses:
            return {'status': 'No training history'}

        return {
            'status': 'Trained',
            'num_epochs': len(self.train_losses),
            'final_loss': self.train_losses[-1],
            'min_loss': min(self.train_losses) if self.train_losses else None,
            'max_loss': max(self.train_losses) if self.train_losses else None,
            'avg_loss': np.mean(self.train_losses) if self.train_losses else None,
            'config': self.config
        }
