"""
Community Detection Module

Detect communities (clusters) in the entity graph using graph clustering algorithms.
"""

import networkx as nx
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import asdict

from .models import Community, Entity, Relationship


class CommunityDetector:
    """
    Detect communities in entity graphs.

    Uses graph clustering algorithms to find groups of closely related entities,
    which represent functional modules or risk clusters.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize community detector.

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.algorithm = self.config.get('community_detection', {}).get('algorithm', 'leiden')
        self.resolution = self.config.get('community_detection', {}).get('resolution', 1.0)
        self.max_level = self.config.get('community_detection', {}).get('max_level', 5)
        self.min_community_size = self.config.get('community_detection', {}).get('min_community_size', 2)
        self.enabled = self.config.get('community_detection', {}).get('enabled', True)

    def detect(
        self,
        entities: List[Entity],
        relationships: List[Relationship],
        level: int = 0
    ) -> List[Community]:
        """
        Detect communities in the entity graph.

        Args:
            entities: List of entities
            relationships: List of relationships
            level: Current hierarchy level

        Returns:
            List of Community objects
        """
        if not self.enabled:
            return []

        if not entities:
            return []

        # Build graph
        G = self._build_graph(entities, relationships)

        # Detect communities
        if self.algorithm == 'leiden':
            communities = self._detect_leiden(G)
        elif self.algorithm == 'louvain':
            communities = self._detect_louvain(G)
        elif self.algorithm == 'spectral':
            communities = self._detect_spectral(G)
        else:
            # Fallback to connected components
            communities = self._detect_connected(G)

        # Filter small communities
        communities = [
            c for c in communities
            if len(c) >= self.min_community_size
        ]

        # Create Community objects
        community_objects = self._create_communities(
            communities,
            entities,
            relationships,
            level
        )

        # Recursively detect sub-communities
        if level < self.max_level and len(community_objects) > 1:
            for community in community_objects:
                if len(community.entities) > self.min_community_size * 2:
                    # Extract subgraph for this community
                    sub_entities = [
                        e for e in entities if e.id in community.entities
                    ]
                    sub_relationships = [
                        r for r in relationships
                        if r.source_id in community.entities and
                           r.target_id in community.entities
                    ]

                    # Detect sub-communities
                    sub_communities = self.detect(
                        sub_entities,
                        sub_relationships,
                        level + 1
                    )

                    # Store sub-communities in properties
                    community.properties['sub_communities'] = [
                        sc.to_dict() for sc in sub_communities
                    ]

        return community_objects

    def _build_graph(
        self,
        entities: List[Entity],
        relationships: List[Relationship]
    ) -> nx.Graph:
        """
        Build a NetworkX graph from entities and relationships.

        Args:
            entities: List of entities
            relationships: List of relationships

        Returns:
            NetworkX graph
        """
        G = nx.Graph()

        # Add nodes (entities)
        for entity in entities:
            G.add_node(
                entity.id,
                label=entity.name,
                type=entity.type.value,
                risk_score=entity.risk_score
            )

        # Add edges (relationships)
        for rel in relationships:
            if G.has_node(rel.source_id) and G.has_node(rel.target_id):
                # If edge already exists, update weight
                if G.has_edge(rel.source_id, rel.target_id):
                    G[rel.source_id][rel.target_id]['weight'] += rel.weight
                    G[rel.source_id][rel.target_id]['count'] += 1
                else:
                    G.add_edge(
                        rel.source_id,
                        rel.target_id,
                        type=rel.type.value,
                        weight=rel.weight,
                        count=1
                    )

        return G

    def _detect_leiden(self, G: nx.Graph) -> List[List[str]]:
        """
        Detect communities using Leiden algorithm.

        Args:
            G: NetworkX graph

        Returns:
            List of communities (each community is a list of node IDs)
        """
        # Leiden is not available in NetworkX, use Louvain as fallback
        # For production, install python-louvain: pip install python-louvain
        try:
            import community as community_louvain
            partition = community_louvain.best_partition(G, resolution=self.resolution)

            # Group nodes by community
            communities_dict = {}
            for node, comm_id in partition.items():
                if comm_id not in communities_dict:
                    communities_dict[comm_id] = []
                communities_dict[comm_id].append(node)

            return list(communities_dict.values())
        except ImportError:
            # Fallback to Louvain via greedy_modularity_communities
            return self._detect_louvain(G)

    def _detect_louvain(self, G: nx.Graph) -> List[List[str]]:
        """
        Detect communities using Louvain algorithm (greedy modularity).

        Args:
            G: NetworkX graph

        Returns:
            List of communities
        """
        try:
            communities = nx.community.greedy_modularity_communities(
                G,
                resolution=self.resolution
            )
            return [list(community) for community in communities]
        except Exception as e:
            # Fallback to connected components
            return self._detect_connected(G)

    def _detect_spectral(self, G: nx.Graph) -> List[List[str]]:
        """
        Detect communities using spectral clustering.

        Args:
            G: NetworkX graph

        Returns:
            List of communities
        """
        try:
            # Use spectral clustering (requires scipy)
            import numpy as np
            from sklearn.cluster import SpectralClustering

            # Get adjacency matrix
            adj_matrix = nx.to_numpy_array(G)

            # Determine number of clusters
            n_clusters = max(2, min(len(G) // 3, 10))

            # Spectral clustering
            clustering = SpectralClustering(
                n_clusters=n_clusters,
                affinity='precomputed',
                random_state=42
            )
            labels = clustering.fit_predict(adj_matrix)

            # Group nodes by cluster
            communities_dict = {}
            for node_id, label in zip(G.nodes(), labels):
                if label not in communities_dict:
                    communities_dict[label] = []
                communities_dict[label].append(node_id)

            return list(communities_dict.values())
        except Exception as e:
            # Fallback to Louvain
            return self._detect_louvain(G)

    def _detect_connected(self, G: nx.Graph) -> List[List[str]]:
        """
        Detect communities using connected components (simple fallback).

        Args:
            G: NetworkX graph

        Returns:
            List of communities
        """
        components = nx.connected_components(G)
        return [list(component) for component in components]

    def _create_communities(
        self,
        communities: List[List[str]],
        entities: List[Entity],
        relationships: List[Relationship],
        level: int
    ) -> List[Community]:
        """
        Create Community objects from detected groups.

        Args:
            communities: List of entity ID groups
            entities: All entities
            relationships: All relationships
            level: Hierarchy level

        Returns:
            List of Community objects
        """
        community_objects = []

        for i, community_entities in enumerate(communities):
            # Create entity lookup
            entity_dict = {e.id: e for e in entities}

            # Calculate community risk score
            risk_scores = [
                entity_dict[eid].risk_score
                for eid in community_entities
                if eid in entity_dict
            ]
            avg_risk = sum(risk_scores) / len(risk_scores) if risk_scores else 0.0

            # Generate description
            description = self._generate_community_description(
                community_entities,
                entity_dict,
                relationships
            )

            community = Community(
                id=f"community_level{level}_{i:03d}",
                level=level,
                entities=community_entities,
                description=description,
                risk_score=avg_risk,
                properties={
                    'size': len(community_entities),
                    'entity_types': list(set(
                        entity_dict[eid].type.value
                        for eid in community_entities
                        if eid in entity_dict
                    ))
                }
            )

            community_objects.append(community)

        return community_objects

    def _generate_community_description(
        self,
        entity_ids: List[str],
        entity_dict: Dict[str, Entity],
        relationships: List[Relationship]
    ) -> str:
        """
        Generate a description for a community.

        Args:
            entity_ids: Entity IDs in the community
            entity_dict: Entity lookup dictionary
            relationships: All relationships

        Returns:
            Community description
        """
        # Gather entity types
        entity_types = [
            entity_dict[eid].type.value
            for eid in entity_ids
            if eid in entity_dict
        ]

        # Count types
        type_counts = {}
        for t in entity_types:
            type_counts[t] = type_counts.get(t, 0) + 1

        # Generate description based on dominant types
        if not type_counts:
            return "Empty community"

        dominant_type = max(type_counts.items(), key=lambda x: x[1])[0]

        # Type-specific descriptions
        descriptions = {
            'tool': "External tools and command execution",
            'api': "API calls and external services",
            'file': "File system operations",
            'config': "Configuration and settings",
            'network': "Network operations and external resources",
            'permission': "Permissions and access controls",
            'code': "Code blocks and functions"
        }

        base_desc = descriptions.get(dominant_type, f"{dominant_type} operations")

        # Add entity count
        desc = f"{base_desc} ({len(entity_ids)} entities)"

        # Add risk level
        risk_scores = [
            entity_dict[eid].risk_score
            for eid in entity_ids
            if eid in entity_dict
        ]
        avg_risk = sum(risk_scores) / len(risk_scores) if risk_scores else 0.0

        if avg_risk > 0.6:
            desc += " [HIGH RISK]"
        elif avg_risk > 0.4:
            desc += " [MEDIUM RISK]"
        elif avg_risk > 0.2:
            desc += " [LOW RISK]"

        return desc

    def get_community_hierarchy(
        self,
        communities: List[Community]
    ) -> Dict[int, List[Community]]:
        """
        Organize communities by hierarchy level.

        Args:
            communities: List of all communities

        Returns:
            Dictionary mapping level to communities at that level
        """
        hierarchy = {}

        for community in communities:
            level = community.level
            if level not in hierarchy:
                hierarchy[level] = []
            hierarchy[level].append(community)

        return hierarchy

    def get_parent_community(
        self,
        entity_id: str,
        communities: List[Community]
    ) -> Optional[Community]:
        """
        Find the parent community containing an entity.

        Args:
            entity_id: Entity to find
            communities: List of communities

        Returns:
            Parent community or None
        """
        for community in communities:
            if entity_id in community.entities:
                return community
        return None
