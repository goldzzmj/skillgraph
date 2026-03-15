"""
Graph Retrieval Module

Retrieve entities and communities from the knowledge graph based on queries.
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict

from .models import (
    Entity, Community, RetrievalResult, GraphRAGAnalysis,
    EntityType, RelationType
)
from .embeddings import EmbeddingGenerator


class GraphRetriever:
    """
    Retrieve entities and communities from the knowledge graph.

    Supports multiple retrieval strategies:
    1. Entity retrieval: Find relevant entities based on semantic similarity
    2. Community retrieval: Find relevant communities based on descriptions
    3. Hybrid retrieval: Combine entity and community retrieval
    4. Risk-focused retrieval: Prioritize high-risk components
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize graph retriever.

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.strategy = self.config.get('retrieval', {}).get('strategy', 'hybrid')
        self.top_k_entities = self.config.get('retrieval', {}).get('top_k_entities', 10)
        self.top_k_communities = self.config.get('retrieval', {}).get('top_k_communities', 5)
        self.similarity_threshold = self.config.get('retrieval', {}).get('similarity_threshold', 0.7)
        self.entity_weight = self.config.get('retrieval', {}).get('entity_weight', 0.6)
        self.community_weight = self.config.get('retrieval', {}).get('community_weight', 0.4)
        self.risk_boost = self.config.get('retrieval', {}).get('risk_boost', 1.5)

        # Initialize embedding generator
        self.embedding_generator = EmbeddingGenerator(config)

    def retrieve(
        self,
        query: str,
        analysis: GraphRAGAnalysis
    ) -> RetrievalResult:
        """
        Retrieve relevant entities and communities based on query.

        Args:
            query: User query
            analysis: Complete GraphRAG analysis

        Returns:
            RetrievalResult with retrieved components
        """
        # Generate query embedding
        query_embedding = self.embedding_generator.generate_query_embedding(query)

        # Retrieve based on strategy
        if self.strategy == 'entity':
            return self._retrieve_entity_only(query, query_embedding, analysis)
        elif self.strategy == 'community':
            return self._retrieve_community_only(query, query_embedding, analysis)
        elif self.strategy == 'risk':
            return self._retrieve_risk_focused(query, query_embedding, analysis)
        else:  # hybrid
            return self._retrieve_hybrid(query, query_embedding, analysis)

    def _retrieve_entity_only(
        self,
        query: str,
        query_embedding: np.ndarray,
        analysis: GraphRAGAnalysis
    ) -> RetrievalResult:
        """
        Retrieve entities only based on semantic similarity.

        Args:
            query: User query
            query_embedding: Query embedding
            analysis: Complete GraphRAG analysis

        Returns:
            RetrievalResult with entities only
        """
        # Find similar entities
        similar_entities = self.embedding_generator.find_similar_entities(
            query_embedding,
            analysis.entities,
            top_k=self.top_k_entities,
            threshold=self.similarity_threshold
        )

        # Extract entities and scores
        entities = [entity for entity, score in similar_entities]
        scores = [score for entity, score in similar_entities]

        # Generate reasoning
        reasoning = self._generate_reasoning(query, entities, [], 'entity')

        return RetrievalResult(
            query=query,
            entities=entities,
            communities=[],
            entity_scores=scores,
            community_scores=[],
            reasoning=reasoning,
            total_score=sum(scores) / len(scores) if scores else 0.0
        )

    def _retrieve_community_only(
        self,
        query: str,
        query_embedding: np.ndarray,
        analysis: GraphRAGAnalysis
    ) -> RetrievalResult:
        """
        Retrieve communities only based on semantic similarity.

        Args:
            query: User query
            query_embedding: Query embedding
            analysis: Complete GraphRAG analysis

        Returns:
            RetrievalResult with communities only
        """
        # Find similar communities
        similar_communities = self.embedding_generator.find_similar_communities(
            query_embedding,
            analysis.communities,
            top_k=self.top_k_communities,
            threshold=self.similarity_threshold
        )

        # Expand communities to include their entities
        entities = []
        community_to_entities = defaultdict(list)
        for community, score in similar_communities:
            for entity_id in community.entities:
                entity = self._find_entity_by_id(entity_id, analysis.entities)
                if entity:
                    entities.append(entity)
                    community_to_entities[community.id].append(entity)

        # Extract communities and scores
        communities = [community for community, score in similar_communities]
        scores = [score for community, score in similar_communities]

        # Generate reasoning
        reasoning = self._generate_reasoning(query, entities, communities, 'community')

        return RetrievalResult(
            query=query,
            entities=entities,
            communities=communities,
            entity_scores=[0.0] * len(entities),  # No direct entity scores
            community_scores=scores,
            reasoning=reasoning,
            total_score=sum(scores) / len(scores) if scores else 0.0
        )

    def _retrieve_risk_focused(
        self,
        query: str,
        query_embedding: np.ndarray,
        analysis: GraphRAGAnalysis
    ) -> RetrievalResult:
        """
        Retrieve components with priority on high-risk items.

        Args:
            query: User query
            query_embedding: Query embedding
            analysis: Complete GraphRAG analysis

        Returns:
            RetrievalResult prioritizing high-risk components
        """
        # Find similar entities
        similar_entities = self.embedding_generator.find_similar_entities(
            query_embedding,
            analysis.entities,
            top_k=self.top_k_entities * 2,  # Get more, then filter
            threshold=self.similarity_threshold * 0.5  # Lower threshold
        )

        # Boost scores for high-risk entities
        boosted_entities = []
        for entity, score in similar_entities:
            boosted_score = score
            if entity.risk_score > 0.6:
                boosted_score = min(1.0, score * self.risk_boost)
            elif entity.risk_score > 0.4:
                boosted_score = min(1.0, score * 1.2)

            boosted_entities.append((entity, boosted_score))

        # Sort by boosted scores
        boosted_entities.sort(key=lambda x: x[1], reverse=True)

        # Take top_k
        entities = [entity for entity, score in boosted_entities[:self.top_k_entities]]
        scores = [score for entity, score in boosted_entities[:self.top_k_entities]]

        # Find communities containing these entities
        related_communities = self._find_communities_for_entities(
            entities,
            analysis.communities
        )

        # Generate reasoning
        reasoning = self._generate_reasoning(
            query,
            entities,
            related_communities,
            'risk-focused'
        )

        return RetrievalResult(
            query=query,
            entities=entities,
            communities=related_communities,
            entity_scores=scores,
            community_scores=[c.risk_score for c in related_communities],
            reasoning=reasoning,
            total_score=sum(scores) / len(scores) if scores else 0.0
        )

    def _retrieve_hybrid(
        self,
        query: str,
        query_embedding: np.ndarray,
        analysis: GraphRAGAnalysis
    ) -> RetrievalResult:
        """
        Retrieve using hybrid strategy (entities + communities).

        Args:
            query: User query
            query_embedding: Query embedding
            analysis: Complete GraphRAG analysis

        Returns:
            RetrievalResult combining entities and communities
        """
        # Retrieve entities
        entity_retrieval = self._retrieve_entity_only(
            query, query_embedding, analysis
        )

        # Retrieve communities
        community_retrieval = self._retrieve_community_only(
            query, query_embedding, analysis
        )

        # Combine results
        entities = entity_retrieval.entities
        communities = community_retrieval.communities

        # Calculate weighted total score
        entity_total = (
            sum(entity_retrieval.entity_scores) / len(entity_retrieval.entity_scores)
            if entity_retrieval.entity_scores else 0.0
        )
        community_total = (
            sum(community_retrieval.community_scores) / len(community_retrieval.community_scores)
            if community_retrieval.community_scores else 0.0
        )
        total_score = (
            self.entity_weight * entity_total +
            self.community_weight * community_total
        )

        # Generate combined reasoning
        reasoning = self._generate_reasoning(
            query,
            entities,
            communities,
            'hybrid'
        )

        return RetrievalResult(
            query=query,
            entities=entities,
            communities=communities,
            entity_scores=entity_retrieval.entity_scores,
            community_scores=community_retrieval.community_scores,
            reasoning=reasoning,
            total_score=total_score
        )

    def _find_entity_by_id(
        self,
        entity_id: str,
        entities: List[Entity]
    ) -> Optional[Entity]:
        """
        Find an entity by ID.

        Args:
            entity_id: Entity ID
            entities: List of entities

        Returns:
            Entity or None
        """
        for entity in entities:
            if entity.id == entity_id:
                return entity
        return None

    def _find_communities_for_entities(
        self,
        entities: List[Entity],
        communities: List[Community]
    ) -> List[Community]:
        """
        Find communities that contain the given entities.

        Args:
            entities: List of entities
            communities: List of communities

        Returns:
            List of relevant communities
        """
        entity_ids = {e.id for e in entities}

        relevant_communities = []
        for community in communities:
            # Check if community contains any of the entities
            if any(eid in entity_ids for eid in community.entities):
                relevant_communities.append(community)

        return relevant_communities

    def _generate_reasoning(
        self,
        query: str,
        entities: List[Entity],
        communities: List[Community],
        strategy: str
    ) -> str:
        """
        Generate reasoning explanation for retrieval.

        Args:
            query: User query
            entities: Retrieved entities
            communities: Retrieved communities
            strategy: Retrieval strategy used

        Returns:
            Reasoning explanation
        """
        parts = []

        # Strategy explanation
        strategy_explanations = {
            'entity': "Entity-based retrieval: matched entities by semantic similarity",
            'community': "Community-based retrieval: matched functional modules",
            'hybrid': "Hybrid retrieval: combined entity and community matching",
            'risk-focused': "Risk-focused retrieval: prioritized high-risk components"
        }
        parts.append(strategy_explanations.get(strategy, 'Unknown strategy'))

        # Entity explanation
        if entities:
            high_risk_entities = [e for e in entities if e.risk_score > 0.6]
            parts.append(f"Retrieved {len(entities)} entities")

            if high_risk_entities:
                parts.append(
                    f"  - Including {len(high_risk_entities)} high-risk entities: " +
                    ", ".join([e.name for e in high_risk_entities[:3]])
                )

            # Entity types
            entity_types = set(e.type.value for e in entities)
            if entity_types:
                parts.append(f"  - Entity types: {', '.join(entity_types)}")

        # Community explanation
        if communities:
            parts.append(f"Retrieved {len(communities)} communities")

            # Community descriptions
            for community in communities[:2]:
                parts.append(f"  - {community.description}")

        # Risk summary
        if entities or communities:
            max_risk = max(
                [e.risk_score for e in entities] +
                [c.risk_score for c in communities]
            )
            if max_risk > 0.6:
                parts.append("⚠️  High-risk components detected")
            elif max_risk > 0.4:
                parts.append("⚡  Moderate-risk components detected")

        return "\n".join(parts)

    def retrieve_by_risk_level(
        self,
        analysis: GraphRAGAnalysis,
        min_risk: float = 0.0,
        max_risk: float = 1.0
    ) -> List[Entity]:
        """
        Retrieve entities within a risk level range.

        Args:
            analysis: Complete GraphRAG analysis
            min_risk: Minimum risk score
            max_risk: Maximum risk score

        Returns:
            List of entities in risk range
        """
        return [
            entity
            for entity in analysis.entities
            if min_risk <= entity.risk_score <= max_risk
        ]

    def retrieve_by_type(
        self,
        analysis: GraphRAGAnalysis,
        entity_type: EntityType
    ) -> List[Entity]:
        """
        Retrieve entities of a specific type.

        Args:
            analysis: Complete GraphRAG analysis
            entity_type: Entity type to filter by

        Returns:
            List of entities of specified type
        """
        return [
            entity
            for entity in analysis.entities
            if entity.type == entity_type
        ]

    def retrieve_related_entities(
        self,
        entity: Entity,
        analysis: GraphRAGAnalysis,
        hops: int = 2
    ) -> List[Entity]:
        """
        Retrieve entities related to a given entity via relationships.

        Args:
            entity: Starting entity
            analysis: Complete GraphRAG analysis
            hops: Number of hops to traverse

        Returns:
            List of related entities
        """
        related = set()
        current_level = {entity.id}

        for _ in range(hops):
            next_level = set()

            for entity_id in current_level:
                # Find relationships involving this entity
                for rel in analysis.relationships:
                    if rel.source_id == entity_id:
                        next_level.add(rel.target_id)
                    elif rel.target_id == entity_id:
                        next_level.add(rel.source_id)

            # Add to related (excluding starting entity)
            related.update(next_level)
            current_level = next_level

            if not current_level:
                break

        # Convert entity IDs to Entity objects
        return [
            e for e in analysis.entities
            if e.id in related and e.id != entity.id
        ]
