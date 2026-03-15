"""
Data models for GraphRAG

Define core data structures for entities, relationships, communities, and retrieval results.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum
import numpy as np


class EntityType(Enum):
    """Types of entities extracted from skills."""
    TOOL = "tool"                    # External tools or commands
    API = "api"                      # API endpoints or functions
    FILE = "file"                    # File paths or resources
    VARIABLE = "variable"            # Variables or configuration items
    CONFIG = "config"                # Configuration settings
    PERMISSION = "permission"        # Permissions or access rights
    NETWORK = "network"              # Network resources (URLs, endpoints)
    CODE = "code"                    # Code blocks or functions
    INSTRUCTION = "instruction"      # Natural language instructions


class RelationType(Enum):
    """Types of relationships between entities."""
    CALLS = "calls"                  # Entity A calls Entity B
    DEPENDS_ON = "depends_on"        # Entity A depends on Entity B
    ACCESSES = "accesses"            # Entity A accesses Entity B
    MODIFIES = "modifies"            # Entity A modifies Entity B
    CONTAINS = "contains"            # Entity A contains Entity B
    REQUIRES = "requires"            # Entity A requires Entity B
    VALIDATES = "validates"          # Entity A validates Entity B
    TRANSFORMS = "transforms"        # Entity A transforms to Entity B
    AUTHENTICATES = "authenticates"  # Entity A authenticates with Entity B


@dataclass
class Entity:
    """
    Represents an entity extracted from skill content.

    Entities are atomic units of information such as tools, APIs,
    files, variables, or configuration items.
    """
    id: str                          # Unique identifier
    name: str                        # Entity name
    type: EntityType                 # Entity type
    description: str                  # Description of the entity
    properties: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[np.ndarray] = None  # Vector embedding
    risk_score: float = 0.0          # Associated risk score (0-1)
    confidence: float = 1.0          # Extraction confidence (0-1)
    source_section: str = ""         # Source section ID
    position: Dict[str, int] = field(default_factory=dict)  # Position in text

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type.value,
            'description': self.description,
            'properties': self.properties,
            'risk_score': self.risk_score,
            'confidence': self.confidence,
            'source_section': self.source_section,
            'position': self.position
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Entity':
        """Create Entity from dictionary."""
        return cls(
            id=data['id'],
            name=data['name'],
            type=EntityType(data['type']),
            description=data['description'],
            properties=data.get('properties', {}),
            risk_score=data.get('risk_score', 0.0),
            confidence=data.get('confidence', 1.0),
            source_section=data.get('source_section', ''),
            position=data.get('position', {})
        )


@dataclass
class Relationship:
    """
    Represents a relationship between two entities.

    Relationships capture how entities interact with each other,
    such as calling, depending on, accessing, or modifying.
    """
    source_id: str                   # Source entity ID
    target_id: str                   # Target entity ID
    type: RelationType               # Relationship type
    description: str = ""            # Description of the relationship
    properties: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[np.ndarray] = None  # Vector embedding
    weight: float = 1.0              # Relationship weight (importance)
    confidence: float = 1.0          # Extraction confidence (0-1)
    source_section: str = ""         # Source section ID

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'source_id': self.source_id,
            'target_id': self.target_id,
            'type': self.type.value,
            'description': self.description,
            'properties': self.properties,
            'weight': self.weight,
            'confidence': self.confidence,
            'source_section': self.source_section
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Relationship':
        """Create Relationship from dictionary."""
        return cls(
            source_id=data['source_id'],
            target_id=data['target_id'],
            type=RelationType(data['type']),
            description=data.get('description', ''),
            properties=data.get('properties', {}),
            weight=data.get('weight', 1.0),
            confidence=data.get('confidence', 1.0),
            source_section=data.get('source_section', '')
        )


@dataclass
class Community:
    """
    Represents a community (cluster) of related entities.

    Communities are detected using graph clustering algorithms
    and represent functional modules or risk clusters.
    """
    id: str                          # Unique identifier
    level: int                       # Hierarchy level (0 = top level)
    entities: List[str]              # List of entity IDs
    description: str                  # Community description/summary
    embedding: Optional[np.ndarray] = None  # Vector embedding of summary
    risk_score: float = 0.0          # Aggregated risk score (0-1)
    properties: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'level': self.level,
            'entities': self.entities,
            'description': self.description,
            'risk_score': self.risk_score,
            'properties': self.properties
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Community':
        """Create Community from dictionary."""
        return cls(
            id=data['id'],
            level=data['level'],
            entities=data['entities'],
            description=data['description'],
            risk_score=data.get('risk_score', 0.0),
            properties=data.get('properties', {})
        )


@dataclass
class RetrievalResult:
    """
    Represents a retrieval result from GraphRAG.

    Includes retrieved entities, communities, and relevance scores.
    """
    query: str                       # Original query
    entities: List[Entity]           # Retrieved entities
    communities: List[Community]    # Retrieved communities
    entity_scores: List[float]        # Entity relevance scores
    community_scores: List[float]    # Community relevance scores
    reasoning: str = ""             # Retrieval reasoning/explanation
    total_score: float = 0.0         # Overall retrieval score

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'query': self.query,
            'entities': [e.to_dict() for e in self.entities],
            'communities': [c.to_dict() for c in self.communities],
            'entity_scores': self.entity_scores,
            'community_scores': self.community_scores,
            'reasoning': self.reasoning,
            'total_score': self.total_score
        }


@dataclass
class GraphRAGAnalysis:
    """
    Complete analysis result from GraphRAG.

    Includes knowledge graph, communities, and risk assessments.
    """
    entities: List[Entity]           # All entities
    relationships: List[Relationship]  # All relationships
    communities: List[Community]    # Detected communities
    risk_findings: List[Dict[str, Any]]  # Risk findings
    summary: str = ""               # Analysis summary

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'entities': [e.to_dict() for e in self.entities],
            'relationships': [r.to_dict() for r in self.relationships],
            'communities': [c.to_dict() for c in self.communities],
            'risk_findings': self.risk_findings,
            'summary': self.summary,
            'stats': {
                'entity_count': len(self.entities),
                'relationship_count': len(self.relationships),
                'community_count': len(self.communities),
                'high_risk_count': sum(1 for e in self.entities if e.risk_score > 0.6)
            }
        }
