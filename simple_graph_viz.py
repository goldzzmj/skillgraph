"""
Simple Graph Visualization without dependencies

Simple graph visualization using basic Python libraries.
"""

import json
from typing import Dict, Any, List
import os


def generate_simple_graphviz_output(graph_data: Dict[str, Any]) -> str:
    """Generate simple GraphViz DOT output without external dependencies."""
    lines = ['digraph SkillGraph {']
    lines.append('  rankdir=LR;')
    lines.append('  node [shape=box, style=rounded];')
    
    # Add entity nodes
    for entity in graph_data.get('entities', []):
        node_name = entity['name']
        lines.append(f'    "{node_name}" [color="#4CAF50", label="{node_name} (Entity)"];')
    
    # Add operation nodes
    operation_colors = {
        'web_search': '#1F77B4',
        'data_processing': '#FF7F0E',
        'file_operation': '#2CA02C',
        'llm_call': '#9467BD'
    }
    
    for operation in graph_data.get('operations', []):
        node_name = operation['name']
        operation_type = operation.get('operation_type', 'unknown')
        color = operation_colors.get(operation_type, '#999999')
        lines.append(f'    "{node_name}" [color="{color}", label="{node_name} (Operation)"];')
    
    # Add edges
    edge_index = {}
    for edge in graph_data.get('edges', []):
        source_name = edge.get('source', 'unknown')
        target_name = edge.get('target', 'unknown')
        edge_type = edge.get('type', 'sequential')
        edge_style = 'solid' if edge_type == 'sequential' else 'dashed'
        lines.append(f'    "{source_name}" -> "{target_name}" [style="{edge_style}"];')
        edge_index[(source_name, target_name)] = len(lines) - 1
    
    # Close graph
    lines.append('}')
    
    return '\n'.join(lines)


def generate_ascii_graph(graph_data: Dict[str, Any]) -> str:
    """Generate simple ASCII graph."""
    lines = []
    
    # Create nodes mapping
    node_id_to_name = {}
    
    # Add entity nodes
    for entity in graph_data.get('entities', []):
        node_id_to_name[entity['id']] = entity['name']
    
    # Add operation nodes
    for operation in graph_data.get('operations', []):
        node_id_to_name[operation['id']] = operation['name']
    
    # Generate edges
    for edge in graph_data.get('edges', []):
        source_name = node_id_to_name.get(edge['source'], 'unknown')
        target_name = node_id_to_name.get(edge['target'], 'unknown')
        edge_type = edge.get('type', 'sequential')
        lines.append(f"{source_name} -> {target_name} [{edge_type}]")
    
    return '\n'.join(lines)


def load_test_graph(data_path: str = 'output/test_graph_data.json') -> Dict[str, Any]:
    """Load test graph data."""
    with open(data_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    """Main function for simple graph visualization."""
    print("=" * 60)
    print("Simple Graph Visualization")
    print("=" * 60)
    
    # Load test data
    print("\n[1] Loading test graph data...")
    graph_data = load_test_graph()
    
    print(f"   Loaded {len(graph_data['entities'])} entities")
    print(f"   Loaded {len(graph_data['operations'])} operations")
    print(f"   Loaded {len(graph_data['edges'])} edges")
    
    # Generate GraphViz output
    print("\n[2] Generating GraphViz DOT output...")
    dot_output = generate_simple_graphviz_output(graph_data)
    
    # Save DOT file
    os.makedirs('output', exist_ok=True)
    dot_file_path = 'output/skill_graph_simple.dot'
    with open(dot_file_path, 'w', encoding='utf-8') as f:
        f.write(dot_output)
    
    print(f"   Saved to: {dot_file_path}")
    
    # Generate ASCII graph
    print("\n[3] Generating ASCII graph...")
    ascii_graph = generate_ascii_graph(graph_data)
    
    # Save ASCII file
    ascii_file_path = 'output/skill_graph_simple.txt'
    with open(ascii_file_path, 'w', encoding='utf-8') as f:
        f.write(ascii_graph)
    
    print(f"   Saved to: {ascii_file_path}")
    
    # Print ASCII graph
    print("\n" + "=" * 60)
    print("Graph Visualization (ASCII)")
    print("=" * 60)
    print(ascii_graph)
    print("=" * 60)
    
    # Print DOT graph
    print("\n" + "=" * 60)
    print("Graph Visualization (DOT)")
    print("=" * 60)
    print(dot_output)
    print("=" * 60)
    
    print("\n" + "=" * 60)
    print("Visualization Complete!")
    print("=" * 60)
    print("\nGenerated Files:")
    print(f"  1. {dot_file_path} - GraphViz DOT file")
    print(f"  2. {ascii_file_path} - ASCII graph file")
    print("\nNext step: Update README.md with graph visualization")


if __name__ == "__main__":
    main()
