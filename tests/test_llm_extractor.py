"""
LLM Extractor Tests - LLM-based Operation Extraction

Tests for LLM operation and relationship extraction.
"""

import pytest
import sys
import os
from typing import Dict, Any, List
from unittest.mock import Mock, patch
import json

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from skillgraph.llm.extractor import (
    LLMOperationExtractor,
    OPERATION_EXTRACTION_PROMPT,
    RELATIONSHIP_EXTRACTION_PROMPT,
    SEQUENTIAL_ORDER_PROMPT,
    CONDITION_EXTRACTION_PROMPT
)


class TestLLMExtractor:
    """Test LLM operation extractor."""

    def setup_method(self):
        """Set up LLM extractor."""
        self.api_key = "test_api_key"
        self.extractor = LLMOperationExtractor(api_key=self.api_key)

    @patch('openai.OpenAI')
    def test_extract_operations(self, mock_openai):
        """Test extract operations from skill content."""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = json.dumps([
            {
                "operation_name": "web_search",
                "operation_type": "web_search",
                "operation_description": "Search the web",
                "operation_parameters": {
                    "required": ["query"],
                    "optional": ["timeout"]
                },
                "input_references": ["agent"],
                "output_references": ["data"],
                "dependencies": []
            }
        ])
        
        mock_openai.return_value.chat.completions.create.return_value = mock_response

        # Extract operations
        skill_content = "# My AI Agent Skill\n..."
        operations = self.extractor.extract_operations(skill_content)
        
        assert len(operations) == 1
        assert operations[0]["operation_name"] == "web_search"
        assert operations[0]["operation_type"] == "web_search"
        assert operations[0]["operation_description"] == "Search the web"
        assert operations[0]["operation_parameters"]["required"] == ["query"]
        assert operations[0]["input_references"] == ["agent"]
        assert operations[0]["output_references"] == ["data"]

    @patch('openai.OpenAI')
    def test_extract_relationships(self, mock_openai):
        """Test extract relationships."""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = json.dumps([
            {
                "source_operation": "web_search",
                "target_operation": "data_processing",
                "relationship_type": "sequential",
                "temporal_order": 0,
                "condition": None,
                "causality": "data_flow",
                "is_required": True,
                "is_critical": False
            }
        ])
        
        mock_openai.return_value.chat.completions.create.return_value = mock_response

        # Extract relationships
        operations = [
            {
                "operation_name": "web_search",
                "operation_type": "web_search"
            },
            {
                "operation_name": "data_processing",
                "operation_type": "data_processing"
            }
        ]
        relationships = self.extractor.extract_relationships(operations)
        
        assert len(relationships) == 1
        assert relationships[0]["source_operation"] == "web_search"
        assert relationships[0]["target_operation"] == "data_processing"
        assert relationships[0]["relationship_type"] == "sequential"
        assert relationships[0]["temporal_order"] == 0
        assert relationships[0]["causality"] == "data_flow"
        assert relationships[0]["is_required"] == True
        assert relationships[0]["is_critical"] == False

    @patch('openai.OpenAI')
    def test_extract_sequential_order(self, mock_openai):
        """Test extract sequential order."""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = json.dumps({
            "execution_order": ["web_search", "data_processing", "save_data"],
            "parallel_groups": [
                ["web_search", "data_processing"]
            ],
            "critical_path": ["web_search", "data_processing"]
        })
        
        mock_openai.return_value.chat.completions.create.return_value = mock_response

        # Extract sequential order
        operations = [
            {
                "operation_name": "web_search",
                "operation_type": "web_search"
            },
            {
                "operation_name": "data_processing",
                "operation_type": "data_processing"
            },
            {
                "operation_name": "save_data",
                "operation_type": "file_operation"
            }
        ]
        relationships = [
            {
                "source_operation": "web_search",
                "target_operation": "data_processing",
                "relationship_type": "sequential",
                "temporal_order": 0
            }
        ]
        sequential_order = self.extractor.extract_sequential_order(operations, relationships)
        
        assert len(sequential_order["execution_order"]) == 3
        assert sequential_order["execution_order"] == ["web_search", "data_processing", "save_data"]
        assert len(sequential_order["parallel_groups"]) == 1
        assert len(sequential_order["critical_path"]) == 2

    @patch('openai.OpenAI')
    def test_extract_conditions(self, mock_openai):
        """Test extract conditions."""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = json.dumps([
            {
                "structure_type": "conditional",
                "operation_name": "check_temperature",
                "condition_expression": "temperature > 30",
                "true_branch_operations": ["turn_on_fan"],
                "false_branch_operations": ["turn_off_fan"]
            }
        ])
        
        mock_openai.return_value.chat.completions.create.return_value = mock_response

        # Extract conditions
        operations = [
            {
                "operation_name": "check_temperature",
                "operation_type": "condition"
            }
        ]
        relationships = []
        conditions = self.extractor.extract_conditions(operations, relationships)
        
        assert len(conditions) == 1
        assert conditions[0]["structure_type"] == "conditional"
        assert conditions[0]["operation_name"] == "check_temperature"
        assert conditions[0]["condition_expression"] == "temperature > 30"
        assert conditions[0]["true_branch_operations"] == ["turn_on_fan"]
        assert conditions[0]["false_branch_operations"] == ["turn_off_fan"]

    @patch('openai.OpenAI')
    def test_extract_operations_error(self, mock_openai):
        """Test extract operations with error."""
        # Mock OpenAI error
        mock_openai.return_value.chat.completions.create.side_effect = Exception("API Error")

        # Extract operations
        skill_content = "# My AI Agent Skill\n..."
        operations = self.extractor.extract_operations(skill_content)
        
        # Should return empty list on error
        assert operations == []

    @patch('openai.OpenAI')
    def test_extract_relationships_error(self, mock_openai):
        """Test extract relationships with error."""
        # Mock OpenAI error
        mock_openai.return_value.chat.completions.create.side_effect = Exception("API Error")

        # Extract relationships
        operations = []
        relationships = self.extractor.extract_relationships(operations)
        
        # Should return empty list on error
        assert relationships == []

    @patch('openai.OpenAI')
    def test_extract_sequential_order_error(self, mock_openai):
        """Test extract sequential order with error."""
        # Mock OpenAI error
        mock_openai.return_value.chat.completions.create.side_effect = Exception("API Error")

        # Extract sequential order
        operations = []
        relationships = []
        sequential_order = self.extractor.extract_sequential_order(operations, relationships)
        
        # Should return empty dict on error
        assert sequential_order == {}

    @patch('openai.OpenAI')
    def test_extract_conditions_error(self, mock_openai):
        """Test extract conditions with error."""
        # Mock OpenAI error
        mock_openai.return_value.chat.completions.create.side_effect = Exception("API Error")

        # Extract conditions
        operations = []
        relationships = []
        conditions = self.extractor.extract_conditions(operations, relationships)
        
        # Should return empty list on error
        assert conditions == []

    def test_prompts_not_empty(self):
        """Test that prompts are not empty."""
        assert len(OPERATION_EXTRACTION_PROMPT) > 0
        assert len(RELATIONSHIP_EXTRACTION_PROMPT) > 0
        assert len(SEQUENTIAL_ORDER_PROMPT) > 0
        assert len(CONDITION_EXTRACTION_PROMPT) > 0

    def test_prompts_contain_placeholders(self):
        """Test that prompts contain required placeholders."""
        assert "{skill_content}" in OPERATION_EXTRACTION_PROMPT
        assert "{operations}" in RELATIONSHIP_EXTRACTION_PROMPT
        assert "{operations}" in SEQUENTIAL_ORDER_PROMPT
        assert "{operations}" in CONDITION_EXTRACTION_PROMPT


class TestLLMExtractionAccuracy:
    """Test LLM extraction accuracy."""

    def test_operation_type_classification(self):
        """Test operation type classification."""
        # Test that all operation types are covered
        operation_types = [
            "web_search",
            "code_execution",
            "api_call",
            "data_processing",
            "llm_call",
            "file_operation",
            "task",
            "condition",
            "loop"
        ]
        
        assert len(operation_types) == 9

    def test_relationship_type_classification(self):
        """Test relationship type classification."""
        # Test that all relationship types are covered
        relationship_types = [
            "sequential",
            "parallel",
            "conditional",
            "iterative"
        ]
        
        assert len(relationship_types) == 4

    def test_causality_classification(self):
        """Test causality classification."""
        # Test that all causality types are covered
        causality_types = [
            "data_flow",
            "control_flow",
            "both"
        ]
        
        assert len(causality_types) == 3

    def test_parallel_type_classification(self):
        """Test parallel type classification."""
        # Test that all parallel types are covered
        parallel_types = [
            "fork",
            "join"
        ]
        
        assert len(parallel_types) == 2

    def test_structure_type_classification(self):
        """Test structure type classification."""
        # Test that all structure types are covered
        structure_types = [
            "conditional",
            "loop"
        ]
        
        assert len(structure_types) == 2


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
