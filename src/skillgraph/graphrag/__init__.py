"""
GraphRAG Integration for SkillGraph

GraphRAG (Graph Retrieval-Augmented Generation) combines knowledge graphs
with LLM-based retrieval to enhance risk detection in AI Agent Skills.

This module provides:
- Entity extraction from skill content
- Relationship extraction between entities
- Community detection for clustering
- Text embedding generation
- Graph-based retrieval strategies
"""

from .knowledge_graph import KnowledgeGraph
from .entity_extraction import EntityExtractor
from .community_detection import CommunityDetector
from .embeddings import EmbeddingGenerator
from .retrieval import GraphRetriever

__all__ = [
    'KnowledgeGraph',
    'EntityExtractor',
    'CommunityDetector',
    'EmbeddingGenerator',
    'GraphRetriever'
]
