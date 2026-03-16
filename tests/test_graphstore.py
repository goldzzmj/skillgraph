"""
Graph Store Tests - Multi-layer Graph Structure

Tests for nodes, edges, and Neo4j graph store.
"""

import pytest
import sys
import os
from typing import Dict, Any, List

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from skillgraph.graphstore.models import (
    BaseNode,
    EntityNode,
    OperationNode,
    BaseEdge,
    TemporalEdge,
    DependencyEdge,
    ParallelEdge,
    ConditionalEdge,
    IterativeEdge,
    NodeType,
    OperationType,
    EdgeType
)
from skillgraph.graphstore.neo4j_store import (
    Neo4jGraphStore,
    MockGraphStore,
    get_graph_store
)


class TestNodeModels:
    """Test node models."""

    def test_base_node_creation(self):
        """Test base node creation."""
        node = BaseNode(
            node_id="node_1",
            node_type=NodeType.OPERATION,
            name="Test Node",
            description="Test Description"
        )
        
        assert node.node_id == "node_1"
        assert node.node_type == NodeType.OPERATION
        assert node.name == "Test Node"
        assert node.description == "Test Description"
        assert isinstance(node.properties, dict)
        assert node.properties == {}

    def test_entity_node_creation(self):
        """Test entity node creation."""
        node = EntityNode(
            node_id="entity_1",
            node_type=NodeType.ENTITY,
            name="Test Agent",
            description="Test Agent Description",
            entity_type="agent",
            attributes={"model": "gpt-4", "max_tokens": 4096},
            metadata={"version": "1.0.0"}
        )
        
        assert node.node_type == NodeType.ENTITY
        assert node.entity_type == "agent"
        assert node.attributes == {"model": "gpt-4", "max_tokens": 4096}
        assert node.metadata == {"version": "1.0.0"}

    def test_operation_node_creation(self):
        """Test operation node creation."""
        node = OperationNode(
            node_id="operation_1",
            node_type=NodeType.OPERATION,
            name="Web Search",
            description="Search for information on the web",
            operation_type=OperationType.WEB_SEARCH,
            operation_parameters={
                "required": ["query"],
                "optional": ["timeout"]
            },
            input_node_ids=["entity_1"],
            output_node_ids=["data_1"],
            execution_time=5.0,
            timeout=10.0,
            retry_policy={
                "max_retries": 3,
                "backoff_factor": 2
            },
            error_handling={
                "ignore_errors": False,
                "continue_on_error": False
            },
            dependencies=[],
            metadata={"priority": "high"}
        )
        
        assert node.node_type == NodeType.OPERATION
        assert node.operation_type == OperationType.WEB_SEARCH
        assert node.operation_parameters == {
            "required": ["query"],
            "optional": ["timeout"]
        }
        assert node.input_node_ids == ["entity_1"]
        assert node.output_node_ids == ["data_1"]
        assert node.execution_time == 5.0
        assert node.timeout == 10.0
        assert node.dependencies == []
        assert node.metadata == {"priority": "high"}


class TestEdgeModels:
    """Test edge models."""

    def test_base_edge_creation(self):
        """Test base edge creation."""
        edge = BaseEdge(
            edge_id="edge_1",
            source_node_id="operation_1",
            target_node_id="operation_2",
            edge_type=EdgeType.SEQUENTIAL,
            weight=1.0
        )
        
        assert edge.edge_id == "edge_1"
        assert edge.source_node_id == "operation_1"
        assert edge.target_node_id == "operation_2"
        assert edge.edge_type == EdgeType.SEQUENTIAL
        assert edge.weight == 1.0
        assert isinstance(edge.properties, dict)
        assert edge.properties == {}

    def test_temporal_edge_creation(self):
        """Test temporal edge creation."""
        edge = TemporalEdge(
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
        
        assert edge.edge_type == EdgeType.SEQUENTIAL
        assert edge.temporal_order == 0
        assert edge.time_interval == 5.0
        assert edge.condition == "if condition then"
        assert edge.causality == "data_flow"
        assert edge.execution_order == 0

    def test_dependency_edge_creation(self):
        """Test dependency edge creation."""
        edge = DependencyEdge(
            edge_id="edge_1",
            source_node_id="operation_1",
            target_node_id="operation_2",
            edge_type=EdgeType.SEQUENTIAL,
            is_required=True,
            is_critical=False,
            alternative_node_ids=["operation_3"]
        )
        
        assert edge.edge_type == EdgeType.SEQUENTIAL
        assert edge.is_required == True
        assert edge.is_critical == False
        assert edge.alternative_node_ids == ["operation_3"]

    def test_parallel_edge_creation(self):
        """Test parallel edge creation."""
        edge = ParallelEdge(
            edge_id="edge_1",
            source_node_id="operation_1",
            target_node_id="operation_2",
            edge_type=EdgeType.PARALLEL,
            parallel_type="fork",
            wait_for_all=True
        )
        
        assert edge.edge_type == EdgeType.PARALLEL
        assert edge.parallel_type == "fork"
        assert edge.wait_for_all == True

    def test_conditional_edge_creation(self):
        """Test conditional edge creation."""
        edge = ConditionalEdge(
            edge_id="edge_1",
            source_node_id="operation_1",
            target_node_id="operation_2",
            edge_type=EdgeType.CONDITIONAL,
            condition_expression="temperature > 30",
            true_branch_node_id="operation_3",
            false_branch_node_id="operation_4"
        )
        
        assert edge.edge_type == EdgeType.CONDITIONAL
        assert edge.condition_expression == "temperature > 30"
        assert edge.true_branch_node_id == "operation_3"
        assert edge.false_branch_node_id == "operation_4"

    def test_iterative_edge_creation(self):
        """Test iterative edge creation."""
        edge = IterativeEdge(
            edge_id="edge_1",
            source_node_id="operation_1",
            target_node_id="operation_2",
            edge_type=EdgeType.ITERATIVE,
            loop_condition="i < 10",
            loop_variable="i",
            loop_variable_source="data_1",
            max_iterations=10
        )
        
        assert edge.edge_type == EdgeType.ITERATIVE
        assert edge.loop_condition == "i < 10"
        assert edge.loop_variable == "i"
        assert edge.loop_variable_source == "data_1"
        assert edge.max_iterations == 10


class TestMockGraphStore:
    """Test mock graph store."""

    def setup_method(self):
        """Set up mock graph store."""
        self.graph_store = MockGraphStore()

    def test_create_entity_node(self):
        """Test create entity node."""
        node = EntityNode(
            node_id="entity_1",
            node_type=NodeType.ENTITY,
            name="Test Agent",
            description="Test Agent",
            entity_type="agent"
        )
        
        node_id = self.graph_store.create_entity_node(node)
        
        assert node_id == "entity_1"
        assert "entity_1" in self.graph_store.nodes
        assert self.graph_store.nodes["entity_1"] == node

    def test_create_operation_node(self):
        """Test create operation node."""
        node = OperationNode(
            node_id="operation_1",
            node_type=NodeType.OPERATION,
            name="Web Search",
            description="Search",
            operation_type=OperationType.WEB_SEARCH
        )
        
        node_id = self.graph_store.create_operation_node(node)
        
        assert node_id == "operation_1"
        assert "operation_1" in self.graph_store.nodes
        assert self.graph_store.nodes["operation_1"] == node

    def test_create_edge(self):
        """Test create edge."""
        # Create nodes first
        node1 = EntityNode(
            node_id="entity_1",
            node_type=NodeType.ENTITY,
            name="Test Agent",
            description="Test"
        )
        node2 = OperationNode(
            node_id="operation_1",
            node_type=NodeType.OPERATION,
            name="Web Search",
            description="Search",
            operation_type=OperationType.WEB_SEARCH
        )
        
        self.graph_store.create_entity_node(node1)
        self.graph_store.create_operation_node(node2)
        
        # Create edge
        edge_data = {
            "source_node_id": "entity_1",
            "target_node_id": "operation_1",
            "edge_type": "sequential",
            "temporal_order": 0
        }
        
        edge_id = self.graph_store.create_edge("entity_1", "operation_1", edge_data)
        
        assert "edge_entity_1_operation_1" in self.graph_store.edges
        assert self.graph_store.edges["edge_entity_1_operation_1"] == edge_data

    def test_get_node(self):
        """Test get node."""
        node = EntityNode(
            node_id="entity_1",
            node_type=NodeType.ENTITY,
            name="Test Agent",
            description="Test"
        )
        
        self.graph_store.create_entity_node(node)
        
        retrieved_node = self.graph_store.get_node("entity_1")
        
        assert retrieved_node is not None
        assert retrieved_node.node_id == "entity_1"
        assert retrieved_node.name == "Test Agent"

    def test_get_operation_dependencies(self):
        """Test get operation dependencies."""
        # Create nodes
        node1 = EntityNode(
            node_id="entity_1",
            node_type=NodeType.ENTITY,
            name="Test Agent",
            description="Test"
        )
        node2 = OperationNode(
            node_id="operation_1",
            node_type=NodeType.OPERATION,
            name="Web Search",
            description="Search",
            operation_type=OperationType.WEB_SEARCH
        )
        node3 = OperationNode(
            node_id="operation_2",
            node_type=NodeType.OPERATION,
            name="Data Processing",
            description="Process",
            operation_type=OperationType.DATA_PROCESSING
        )
        
        self.graph_store.create_entity_node(node1)
        self.graph_store.create_operation_node(node2)
        self.graph_store.create_operation_node(node3)
        
        # Create edges
        edge1_data = {
            "source_node_id": "entity_1",
            "target_node_id": "operation_1",
            "edge_type": "sequential",
            "temporal_order": 0
        }
        edge2_data = {
            "source_node_id": "operation_1",
            "target_node_id": "operation_2",
            "edge_type": "sequential",
            "temporal_order": 1
        }
        
        self.graph_store.create_edge("entity_1", "operation_1", edge1_data)
        self.graph_store.create_edge("operation_1", "operation_2", edge2_data)
        
        # Get dependencies
        dependencies = self.graph_store.get_operation_dependencies("operation_2")
        
        assert len(dependencies) == 1
        assert dependencies[0]['node'].node_id == "operation_1"
        assert dependencies[0]['edge']['source_node_id'] == "operation_1"
        assert dependencies[0]['edge']['target_node_id'] == "operation_2"

    def test_get_execution_path(self):
        """Test get execution path."""
        # Create nodes
        node1 = EntityNode(
            node_id="entity_1",
            node_type=NodeType.ENTITY,
            name="Test Agent",
            description="Test"
        )
        node2 = OperationNode(
            node_id="operation_1",
            node_type=NodeType.OPERATION,
            name="Web Search",
            description="Search",
            operation_type=OperationType.WEB_SEARCH
        )
        node3 = OperationNode(
            node_id="operation_2",
            node_type=NodeType.OPERATION,
            name="Data Processing",
            description="Process",
            operation_type=OperationType.DATA_PROCESSING
        )
        
        self.graph_store.create_entity_node(node1)
        self.graph_store.create_operation_node(node2)
        self.graph_store.create_operation_node(node3)
        
        # Create edges
        edge1_data = {
            "source_node_id": "entity_1",
            "target_node_id": "operation_1",
            "edge_type": "sequential",
            "temporal_order": 0
        }
        edge2_data = {
            "source_node_id": "operation_1",
            "target_node_id": "operation_2",
            "edge_type": "sequential",
            "temporal_order": 1
        }
        
        self.graph_store.create_edge("entity_1", "operation_1", edge1_data)
        self.graph_store.create_edge("operation_1", "operation_2", edge2_data)
        
        # Get execution path
        path = self.graph_store.get_execution_path("entity_1", "operation_2")
        
        assert path == ["entity_1", "operation_1", "operation_2"]

    def test_delete_node(self):
        """Test delete node."""
        node = EntityNode(
            node_id="entity_1",
            node_type=NodeType.ENTITY,
            name="Test Agent",
            description="Test"
        )
        
        self.graph_store.create_entity_node(node)
        
        success = self.graph_store.delete_node("entity_1")
        
        assert success == True
        assert "entity_1" not in self.graph_store.nodes

    def test_close(self):
        """Test close graph store."""
        self.graph_store.close()
        assert True  # Mock store should close without error


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
