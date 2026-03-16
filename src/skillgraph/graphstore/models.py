"""
Graph Models - Multi-layer Graph Structure

Node and edge models for operation-based and temporal-based graph.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional, Literal, Union
from enum import Enum
from datetime import datetime

class NodeType(str, Enum):
    """Node type enumeration."""
    ENTITY = "entity"
    OPERATION = "operation"

class OperationType(str, Enum):
    """Operation type enumeration."""
    WEB_SEARCH = "web_search"
    CODE_EXECUTION = "code_execution"
    API_CALL = "api_call"
    DATA_PROCESSING = "data_processing"
    LLM_CALL = "llm_call"
    FILE_OPERATION = "file_operation"
    TASK = "task"
    CONDITION = "condition"
    LOOP = "loop"

class EdgeType(str, Enum):
    """Edge type enumeration."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    ITERATIVE = "iterative"
    CAUSAL_DATA = "causal_data"
    CAUSAL_CONTROL = "causal_control"


class BaseNode(BaseModel):
    """Base node model."""
    node_id: str = Field(..., description="Unique node ID")
    node_type: NodeType = Field(..., description="Node type (entity or operation)")
    name: str = Field(..., description="Node name")
    description: str = Field(..., description="Node description")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Node properties")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Update timestamp")


class EntityNode(BaseNode):
    """Entity node model."""
    node_type: Literal[NodeType.ENTITY] = NodeType.ENTITY
    entity_type: str = Field(..., description="Entity type (agent, tool, data, task, etc.)")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Entity attributes")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Entity metadata")


class OperationNode(BaseNode):
    """Operation node model."""
    node_type: Literal[NodeType.OPERATION] = NodeType.OPERATION
    operation_type: OperationType = Field(..., description="Operation type")
    operation_parameters: Dict[str, Any] = Field(default_factory=dict, description="Operation parameters")
    input_node_ids: List[str] = Field(default_factory=list, description="Input node IDs")
    output_node_ids: List[str] = Field(default_factory=list, description="Output node IDs")
    execution_time: Optional[float] = Field(None, description="Expected execution time in seconds")
    timeout: Optional[float] = Field(None, description="Operation timeout in seconds")
    retry_policy: Optional[Dict[str, Any]] = Field(None, description="Retry policy")
    error_handling: Optional[Dict[str, Any]] = Field(None, description="Error handling policy")
    dependencies: List[str] = Field(default_factory=list, description="Dependent operation node IDs")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Operation metadata")


class BaseEdge(BaseModel):
    """Base edge model."""
    edge_id: str = Field(..., description="Unique edge ID")
    source_node_id: str = Field(..., description="Source node ID")
    target_node_id: str = Field(..., description="Target node ID")
    edge_type: EdgeType = Field(..., description="Edge type")
    weight: float = Field(default=1.0, description="Edge weight")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Edge properties")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Update timestamp")


class TemporalEdge(BaseEdge):
    """Temporal edge model."""
    edge_type: Literal[
        EdgeType.SEQUENTIAL,
        EdgeType.PARALLEL,
        EdgeType.CONDITIONAL,
        EdgeType.ITERATIVE
    ]
    temporal_order: int = Field(..., description="Temporal order (0-based index)")
    time_interval: Optional[float] = Field(None, description="Time interval between operations (seconds)")
    condition: Optional[str] = Field(None, description="Branch or loop condition")
    causality: Optional[Literal["data_flow", "control_flow", "both"]] = Field(None, description="Causality type")
    execution_order: Optional[int] = Field(None, description="Execution order (topological sort)")


class DependencyEdge(BaseEdge):
    """Dependency edge model."""
    edge_type: Literal[EdgeType.SEQUENTIAL] = EdgeType.SEQUENTIAL
    is_required: bool = Field(..., description="Whether dependency is required")
    is_critical: bool = Field(default=False, description="Whether dependency is critical for execution")
    alternative_node_ids: List[str] = Field(default_factory=list, description="Alternative operation node IDs")


class ParallelEdge(BaseEdge):
    """Parallel edge model."""
    edge_type: Literal[EdgeType.PARALLEL] = EdgeType.PARALLEL
    parallel_type: Literal["fork", "join"] = Field(..., description="Fork or join parallel")
    wait_for_all: bool = Field(default=True, description="Whether to wait for all parallel operations")


class ConditionalEdge(BaseEdge):
    """Conditional edge model."""
    edge_type: Literal[EdgeType.CONDITIONAL] = EdgeType.CONDITIONAL
    condition_expression: str = Field(..., description="Boolean condition expression")
    true_branch_node_id: str = Field(..., description="True branch node ID")
    false_branch_node_id: str = Field(..., description="False branch node ID")


class IterativeEdge(BaseEdge):
    """Iterative edge model."""
    edge_type: Literal[EdgeType.ITERATIVE] = EdgeType.ITERATIVE
    loop_condition: str = Field(..., description="Loop condition expression")
    loop_variable: str = Field(..., description="Loop variable name")
    loop_variable_source: str = Field(..., description="Source node ID for loop variable")
    max_iterations: Optional[int] = Field(None, description="Maximum iterations (if known)")
