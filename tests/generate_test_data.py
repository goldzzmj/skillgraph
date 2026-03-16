"""
Test Data Generation for Graph Visualization

Generate test data for graph visualization
"""

from skillgraph.graphstore.models import EntityNode, OperationNode, NodeType, OperationType
from datetime import datetime
import json


def generate_test_entities() -> list:
    """Generate test entities."""
    entities = [
        {
            "id": "entity_1",
            "type": NodeType.ENTITY,
            "name": "Search Agent",
            "description": "Agent for web search",
            "entity_type": "agent",
            "attributes": {
                "model": "gpt-4",
                "max_tokens": 4096,
                "temperature": 0.7
            },
            "metadata": {
                "version": "1.0.1"
            }
        },
        {
            "id": "entity_2",
            "type": NodeType.ENTITY,
            "name": "Data Store",
            "description": "Database for storing results",
            "entity_type": "data",
            "attributes": {
                "type": "neo4j",
                "host": "localhost",
                "port": 7687
            },
            "metadata": {
                "version": "1.0.1"
            }
        }
    ]
    
    return entities


def generate_test_operations() -> list:
    """Generate test operations."""
    operations = [
        {
            "id": "operation_1",
            "type": NodeType.OPERATION,
            "name": "Web Search",
            "description": "Search web for information",
            "operation_type": OperationType.WEB_SEARCH,
            "operation_parameters": {
                "required": ["query"],
                "optional": ["timeout", "max_results"]
            },
            "input_node_ids": ["entity_1"],
            "output_node_ids": ["entity_2"],
            "execution_time": 5.0,
            "timeout": 10.0,
            "retry_policy": {
                "max_retries": 3,
                "backoff_factor": 2.0
            },
            "error_handling": {
                "ignore_errors": False,
                "continue_on_error": False
            },
            "dependencies": [],
            "metadata": {
                "priority": "high"
            }
        },
        {
            "id": "operation_2",
            "type": NodeType.OPERATION,
            "name": "Data Processing",
            "description": "Process and analyze search results",
            "operation_type": OperationType.DATA_PROCESSING,
            "operation_parameters": {
                "required": ["data"],
                "optional": ["processing_mode"]
            },
            "input_node_ids": ["entity_2"],
            "output_node_ids": ["entity_2"],
            "execution_time": 3.0,
            "timeout": 10.0,
            "retry_policy": {
                "max_retries": 3,
                "backoff_factor": 2.0
            },
            "error_handling": {
                "ignore_errors": False,
                "continue_on_error": False
            },
            "dependencies": ["operation_1"],
            "metadata": {
                "priority": "high"
            }
        },
        {
            "id": "operation_3",
            "type": NodeType.OPERATION,
            "name": "Save Results",
            "description": "Save processed results to database",
            "operation_type": OperationType.FILE_OPERATION,
            "operation_parameters": {
                "required": ["results", "file_path"],
                "optional": ["overwrite"]
            },
            "input_node_ids": ["entity_2"],
            "output_node_ids": ["entity_2"],
            "execution_time": 2.0,
            "timeout": 10.0,
            "retry_policy": {
                "max_retries": 3,
                "backoff_factor": 2.0
            },
            "error_handling": {
                "ignore_errors": False,
                "continue_on_error": False
            },
            "dependencies": ["operation_2"],
            "metadata": {
                "priority": "medium"
            }
        }
    ]
    
    return operations


def generate_test_edges() -> list:
    """Generate test edges."""
    edges = [
        {
            "id": "edge_1",
            "source": "entity_1",
            "target": "operation_1",
            "type": "sequential",
            "temporal_order": 0,
            "properties": {
                "weight": 1.0,
                "causality": "data_flow"
            }
        },
        {
            "id": "edge_2",
            "source": "operation_1",
            "target": "operation_2",
            "type": "sequential",
            "temporal_order": 1,
            "properties": {
                "weight": 1.0,
                "causality": "data_flow"
            }
        },
        {
            "id": "edge_3",
            "source": "operation_2",
            "target": "operation_3",
            "type": "sequential",
            "temporal_order": 2,
            "properties": {
                "weight": 1.0,
                "causality": "control_flow"
            }
        }
    ]
    
    return edges


def generate_test_graph():
    """Generate complete test graph data."""
    entities = generate_test_entities()
    operations = generate_test_operations()
    edges = generate_test_edges()
    
    graph_data = {
        "entities": entities,
        "operations": operations,
        "edges": edges,
        "metadata": {
            "version": "1.0.1-beta",
            "created_at": datetime.utcnow().isoformat(),
            "total_nodes": len(entities) + len(operations),
            "total_edges": len(edges)
        }
    }
    
    return graph_data


def save_graph_data(graph_data, output_path="output/test_graph_data.json"):
    """Save graph data to JSON file."""
    import os
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(graph_data, f, indent=2, ensure_ascii=False)
    
    print(f"Test graph data saved to: {output_path}")


if __name__ == "__main__":
    print("=" * 60)
    print("Generating Test Graph Data for Visualization")
    print("=" * 60)
    
    graph_data = generate_test_graph()
    save_graph_data(graph_data)
    
    print("\nGraph Statistics:")
    print(f"  Total Nodes: {graph_data['metadata']['total_nodes']}")
    print(f"  - Entities: {len(graph_data['entities'])}")
    print(f"  - Operations: {len(graph_data['operations'])}")
    print(f"  Total Edges: {graph_data['metadata']['total_edges']}")
    
    print(f"\nData exported to: output/test_graph_data.json")
    print("\nNext step: Create graph visualization")
