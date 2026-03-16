"""
Graph Store - Neo4j Graph Database

Multi-layer graph implementation with entity and operation nodes.
"""

from typing import Dict, Any, List, Optional, Union
import logging

try:
    from neo4j import GraphDatabase
    from neo4j.exceptions import ServiceUnavailable, AuthError
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    GraphDatabase = None

from .models import (
    BaseNode,
    EntityNode,
    OperationNode,
    BaseEdge,
    TemporalEdge,
    DependencyEdge,
    ParallelEdge,
    ConditionalEdge,
    IterativeEdge,
    NodeType,
    OperationType,
    EdgeType
)

logger = logging.getLogger(__name__)


class MockGraphStore:
    """Mock graph store for testing without Neo4j."""

    def __init__(self):
        self.nodes: Dict[str, BaseNode] = {}
        self.edges: Dict[str, BaseEdge] = {}

    def create_entity_node(self, entity_node: EntityNode) -> str:
        """Create entity node."""
        self.nodes[entity_node.node_id] = entity_node
        logger.info(f"Created entity node: {entity_node.node_id}")
        return entity_node.node_id

    def create_operation_node(self, operation_node: OperationNode) -> str:
        """Create operation node."""
        self.nodes[operation_node.node_id] = operation_node
        logger.info(f"Created operation node: {operation_node.node_id}")
        return operation_node.node_id

    def create_edge(
        self,
        source_id: str,
        target_id: str,
        edge_data: Dict[str, Any]
    ) -> str:
        """Create edge between nodes."""
        edge_id = f"edge_{source_id}_{target_id}"
        self.edges[edge_id] = edge_data
        logger.info(f"Created edge: {edge_id}")
        return edge_id

    def get_node(self, node_id: str) -> Optional[BaseNode]:
        """Get node by ID."""
        return self.nodes.get(node_id)

    def get_operation_dependencies(
        self, operation_id: str
    ) -> List[Dict[str, Any]]:
        """Get operation dependencies."""
        dependencies = []
        for edge in self.edges.values():
            if edge.get('source_node_id') == operation_id:
                target_node = self.get_node(edge.get('target_node_id'))
                if target_node:
                    dependencies.append({
                        'node': target_node,
                        'edge': edge
                    })
        return dependencies

    def get_execution_path(self, start_id: str, end_id: str) -> List[str]:
        """Get execution path between nodes."""
        # Simple BFS for mock implementation
        visited = set()
        queue = [start_id]
        parent = {start_id: None}

        while queue:
            current = queue.pop(0)

            if current == end_id:
                # Reconstruct path
                path = [current]
                parent_node = parent[current]
                while parent_node is not None:
                    path.append(parent_node)
                    parent_node = parent[parent_node]
                return list(reversed(path))

            for edge in self.edges.values():
                if edge.get('source_node_id') == current:
                    target = edge.get('target_node_id')
                    if target not in visited:
                        visited.add(target)
                        queue.append(target)
                        parent[target] = current

        return []

    def delete_node(self, node_id: str) -> bool:
        """Delete node by ID."""
        if node_id in self.nodes:
            del self.nodes[node_id]
            logger.info(f"Deleted node: {node_id}")
            return True
        return False

    def close(self):
        """Close graph store."""
        logger.info("Mock graph store closed")


class Neo4jGraphStore:
    """Neo4j graph database for multi-layer graph."""

    def __init__(self, uri: str, user: str, password: str):
        if not NEO4J_AVAILABLE:
            logger.warning("Neo4j not available, using mock store")
            self._mock = MockGraphStore()
            return

        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            self._mock = None
            self._create_constraints()
            logger.info(f"Connected to Neo4j at {uri}")
        except ServiceUnavailable as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            self._mock = MockGraphStore()
        except AuthError as e:
            logger.error(f"Authentication failed: {e}")
            self._mock = MockGraphStore()

    def close(self):
        """Close Neo4j driver."""
        if self._mock:
            self._mock.close()
        elif self.driver:
            self.driver.close()
            logger.info("Neo4j driver closed")

    def _create_constraints(self):
        """Create graph constraints and indexes."""
        try:
            with self.driver.session() as session:
                # Create node indexes
                session.run("CREATE INDEX node_id_index IF NOT EXISTS FOR (n:Node) ON (n.node_id)")
                session.run("CREATE INDEX node_name_index IF NOT EXISTS FOR (n:Node) ON (n.name)")
                session.run("CREATE INDEX node_type_index IF NOT EXISTS FOR (n:Node) ON (n.node_type)")

                # Create edge indexes
                session.run("CREATE INDEX edge_source_index IF NOT EXISTS FOR (e:Edge) ON (e.source_node_id)")
                session.run("CREATE INDEX edge_target_index IF NOT EXISTS FOR (e:Edge) ON (e.target_node_id)")
                session.run("CREATE INDEX edge_type_index IF NOT EXISTS FOR (e:Edge) ON (e.edge_type)")

                logger.info("Created constraints and indexes")
        except Exception as e:
            logger.error(f"Failed to create constraints: {e}")

    def create_entity_node(self, entity_node: EntityNode) -> str:
        """Create entity node."""
        if self._mock:
            return self._mock.create_entity_node(entity_node)

        try:
            with self.driver.session() as session:
                result = session.run(
                    """
                    CREATE (n:Entity:Node)
                    SET n = $properties
                    RETURN n.node_id AS node_id
                    """,
                    properties=entity_node.dict()
                )
                node_id = result.single()["node_id"]
                logger.info(f"Created entity node: {node_id}")
                return node_id
        except Exception as e:
            logger.error(f"Failed to create entity node: {e}")
            return ""

    def create_operation_node(self, operation_node: OperationNode) -> str:
        """Create operation node."""
        if self._mock:
            return self._mock.create_operation_node(operation_node)

        try:
            with self.driver.session() as session:
                result = session.run(
                    """
                    CREATE (n:Operation:Node)
                    SET n = $properties
                    RETURN n.node_id AS node_id
                    """,
                    properties=operation_node.dict()
                )
                node_id = result.single()["node_id"]
                logger.info(f"Created operation node: {node_id}")
                return node_id
        except Exception as e:
            logger.error(f"Failed to create operation node: {e}")
            return ""

    def create_edge(
        self,
        source_id: str,
        target_id: str,
        edge_data: Dict[str, Any]
    ) -> str:
        """Create edge between nodes."""
        if self._mock:
            return self._mock.create_edge(source_id, target_id, edge_data)

        try:
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
                edge_id = result.single()["edge_id"]
                logger.info(f"Created edge: {edge_id}")
                return edge_id
        except Exception as e:
            logger.error(f"Failed to create edge: {e}")
            return ""

    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get node by ID."""
        if self._mock:
            return self._mock.get_node(node_id)

        try:
            with self.driver.session() as session:
                result = session.run(
                    """
                    MATCH (n:Node {node_id: $node_id})
                    RETURN n AS node
                    """,
                    node_id=node_id
                )
                if result.single():
                    return result.single()["node"]
                return None
        except Exception as e:
            logger.error(f"Failed to get node: {e}")
            return None

    def get_operation_dependencies(
        self,
        operation_id: str
    ) -> List[Dict[str, Any]]:
        """Get operation dependencies."""
        if self._mock:
            return self._mock.get_operation_dependencies(operation_id)

        try:
            with self.driver.session() as session:
                result = session.run(
                    """
                    MATCH (op:Operation:Node {node_id: $operation_id})-[e:Dependency:Edge]->(dep:Node)
                    RETURN dep AS dependency, e AS edge
                    ORDER BY e.temporal_order ASC
                    """,
                    operation_id=operation_id
                )
                dependencies = []
                for record in result:
                    dependencies.append({
                        'node': record['dependency'],
                        'edge': record['edge']
                    })
                return dependencies
        except Exception as e:
            logger.error(f"Failed to get operation dependencies: {e}")
            return []

    def get_execution_path(self, start_id: str, end_id: str) -> List[str]:
        """Get execution path between nodes."""
        if self._mock:
            return self._mock.get_execution_path(start_id, end_id)

        try:
            with self.driver.session() as session:
                result = session.run(
                    """
                    MATCH path = shortestPath((start:Node {node_id: $start_id})-[:Dependency:Edge*]->(end:Node {node_id: $end_id}))
                    RETURN [node.node_id FOR node IN nodes(path)]
                    """,
                    start_id=start_id,
                    end_id=end_id
                )
                if result.single():
                    return result.single()[0]
                return []
        except Exception as e:
            logger.error(f"Failed to get execution path: {e}")
            return []

    def delete_node(self, node_id: str) -> bool:
        """Delete node by ID."""
        if self._mock:
            return self._mock.delete_node(node_id)

        try:
            with self.driver.session() as session:
                result = session.run(
                    """
                    MATCH (n:Node {node_id: $node_id})
                    DETACH DELETE n
                    RETURN TRUE AS success
                    """,
                    node_id=node_id
                )
                success = result.single()["success"]
                logger.info(f"Deleted node: {node_id}")
                return success
        except Exception as e:
            logger.error(f"Failed to delete node: {e}")
            return False

    def get_all_nodes(self, node_type: Optional[NodeType] = None) -> List[Dict[str, Any]]:
        """Get all nodes, optionally filtered by type."""
        if self._mock:
            return list(self._mock.nodes.values())

        try:
            with self.driver.session() as session:
                if node_type:
                    result = session.run(
                        """
                        MATCH (n:Node {node_type: $node_type})
                        RETURN n AS node
                        ORDER BY n.created_at DESC
                        """,
                        node_type=node_type.value
                    )
                else:
                    result = session.run(
                        """
                        MATCH (n:Node)
                        RETURN n AS node
                        ORDER BY n.created_at DESC
                        """
                    )
                nodes = []
                for record in result:
                    nodes.append(record["node"])
                return nodes
        except Exception as e:
            logger.error(f"Failed to get all nodes: {e}")
            return []

    def get_all_edges(self, edge_type: Optional[EdgeType] = None) -> List[Dict[str, Any]]:
        """Get all edges, optionally filtered by type."""
        if self._mock:
            return list(self._mock.edges.values())

        try:
            with self.driver.session() as session:
                if edge_type:
                    result = session.run(
                        """
                        MATCH ()-[e:Edge {edge_type: $edge_type}]->()
                        RETURN e AS edge
                        ORDER BY e.created_at DESC
                        """,
                        edge_type=edge_type.value
                    )
                else:
                    result = session.run(
                        """
                        MATCH ()-[e:Edge]->()
                        RETURN e AS edge
                        ORDER BY e.created_at DESC
                        """
                    )
                edges = []
                for record in result:
                    edges.append(record["edge"])
                return edges
        except Exception as e:
            logger.error(f"Failed to get all edges: {e}")
            return []


def get_graph_store(uri: str = None, user: str = None, password: str = None) -> Union[Neo4jGraphStore, MockGraphStore]:
    """
    Get graph store instance.

    Args:
        uri: Neo4j connection URI
        user: Neo4j username
        password: Neo4j password

    Returns:
        Graph store instance
    """
    import os

    uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = user or os.getenv("NEO4J_USER", "neo4j")
    password = password or os.getenv("NEO4J_PASSWORD", "password")

    return Neo4jGraphStore(uri, user, password)
