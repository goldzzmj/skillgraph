"""
Knowledge Graph Module

Build and manage knowledge graph for GraphRAG analysis.
"""

import networkx as nx
from typing import List, Dict, Any, Optional
from dataclasses import asdict
from pathlib import Path
import json

from .models import (
    Entity, Relationship, Community, GraphRAGAnalysis,
    EntityType, RelationType
)
from .entity_extraction import EntityExtractor
from .community_detection import CommunityDetector
from .embeddings import EmbeddingGenerator
from .retrieval import GraphRetriever


class KnowledgeGraph:
    """
    Knowledge graph for AI Agent Skills security analysis.

    Integrates entity extraction, relationship detection, community detection,
    embedding generation, and graph retrieval into a unified workflow.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize knowledge graph builder.

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}

        # Initialize components
        self.entity_extractor = EntityExtractor(config)
        self.community_detector = CommunityDetector(config)
        self.embedding_generator = EmbeddingGenerator(config)
        self.retriever = GraphRetriever(config)

        # Graph data
        self.entities: List[Entity] = []
        self.relationships: List[Relationship] = []
        self.communities: List[Community] = []
        self.nx_graph: Optional[nx.DiGraph] = None

    def build(
        self,
        parsed_skill,
        risk_findings: List[Dict[str, Any]] = None
    ) -> GraphRAGAnalysis:
        """
        Build complete knowledge graph from parsed skill.

        Args:
            parsed_skill: ParsedSkill object from parser
            risk_findings: Optional list of risk findings

        Returns:
            Complete GraphRAGAnalysis object
        """
        # Step 1: Extract entities
        self.entities = self.entity_extractor.extract(
            parsed_skill.content if hasattr(parsed_skill, 'content') else '',
            parsed_skill.sections if hasattr(parsed_skill, 'sections') else [],
            parsed_skill.code_blocks if hasattr(parsed_skill, 'code_blocks') else []
        )

        # Step 2: Extract relationships
        self.relationships = self._extract_relationships()

        # Step 3: Detect communities
        self.communities = self.community_detector.detect(
            self.entities,
            self.relationships
        )

        # Step 4: Assign risk scores
        if risk_findings:
            self._assign_risk_scores(risk_findings)

        # Step 5: Generate embeddings (with consistent TF-IDF fitting)
        self._generate_all_embeddings()

        # Step 6: Build NetworkX graph
        self.nx_graph = self._build_nx_graph()

        # Step 7: Generate analysis summary
        summary = self._generate_summary()

        # Create analysis object
        analysis = GraphRAGAnalysis(
            entities=self.entities,
            relationships=self.relationships,
            communities=self.communities,
            risk_findings=risk_findings or [],
            summary=summary
        )

        return analysis

    def _extract_relationships(self) -> List[Relationship]:
        """
        Extract relationships between entities.

        Returns:
            List of Relationship objects
        """
        # Use entity extractor's relationship extraction
        relationship_dicts = self.entity_extractor.extract_relationships(
            self.entities,
            self._get_full_content()
        )

        # Convert to Relationship objects
        relationships = []
        for rel_dict in relationship_dicts:
            try:
                rel = Relationship(
                    source_id=rel_dict['source_id'],
                    target_id=rel_dict['target_id'],
                    type=RelationType(rel_dict['type']),
                    description=self._generate_relationship_description(
                        rel_dict['type']
                    ),
                    confidence=rel_dict.get('confidence', 1.0)
                )
                relationships.append(rel)
            except ValueError:
                # Invalid relation type, skip
                continue

        return relationships

    def _generate_relationship_description(self, relation_type: str) -> str:
        """
        Generate description for a relationship type.

        Args:
            relation_type: Type of relationship

        Returns:
            Description string
        """
        descriptions = {
            'calls': 'executes or invokes',
            'depends_on': 'depends on or requires',
            'accesses': 'reads or accesses',
            'modifies': 'writes to or modifies',
            'contains': 'contains or includes',
            'requires': 'requires for operation',
            'validates': 'checks or verifies',
            'transforms': 'converts or transforms',
            'authenticates': 'authenticates with'
        }
        return descriptions.get(relation_type, 'related to')

    def _assign_risk_scores(self, risk_findings: List[Dict[str, Any]]):
        """
        Assign risk scores to entities based on risk findings.

        Args:
            risk_findings: List of risk findings
        """
        # Get risk weights from config
        entity_weights = self.config.get('risk_assessment', {}).get(
            'entity_risk_weights', {}
        )

        for entity in self.entities:
            # Base risk from entity type
            base_risk = entity_weights.get(entity.type.value, 0.2)

            # Check if entity appears in risk findings
            entity_in_findings = False
            for finding in risk_findings:
                content = finding.get('content_snippet', '')
                if entity.name.lower() in content.lower():
                    entity_in_findings = True
                    # Boost risk if in findings
                    base_risk = min(1.0, base_risk * 1.5)
                    break

            # Check entity properties for risk indicators
            risk_indicators = [
                '.env', '.ssh', '.key', '.pem', 'password', 'secret',
                'token', 'credential', 'admin', 'root', 'sudo',
                'http://', 'https://', 'upload', 'download', 'exec'
            ]

            for indicator in risk_indicators:
                if indicator in entity.name.lower() or indicator in entity.description.lower():
                    base_risk = min(1.0, base_risk + 0.1)

            # Cap risk at 1.0
            entity.risk_score = min(1.0, base_risk)

    def _generate_all_embeddings(self):
        """
        Generate embeddings for entities, relationships, and communities
        with consistent TF-IDF fitting.
        """
        # Collect all texts that need embedding
        entity_texts = [
            f"{entity.name}. {entity.description}"
            for entity in self.entities
        ]

        relationship_texts = [
            f"{rel.type.value}. {rel.description}"
            for rel in self.relationships
        ]

        community_texts = [
            community.description
            for community in self.communities
        ]

        # Fit TF-IDF vectorizer on ALL texts together (for consistent dimensions)
        all_texts = entity_texts + relationship_texts + community_texts
        self.embedding_generator._fit_tfidf(all_texts)

        # Now generate embeddings for each type
        self.entities = self.embedding_generator.generate_entity_embeddings(
            self.entities
        )
        self.relationships = self.embedding_generator.generate_relationship_embeddings(
            self.relationships
        )
        self.communities = self.embedding_generator.generate_community_embeddings(
            self.communities
        )

    def _build_nx_graph(self) -> nx.DiGraph:
        """
        Build NetworkX directed graph.

        Returns:
            NetworkX DiGraph
        """
        G = nx.DiGraph()

        # Add nodes (entities)
        for entity in self.entities:
            G.add_node(
                entity.id,
                label=entity.name,
                type=entity.type.value,
                risk_score=entity.risk_score,
                description=entity.description
            )

        # Add edges (relationships)
        for rel in self.relationships:
            if G.has_node(rel.source_id) and G.has_node(rel.target_id):
                G.add_edge(
                    rel.source_id,
                    rel.target_id,
                    type=rel.type.value,
                    weight=rel.weight,
                    confidence=rel.confidence
                )

        return G

    def _generate_summary(self) -> str:
        """
        Generate a summary of the knowledge graph.

        Returns:
            Summary string
        """
        parts = []

        # Entity summary
        entity_types = {}
        for entity in self.entities:
            entity_types[entity.type.value] = entity_types.get(entity.type.value, 0) + 1

        parts.append("Knowledge Graph Summary:")
        parts.append(f"  - Total entities: {len(self.entities)}")
        parts.append(f"  - Total relationships: {len(self.relationships)}")
        parts.append(f"  - Total communities: {len(self.communities)}")

        # Entity type breakdown
        if entity_types:
            parts.append(f"  - Entity types:")
            for entity_type, count in sorted(entity_types.items(), key=lambda x: x[1], reverse=True):
                parts.append(f"    * {entity_type}: {count}")

        # Risk summary
        high_risk = sum(1 for e in self.entities if e.risk_score > 0.6)
        medium_risk = sum(1 for e in self.entities if 0.4 < e.risk_score <= 0.6)
        low_risk = sum(1 for e in self.entities if 0.2 < e.risk_score <= 0.4)

        if high_risk > 0:
            parts.append(f"  ⚠️  High-risk entities: {high_risk}")
        if medium_risk > 0:
            parts.append(f"  ⚡  Medium-risk entities: {medium_risk}")
        if low_risk > 0:
            parts.append(f"  ⚡  Low-risk entities: {low_risk}")

        # Community summary
        if self.communities:
            avg_community_size = sum(len(c.entities) for c in self.communities) / len(self.communities)
            parts.append(f"  - Average community size: {avg_community_size:.1f} entities")

        return "\n".join(parts)

    def _get_full_content(self) -> str:
        """
        Get full content for relationship extraction.

        Returns:
            Concatenated content string
        """
        parts = []

        for entity in self.entities:
            parts.append(entity.name)
            parts.append(entity.description)

        return "\n".join(parts)

    def query(
        self,
        query: str
    ) -> GraphRAGAnalysis:
        """
        Query knowledge graph.

        Args:
            query: Query string

        Returns:
            GraphRAGAnalysis with query results
        """
        analysis = GraphRAGAnalysis(
            entities=self.entities,
            relationships=self.relationships,
            communities=self.communities,
            risk_findings=[]
        )

        # Perform retrieval
        result = self.retriever.retrieve(query, analysis)

        # Create analysis with retrieved components
        return GraphRAGAnalysis(
            entities=result.entities,
            relationships=[],
            communities=result.communities,
            risk_findings=[],
            summary=f"Query: {query}\n\n{result.reasoning}"
        )

    def export_to_networkx(self) -> nx.DiGraph:
        """
        Export knowledge graph as NetworkX graph.

        Returns:
            NetworkX DiGraph
        """
        if self.nx_graph is None:
            self.nx_graph = self._build_nx_graph()
        return self.nx_graph

    def export_to_json(self, filepath: str):
        """
        Export knowledge graph to JSON file.

        Args:
            filepath: Output file path
        """
        analysis = GraphRAGAnalysis(
            entities=self.entities,
            relationships=self.relationships,
            communities=self.communities,
            risk_findings=[],
            summary=self._generate_summary()
        )

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(analysis.to_dict(), f, indent=2, ensure_ascii=False)

    def export_to_gexf(self, filepath: str):
        """
        Export knowledge graph to GEXF file (for visualization).

        Args:
            filepath: Output file path
        """
        G = self.export_to_networkx()
        nx.write_gexf(G, filepath)

    def export_to_graphml(self, filepath: str):
        """
        Export knowledge graph to GraphML file.

        Args:
            filepath: Output file path
        """
        G = self.export_to_networkx()
        nx.write_graphml(G, filepath)

    def get_high_risk_entities(self, threshold: float = 0.6) -> List[Entity]:
        """
        Get all high-risk entities.

        Args:
            threshold: Risk score threshold

        Returns:
            List of high-risk entities
        """
        return [
            entity
            for entity in self.entities
            if entity.risk_score >= threshold
        ]

    def get_entities_by_type(self, entity_type: EntityType) -> List[Entity]:
        """
        Get all entities of a specific type.

        Args:
            entity_type: Entity type to filter by

        Returns:
            List of entities
        """
        return [
            entity
            for entity in self.entities
            if entity.type == entity_type
        ]

    def get_community_hierarchy(self) -> Dict[int, List[Community]]:
        """
        Get community hierarchy organized by level.

        Returns:
            Dictionary mapping level to communities
        """
        return self.community_detector.get_community_hierarchy(self.communities)
