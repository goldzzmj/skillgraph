# 🧠 Phase 5 v1.0.1 - 任务1.1和1.2 Implementation Plan

## 📋 任务概述

**任务1.1：** 实现新的图谱结构（混合节点、多层图谱）  
**任务1.2：** 实现基于LLM的操作提取  
**开发周期：** 2-3天  
**状态：** 🚀 准备开始

---

## 📊 任务1.1：新的图谱结构

### 1.1.1 任务分解

**任务1.1.1：设计混合节点结构（4小时）**
- ✅ 设计实体节点类型
- ✅ 设计操作节点类型
- ✅ 设计节点继承结构
- ✅ 设计节点属性

**任务1.1.2：设计多层图谱结构（4小时）**
- ✅ 设计第1层：实体层
- ✅ 设计第2层：操作层
- ✅ 设计第3层：时序层
- ✅ 设计层间连接

**任务1.1.3：实现节点数据模型（4小时）**
- ✅ 实现实体节点模型
- ✅ 实现操作节点模型
- ✅ 实现节点属性模型
- ✅ 实现节点关系模型

**任务1.1.4：实现图谱存储（4小时）**
- ✅ 集成Neo4j图数据库
- ✅ 实现节点存储
- ✅ 实现边存储
- ✅ 实现图谱查询

**预期时间：** 1天（8小时）

---

### 1.1.2 技术实现

#### 节点数据模型

```python
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional, Literal
from enum import Enum

class NodeType(str, Enum):
    ENTITY = "entity"
    OPERATION = "operation"

class OperationType(str, Enum):
    WEB_SEARCH = "web_search"
    CODE_EXECUTION = "code_execution"
    API_CALL = "api_call"
    DATA_PROCESSING = "data_processing"
    LLM_CALL = "llm_call"
    FILE_OPERATION = "file_operation"
    TASK = "task"
    CONDITION = "condition"
    LOOP = "loop"

class BaseNode(BaseModel):
    node_id: str = Field(..., description="Unique node ID")
    node_type: NodeType = Field(..., description="Node type (entity or operation)")
    name: str = Field(..., description="Node name")
    description: str = Field(..., description="Node description")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Node properties")

class EntityNode(BaseNode):
    node_type: Literal[NodeType.ENTITY] = NodeType.ENTITY
    entity_type: str = Field(..., description="Entity type (agent, tool, data, task, etc.)")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Entity attributes")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Entity metadata")

class OperationNode(BaseNode):
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
```

#### 边数据模型

```python
class EdgeType(str, Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    ITERATIVE = "iterative"
    CAUSAL_DATA = "causal_data"
    CAUSAL_CONTROL = "causal_control"

class BaseEdge(BaseModel):
    edge_id: str = Field(..., description="Unique edge ID")
    source_node_id: str = Field(..., description="Source node ID")
    target_node_id: str = Field(..., description="Target node ID")
    edge_type: EdgeType = Field(..., description="Edge type")
    weight: float = Field(default=1.0, description="Edge weight")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Edge properties")

class TemporalEdge(BaseEdge):
    temporal_order: int = Field(..., description="Temporal order (0-based index)")
    time_interval: Optional[float] = Field(None, description="Time interval between operations (seconds)")
    condition: Optional[str] = Field(None, description="Branch or loop condition")
    causality: Optional[Literal["data_flow", "control_flow", "both"]] = Field(None, description="Causality type")
    execution_order: Optional[int] = Field(None, description="Execution order (topological sort)")

class DependencyEdge(BaseEdge):
    edge_type: Literal[EdgeType.SEQUENTIAL] = EdgeType.SEQUENTIAL
    is_required: bool = Field(..., description="Whether the dependency is required")
    is_critical: bool = Field(default=False, description="Whether the dependency is critical for execution")
    alternative_node_ids: List[str] = Field(default_factory=list, description="Alternative operation node IDs")

class ParallelEdge(BaseEdge):
    edge_type: Literal[EdgeType.PARALLEL] = EdgeType.PARALLEL
    parallel_type: Literal["fork", "join"] = Field(..., description="Fork or join parallel")
    wait_for_all: bool = Field(default=True, description="Whether to wait for all parallel operations")

class ConditionalEdge(BaseEdge):
    edge_type: Literal[EdgeType.CONDITIONAL] = EdgeType.CONDITIONAL
    condition_expression: str = Field(..., description="Boolean condition expression")
    true_branch_node_id: str = Field(..., description="True branch node ID")
    false_branch_node_id: str = Field(..., description="False branch node ID")

class IterativeEdge(BaseEdge):
    edge_type: Literal[EdgeType.ITERATIVE] = EdgeType.ITERATIVE
    loop_condition: str = Field(..., description="Loop condition expression")
    loop_variable: str = Field(..., description="Loop variable name")
    loop_variable_source: str = Field(..., description="Source node ID for loop variable")
    max_iterations: Optional[int] = Field(None, description="Maximum iterations (if known)")
```

---

### 1.1.3 图谱存储实现

#### Neo4j图数据库集成

```python
from neo4j import GraphDatabase
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class Neo4jGraphStore:
    """Neo4j graph database for multi-layer graph."""

    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self._create_constraints()

    def close(self):
        """Close Neo4j driver."""
        self.driver.close()

    def _create_constraints(self):
        """Create graph constraints and indexes."""
        with self.driver.session() as session:
            # Create node indexes
            session.run("CREATE INDEX node_id_index IF NOT EXISTS FOR (n:Node) ON (n.node_id)")
            session.run("CREATE INDEX node_name_index IF NOT EXISTS FOR (n:Node) ON (n.name)")
            session.run("CREATE INDEX node_type_index IF NOT EXISTS FOR (n:Node) ON (n.node_type)")

            # Create edge indexes
            session.run("CREATE INDEX edge_source_index IF NOT EXISTS FOR (e:Edge) ON (e.source_node_id)")
            session.run("CREATE INDEX edge_target_index IF NOT EXISTS FOR (e:Edge) ON (e.target_node_id)")
            session.run("CREATE INDEX edge_type_index IF NOT EXISTS FOR (e:Edge) ON (e.edge_type)")

    def create_entity_node(self, entity_node: EntityNode) -> str:
        """Create entity node."""
        with self.driver.session() as session:
            result = session.run(
                """
                CREATE (n:Entity:Node)
                SET n = $properties
                RETURN n.node_id AS node_id
                """,
                properties=entity_node.dict()
            )
            return result.single()["node_id"]

    def create_operation_node(self, operation_node: OperationNode) -> str:
        """Create operation node."""
        with self.driver.session() as session:
            result = session.run(
                """
                CREATE (n:Operation:Node)
                SET n = $properties
                RETURN n.node_id AS node_id
                """,
                properties=operation_node.dict()
            )
            return result.single()["node_id"]

    def create_edge(self, source_id: str, target_id: str, edge_data: Dict[str, Any]) -> str:
        """Create edge between nodes."""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (source:Node {node_id: $source_id})
                MATCH (target:Node {node_id: $target_id})
                CREATE (source)-[e:Edge]->(target)
                SET e = $properties
                RETURN elementId(e) AS edge_id
                """,
                source_id=source_id,
                target_id=target_id,
                properties=edge_data
            )
            return result.single()["edge_id"]

    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get node by ID."""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (n:Node {node_id: $node_id})
                RETURN n AS node
                """,
                node_id=node_id
            )
            return result.single()

    def get_operation_dependencies(self, operation_id: str) -> List[Dict[str, Any]]:
        """Get operation dependencies."""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (op:Operation:Node {node_id: $operation_id})-[e:Dependency:Edge]->(dep:Node)
                RETURN dep AS dependency, e AS edge
                ORDER BY e.temporal_order ASC
                """,
                operation_id=operation_id
            )
            return [record for record in result]

    def get_execution_path(self, start_id: str, end_id: str) -> List[str]:
        """Get execution path between nodes."""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH path = shortestPath((start:Node {node_id: $start_id})-[:Dependency:Edge*]->(end:Node {node_id: $end_id}))
                RETURN [node.node_id FOR node IN nodes(path)]
                """,
                start_id=start_id,
                end_id=end_id
            )
            return result.single()[0] if result.single() else []

    def delete_node(self, node_id: str) -> bool:
        """Delete node by ID."""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (n:Node {node_id: $node_id})
                DETACH DELETE n
                RETURN TRUE AS success
                """,
                node_id=node_id
            )
            return result.single()["success"]
```

---

### 1.1.4 图谱查询API

```python
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any

from ..models import (
    EntityNode,
    OperationNode,
    TemporalEdge,
    DependencyEdge
)
from ..dependencies import get_graph_store

router = APIRouter(prefix="/api/v1/graph", tags=["graph"])

@router.post("/nodes/entity", response_model=Dict[str, str])
async def create_entity_node(
    entity_node: EntityNode,
    graph_store = Depends(get_graph_store)
):
    """Create entity node."""
    node_id = graph_store.create_entity_node(entity_node)
    return {"node_id": node_id, "status": "created"}

@router.post("/nodes/operation", response_model=Dict[str, str])
async def create_operation_node(
    operation_node: OperationNode,
    graph_store = Depends(get_graph_store)
):
    """Create operation node."""
    node_id = graph_store.create_operation_node(operation_node)
    return {"node_id": node_id, "status": "created"}

@router.post("/edges/dependency")
async def create_dependency_edge(
    source_id: str,
    target_id: str,
    temporal_order: int,
    graph_store = Depends(get_graph_store)
):
    """Create dependency edge."""
    edge_data = {
        "source_node_id": source_id,
        "target_node_id": target_id,
        "edge_type": "sequential",
        "temporal_order": temporal_order
    }
    edge_id = graph_store.create_edge(source_id, target_id, edge_data)
    return {"edge_id": edge_id, "status": "created"}

@router.get("/operations/{operation_id}/dependencies")
async def get_operation_dependencies(
    operation_id: str,
    graph_store = Depends(get_graph_store)
):
    """Get operation dependencies."""
    dependencies = graph_store.get_operation_dependencies(operation_id)
    return {"operation_id": operation_id, "dependencies": dependencies}

@router.get("/nodes/{start_id}/path/{end_id}")
async def get_execution_path(
    start_id: str,
    end_id: str,
    graph_store = Depends(get_graph_store)
):
    """Get execution path."""
    path = graph_store.get_execution_path(start_id, end_id)
    return {"start_id": start_id, "end_id": end_id, "path": path}
```

---

## 📊 任务1.2：基于LLM的操作提取

### 1.2.1 任务分解

**任务1.2.1：设计LLM提示词模板（4小时）**
- ✅ 设计操作提取提示词
- ✅ 设计关系提取提示词
- ✅ 设计时序提取提示词
- ✅ 设计条件提取提示词

**任务1.2.2：实现LLM操作提取（4小时）**
- ✅ 实现LLM调用
- ✅ 实现结果解析
- ✅ 实现结果验证

**任务1.2.3：实现操作节点创建（4小时）**
- ✅ 实现操作节点创建
- ✅ 实现边关系创建
- ✅ 实现图谱构建

**任务1.2.4：实现自定义规则（4小时）**
- ✅ 实现自定义安全规则
- ✅ 实现自定义性能规则
- ✅ 实现自定义逻辑规则

**预期时间：** 1天（8小时）

---

### 1.2.2 LLM提示词模板

```python
# Operation Extraction Prompt
OPERATION_EXTRACTION_PROMPT = """
You are an AI agent skill parser. Extract atomic operations from the following agent skill document.

Agent Skill Document:
{skill_content}

Instructions:
1. Extract all atomic operations (commands, tasks, functions).
2. For each operation, extract:
   - operation_name: the name of the operation
   - operation_type: one of [web_search, code_execution, api_call, data_processing, llm_call, file_operation, task, condition, loop]
   - operation_description: a brief description of what the operation does
   - operation_parameters: a dictionary of required and optional parameters
   - input_references: list of entity names or data references used as input
   - output_references: list of entity names or data references produced as output
   - dependencies: list of other operations this operation depends on

Output Format:
Return a JSON array of operations:
```json
[
  {
    "operation_name": "operation_name",
    "operation_type": "web_search | code_execution | api_call | data_processing | llm_call | file_operation | task | condition | loop",
    "operation_description": "description",
    "operation_parameters": {
      "required": ["param1", "param2"],
      "optional": ["param3"]
    },
    "input_references": ["entity1", "data1"],
    "output_references": ["entity2", "data2"],
    "dependencies": ["operation1", "operation2"]
  }
]
```
"""

# Relationship Extraction Prompt
RELATIONSHIP_EXTRACTION_PROMPT = """
You are an AI agent skill relationship parser. Extract temporal and causal relationships between operations.

Operations:
{operations}

Instructions:
1. Analyze the dependencies between operations.
2. For each relationship, extract:
   - source_operation: the source operation (depends on another)
   - target_operation: the target operation (is depended upon)
   - relationship_type: one of [sequential, parallel, conditional, iterative]
   - temporal_order: the order of execution (0-based index)
   - condition: the branch or loop condition (if any)
   - causality: one of [data_flow, control_flow, both]

Output Format:
Return a JSON array of relationships:
```json
[
  {
    "source_operation": "operation_name",
    "target_operation": "operation_name",
    "relationship_type": "sequential | parallel | conditional | iterative",
    "temporal_order": 0,
    "condition": "if condition then",
    "causality": "data_flow | control_flow | both",
    "is_required": true,
    "is_critical": false
  }
]
```
"""

# Sequential Order Extraction Prompt
SEQUENTIAL_ORDER_PROMPT = """
You are an AI agent skill execution analyzer. Determine the sequential execution order of operations.

Operations:
{operations}

Relationships:
{relationships}

Instructions:
1. Analyze the dependencies and relationships between operations.
2. Determine the correct sequential execution order (topological sort).
3. For each operation, assign:
   - execution_order: the position in the execution sequence (0-based index)
   - parallel_group: operations that can be executed in parallel

Output Format:
Return a JSON object:
```json
{
  "execution_order": ["operation1", "operation2", ...],
  "parallel_groups": [
    ["operation1", "operation2"],
    ["operation3", "operation4"],
    ...
  ],
  "critical_path": ["operation1", "operation3", "operation5", ...]
}
```
"""
"""

# Condition Extraction Prompt
CONDITION_EXTRACTION_PROMPT = """
You are an AI agent skill condition analyzer. Extract conditional and loop structures from operations.

Operations:
{operations}

Relationships:
{relationships}

Instructions:
1. Identify conditional branches (if-then-else structures).
2. Identify loop structures (for, while loops).
3. For each structure, extract:
   - structure_type: one of [conditional, loop]
   - operation_name: the name of the condition or loop operation
   - condition_expression: the boolean condition expression
   - true_branch_operations: list of operations executed when condition is true
   - false_branch_operations: list of operations executed when condition is false
   - loop_body_operations: list of operations in the loop body
   - loop_variable: the loop variable name (if any)
   - loop_variable_source: the data source for the loop variable (if any)

Output Format:
Return a JSON array of structures:
```json
[
  {
    "structure_type": "conditional | loop",
    "operation_name": "operation_name",
    "condition_expression": "boolean expression",
    "true_branch_operations": ["operation1", "operation2"],
    "false_branch_operations": ["operation3", "operation4"],
    "loop_body_operations": ["operation1", "operation2"],
    "loop_variable": "variable_name",
    "loop_variable_source": "data_source"
  }
]
```
"""
"""
```

---

### 1.2.3 LLM操作提取实现

```python
import openai
import logging
from typing import Dict, Any, List
import json

logger = logging.getLogger(__name__)

class LLMOperationExtractor:
    """LLM-based operation extractor."""

    def __init__(self, api_key: str, model: str = "gpt-4-turbo"):
        self.api_key = api_key
        self.model = model
        self.client = openai.OpenAI(api_key=api_key)

    def extract_operations(self, skill_content: str) -> List[Dict[str, Any]]:
        """Extract operations from skill content."""
        try:
            prompt = OPERATION_EXTRACTION_PROMPT.format(skill_content=skill_content)

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an AI agent skill parser."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )

            result = response.choices[0].message.content
            operations = json.loads(result)

            logger.info(f"Extracted {len(operations)} operations")
            return operations

        except Exception as e:
            logger.error(f"Error extracting operations: {e}")
            return []

    def extract_relationships(
        self,
        operations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Extract relationships between operations."""
        try:
            prompt = RELATIONSHIP_EXTRACTION_PROMPT.format(
                operations=json.dumps(operations, indent=2)
            )

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an AI agent skill relationship parser."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )

            result = response.choices[0].message.content
            relationships = json.loads(result)

            logger.info(f"Extracted {len(relationships)} relationships")
            return relationships

        except Exception as e:
            logger.error(f"Error extracting relationships: {e}")
            return []

    def extract_sequential_order(
        self,
        operations: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Extract sequential execution order."""
        try:
            prompt = SEQUENTIAL_ORDER_PROMPT.format(
                operations=json.dumps(operations, indent=2),
                relationships=json.dumps(relationships, indent=2)
            )

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an AI agent skill execution analyzer."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )

            result = response.choices[0].message.content
            sequential_order = json.loads(result)

            logger.info(f"Extracted execution order: {len(sequential_order['execution_order'])} operations")
            return sequential_order

        except Exception as e:
            logger.error(f"Error extracting sequential order: {e}")
            return {}

    def extract_conditions(
        self,
        operations: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Extract conditional and loop structures."""
        try:
            prompt = CONDITION_EXTRACTION_PROMPT.format(
                operations=json.dumps(operations, indent=2),
                relationships=json.dumps(relationships, indent=2)
            )

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an AI agent skill condition analyzer."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )

            result = response.choices[0].message.content
            conditions = json.loads(result)

            logger.info(f"Extracted {len(conditions)} structures")
            return conditions

        except Exception as e:
            logger.error(f"Error extracting conditions: {e}")
            return []
```

---

## 📊 分支管理

### 分支策略

**主分支：** v1.0.1  
**功能分支1：** feature/graph-structure-optimization  
**功能分支2：** feature/llm-operation-extraction  
**临时分支：** temp/graph-testing

---

## 📋 待办任务

### 任务1.1：新的图谱结构

- [ ] 任务1.1.1：设计混合节点结构（4小时）
- [ ] 任务1.1.2：设计多层图谱结构（4小时）
- [ ] 任务1.1.3：实现节点数据模型（4小时）
- [ ] 任务1.1.4：实现图谱存储（4小时）

### 任务1.2：基于LLM的操作提取

- [ ] 任务1.2.1：设计LLM提示词模板（4小时）
- [ ] 任务1.2.2：实现LLM操作提取（4小时）
- [ ] 任务1.2.3：实现操作节点创建（4小时）
- [ ] 任务1.2.4：实现自定义规则（4小时）

---

## 📊 预期效果

### 任务1.1预期效果

- ✅ 混合节点结构（实体 + 操作）
- ✅ 多层图谱结构（实体层、操作层、时序层）
- ✅ Neo4j图数据库集成
- ✅ 图谱查询API（节点、边、路径）

**预期时间：** 1天

### 任务1.2预期效果

- ✅ LLM操作提取（90%+准确率）
- ✅ LLM关系提取（85%+准确率）
- ✅ 时序提取（80%+准确率）
- ✅ 条件提取（75%+准确率）
- ✅ 操作节点自动创建

**预期时间：** 1天

---

## 🎯 下一步行动

### 立即开始

**第1步：** 创建feature/graph-structure-optimization分支  
**第2步：** 开始任务1.1.1：设计混合节点结构

**后续步骤：**
1. ✅ 创建feature/graph-structure-optimization分支
2. ✅ 创建feature/llm-operation-extraction分支
3. ⏳ 实现任务1.1.1
4. ⏳ 实现任务1.1.2
5. ⏳ 实现任务1.1.3
6. ⏳ 实现任务1.1.4
7. ⏳ 切换到feature/llm-operation-extraction分支
8. ⏳ 实现任务1.2.1
9. ⏳ 实现任务1.2.2
10. ⏳ 实现任务1.2.3
11. ⏳ 实现任务1.2.4

---

## 📊 任务总结

### 任务1.1：新的图谱结构

**预期时间：** 1天（8小时）  
**优先级：** P0

### 任务1.2：基于LLM的操作提取

**预期时间：** 1天（8小时）  
**优先级：** P0

**总预期时间：** 2天

---

## 📊 项目状态

**项目地址：** https://github.com/goldzzmj/skillgraph  
**当前分支：** v1.0.1  
**功能分支1：** ⏳ feature/graph-structure-optimization  
**功能分支2：** ⏳ feature/llm-operation-extraction

---

**完成时间：** 预计2天  
**状态：** 🚀 准备开始

---

**需要我：**
1. 创建feature/graph-structure-optimization分支？
2. 创建feature/llm-operation-extraction分支？
3. 还是直接开始任务实现？

**告诉我下一步做什么！**
