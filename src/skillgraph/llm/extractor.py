"""
LLM Operation Extractor

LLM-based operation and relationship extraction from agent skills.
"""

import openai
import logging
from typing import Dict, Any, List, Optional
import json
import os

logger = logging.getLogger(__name__)


# LLM Prompt Templates
OPERATION_EXTRACTION_PROMPT = """
You are an AI agent skill parser. Extract atomic operations from the following agent skill document.

Agent Skill Document:
{skill_content}

Instructions:
1. Extract all atomic operations (commands, tasks, functions).
2. For each operation, extract:
   - operation_name: name of the operation
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
  {{
    "operation_name": "operation_name",
    "operation_type": "web_search | code_execution | api_call | data_processing | llm_call | file_operation | task | condition | loop",
    "operation_description": "description",
    "operation_parameters": {{
      "required": ["param1", "param2"],
      "optional": ["param3"]
    }},
    "input_references": ["entity1", "data1"],
    "output_references": ["entity2", "data2"],
    "dependencies": ["operation1", "operation2"]
  }}
]
```
"""


RELATIONSHIP_EXTRACTION_PROMPT = """
You are an AI agent skill relationship parser. Extract temporal and causal relationships between operations.

Operations:
{operations}

Instructions:
1. Analyze the dependencies and relationships between operations.
2. For each relationship, extract:
   - source_operation: the source operation (depends on another)
   - target_operation: the target operation (is depended upon)
   - relationship_type: one of [sequential, parallel, conditional, iterative]
   - temporal_order: the order of execution (0-based index)
   - condition: a branch or loop condition (if any)
   - causality: one of [data_flow, control_flow, both]
   - is_required: whether the dependency is required
   - is_critical: whether the dependency is critical for execution

Output Format:
Return a JSON array of relationships:
```json
[
  {{
    "source_operation": "operation_name",
    "target_operation": "operation_name",
    "relationship_type": "sequential | parallel | conditional | iterative",
    "temporal_order": 0,
    "condition": "if condition then",
    "causality": "data_flow | control_flow | both",
    "is_required": true,
    "is_critical": false
  }}
]
```
"""


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
   - execution_order: position in the execution sequence (0-based index)
   - parallel_group: operations that can be executed in parallel

Output Format:
Return a JSON object:
```json
{{
  "execution_order": ["operation1", "operation2", ...],
  "parallel_groups": [
    ["operation1", "operation2"],
    ["operation3", "operation4"],
    ...
  ],
  "critical_path": ["operation1", "operation3", "operation5", ...]
}}
```
"""


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
   - operation_name: name of the condition or loop operation
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
  {{
    "structure_type": "conditional | loop",
    "operation_name": "operation_name",
    "condition_expression": "boolean expression",
    "true_branch_operations": ["operation1", "operation2"],
    "false_branch_operations": ["operation3", "operation4"],
    "loop_body_operations": ["operation1", "operation2"],
    "loop_variable": "variable_name",
    "loop_variable_source": "data_source"
  }}
]
```
"""


class LLMOperationExtractor:
    """LLM-based operation extractor."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4-turbo"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.client = openai.OpenAI(api_key=self.api_key)
        logger.info(f"Initialized LLMOperationExtractor with model: {model}")

    def extract_operations(self, skill_content: str) -> List[Dict[str, Any]]:
        """
        Extract operations from skill content.

        Args:
            skill_content: Agent skill content (markdown)

        Returns:
            List of operations
        """
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
        """
        Extract relationships between operations.

        Args:
            operations: List of operations

        Returns:
            List of relationships
        """
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
        """
        Extract sequential execution order.

        Args:
            operations: List of operations
            relationships: List of relationships

        Returns:
            Sequential execution order
        """
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
        """
        Extract conditional and loop structures.

        Args:
            operations: List of operations
            relationships: List of relationships

        Returns:
            List of structures (conditions and loops)
        """
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

            logger.info(f"Extracted {len(conditions)} structures (conditions and loops)")
            return conditions

        except Exception as e:
            logger.error(f"Error extracting conditions: {e}")
            return []
