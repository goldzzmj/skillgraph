"""
Optimized Graph Retrieval Module with FAISS Acceleration

Retrieve entities and communities from knowledge graph with high-performance vector search.
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict

from .models import (
    Entity, Community, RetrievalResult, GraphRAGAnalysis,
    EntityType, RelationType
)
from .embeddings import EmbeddingGenerator
from .vector_index import VectorIndex, CachedVectorIndex


class OptimizedGraphRetriever:
    """
    High-performance graph retriever with FAISS acceleration.

    Features:
    - FAISS vector indexing for 10-100x speedup
    - In-memory caching for frequently accessed vectors
    - Multiple retrieval strategies
    - Risk-focused retrieval
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize optimized graph retriever.

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

        # Initialize vector indexes
        self.entity_index: Optional[CachedVectorIndex] = None
        self.community_index: Optional[VectorIndex] = None

        # Enable FAISS acceleration?
        self.use_faiss = self.config.get('retrieval', {}).get('use_faiss', True)

    def build_indexes(
        self,
        entities: List[Entity],
        communities: List[Community]
    ):
        """
        Build FAISS vector indexes for fast retrieval.

        Args:
            entities: List of entities
            communities: List of communities
        """
        if not self.use_faiss:
            print("FAISS acceleration disabled, using linear search")
            return

        # Build entity index
        entity_vectors = []
        entity_ids = []

        for entity in entities:
            if entity.embedding is not None:
                entity_vectors.append(entity.embedding)
                entity_ids.append(entity.id)

        if entity_vectors:
            entity_vectors = np.array(entity_vectors)
            dimension = entity_vectors.shape[1]

            self.entity_index = CachedVectorIndex(
                dimension=dimension,
                index_type="ivf",
                cache_size=1000
            )

            # Add vectors to index
            self.entity_index.add(entity_vectors, entity_ids)

            # Warm up cache with frequently accessed entities
            for entity in entities[:100]:  # Cache first 100 entities
                if entity.embedding is not None:
                    self.entity_index.cache_vector(entity.id, entity.embedding)

            print(f"Built entity index: {self.entity_index}")

        # Build community index
        community_vectors = []
        community_ids = []

        for community in communities:
            if community.embedding is not None:
                community_vectors.append(community.embedding)
                community_ids.append(community.id)

        if community_vectors:
            community_vectors = np.array(community_vectors)
            dimension = community_vectors.shape[1]

            self.community_index = VectorIndex(
                dimension=dimension,
                index_type="ivf"
            )

            self.community_index.add(community_vectors, community_ids)
            print(f"Built community index: {self.community_index}")

    def retrieve(
        self,
        query: str,
        analysis: GraphRAGAnalysis
    ) -> RetrievalResult:
        """
        Retrieve relevant entities and communities.

        Args:
            query: Query string
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

    def _retrieve_with_faiss(
        self,
        query_embedding: np.ndarray,
        index: VectorIndex,
        analysis: GraphRAGAnalysis,
        is_entities: bool,
        top_k: int
    ) -> Tuple[List[Entity], List[float]]:
        """
        Retrieve using FAISS index for fast search.

        Args:
            query_embedding: Query vector
            index: Vector index to search
            analysis: Analysis containing entities/communities
            is_entities: Whether to retrieve entities or communities
            top_k: Number of results to return

        Returns:
            Tuple of (retrieved items, similarity scores)
        """
        if index is None:
            # Fall back to linear search if index not built
            return self._retrieve_linear(
                query_embedding,
                analysis,
                is_entities,
                top_k
            )

        # Fast FAISS search
        distances, indices, ids = index.search(query_embedding, k=top_k)

        # Convert to entities/communities
        items = []
        scores = []

        source = analysis.entities if is_entities else analysis.communities
        id_to_item = {item.id: item for item in source}

        for idx, item_id in zip(indices, ids):
            if idx >= 0 and item_id is not None and item_id in id_to_item:
                items.append(id_to_item[item_id])
                # Convert distance to similarity
                similarity = 1.0 / (1.0 + float(distances[indices == idx][0] if len(indices) > 0 else 0))
                scores.append(similarity)

        return items, scores

    def _retrieve_linear(
        self,
        query_embedding: np.ndarray,
        analysis: GraphRAGAnalysis,
        is_entities: bool,
        top_k: int
    ) -> Tuple[List[Entity], List[float]]:
        """
        Linear search fallback for small datasets.

        Args:
            query_embedding: Query vector
            analysis: Analysis containing entities/communities
            is_entities: Whether to retrieve entities or communities
            top_k: Number of results to return

        Returns:
            Tuple of (retrieved items, similarity scores)
        """
        items = []
        scores = []

        source = analysis.entities if is_entities else analysis.communities

        for item in source:
            if item.embedding is not None:
                # Compute cosine similarity
                similarity = self._cosine_similarity(query_embedding, item.embedding)
                if similarity >= self.similarity_threshold:
                    items.append(item)
                    scores.append(similarity)

        # Sort by similarity and take top-k
        sorted_indices = np.argsort(scores)[::-1][:top_k]
        items = [items[i] for i in sorted_indices]
        scores = [scores[i] for i in sorted_indices]

        return items, scores

    def _cosine_similarity(
        self,
        vec1: np.ndarray,
        vec2: np.ndarray
    ) -> float:
        """
        Compute cosine similarity between two vectors.

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Cosine similarity (0-1)
        """
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def _retrieve_entity_only(
        self,
        query: str,
        query_embedding: np.ndarray,
        analysis: GraphRAGAnalysis
    ) -> RetrievalResult:
        """Retrieve entities only."""
        entities, scores = self._retrieve_with_faiss(
            query_embedding,
            self.entity_index,
            analysis,
            is_entities=True,
            top_k=self.top_k_entities
        )

        return RetrievalResult(
            entities=entities,
            entity_similarities=scores,
            communities=[],
            community_similarities=[],
            reasoning=f"Retrieved {len(entities)} entities based on semantic similarity"
        )

    def _retrieve_community_only(
        self,
        query: str,
        query_embedding: np.ndarray,
        analysis: GraphRAGAnalysis
    ) -> RetrievalResult:
        """Retrieve communities only."""
        communities, scores = self._retrieve_with_faiss(
            query_embedding,
            self.community_index,
            analysis,
            is_entities=False,
            top_k=self.top_k_communities
        )

        return RetrievalResult(
            entities=[],
            entity_similarities=[],
            communities=communities,
            community_similarities=scores,
            reasoning=f"Retrieved {len(communities)} communities based on semantic similarity"
        )

    def _retrieve_risk_focused(
        self,
        query: str,
        query_embedding: np.ndarray,
        analysis: GraphRAGAnalysis
    ) -> RetrievalResult:
        """Retrieve with risk boosting."""
        # First retrieve normally
        result = self._retrieve_entity_only(query, query_embedding, analysis)

        # Boost high-risk entities
        for i, entity in enumerate(result.entities):
            if entity.risk_score > 0.6:
                result.entity_similarities[i] *= self.risk_boost

        # Re-sort
        sorted_indices = np.argsort(result.entity_similarities)[::-1]
        result.entities = [result.entities[i] for i in sorted_indices]
        result.entity_similarities = [result.entity_similarities[i] for i in sorted_indices]

        result.reasoning += f" (risk boosting applied)"
        return result

    def _retrieve_hybrid(
        self,
        query: str,
        query_embedding: np.ndarray,
        analysis: GraphRAGAnalysis
    ) -> RetrievalResult:
        """Hybrid retrieval combining entities and communities."""
        # Retrieve entities
        entities, entity_scores = self._retrieve_with_faiss(
            query_embedding,
            self.entity_index,
            analysis,
            is_entities=True,
            top_k=self.top_k_entities
        )

        # Retrieve communities
        communities, community_scores = self._retrieve_with_faiss(
            query_embedding,
            self.community_index,
            analysis,
            is_entities=False,
            top_k=self.top_k_communities
        )

        # Combine with weights
        combined_scores = entity_scores * self.entity_weight + \
                        community_scores * self.community_weight

        reasoning = f"Retrieved {len(entities)} entities and {len(communities)} communities (hybrid mode)"

        return RetrievalResult(
            entities=entities,
            entity_similarities=entity_scores,
            communities=communities,
            community_similarities=community_scores,
            reasoning=reasoning
        )

    def save_indexes(self, output_dir: str):
        """
        Save indexes to disk.

        Args:
            output_dir: Directory to save indexes
        """
        import os
        os.makedirs(output_dir, exist_ok=True)

        if self.entity_index is not None:
            self.entity_index.save(os.path.join(output_dir, "entity_index"))

        if self.community_index is not None:
            self.community_index.save(os.path.join(output_dir, "community_index"))

    @classmethod
    def load_indexes(
        cls,
        config: Dict[str, Any],
        output_dir: str
    ) -> 'OptimizedGraphRetriever':
        """
        Load indexes from disk.

        Args:
            config: Configuration dictionary
            output_dir: Directory to load indexes from

        Returns:
            Loaded OptimizedGraphRetriever instance
        """
        import os

        retriever = cls(config)

        entity_index_path = os.path.join(output_dir, "entity_index")
        community_index_path = os.path.join(output_dir, "community_index")

        if os.path.exists(entity_index_path + ".index"):
            retriever.entity_index = CachedVectorIndex.load(entity_index_path)

        if os.path.exists(community_index_path + ".index"):
            retriever.community_index = VectorIndex.load(community_index_path)

        return retriever
