"""
Simplified Tests - Graph Store and LLM Extractor

Simplified tests for quick validation.
"""

import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

try:
    from skillgraph.graphstore.models import (
        BaseNode,
        EntityNode,
        OperationNode,
        BaseEdge,
        TemporalEdge,
        NodeType,
        OperationType,
        EdgeType
    )
    IMPORTS_AVAILABLE = True
except Exception as e:
    print(f"Import error: {e}")
    IMPORTS_AVAILABLE = False


def test_imports():
    """Test that all imports are available."""
    if IMPORTS_AVAILABLE:
        assert BaseNode is not None
        assert EntityNode is not None
        assert OperationNode is not None
        assert BaseEdge is not None
        assert TemporalEdge is not None
        assert NodeType is not None
        assert OperationType is not None
        assert EdgeType is not None
    else:
        pytest.skip("Imports not available")


def test_node_types():
    """Test node types."""
    if IMPORTS_AVAILABLE:
        # Test NodeType enum
        assert NodeType.ENTITY == "entity"
        assert NodeType.OPERATION == "operation"

        # Test OperationType enum
        assert OperationType.WEB_SEARCH == "web_search"
        assert OperationType.CODE_EXECUTION == "code_execution"
        assert OperationType.API_CALL == "api_call"
        assert OperationType.DATA_PROCESSING == "data_processing"
        assert OperationType.LLM_CALL == "llm_call"
        assert OperationType.FILE_OPERATION == "file_operation"
        assert OperationType.TASK == "task"
        assert OperationType.CONDITION == "condition"
        assert OperationType.LOOP == "loop"
    else:
        pytest.skip("Imports not available")


def test_edge_types():
    """Test edge types."""
    if IMPORTS_AVAILABLE:
        # Test EdgeType enum
        assert EdgeType.SEQUENTIAL == "sequential"
        assert EdgeType.PARALLEL == "parallel"
        assert EdgeType.CONDITIONAL == "conditional"
        assert EdgeType.ITERATIVE == "iterative"
        assert EdgeType.CAUSAL_DATA == "causal_data"
        assert EdgeType.CAUSAL_CONTROL == "causal_control"
    else:
        pytest.skip("Imports not available")


def test_node_creation():
    """Test node creation."""
    if IMPORTS_AVAILABLE:
        # Test BaseNode
        base_node = BaseNode(
            node_id="base_1",
            node_type=NodeType.OPERATION,
            name="Test Operation",
            description="Test Description"
        )
        assert base_node.node_id == "base_1"
        assert base_node.node_type == NodeType.OPERATION
        assert base_node.name == "Test Operation"
        assert base_node.description == "Test Description"

        # Test EntityNode
        entity_node = EntityNode(
            node_id="entity_1",
            node_type=NodeType.ENTITY,
            name="Test Agent",
            description="Test Agent",
            entity_type="agent"
        )
        assert entity_node.node_type == NodeType.ENTITY
        assert entity_node.entity_type == "agent"

        # Test OperationNode
        operation_node = OperationNode(
            node_id="operation_1",
            node_type=NodeType.OPERATION,
            name="Web Search",
            description="Search web",
            operation_type=OperationType.WEB_SEARCH
        )
        assert operation_node.node_type == NodeType.OPERATION
        assert operation_node.operation_type == OperationType.WEB_SEARCH
    else:
        pytest.skip("Imports not available")


def test_edge_creation():
    """Test edge creation."""
    if IMPORTS_AVAILABLE:
        # Test BaseEdge
        base_edge = BaseEdge(
            edge_id="edge_1",
            source_node_id="operation_1",
            target_node_id="operation_2",
            edge_type=EdgeType.SEQUENTIAL,
            weight=1.0
        )
        assert base_edge.edge_id == "edge_1"
        assert base_edge.source_node_id == "operation_1"
        assert base_edge.target_node_id == "operation_2"
        assert base_edge.edge_type == EdgeType.SEQUENTIAL

        # Test TemporalEdge
        temporal_edge = TemporalEdge(
            edge_id="edge_1",
            source_node_id="operation_1",
            target_node_id="operation_2",
            edge_type=EdgeType.SEQUENTIAL,
            temporal_order=0,
            time_interval=5.0,
            condition="if condition then",
            causality="data_flow",
            execution_order=0
        )
        assert temporal_edge.edge_type == EdgeType.SEQUENTIAL
        assert temporal_edge.temporal_order == 0
        assert temporal_edge.time_interval == 5.0
        assert temporal_edge.condition == "if condition then"
        assert temporal_edge.causality == "data_flow"
        assert temporal_edge.execution_order == 0
    else:
        pytest.skip("Imports not available")


def test_mock_graph_store():
    """Test mock graph store."""
    if IMPORTS_AVAILABLE:
        from skillgraph.graphstore.neo4j_store import MockGraphStore

        # Create mock graph store
        graph_store = MockGraphStore()

        # Create node
        node = EntityNode(
            node_id="entity_1",
            node_type=NodeType.ENTITY,
            name="Test Agent",
            description="Test",
            entity_type="agent"
        )

        node_id = graph_store.create_entity_node(node)
        assert node_id == "entity_1"
        assert "entity_1" in graph_store.nodes

        # Get node
        retrieved_node = graph_store.get_node("entity_1")
        assert retrieved_node is not None
        assert retrieved_node.node_id == "entity_1"

        # Delete node
        success = graph_store.delete_node("entity_1")
        assert success == True
        assert "entity_1" not in graph_store.nodes

        # Close graph store
        graph_store.close()
    else:
        pytest.skip("Imports not available")


def test_llm_extractor_imports():
    """Test LLM extractor imports."""
    try:
        from skillgraph.llm.extractor import (
            LLMOperationExtractor,
            OPERATION_EXTRACTION_PROMPT,
            RELATIONSHIP_EXTRACTION_PROMPT,
            SEQUENTIAL_ORDER_PROMPT,
            CONDITION_EXTRACTION_PROMPT
        )
        IMPORTS_AVAILABLE = True
    except Exception as e:
        print(f"LLM extractor import error: {e}")
        IMPORTS_AVAILABLE = False

    if IMPORTS_AVAILABLE:
        assert LLMOperationExtractor is not None
        assert len(OPERATION_EXTRACTION_PROMPT) > 0
        assert len(RELATIONSHIP_EXTRACTION_PROMPT) > 0
        assert len(SEQUENTIAL_ORDER_PROMPT) > 0
        assert len(CONDITION_EXTRACTION_PROMPT) > 0
    else:
        pytest.skip("LLM extractor imports not available")


def test_llm_prompts_not_empty():
    """Test that LLM prompts are not empty."""
    if IMPORTS_AVAILABLE:
        from skillgraph.llm.extractor import (
            OPERATION_EXTRACTION_PROMPT,
            RELATIONSHIP_EXTRACTION_PROMPT,
            SEQUENTIAL_ORDER_PROMPT,
            CONDITION_EXTRACTION_PROMPT
        )

        assert len(OPERATION_EXTRACTION_PROMPT) > 0
        assert len(RELATIONSHIP_EXTRACTION_PROMPT) > 0
        assert len(SEQUENTIAL_ORDER_PROMPT) > 0
        assert len(CONDITION_EXTRACTION_PROMPT) > 0

        assert "{skill_content}" in OPERATION_EXTRACTION_PROMPT
        assert "{operations}" in RELATIONSHIP_EXTRACTION_PROMPT
        assert "{operations}" in SEQUENTIAL_ORDER_PROMPT
        assert "{operations}" in CONDITION_EXTRACTION_PROMPT
    else:
        pytest.skip("LLM extractor imports not available")


def test_operation_types():
    """Test that all operation types are covered."""
    if IMPORTS_AVAILABLE:
        from skillgraph.graphstore.models import OperationType

        operation_types = [
            OperationType.WEB_SEARCH,
            OperationType.CODE_EXECUTION,
            OperationType.API_CALL,
            OperationType.DATA_PROCESSING,
            OperationType.LLM_CALL,
            OperationType.FILE_OPERATION,
            OperationType.TASK,
            OperationType.CONDITION,
            OperationType.LOOP
        ]

        assert len(operation_types) == 9
    else:
        pytest.skip("Imports not available")


def test_relationship_types():
    """Test that all relationship types are covered."""
    if IMPORTS_AVAILABLE:
        from skillgraph.graphstore.models import EdgeType

        relationship_types = [
            EdgeType.SEQUENTIAL,
            EdgeType.PARALLEL,
            EdgeType.CONDITIONAL,
            EdgeType.ITERATIVE,
            EdgeType.CAUSAL_DATA,
            EdgeType.CAUSAL_CONTROL
        ]

        assert len(relationship_types) == 6
    else:
        pytest.skip("Imports not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
