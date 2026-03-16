"""
Streamlit Graph Visualization

Streamlit application to visualize test graph data.
"""

import sys
import os

# 确保使用虚拟环境中的包，但保留标准库
venv_site_packages = r'E:\Project\SkillGraph\venv\Lib\site-packages'
if os.path.exists(venv_site_packages):
    # 只移除 Anaconda 的 site-packages 路径，保留标准库
    sys.path = [p for p in sys.path if 'anaconda' not in p.lower() or 'site-packages' not in p.lower()]
    if venv_site_packages not in sys.path:
        sys.path.insert(0, venv_site_packages)

import streamlit as st
import json
import networkx as nx
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from typing import Dict, Any, List

# Set page configuration
st.set_page_config(
    page_title="SkillGraph Graph Visualization",
    page_icon="📊",
    layout="wide"
)

# Load test graph data
@st.cache_data
def load_test_graph():
    """Load test graph data."""
    # 使用脚本所在目录的相对路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(script_dir, 'output', 'test_graph_data.json')
    with open(data_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def create_networkx_graph(graph_data: Dict[str, Any]) -> nx.Graph:
    """Create NetworkX graph from graph data."""
    G = nx.DiGraph()
    
    # Create node ID to name mapping
    node_id_to_name = {}
    
    # Add entity nodes
    for entity in graph_data['entities']:
        node_id = entity['id']
        node_name = entity['name']
        node_id_to_name[node_id] = node_name
        
        # Add node with attributes
        G.add_node(node_name, **{
            'id': entity['id'],
            'type': entity['type'] if isinstance(entity['type'], str) else entity['type'].value,
            'entity_type': entity.get('entity_type', 'unknown'),
            'description': entity['description'],
            'color': '#4CAF50'  # Green for entities
        })

    # Add operation nodes
    for operation in graph_data['operations']:
        node_id = operation['id']
        node_name = operation['name']
        node_id_to_name[node_id] = node_name

        # Color coding based on operation type
        operation_type = operation['operation_type'] if isinstance(operation['operation_type'], str) else operation['operation_type'].value
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
            'type': operation['type'] if isinstance(operation['type'], str) else operation['type'].value,
            'operation_type': operation_type,
            'description': operation['description'],
            'color': color
        })
    
    # Add edges
    for edge in graph_data['edges']:
        source_name = node_id_to_name.get(edge['source'], 'unknown')
        target_name = node_id_to_name.get(edge['target'], 'unknown')
        
        # Get edge type and weight
        edge_type = edge.get('type', 'sequential')
        weight = edge.get('properties', {}).get('weight', 1.0)
        
        # Edge styling based on type
        if edge_type == 'sequential':
            edge_style = 'solid'
            edge_color = '#555555'
        else:
            edge_style = 'dashed'
            edge_color = '#FF69B4'
        
        # Add edge
        G.add_edge(source_name, target_name, **{
            'id': edge['id'],
            'type': edge_type,
            'weight': weight,
            'style': edge_style,
            'color': edge_color
        })
    
    return G

def visualize_graph_matplotlib(G: nx.Graph):
    """Visualize graph using Matplotlib."""
    plt.figure(figsize=(16, 12))
    pos = nx.spring_layout(G, k=2, iterations=50, seed=42)
    
    # Create color map
    colors = [G.nodes[node]['color'] for node in G.nodes()]
    
    # Draw nodes
    nx.draw_networkx_nodes(
        G,
        pos,
        node_color=colors,
        node_size=2000,
        alpha=0.8
    )
    
    # Draw edges
    edge_colors = [G.edges[edge[0], edge[1]]['color'] for edge in G.edges()]
    nx.draw_networkx_edges(
        G,
        pos,
        edge_color=edge_colors,
        width=2.0,
        alpha=0.6,
        arrowsize=20
    )
    
    # Draw node labels
    node_labels = {node: node for node in G.nodes()}
    nx.draw_networkx_labels(
        G,
        pos,
        labels=node_labels,
        font_size=8,
        font_weight='normal'
    )
    
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
    
    # Save figure to BytesIO
    buffer = BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight', dpi=150)
    plt.close()
    
    return buffer

def display_graph_statistics(graph_data: Dict[str, Any]):
    """Display graph statistics."""
    st.subheader("Graph Statistics", anchor='stats')
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Total Nodes", len(graph_data['entities']) + len(graph_data['operations']))
        st.metric("Entity Nodes", len(graph_data['entities']))
        st.metric("Operation Nodes", len(graph_data['operations']))
    
    with col2:
        st.metric("Total Edges", len(graph_data['edges']))
        st.metric("Sequential Edges", len(graph_data['edges']))
        st.metric("Graph Layers", 3)

def display_graph_structure(graph_data: Dict[str, Any]):
    """Display graph structure details."""
    st.subheader("Graph Structure", anchor='structure')
    
    # Display entities
    st.write("### Entity Nodes")
    for entity in graph_data['entities']:
        st.info(f"**{entity['name']}** - {entity['description']}")
    
    st.write("---")
    
    # Display operations
    st.write("### Operation Nodes")
    for operation in graph_data['operations']:
        st.info(f"**{operation['name']}** - {operation['description']}")
    
    st.write("---")
    
    # Display edges
    st.write("### Graph Edges")
    for edge in graph_data['edges']:
        source = edge['source']
        target = edge['target']
        edge_type = edge['type']
        
        # Find source and target names
        source_name = next((e['name'] for e in graph_data['entities'] if e['id'] == source), None)
        if not source_name:
            source_name = next((o['name'] for o in graph_data['operations'] if o['id'] == source), None)
        
        target_name = next((o['name'] for o in graph_data['operations'] if o['id'] == target), None)
        
        if source_name and target_name:
            st.info(f"**{source_name}** → **{target_name}** [{edge_type}]")

def display_node_details(graph_data: Dict[str, Any]):
    """Display detailed node information."""
    st.subheader("Node Details", anchor='details')
    
    # Entity nodes
    with st.expander("Entity Nodes", expanded=True):
        for i, entity in enumerate(graph_data['entities'], 1):
            st.write(f"**{i}. {entity['name']}**")
            st.json(entity)
    
    # Operation nodes
    with st.expander("Operation Nodes", expanded=True):
        for i, operation in enumerate(graph_data['operations'], 1):
            st.write(f"**{i}. {operation['name']}**")
            st.json(operation)

def main():
    """Main function for Streamlit app."""
    # Load test graph data
    graph_data = load_test_graph()
    
    # Page title
    st.title("📊 SkillGraph v1.0.1-beta - Test Graph Visualization")
    st.markdown("Multi-layer graph-based AI agent skills analysis")
    
    # Display graph statistics
    display_graph_statistics(graph_data)
    
    st.write("---")
    
    # Create and visualize graph
    st.subheader("Graph Visualization", anchor='visualization')
    
    # Create NetworkX graph
    G = create_networkx_graph(graph_data)
    
    # Generate visualization
    buffer = visualize_graph_matplotlib(G)
    
    # Display image
    st.subheader("Test Graph Visualization")
    st.image(buffer.getvalue(), caption='SkillGraph Test Graph Visualization')
    
    # Display graph structure
    st.write("---")
    display_graph_structure(graph_data)
    
    st.write("---")
    display_node_details(graph_data)
    
    # Display graph data
    st.write("---")
    st.subheader("Graph Data (JSON)", anchor='data')
    st.json(graph_data)

if __name__ == "__main__":
    main()
