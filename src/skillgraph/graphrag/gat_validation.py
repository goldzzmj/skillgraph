"""
GAT Technical Validation Prototype

Small-scale GAT implementation for validating the hybrid approach:
- GAT risk model with attention mechanism
- Pseudo-label generation
- Training and validation
- Attention weight visualization
- Risk score validation
"""

import os
import json
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import asdict
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("Warning: PyTorch not installed. Install with: pip install torch")

try:
    from torch_geometric.nn import GATConv
    from torch_geometric.data import Data, DataLoader
    from torch_geometric.utils import negative_sampling
    TORCH_GEOMETRIC_AVAILABLE = True
except ImportError:
    TORCH_GEOMETRIC_AVAILABLE = False
    print("Warning: torch-geometric not installed. Install with: pip install torch-geometric")


class GATRiskValidator:
    """
    Technical validator for GAT-based risk detection.

    Features:
    - Small-scale GAT model (for validation)
    - Pseudo-label generation from rules
    - Attention weight visualization
    - Risk score validation
    - Performance benchmarks
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize GAT validator.

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.device = self.config.get('validation', {}).get('device', 'cpu')

        # Model parameters
        self.in_channels = self.config.get('model', {}).get('in_channels', 1536)
        self.hidden_channels = self.config.get('model', {}).get('hidden_channels', 64)
        self.out_channels = self.config.get('model', {}).get('out_channels', 1)
        self.num_heads = self.config.get('model', {}).get('num_heads', 4)
        self.dropout = self.config.get('model', {}).get('dropout', 0.6)

        # Training parameters
        self.learning_rate = self.config.get('training', {}).get('learning_rate', 0.001)
        self.epochs = self.config.get('training', {}).get('epochs', 50)
        self.batch_size = self.config.get('training', {}).get('batch_size', 32)

        # Validation thresholds
        self.risk_threshold = self.config.get('validation', {}).get('risk_threshold', 0.5)

        # Initialize model
        self.model = None

    def generate_pseudo_labels(
        self,
        entities: List[Any],
        risk_findings: List[Dict[str, Any]]
    ) -> np.ndarray:
        """
        Generate pseudo-labels from rule-based risk scores.

        Args:
            entities: List of entities
            risk_findings: List of risk findings

        Returns:
            Array of pseudo-labels (0 = low risk, 1 = high risk)
        """
        pseudo_labels = []

        for entity in entities:
            # Base risk from entity properties
            base_risk = getattr(entity, 'risk_score', 0.0)

            # Boost risk if entity appears in findings
            entity_name = getattr(entity, 'name', '').lower()
            in_findings = False

            for finding in risk_findings:
                content = finding.get('content_snippet', '')
                if entity_name in content.lower():
                    in_findings = True
                    base_risk = min(1.0, base_risk * 1.5)
                    break

            # Check for risk indicators in name
            risk_keywords = [
                '.env', '.ssh', '.key', '.pem', 'password', 'secret',
                'token', 'credential', 'admin', 'root', 'sudo',
                'http://', 'https://', 'upload', 'download', 'exec'
            ]

            for keyword in risk_keywords:
                if keyword in entity_name.lower():
                    base_risk = min(1.0, base_risk + 0.1)

            # Generate pseudo-label
            pseudo_label = 1 if base_risk >= self.risk_threshold else 0
            pseudo_labels.append(pseudo_label)

        return np.array(pseudo_labels)

    def create_small_graph(
        self,
        entities: List[Any],
        relationships: List[Any],
        pseudo_labels: np.ndarray
    ) -> Optional[Data]:
        """
        Create small-scale graph for validation.

        Args:
            entities: List of entities
            relationships: List of relationships
            pseudo_labels: Pseudo-labels

        Returns:
            PyTorch Geometric Data object
        """
        if not TORCH_AVAILABLE or not TORCH_GEOMETRIC_AVAILABLE:
            print("PyTorch or PyTorch Geometric not available")
            return None

        # Limit to small scale for validation
        max_nodes = 100
        entities = entities[:max_nodes]
        pseudo_labels = pseudo_labels[:max_nodes]

        if len(entities) == 0:
            print("No entities provided")
            return None

        # Create node features (embeddings)
        node_features = []
        for entity in entities:
            embedding = getattr(entity, 'embedding', None)
            if embedding is None:
                # Random embedding for validation
                embedding = np.random.randn(self.in_channels)
            node_features.append(embedding)

        node_features = torch.FloatTensor(np.array(node_features))

        # Create edge index
        entity_id_to_idx = {entity.id: i for i, entity in enumerate(entities)}
        edge_list = []

        for rel in relationships:
            source_idx = entity_id_to_idx.get(rel.source_id)
            target_idx = entity_id_to_idx.get(rel.target_id)

            if source_idx is not None and target_idx is not None:
                if source_idx < max_nodes and target_idx < max_nodes:
                    edge_list.append([source_idx, target_idx])
                    edge_list.append([target_idx, source_idx])  # Undirected

        if len(edge_list) == 0:
            # Create a simple chain graph if no edges
            for i in range(len(entities) - 1):
                edge_list.append([i, i + 1])
                edge_list.append([i + 1, i])

        edge_index = torch.tensor(edge_list, dtype=torch.long).t().contiguous()

        # Create labels
        labels = torch.FloatTensor(pseudo_labels)

        # Create PyTorch Geometric Data object
        data = Data(
            x=node_features,
            edge_index=edge_index,
            y=labels
        )

        return data

    def build_gat_model(self) -> Optional[nn.Module]:
        """
        Build small-scale GAT model for validation.

        Returns:
            GAT model or None if dependencies unavailable
        """
        if not TORCH_AVAILABLE or not TORCH_GEOMETRIC_AVAILABLE:
            return None

        class GATRiskModel(nn.Module):
            """
            Small-scale GAT model for risk prediction.
            """
            def __init__(self, in_channels, hidden_channels, out_channels, num_heads, dropout):
                super().__init__()
                self.dropout = dropout

                # First GAT layer
                self.conv1 = GATConv(
                    in_channels,
                    hidden_channels,
                    heads=num_heads,
                    dropout=dropout,
                    concat=True
                )

                # Second GAT layer
                self.conv2 = GATConv(
                    hidden_channels * num_heads,
                    out_channels,
                    heads=1,
                    concat=False
                )

            def forward(self, x, edge_index):
                # Apply dropout
                x = F.dropout(x, p=self.dropout, training=self.training)

                # First GAT layer
                x = F.elu(self.conv1(x, edge_index))
                x = F.dropout(x, p=self.dropout, training=self.training)

                # Second GAT layer
                x = self.conv2(x, edge_index)

                return x

        model = GATRiskModel(
            self.in_channels,
            self.hidden_channels,
            self.out_channels,
            self.num_heads,
            self.dropout
        )

        return model

    def train_model(
        self,
        data: Data,
        validation_split: float = 0.2
    ) -> Dict[str, Any]:
        """
        Train GAT model with validation.

        Args:
            data: PyTorch Geometric Data object
            validation_split: Validation split ratio

        Returns:
            Dictionary with training metrics
        """
        if self.model is None:
            self.model = self.build_gat_model()

        if self.model is None:
            return {'error': 'Model not available'}

        # Move model to device
        self.model = self.model.to(self.device)
        data = data.to(self.device)

        # Split into train/val
        num_nodes = data.num_nodes
        val_size = int(num_nodes * validation_split)
        train_size = num_nodes - val_size

        # Simple train/val split
        train_mask = torch.zeros(num_nodes, dtype=torch.bool)
        train_mask[:train_size] = True

        val_mask = torch.zeros(num_nodes, dtype=torch.bool)
        val_mask[train_size:train_size+val_size] = True

        # Optimizer
        optimizer = torch.optim.Adam(self.model.parameters(), lr=self.learning_rate)

        # Training loop
        train_losses = []
        val_losses = []
        val_accuracies = []

        print(f"Training GAT model for {self.epochs} epochs...")

        for epoch in range(self.epochs):
            # Train
            self.model.train()
            optimizer.zero_grad()

            # Forward pass
            out = self.model(data.x, data.edge_index)
            out = out.squeeze()

            # Loss (binary cross-entropy)
            loss = F.binary_cross_entropy_with_logits(
                out[train_mask],
                data.y[train_mask]
            )

            # Backward pass
            loss.backward()
            optimizer.step()

            train_losses.append(loss.item())

            # Validation
            self.model.eval()
            with torch.no_grad():
                out = self.model(data.x, data.edge_index)
                out = out.squeeze()

                val_loss = F.binary_cross_entropy_with_logits(
                    out[val_mask],
                    data.y[val_mask]
                )

                # Accuracy
                val_pred = torch.sigmoid(out[val_mask])
                val_labels = data.y[val_mask]
                val_acc = ((val_pred > 0.5) == val_labels).float().mean().item()

                val_losses.append(val_loss.item())
                val_accuracies.append(val_acc)

            if (epoch + 1) % 10 == 0:
                print(f"  Epoch {epoch+1}/{self.epochs}: "
                      f"Train Loss: {loss.item():.4f}, "
                      f"Val Loss: {val_loss.item():.4f}, "
                      f"Val Acc: {val_acc:.2%}")

        # Final metrics
        metrics = {
            'train_loss': train_losses[-1],
            'val_loss': val_losses[-1],
            'val_accuracy': val_accuracies[-1],
            'best_val_accuracy': max(val_accuracies),
            'all_train_losses': train_losses,
            'all_val_losses': val_losses,
            'all_val_accuracies': val_accuracies
        }

        return metrics

    def extract_attention_weights(
        self,
        data: Data,
        entities: List[Any]
    ) -> Dict[int, List[Tuple[int, float]]]:
        """
        Extract attention weights for interpretability.

        Args:
            data: PyTorch Geometric Data object
            entities: List of entities

        Returns:
            Dictionary mapping entity index to attention weights
        """
        if self.model is None:
            return {}

        # Forward pass with gradients disabled
        self.model.eval()
        with torch.no_grad():
            out = self.model(data.x, data.edge_index)

        # Extract attention weights from first GAT layer
        att_weights = self.model.conv1.attentions
        att_weights = att_weights.cpu().numpy()

        # Group attention by target node
        attention_dict = {}
        num_heads = att_weights.shape[1]

        for i, entity in enumerate(entities):
            entity_attention = []

            # Get attention to this node from first layer
            for head in range(num_heads):
                head_attention = att_weights[head, :, i, :]
                # Average attention over all neighbors
                avg_attention = np.mean(head_attention)
                entity_attention.append((head, avg_attention))

            attention_dict[i] = entity_attention

        return attention_dict

    def visualize_attention_weights(
        self,
        attention_dict: Dict[int, List[Tuple[int, float]]],
        entities: List[Any],
        output_path: str = 'output/attention_visualization.png'
    ):
        """
        Visualize attention weights.

        Args:
            attention_dict: Dictionary of attention weights
            entities: List of entities
            output_path: Output path for visualization
        """
        # Create output directory
        import os
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Prepare data for visualization
        max_nodes = 20  # Show only first 20 nodes
        node_names = [e.name for e in entities[:max_nodes]]
        avg_attentions = []

        for i in range(max_nodes):
            if i in attention_dict:
                attentions = attention_dict[i]
                avg_attention = np.mean([att[1] for att in attentions])
                avg_attentions.append(avg_attention)
            else:
                avg_attentions.append(0.0)

        # Create bar chart
        fig, ax = plt.subplots(figsize=(12, 6))
        y_pos = np.arange(max_nodes)
        ax.barh(y_pos, avg_attentions, align='center')
        ax.set_yticks(y_pos)
        ax.set_yticklabels(node_names)
        ax.invert_yaxis()
        ax.set_xlabel('Average Attention Weight')
        ax.set_title('GAT Attention Weights (First 20 Entities)')
        ax.grid(axis='x', alpha=0.3)

        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()

        print(f"Attention visualization saved to: {output_path}")

    def validate_risk_scores(
        self,
        entities: List[Any],
        predictions: np.ndarray,
        pseudo_labels: np.ndarray
    ) -> Dict[str, Any]:
        """
        Validate predicted risk scores against pseudo-labels.

        Args:
            entities: List of entities
            predictions: Predicted risk scores
            pseudo_labels: Ground truth pseudo-labels

        Returns:
            Dictionary with validation metrics
        """
        # Convert predictions to binary labels
        pred_labels = (predictions > 0.5).astype(int)

        # Calculate metrics
        correct = (pred_labels == pseudo_labels).sum()
        total = len(pseudo_labels)
        accuracy = correct / total if total > 0 else 0.0

        # Per-class metrics
        high_risk_correct = ((pred_labels == 1) & (pseudo_labels == 1)).sum()
        high_risk_total = (pseudo_labels == 1).sum()
        high_risk_precision = high_risk_correct / high_risk_total if high_risk_total > 0 else 0.0

        low_risk_correct = ((pred_labels == 0) & (pseudo_labels == 0)).sum()
        low_risk_total = (pseudo_labels == 0).sum()
        low_risk_precision = low_risk_correct / low_risk_total if low_risk_total > 0 else 0.0

        return {
            'accuracy': accuracy,
            'high_risk_precision': high_risk_precision,
            'low_risk_precision': low_risk_precision,
            'total_correct': int(correct),
            'total_predictions': int(total),
            'high_risk_correct': int(high_risk_correct),
            'low_risk_correct': int(low_risk_correct)
        }

    def run_validation(
        self,
        entities: List[Any],
        relationships: List[Any],
        risk_findings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Run complete technical validation.

        Args:
            entities: List of entities
            relationships: List of relationships
            risk_findings: List of risk findings

        Returns:
            Dictionary with validation results
        """
        print("=" * 60)
        print("GAT Technical Validation")
        print("=" * 60)

        results = {}

        # Step 1: Generate pseudo-labels
        print("\n[1] Generating pseudo-labels...")

        pseudo_labels = self.generate_pseudo_labels(entities, risk_findings)

        high_risk_count = (pseudo_labels == 1).sum()
        low_risk_count = (pseudo_labels == 0).sum()

        print(f"   High risk: {high_risk_count}")
        print(f"   Low risk: {low_risk_count}")
        print(f"   Total: {len(pseudo_labels)}")

        results['pseudo_labels'] = {
            'high_risk': int(high_risk_count),
            'low_risk': int(low_risk_count),
            'total': int(len(pseudo_labels))
        }

        # Step 2: Create graph
        print("\n[2] Creating small-scale graph...")

        data = self.create_small_graph(entities, relationships, pseudo_labels)

        if data is None:
            print("   [ERROR] Failed to create graph")
            return results

        print(f"   Nodes: {data.num_nodes}")
        print(f"   Edges: {data.num_edges}")
        print(f"   Features shape: {data.x.shape}")

        results['graph'] = {
            'nodes': int(data.num_nodes),
            'edges': int(data.num_edges),
            'features_shape': list(data.x.shape)
        }

        # Step 3: Train model
        print("\n[3] Training GAT model...")

        if not TORCH_AVAILABLE or not TORCH_GEOMETRIC_AVAILABLE:
            print("   [SKIP] PyTorch or PyTorch Geometric not available")
            return results

        training_metrics = self.train_model(data)

        results['training'] = training_metrics

        print(f"\n   Final Train Loss: {training_metrics['train_loss']:.4f}")
        print(f"   Final Val Loss: {training_metrics['val_loss']:.4f}")
        print(f"   Final Val Acc: {training_metrics['val_accuracy']:.2%}")
        print(f"   Best Val Acc: {training_metrics['best_val_accuracy']:.2%}")

        # Step 4: Extract attention weights
        print("\n[4] Extracting attention weights...")

        attention_dict = self.extract_attention_weights(data, entities)

        print(f"   Extracted attention for {len(attention_dict)} nodes")

        results['attention'] = {
            'num_nodes_with_attention': len(attention_dict)
            'sample_nodes': list(attention_dict.keys())[:5]
        }

        # Step 5: Visualize attention
        print("\n[5] Visualizing attention weights...")

        output_dir = "output/validation"
        attention_path = os.path.join(output_dir, "attention_weights.png")

        try:
            self.visualize_attention_weights(attention_dict, entities, attention_path)
            results['visualization'] = {
                'path': attention_path,
                'success': True
            }
            print(f"   [OK] Attention visualization saved")
        except Exception as e:
            print(f"   [ERROR] Visualization failed: {e}")
            results['visualization'] = {
                'path': attention_path,
                'success': False,
                'error': str(e)
            }

        # Step 6: Validate risk scores
        print("\n[6] Validating risk scores...")

        self.model.eval()
        with torch.no_grad():
            predictions = self.model(data.x, data.edge_index)
            predictions = predictions.squeeze().cpu().numpy()

        validation_metrics = self.validate_risk_scores(
            entities,
            predictions,
            pseudo_labels
        )

        results['validation'] = validation_metrics

        print(f"   Accuracy: {validation_metrics['accuracy']:.2%}")
        print(f"   High Risk Precision: {validation_metrics['high_risk_precision']:.2%}")
        print(f"   Low Risk Precision: {validation_metrics['low_risk_precision']:.2%}")
        print(f"   Correct: {validation_metrics['total_correct']}/{validation_metrics['total_predictions']}")

        # Step 7: Summary
        print("\n" + "=" * 60)
        print("Validation Summary")
        print("=" * 60)

        print(f"\n✓ Pseudo-labels: {high_risk_count} high, {low_risk_count} low")
        print(f"✓ Graph: {data.num_nodes} nodes, {data.num_edges} edges")
        print(f"✓ Training: Final val acc = {training_metrics['val_accuracy']:.2%}")
        print(f"✓ Validation: Overall acc = {validation_metrics['accuracy']:.2%}")
        print(f"✓ Visualization: Attention weights saved")

        # Overall assessment
        print(f"\n🎯 Overall Assessment:")

        if training_metrics['val_accuracy'] > 0.8:
            print(f"   ✅ GAT model learned effectively (>80% accuracy)")
        elif training_metrics['val_accuracy'] > 0.7:
            print(f"   ⚠️  GAT model performed adequately (70-80% accuracy)")
        else:
            print(f"   ❌ GAT model needs improvement (<70% accuracy)")

        if validation_metrics['accuracy'] > 0.8:
            print(f"   ✅ Risk prediction is highly accurate (>80% accuracy)")
        elif validation_metrics['accuracy'] > 0.7:
            print(f"   ⚠️  Risk prediction is reasonably accurate (70-80% accuracy)")
        else:
            print(f"   ❌ Risk prediction needs improvement (<70% accuracy)")

        # Recommendation
        print(f"\n📋 Recommendation:")

        if training_metrics['val_accuracy'] > 0.8 and validation_metrics['accuracy'] > 0.8:
            print(f"   ✅ PROCEED: GAT approach is validated and recommended")
        elif training_metrics['val_accuracy'] > 0.7:
            print(f"   ⚠️  PROCEED WITH CAUTION: GAT shows promise, needs tuning")
        else:
            print(f"   ❌ RECONSIDER: GAT may not be suitable, try simpler approaches")

        print("=" * 60)

        return results

    def save_results(
        self,
        results: Dict[str, Any],
        output_path: str = 'output/validation_results.json'
    ):
        """
        Save validation results to JSON file.

        Args:
            results: Validation results dictionary
            output_path: Output file path
        """
        import os
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Convert numpy arrays to lists for JSON serialization
        serializable_results = {}
        for key, value in results.items():
            serializable_results[key] = self._make_serializable(value)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(serializable_results, f, indent=2)

        print(f"\nValidation results saved to: {output_path}")

    def _make_serializable(self, obj: Any) -> Any:
        """
        Convert object to JSON-serializable format.

        Args:
            obj: Object to convert

        Returns:
            Serializable object
        """
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        elif hasattr(obj, 'tolist'):  # numpy types
            return obj.tolist()
        else:
            return obj


def main():
    """Main function for GAT validation."""
    # This is a prototype - in real usage, you would:
    # 1. Load real entities and relationships from SkillGraph
    # 2. Load real risk findings
    # 3. Run validation

    print("GAT Technical Validation Prototype")
    print("This is a small-scale prototype for validating the GAT approach")
    print("In production, this will be integrated with the full SkillGraph pipeline")

    # Example usage:
    validator = GATRiskValidator()

    # validator.run_validation(entities, relationships, risk_findings)
    # validator.save_results(results)

if __name__ == '__main__':
    main()
