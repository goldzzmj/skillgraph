"""
Graph Visualization - Test Graph Visualization

Generate visualization for test graph.
"""

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import networkx as nx
from typing import Dict, Any, List, Optional
import json
import os


def create_test_graph(graph_data: Dict[str, Any]) -> nx.Graph:
    """Create NetworkX graph from graph data."""
    G = nx.Graph()
    
    # Create a mapping for node IDs
    node_id_to_name = {}
    
    # Add entity nodes
    for entity in graph_data['entities']:
        node_id = entity['id']
        node_name = entity['name']
        node_id_to_name[node_id] = node_name
        
        # Add node with attributes
        G.add_node(node_name, **{
            'id': entity['id'],
            'type': entity['type'].value,
            'entity_type': entity['entity_type'],
            'description': entity['description'],
            'color': '#4CAF50'  # Green for entities
        })
    
    # Add operation nodes
    for operation in graph_data['operations']:
        node_id = operation['id']
        node_name = operation['name']
        node_id_to_name[node_id] = node_name
        
        # Color coding based on operation type
        operation_type = operation['operation_type'].value
        if operation_type == 'web_search':
            color = '#1F77B4'  # Blue
        elif operation_type == 'data_processing':
            color = '#FF7F0E'  # Orange
        elif operation_type == 'file_operation':
            color = '#2CA02C'  # Red
        else:
            color = '#9467BD'  # Purple
        
        # Add node with attributes
        G.add_node(node_name, **{
            'id': operation['id'],
            'type': operation['type'].value,
            'operation_type': operation_type['operation_type'].value,
            'description': operation['description'],
            'color': color
        })
    
    # Add edges
    for edge in graph_data['edges']:
        source_name = node_id_to_name[edge['source']]
        target_name = node_id_to_name[edge['target']]
        
        # Get edge type and weight
        edge_type = edge['type']
        weight = edge['properties'].get('weight', 1.0)
        
        # Edge styling based on type
        if edge_type == 'sequential':
            edge_style = 'solid'
            edge_color = '#555555'
        elif edge_type == 'parallel':
            edge_style = 'dashed'
            edge_color = '#FF69B4'
        else:
            edge_style = 'solid'
            edge_color = '#999999'
        
        # Add edge
        G.add_edge(source_name, target_name, **{
            'type': edge_type,
            'weight': weight,
            'style': edge_style,
            'color': edge_color
        })
    
    return G, node_id_to_name


def visualize_graph(G: nx.Graph, output_path: str = 'output/graph_visualization.png'):
    """Visualize graph."""
    # Set up the plot
    plt.figure(figsize=(16, 12))
    pos = nx.spring_layout(G, k=2, iterations=50, seed=42)
    
    # Create color map
    colors = [G.nodes[node]['color'] for node in G.nodes()]
    
    # Draw nodes
    nx.draw_networkx_nodes(G, pos, node_color=colors, node_size=2000, alpha=0.8, font_size=12, font_weight='bold')
    
    # Draw edges
    edge_colors = [G.edges[edge[0], edge[1]]['color'] for edge in G.edges()]
    nx.draw_networkx_edges(G, pos, edge_color=edge_colors, width=2.0, alpha=0.6, arrowsize=20, edge_style='solid')
    
    # Draw node labels
    node_labels = {node: node for node in G.nodes()}
    nx.draw_networkx_labels(G, pos, labels=node_labels, font_size=8, font_weight='normal')
    
    # Add legend
    legend_elements = [
        plt.Line2D([0], [1], color='#4CAF50', linewidth=4, label='Entity'),
        plt.Line2D([0], [1], color='#1F77B4', linewidth=4, label='Web Search'),
        plt.Line2D([0], [1], color='#FF7F0E', linewidth=4, label='Data Processing'),
        plt.Line2D([0], [1], color='#2CA02C', linewidth=4, label='File Operation')
    ]
    plt.legend(handles=legend_elements, loc='upper right', fontsize=12)
    
    # Add title and labels
    plt.title('SkillGraph v1.0.1-beta - Test Graph Visualization', fontsize=16, fontweight='bold', pad=20)
    plt.axis('off')
    
    # Create output directory
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save figure
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Graph visualization saved to: {output_path}")
    
    plt.close()


def create_graphviz_graph(graph_data: Dict[str, Any], output_path: str = 'output/graph_visualization.dot'):
    """Create GraphViz DOT file."""
    dot_lines = [
        'digraph SkillGraph {',
        '  rankdir=LR;',
        '  node [shape=box, style=rounded];'
    ]
    
    # Add entity nodes
    for entity in graph_data['entities']:
        node_name = entity['name']
        dot_lines.append(f'    "{node_name}" [color="#4CAF50"];')
    
    # Add operation nodes
    operation_colors = {
        'web_search': '#1F77B4',
        'data_processing': '#FF7F0E',
        'file_operation': '#2CA02C',
        'llm_call': '#9467BD'
    }
    
    for operation in graph_data['operations']:
        node_name = operation['name']
        operation_type = operation['operation_type'].value
        color = operation_colors.get(operation_type, '#9467BD')
        dot_lines.append(f'    "{node_name}" [color="{color}"];')
    
    # Add edges
    for edge in graph_data['edges']:
        source_name = None
        target_name = None
        
        # Find source node
        if edge['source'] in [e['id'] for e in graph_data['entities']]:
            source_name = next((e['name'] for e in graph_data['entities'] if e['id'] == edge['source']), None)
        else:
            source_name = next((o['name'] for o in graph_data['operations'] if o['id'] == edge['source']), None)
        
        # Find target node
        if edge['target'] in [e['id'] for e in graph_data['entities']]:
            target_name = next((e['name'] for e in graph_data['entities'] if e['id'] == edge['target']), None)
        else:
            target_name = next((o['name'] for o in graph_data['operations'] if o['id'] == edge['target']), None)
        
        if source_name and target_name:
            edge_style = 'solid' if edge['type'] == 'sequential' else 'dashed'
            dot_lines.append(f'    "{source_name}" -> "{target_name}" [style="{edge_style}"];')
    
    # Close graph
    dot_lines.append('}')
    
    # Save DOT file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(dot_lines))
    
    print(f"GraphViz DOT file saved to: {output_path}")


def load_graph_data(data_path: str = 'output/test_graph_data.json') -> Dict[str, Any]:
    """Load graph data from JSON file."""
    with open(data_path, 'r', encoding='utf-8') as f:
        return json.load(f)


if __name__ == "__main__":
    print("=" * 60)
    print("Creating Graph Visualization")
    print("=" * 60)
    
    # Load test data
    graph_data = load_graph_data()
    
    # Create NetworkX graph
    G, node_id_to_name = create_test_graph(graph_data)
    
    # Visualize with Matplotlib
    print("\n[1] Creating Matplotlib visualization...")
    visualize_graph(G, 'output/graph_visualization_matplotlib.png')
    
    # Create GraphViz DOT file
    print("\n[2] Creating GraphViz DOT file...")
    create_graphviz_graph(graph_data, 'output/graph_visualization.dot')
    
    print("\n" + "=" * 60)
    print("Visualization Complete!")
    print("=" * 60)
    print("\nGenerated Files:")
    print("  1. output/test_graph_data.json - Test graph data")
    print("  2. output/graph_visualization_matplotlib.png - Matplotlib visualization")
    print("  3. output/graph_visualization.dot - GraphViz DOT file")
    print("\nNext step: Update README.md with graph visualization")
