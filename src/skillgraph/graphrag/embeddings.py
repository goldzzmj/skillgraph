"""
Embedding Generation Module

Generate vector embeddings for entities, relationships, and communities.
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import asdict
from pathlib import Path

from .models import Entity, Relationship, Community


class EmbeddingGenerator:
    """
    Generate vector embeddings for GraphRAG components.

    Supports multiple embedding strategies:
    1. LLM-based embeddings (high quality, requires API)
    2. TF-IDF embeddings (fast, no API required)
    3. Hash-based embeddings (fastest, very basic)
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize embedding generator.

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.enabled = self.config.get('embeddings', {}).get('enabled', True)
        self.batch_size = self.config.get('embeddings', {}).get('batch_size', 100)
        self.dimension = self.config.get('embeddings', {}).get('dimension', 1536)
        self.cache_enabled = self.config.get('embeddings', {}).get('cache_embeddings', True)
        self.cache_dir = Path(self.config.get('embeddings', {}).get('cache_dir', '.cache/embeddings'))

        # Create cache directory
        if self.cache_enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Determine embedding method
        self.embedding_method = self._determine_method()

        # Initialize TF-IDF vectorizer (for consistent embeddings)
        self._tfidf_vectorizer = None

    def _determine_method(self) -> str:
        """
        Determine which embedding method to use.

        Returns:
            'llm', 'tfidf', or 'hash'
        """
        try:
            # Try to import OpenAI
            import openai
            api_key = self.config.get('model', {}).get('api_key', '')
            if api_key and api_key != "${OPENAI_API_KEY}":
                return 'llm'
        except ImportError:
            pass

        try:
            # Try to import scikit-learn for TF-IDF
            from sklearn.feature_extraction.text import TfidfVectorizer
            return 'tfidf'
        except ImportError:
            pass

        # Fallback to hash-based embeddings
        return 'hash'

    def _fit_tfidf(self, texts: List[str]):
        """
        Fit TF-IDF vectorizer on all texts (for consistent dimensions).

        Args:
            texts: All texts to fit on
        """
        from sklearn.feature_extraction.text import TfidfVectorizer

        self._tfidf_vectorizer = TfidfVectorizer(
            max_features=self.dimension,
            stop_words='english'
        )

        # Fit on all texts
        self._tfidf_vectorizer.fit(texts)

        print(f"[INFO] TF-IDF vectorizer fitted on {len(texts)} texts, vocabulary size: {len(self._tfidf_vectorizer.vocabulary_)}")

    def generate_entity_embeddings(
        self,
        entities: List[Entity],
        batch: bool = True
    ) -> List[Entity]:
        """
        Generate embeddings for entities.

        Args:
            entities: List of entities
            batch: Whether to process in batches

        Returns:
            List of entities with embeddings
        """
        if not self.enabled:
            return entities

        # Prepare text for embedding
        texts = [
            f"{entity.name}. {entity.description}"
            for entity in entities
        ]

        # Generate embeddings
        embeddings = self._generate_embeddings(texts, batch)

        # Assign embeddings to entities
        for entity, embedding in zip(entities, embeddings):
            entity.embedding = embedding

        return entities

    def generate_relationship_embeddings(
        self,
        relationships: List[Relationship],
        batch: bool = True
    ) -> List[Relationship]:
        """
        Generate embeddings for relationships.

        Args:
            relationships: List of relationships
            batch: Whether to process in batches

        Returns:
            List of relationships with embeddings
        """
        if not self.enabled:
            return relationships

        # Prepare text for embedding
        texts = [
            f"{rel.type.value}. {rel.description}"
            for rel in relationships
        ]

        # Generate embeddings
        embeddings = self._generate_embeddings(texts, batch)

        # Assign embeddings to relationships
        for relationship, embedding in zip(relationships, embeddings):
            relationship.embedding = embedding

        return relationships

    def generate_community_embeddings(
        self,
        communities: List[Community],
        batch: bool = True
    ) -> List[Community]:
        """
        Generate embeddings for communities.

        Args:
            communities: List of communities
            batch: Whether to process in batches

        Returns:
            List of communities with embeddings
        """
        if not self.enabled:
            return communities

        # Prepare text for embedding (community descriptions)
        texts = [community.description for community in communities]

        # Generate embeddings
        embeddings = self._generate_embeddings(texts, batch)

        # Assign embeddings to communities
        for community, embedding in zip(communities, embeddings):
            community.embedding = embedding

        return communities

    def generate_query_embedding(self, query: str) -> np.ndarray:
        """
        Generate embedding for a query string.

        Args:
            query: Query text

        Returns:
            Query embedding vector
        """
        if not self.enabled:
            # Return zero vector
            return np.zeros(self.dimension)

        return self._generate_embeddings([query], batch=False)[0]

    def _generate_embeddings(
        self,
        texts: List[str],
        batch: bool = True
    ) -> List[np.ndarray]:
        """
        Generate embeddings for a list of texts.

        Args:
            texts: List of text strings
            batch: Whether to process in batches

        Returns:
            List of embedding vectors
        """
        if self.embedding_method == 'llm':
            return self._generate_llm_embeddings(texts, batch)
        elif self.embedding_method == 'tfidf':
            return self._generate_tfidf_embeddings(texts)
        else:
            return self._generate_hash_embeddings(texts)

    def _generate_llm_embeddings(
        self,
        texts: List[str],
        batch: bool = True
    ) -> List[np.ndarray]:
        """
        Generate embeddings using LLM API.

        Args:
            texts: List of text strings
            batch: Whether to process in batches

        Returns:
            List of embedding vectors
        """
        import openai

        api_key = self.config.get('model', {}).get('api_key', '')
        if not api_key or api_key == "${OPENAI_API_KEY}":
            # Fallback to TF-IDF
            return self._generate_tfidf_embeddings(texts)

        client = openai.OpenAI(api_key=api_key)

        if batch and len(texts) > self.batch_size:
            # Process in batches
            all_embeddings = []
            for i in range(0, len(texts), self.batch_size):
                batch_texts = texts[i:i+self.batch_size]
                batch_embeddings = self._call_openai_embeddings(client, batch_texts)
                all_embeddings.extend(batch_embeddings)
            return all_embeddings
        else:
            # Single batch
            return self._call_openai_embeddings(client, texts)

    def _call_openai_embeddings(
        self,
        client: Any,
        texts: List[str]
    ) -> List[np.ndarray]:
        """
        Call OpenAI embeddings API.

        Args:
            client: OpenAI client
            texts: Texts to embed

        Returns:
            List of embedding vectors
        """
        try:
            response = client.embeddings.create(
                model=self.config.get('model', {}).get('embedding_model', 'text-embedding-3-small'),
                input=texts
            )

            return [np.array(item.embedding) for item in response.data]
        except Exception as e:
            # Fallback to TF-IDF on error
            print(f"OpenAI embedding error: {e}, falling back to TF-IDF")
            return self._generate_tfidf_embeddings(texts)

    def _generate_tfidf_embeddings(
        self,
        texts: List[str],
        fit: bool = True
    ) -> List[np.ndarray]:
        """
        Generate TF-IDF embeddings (fallback method).

        Args:
            texts: List of text strings
            fit: Whether to fit the vectorizer (only first time)

        Returns:
            List of embedding vectors
        """
        from sklearn.feature_extraction.text import TfidfVectorizer

        # Create or use existing vectorizer
        if self._tfidf_vectorizer is None or fit:
            self._tfidf_vectorizer = TfidfVectorizer(
                max_features=self.dimension,
                stop_words='english'
            )
            # Fit on all texts
            self._tfidf_vectorizer.fit(texts)

        # Transform to TF-IDF vectors
        tfidf_matrix = self._tfidf_vectorizer.transform(texts)

        # Convert to dense arrays and pad/truncate to consistent dimension
        embeddings = []
        for i in range(len(texts)):
            # Get dense vector
            vector = tfidf_matrix[i].toarray().flatten()

            # Ensure consistent dimension
            if len(vector) < self.dimension:
                # Pad with zeros
                vector = np.pad(vector, (0, self.dimension - len(vector)))
            elif len(vector) > self.dimension:
                # Truncate
                vector = vector[:self.dimension]

            embeddings.append(vector)

        return embeddings

    def _generate_hash_embeddings(
        self,
        texts: List[str]
    ) -> List[np.ndarray]:
        """
        Generate hash-based embeddings (simplest fallback).

        Args:
            texts: List of text strings

        Returns:
            List of embedding vectors
        """
        import hashlib

        embeddings = []

        for text in texts:
            # Hash the text
            hash_obj = hashlib.sha256(text.encode())
            hash_bytes = hash_obj.digest()

            # Convert to array
            hash_array = np.frombuffer(hash_bytes, dtype=np.uint8)

            # Pad or truncate to desired dimension
            if len(hash_array) < self.dimension:
                padding = np.zeros(self.dimension - len(hash_array), dtype=np.uint8)
                hash_array = np.concatenate([hash_array, padding])
            elif len(hash_array) > self.dimension:
                hash_array = hash_array[:self.dimension]

            # Normalize to float [0, 1]
            embedding = hash_array.astype(np.float32) / 255.0

            embeddings.append(embedding)

        return embeddings

    def compute_similarity(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray
    ) -> float:
        """
        Compute cosine similarity between two embeddings.

        Args:
            embedding1: First embedding
            embedding2: Second embedding

        Returns:
            Similarity score between 0 and 1
        """
        if embedding1 is None or embedding2 is None:
            return 0.0

        # Normalize
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        # Cosine similarity
        similarity = np.dot(embedding1, embedding2) / (norm1 * norm2)

        return float(similarity)

    def find_similar_entities(
        self,
        query_embedding: np.ndarray,
        entities: List[Entity],
        top_k: int = 10,
        threshold: float = 0.0
    ) -> List[Tuple[Entity, float]]:
        """
        Find entities similar to a query.

        Args:
            query_embedding: Query embedding
            entities: List of entities with embeddings
            top_k: Number of results to return
            threshold: Minimum similarity threshold

        Returns:
            List of (entity, similarity) tuples, sorted by similarity
        """
        # Compute similarities
        similarities = [
            (entity, self.compute_similarity(query_embedding, entity.embedding))
            for entity in entities
            if entity.embedding is not None
        ]

        # Filter by threshold
        similarities = [
            (entity, score)
            for entity, score in similarities
            if score >= threshold
        ]

        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)

        # Return top_k
        return similarities[:top_k]

    def find_similar_communities(
        self,
        query_embedding: np.ndarray,
        communities: List[Community],
        top_k: int = 5,
        threshold: float = 0.0
    ) -> List[Tuple[Community, float]]:
        """
        Find communities similar to a query.

        Args:
            query_embedding: Query embedding
            communities: List of communities with embeddings
            top_k: Number of results to return
            threshold: Minimum similarity threshold

        Returns:
            List of (community, similarity) tuples, sorted by similarity
        """
        # Compute similarities
        similarities = [
            (community, self.compute_similarity(query_embedding, community.embedding))
            for community in communities
            if community.embedding is not None
        ]

        # Filter by threshold
        similarities = [
            (community, score)
            for community, score in similarities
            if score >= threshold
        ]

        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)

        # Return top_k
        return similarities[:top_k]
