"""
Graph Query API

Multi-layer graph query endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any, Optional
import logging

from .models import (
    BaseNode,
    EntityNode,
    OperationNode,
    BaseEdge,
    TemporalEdge,
    DependencyEdge,
    NodeType,
    OperationType
)
from .neo4j_store import Neo4jGraphStore, MockGraphStore, get_graph_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/graph", tags=["graph"])


@router.post("/nodes/entity", response_model=Dict[str, str])
async def create_entity_node(
    entity_node: EntityNode,
    graph_store: Neo4jGraphStore = Depends(get_graph_store)
):
    """
    Create entity node in graph.

    Args:
        entity_node: Entity node data
        graph_store: Graph store instance

    Returns:
        Created node ID
    """
    try:
        node_id = graph_store.create_entity_node(entity_node)
        logger.info(f"Created entity node: {node_id}")
        return {"node_id": node_id, "status": "created"}
    except Exception as e:
        logger.error(f"Failed to create entity node: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create entity node: {str(e)}"
        )


@router.post("/nodes/operation", response_model=Dict[str, str])
async def create_operation_node(
    operation_node: OperationNode,
    graph_store: Neo4jGraphStore = Depends(get_graph_store)
):
    """
    Create operation node in graph.

    Args:
        operation_node: Operation node data
        graph_store: Graph store instance

    Returns:
        Created node ID
    """
    try:
        node_id = graph_store.create_operation_node(operation_node)
        logger.info(f"Created operation node: {node_id}")
        return {"node_id": node_id, "status": "created"}
    except Exception as e:
        logger.error(f"Failed to create operation node: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create operation node: {str(e)}"
        )


@router.post("/edges/dependency")
async def create_dependency_edge(
    source_id: str,
    target_id: str,
    temporal_order: int,
    is_required: bool = True,
    is_critical: bool = False,
    graph_store: Neo4jGraphStore = Depends(get_graph_store)
):
    """
    Create dependency edge between operations.

    Args:
        source_id: Source operation node ID
        target_id: Target operation node ID
        temporal_order: Temporal order (0-based index)
        is_required: Whether dependency is required
        is_critical: Whether dependency is critical
        graph_store: Graph store instance

    Returns:
        Created edge ID
    """
    try:
        edge_data = {
            "source_node_id": source_id,
            "target_node_id": target_id,
            "edge_type": "sequential",
            "temporal_order": temporal_order,
            "is_required": is_required,
            "is_critical": is_critical
        }
        edge_id = graph_store.create_edge(source_id, target_id, edge_data)
        logger.info(f"Created dependency edge: {edge_id}")
        return {"edge_id": edge_id, "status": "created"}
    except Exception as e:
        logger.error(f"Failed to create dependency edge: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create dependency edge: {str(e)}"
        )


@router.get("/nodes/{node_id}")
async def get_node(
    node_id: str,
    graph_store: Neo4jGraphStore = Depends(get_graph_store)
):
    """
    Get node by ID.

    Args:
        node_id: Node ID
        graph_store: Graph store instance

    Returns:
        Node data
    """
    try:
        node = graph_store.get_node(node_id)
        if not node:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Node not found: {node_id}"
            )
        return {"node_id": node_id, "node": node}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get node: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get node: {str(e)}"
        )


@router.get("/operations/{operation_id}/dependencies")
async def get_operation_dependencies(
    operation_id: str,
    graph_store: Neo4jGraphStore = Depends(get_graph_store)
):
    """
    Get operation dependencies.

    Args:
        operation_id: Operation node ID
        graph_store: Graph store instance

    Returns:
        Operation dependencies
    """
    try:
        dependencies = graph_store.get_operation_dependencies(operation_id)
        return {"operation_id": operation_id, "dependencies": dependencies}
    except Exception as e:
        logger.error(f"Failed to get operation dependencies: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get operation dependencies: {str(e)}"
        )


@router.get("/nodes/{start_id}/path/{end_id}")
async def get_execution_path(
    start_id: str,
    end_id: str,
    graph_store: Neo4jGraphStore = Depends(get_graph_store)
):
    """
    Get execution path between nodes.

    Args:
        start_id: Start node ID
        end_id: End node ID
        graph_store: Graph store instance

    Returns:
        Execution path (ordered list of node IDs)
    """
    try:
        path = graph_store.get_execution_path(start_id, end_id)
        if not path:
            return {"start_id": start_id, "end_id": end_id, "path": [], "message": "No path found"}
        return {"start_id": start_id, "end_id": end_id, "path": path}
    except Exception as e:
        logger.error(f"Failed to get execution path: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get execution path: {str(e)}"
        )


@router.get("/nodes")
async def get_all_nodes(
    node_type: Optional[NodeType] = None,
    graph_store: Neo4jGraphStore = Depends(get_graph_store)
):
    """
    Get all nodes, optionally filtered by type.

    Args:
        node_type: Optional node type filter
        graph_store: Graph store instance

    Returns:
        List of nodes
    """
    try:
        nodes = graph_store.get_all_nodes(node_type)
        return {"node_type": node_type.value if node_type else "all", "nodes": nodes}
    except Exception as e:
        logger.error(f"Failed to get all nodes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get all nodes: {str(e)}"
        )


@router.get("/edges")
async def get_all_edges(
    edge_type: Optional[str] = None,
    graph_store: Neo4jGraphStore = Depends(get_graph_store)
):
    """
    Get all edges, optionally filtered by type.

    Args:
        edge_type: Optional edge type filter
        graph_store: Graph store instance

    Returns:
        List of edges
    """
    try:
        edges = graph_store.get_all_edges(edge_type)
        return {"edge_type": edge_type or "all", "edges": edges}
    except Exception as e:
        logger.error(f"Failed to get all edges: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get all edges: {str(e)}"
        )


@router.delete("/nodes/{node_id}")
async def delete_node(
    node_id: str,
    graph_store: Neo4jGraphStore = Depends(get_graph_store)
):
    """
    Delete node by ID.

    Args:
        node_id: Node ID
        graph_store: Graph store instance

    Returns:
        Success status
    """
    try:
        success = graph_store.delete_node(node_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Node not found: {node_id}"
            )
        return {"node_id": node_id, "status": "deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete node: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete node: {str(e)}"
        )


@router.post("/graph/operations/extract")
async def extract_operations_from_skill(
    skill_content: str,
    create_nodes: bool = True,
    llm_model: Optional[str] = None,
    llm_base_url: Optional[str] = None,
    graph_store: Neo4jGraphStore = Depends(get_graph_store)
):
    """
    Extract operations from skill content using LLM and create graph nodes.

    Args:
        skill_content: Agent skill content (markdown)
        create_nodes: Whether to create nodes in graph
        graph_store: Graph store instance

    Returns:
        Extracted operations and created node IDs
    """
    try:
        # Import LLM extractor
        from ..llm.extractor import LLMOperationExtractor

        # Get API key
        import os
        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="OpenAI API key not configured"
            )

        # Initialize LLM extractor
        model_name = llm_model or os.getenv("OPENAI_MODEL") or os.getenv("LLM_MODEL") or "glm-5"
        base_url = llm_base_url or os.getenv("OPENAI_BASE_URL") or os.getenv("LLM_BASE_URL")

        extractor = LLMOperationExtractor(
            api_key=api_key,
            model=model_name,
            base_url=base_url,
        )

        # Extract operations
        operations = extractor.extract_operations(skill_content)

        # Extract relationships
        relationships = extractor.extract_relationships(operations)

        # Create operation nodes
        node_ids = []
        if create_nodes:
            for op in operations:
                # Create operation node
                operation_node = OperationNode(
                    node_id=f"op_{op['operation_name'].replace(' ', '_').lower()}",
                    node_type="operation",
                    name=op['operation_name'],
                    description=op.get('operation_description', ''),
                    properties={
                        "operation_type": op['operation_type'],
                        "parameters": op.get('operation_parameters', {}),
                        "inputs": op.get('input_references', []),
                        "outputs": op.get('output_references', []),
                        "dependencies": op.get('dependencies', [])
                    }
                )
                node_id = graph_store.create_operation_node(operation_node)
                node_ids.append(node_id)

        # Create dependency edges
        edge_ids = []
        if create_nodes:
            for rel in relationships:
                # Find source and target nodes
                source_op = next((op for op in operations if op['operation_name'] == rel['source_operation']), None)
                target_op = next((op for op in operations if op['operation_name'] == rel['target_operation']), None)

                if source_op and target_op:
                    source_id = f"op_{source_op['operation_name'].replace(' ', '_').lower()}"
                    target_id = f"op_{target_op['operation_name'].replace(' ', '_').lower()}"

                    edge_id = graph_store.create_edge(
                        source_id=source_id,
                        target_id=target_id,
                        edge_data={
                            "edge_type": rel['relationship_type'],
                            "source_node_id": source_id,
                            "target_node_id": target_id,
                            "temporal_order": rel.get('temporal_order', 0),
                            "weight": 1.0,
                            "properties": {
                                "causality": rel.get('causality'),
                                "condition": rel.get('condition')
                            }
                        }
                    )
                    edge_ids.append(edge_id)

        logger.info(f"Extracted {len(operations)} operations and {len(relationships)} relationships")
        logger.info(f"Created {len(node_ids)} nodes and {len(edge_ids)} edges")

        return {
            "operations": operations,
            "relationships": relationships,
            "created_nodes": node_ids,
            "created_edges": edge_ids
        }
    except Exception as e:
        logger.error(f"Failed to extract operations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract operations: {str(e)}"
        )
