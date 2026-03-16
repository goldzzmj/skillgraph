"""
Adaptive Community Detection Module

Automatically selects the best community detection algorithm based on graph characteristics.
"""

import networkx as nx
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

from .models import Community, Entity, Relationship
from .community_detection import CommunityDetector


class AdaptiveCommunityDetector:
    """
    Adaptive community detector that selects the best algorithm.

    Features:
    - Automatic algorithm selection based on graph properties
    - Multiple algorithm options (Leiden, Louvain, Spectral, Label Propagation)
    - Graph analysis and characterization
    - Performance optimization
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize adaptive community detector.

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.resolution = self.config.get('community_detection', {}).get('resolution', 1.0)
        self.max_level = self.config.get('community_detection', {}).get('max_level', 5)
        self.min_community_size = self.config.get('community_detection', {}).get('min_community_size', 2)

        # Algorithm preferences
        self.preferred_algorithm = self.config.get('community_detection', {}).get('algorithm', 'auto')
        self.enable_adaptive = self.config.get('community_detection', {}).get('enable_adaptive', True)

        # Base detector for specific algorithms
        self.base_detector = CommunityDetector(config)

    def detect(
        self,
        entities: List[Entity],
        relationships: List[Relationship],
        level: int = 0
    ) -> List[Community]:
        """
        Detect communities with adaptive algorithm selection.

        Args:
            entities: List of entities
            relationships: List of relationships
            level: Current hierarchy level

        Returns:
            List of detected communities
        """
        # Build graph
        G = self._build_graph(entities, relationships)

        if G.number_of_nodes() == 0:
            return []

        # Analyze graph
        graph_properties = self._analyze_graph(G)

        # Select algorithm
        if self.enable_adaptive and self.preferred_algorithm == 'auto':
            algorithm = self._select_algorithm(graph_properties)
        else:
            algorithm = self.preferred_algorithm

        print(f"Graph properties: {graph_properties}")
        print(f"Selected algorithm: {algorithm}")

        # Detect communities with selected algorithm
        communities = self._detect_with_algorithm(
            G,
            algorithm,
            entities,
            level
        )

        # Assign risk scores
        self._assign_risk_scores(communities, entities)

        # Filter small communities
        communities = [c for c in communities if len(c.entities) >= self.min_community_size]

        # Build hierarchy if needed
        if level < self.max_level:
            hierarchical = self._build_hierarchy(communities, entities, relationships, level + 1)
            communities.extend(hierarchical)

        return communities

    def _build_graph(
        self,
        entities: List[Entity],
        relationships: List[Relationship]
    ) -> nx.DiGraph:
        """
        Build NetworkX graph from entities and relationships.

        Args:
            entities: List of entities
            relationships: List of relationships

        Returns:
            NetworkX DiGraph
        """
        G = nx.DiGraph()

        # Add nodes
        for entity in entities:
            G.add_node(
                entity.id,
                label=entity.name,
                type=entity.type.value,
                risk_score=entity.risk_score
            )

        # Add edges
        for rel in relationships:
            if G.has_node(rel.source_id) and G.has_node(rel.target_id):
                G.add_edge(
                    rel.source_id,
                    rel.target_id,
                    type=rel.type.value,
                    weight=rel.weight
                )

        return G

    def _analyze_graph(self, G: nx.DiGraph) -> Dict[str, Any]:
        """
        Analyze graph properties for algorithm selection.

        Args:
            G: NetworkX graph

        Returns:
            Dictionary of graph properties
        """
        properties = {}

        # Basic properties
        properties['num_nodes'] = G.number_of_nodes()
        properties['num_edges'] = G.number_of_edges()
        properties['is_directed'] = G.is_directed()

        # Density
        if G.number_of_nodes() > 1:
            properties['density'] = nx.density(G)
        else:
            properties['density'] = 0.0

        # Connectivity
        if G.is_directed():
            G_undirected = G.to_undirected()
            properties['is_connected'] = nx.is_connected(G_undirected)
            properties['num_components'] = nx.number_connected_components(G_undirected)
        else:
            properties['is_connected'] = nx.is_connected(G)
            properties['num_components'] = nx.number_connected_components(G)

        # Clustering coefficient
        if G.number_of_nodes() > 2:
            if G.is_directed():
                G_undirected = G.to_undirected()
                properties['avg_clustering'] = nx.average_clustering(G_undirected)
            else:
                properties['avg_clustering'] = nx.average_clustering(G)
        else:
            properties['avg_clustering'] = 0.0

        # Degree statistics
        degrees = [d for n, d in G.degree()]
        if degrees:
            properties['avg_degree'] = np.mean(degrees)
            properties['max_degree'] = np.max(degrees)
            properties['min_degree'] = np.min(degrees)
            properties['std_degree'] = np.std(degrees)
        else:
            properties['avg_degree'] = 0.0
            properties['max_degree'] = 0.0
            properties['min_degree'] = 0.0
            properties['std_degree'] = 0.0

        # Categorize graph type
        properties['graph_type'] = self._categorize_graph(properties)

        return properties

    def _categorize_graph(self, properties: Dict[str, Any]) -> str:
        """
        Categorize graph type based on properties.

        Args:
            properties: Graph properties

        Returns:
            Graph type string
        """
        num_nodes = properties['num_nodes']
        density = properties['density']
        avg_clustering = properties['avg_clustering']
        num_components = properties['num_components']

        if num_nodes < 50:
            return 'small'
        elif num_nodes < 500:
            return 'medium'
        else:
            return 'large'

    def _select_algorithm(self, properties: Dict[str, Any]) -> str:
        """
        Select the best algorithm based on graph properties.

        Args:
            properties: Graph properties

        Returns:
            Algorithm name
        """
        num_nodes = properties['num_nodes']
        density = properties['density']
        is_connected = properties['is_connected']
        graph_type = properties['graph_type']

        # Decision rules
        if not is_connected:
            # Disconnected graph - use label propagation
            return 'label_propagation'

        elif graph_type == 'small' or num_nodes < 100:
            # Small graphs - use Leiden for quality
            return 'leiden'

        elif graph_type == 'medium' or num_nodes < 1000:
            # Medium graphs - use Louvain for speed
            return 'louvain'

        else:
            # Large graphs - use spectral for scalability
            return 'spectral'

    def _detect_with_algorithm(
        self,
        G: nx.DiGraph,
        algorithm: str,
        entities: List[Entity],
        level: int
    ) -> List[Community]:
        """
        Detect communities using specific algorithm.

        Args:
            G: NetworkX graph
            algorithm: Algorithm name
            entities: List of entities
            level: Current hierarchy level

        Returns:
            List of communities
        """
        try:
            if algorithm == 'leiden':
                return self._detect_leiden(G, entities, level)
            elif algorithm == 'louvain':
                return self._detect_louvain(G, entities, level)
            elif algorithm == 'spectral':
                return self._detect_spectral(G, entities, level)
            elif algorithm == 'label_propagation':
                return self._detect_label_propagation(G, entities, level)
            else:
                print(f"Unknown algorithm: {algorithm}, using Leiden")
                return self._detect_leiden(G, entities, level)

        except Exception as e:
            print(f"Error with algorithm {algorithm}: {e}")
            # Fall back to base detector
            return self.base_detector.detect(entities, [], level)

    def _detect_leiden(
        self,
        G: nx.DiGraph,
        entities: List[Entity],
        level: int
    ) -> List[Community]:
        """Detect communities using Leiden algorithm."""
        try:
            import community as community_louvain

            # Convert to undirected for community detection
            G_undirected = G.to_undirected()

            # Detect communities
            partition = community_louvain.best_partition(
                G_undirected,
                resolution=self.resolution
            )

            # Build community objects
            communities = self._build_communities_from_partition(
                partition,
                entities,
                level
            )

            return communities

        except ImportError:
            print("Warning: python-leiden not installed, falling back to Louvain")
            return self._detect_louvain(G, entities, level)

    def _detect_louvain(
        self,
        G: nx.DiGraph,
        entities: List[Entity],
        level: int
    ) -> List[Community]:
        """Detect communities using Louvain algorithm."""
        try:
            import community as community_louvain

            # Convert to undirected
            G_undirected = G.to_undirected()

            # Detect communities
            partition = community_louvain.best_partition(
                G_undirected,
                resolution=self.resolution
            )

            # Build community objects
            communities = self._build_communities_from_partition(
                partition,
                entities,
                level
            )

            return communities

        except ImportError:
            print("Warning: python-louvain not installed, falling back to spectral")
            return self._detect_spectral(G, entities, level)

    def _detect_spectral(
        self,
        G: nx.DiGraph,
        entities: List[Entity],
        level: int
    ) -> List[Community]:
        """Detect communities using spectral clustering."""
        # Convert to undirected
        G_undirected = G.to_undirected()

        # Detect communities
        num_communities = min(len(entities) // self.min_community_size, 20)

        if G_undirected.number_of_nodes() < num_communities:
            num_communities = max(1, G_undirected.number_of_nodes() // 5)

        try:
            labels = nx.algorithms.community.spectral_clustering(
                G_undirected,
                k=num_communities
            )

            # Build partition
            partition = {node: label for node, label in labels.items()}

            # Build community objects
            communities = self._build_communities_from_partition(
                partition,
                entities,
                level
            )

            return communities

        except Exception as e:
            print(f"Error in spectral clustering: {e}")
            return []

    def _detect_label_propagation(
        self,
        G: nx.DiGraph,
        entities: List[Entity],
        level: int
    ) -> List[Community]:
        """Detect communities using label propagation."""
        # Convert to undirected
        G_undirected = G.to_undirected()

        try:
            labels = nx.algorithms.community.label_propagation_communities(G_undirected)

            # Build partition
            partition = {}
            for i, community_nodes in enumerate(labels):
                for node in community_nodes:
                    partition[node] = i

            # Build community objects
            communities = self._build_communities_from_partition(
                partition,
                entities,
                level
            )

            return communities

        except Exception as e:
            print(f"Error in label propagation: {e}")
            return []

    def _build_communities_from_partition(
        self,
        partition: Dict[str, int],
        entities: List[Entity],
        level: int
    ) -> List[Community]:
        """
        Build community objects from partition.

        Args:
            partition: Node to community ID mapping
            entities: List of entities
            level: Current hierarchy level

        Returns:
            List of Community objects
        """
        from .models import Community, CommunityLevel

        # Group entities by community
        communities_dict = {}
        for entity in entities:
            comm_id = partition.get(entity.id, 0)
            if comm_id not in communities_dict:
                communities_dict[comm_id] = []
            communities_dict[comm_id].append(entity)

        # Build Community objects
        communities = []
        for comm_id, comm_entities in communities_dict.items():
            if len(comm_entities) < self.min_community_size:
                continue

            # Determine risk level
            avg_risk = sum(e.risk_score for e in comm_entities) / len(comm_entities)

            # Build description
            entity_types = list(set(e.type.value for e in comm_entities))
            description = f"Community {comm_id}: {', '.join(entity_types[:3])}"

            # Create community object
            from .models import CommunityLevel

            community = Community(
                id=f"community_{comm_id}_level{level}",
                description=description,
                entities=[e.id for e in comm_entities],
                level=CommunityLevel(level),
                risk_score=avg_risk,
                properties={
                    'algorithm': 'adaptive',
                    'entity_types': entity_types,
                    'size': len(comm_entities)
                }
            )

            communities.append(community)

        return communities

    def _assign_risk_scores(self, communities: List[Community], entities: List[Entity]):
        """
        Assign risk scores to communities.

        Args:
            communities: List of communities
            entities: List of entities
        """
        entity_dict = {e.id: e for e in entities}

        for community in communities:
            entity_ids = community.entities
            entity_risks = []

            for eid in entity_ids:
                if eid in entity_dict:
                    entity_risks.append(entity_dict[eid].risk_score)

            if entity_risks:
                # Average risk of entities in community
                community.risk_score = sum(entity_risks) / len(entity_risks)

                # Boost risk if contains high-risk entities
                high_risk_count = sum(1 for r in entity_risks if r > 0.6)
                if high_risk_count > len(entity_risks) / 2:
                    community.risk_score = min(1.0, community.risk_score * 1.2)

    def _build_hierarchy(
        self,
        communities: List[Community],
        entities: List[Entity],
        relationships: List[Relationship],
        level: int
    ) -> List[Community]:
        """
        Build hierarchical communities.

        Args:
            communities: Communities at current level
            entities: List of entities
            relationships: List of relationships
            level: Next level to build

        Returns:
            List of hierarchical communities
        """
        # For now, return empty (hierarchical detection is complex)
        # This can be extended in future versions
        return []

    def get_community_hierarchy(self, communities: List[Community]) -> Dict[int, List[Community]]:
        """
        Get community hierarchy.

        Args:
            communities: List of communities

        Returns:
            Dictionary mapping level to communities
        """
        hierarchy = {}
        for community in communities:
            level = community.level.value if hasattr(community.level, 'value') else community.level
            if level not in hierarchy:
                hierarchy[level] = []
            hierarchy[level].append(community)

        return hierarchy
