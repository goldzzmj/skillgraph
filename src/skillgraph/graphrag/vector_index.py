"""
Vector Index Module

Efficient vector indexing using FAISS for fast similarity search.
"""

import numpy as np
from typing import List, Optional, Tuple
import os
import pickle

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    print("Warning: FAISS not installed. Install with: pip install faiss-cpu")


class VectorIndex:
    """
    Vector index for fast similarity search using FAISS.

    Provides efficient nearest neighbor search for high-dimensional vectors.
    Supports both flat index (exact) and IVF index (approximate).
    """

    def __init__(
        self,
        dimension: int,
        index_type: str = "flat",
        nlist: int = 100,
        use_gpu: bool = False
    ):
        """
        Initialize vector index.

        Args:
            dimension: Vector dimension
            index_type: Index type ('flat' or 'ivf')
            nlist: Number of clusters for IVF index
            use_gpu: Whether to use GPU (requires faiss-gpu)
        """
        if not FAISS_AVAILABLE:
            raise RuntimeError("FAISS is not installed. Install with: pip install faiss-cpu")

        self.dimension = dimension
        self.index_type = index_type
        self.use_gpu = use_gpu

        # Build index
        if index_type == "flat":
            # Flat index - exact search
            self.index = faiss.IndexFlatL2(dimension)
        elif index_type == "ivf":
            # IVF index - approximate search, faster
            quantizer = faiss.IndexFlatL2(dimension)
            self.index = faiss.IndexIVFFlat(quantizer, dimension, nlist)
        else:
            raise ValueError(f"Unknown index type: {index_type}")

        # Store vectors and IDs
        self.vectors: np.ndarray = None
        self.ids: List[str] = []

        # Is index trained?
        self.is_trained = False

    def add(
        self,
        vectors: np.ndarray,
        ids: List[str]
    ):
        """
        Add vectors to index.

        Args:
            vectors: Array of vectors to add (N x D)
            ids: List of IDs corresponding to vectors
        """
        if len(vectors) != len(ids):
            raise ValueError("Number of vectors and IDs must match")

        # Convert to float32 if needed
        if vectors.dtype != np.float32:
            vectors = vectors.astype(np.float32)

        # Store vectors and IDs
        if self.vectors is None:
            self.vectors = vectors
            self.ids = ids
        else:
            self.vectors = np.vstack([self.vectors, vectors])
            self.ids.extend(ids)

        # Train index if needed (for IVF)
        if self.index_type == "ivf" and not self.is_trained:
            # Need to train IVF index before adding
            if len(vectors) >= self.index.nlist:
                self.index.train(vectors)
                self.is_trained = True
            else:
                print(f"Warning: Not enough vectors to train IVF index ({len(vectors)} < {self.index.nlist})")

        # Add vectors to index
        if self.index_type == "flat" or self.is_trained:
            self.index.add(vectors)

    def search(
        self,
        query_vector: np.ndarray,
        k: int = 10
    ) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """
        Search for nearest neighbors.

        Args:
            query_vector: Query vector (D,)
            k: Number of nearest neighbors to return

        Returns:
            Tuple of (distances, indices, ids)
        """
        # Convert query to correct shape and type
        if len(query_vector.shape) == 1:
            query_vector = query_vector.reshape(1, -1)

        if query_vector.dtype != np.float32:
            query_vector = query_vector.astype(np.float32)

        # Search
        distances, indices = self.index.search(query_vector, k)

        # Convert indices to IDs
        result_ids = []
        for idx in indices[0]:
            if idx >= 0 and idx < len(self.ids):
                result_ids.append(self.ids[idx])
            else:
                result_ids.append(None)

        return distances[0], indices[0], result_ids

    def save(self, filepath: str):
        """
        Save index to disk.

        Args:
            filepath: Path to save index
        """
        # Save FAISS index
        faiss.write_index(self.index, f"{filepath}.index")

        # Save metadata
        metadata = {
            'dimension': self.dimension,
            'index_type': self.index_type,
            'is_trained': self.is_trained,
            'vectors': self.vectors,
            'ids': self.ids
        }
        with open(f"{filepath}.metadata", 'wb') as f:
            pickle.dump(metadata, f)

    @classmethod
    def load(cls, filepath: str) -> 'VectorIndex':
        """
        Load index from disk.

        Args:
            filepath: Path to load index from

        Returns:
            Loaded VectorIndex instance
        """
        # Load metadata
        with open(f"{filepath}.metadata", 'rb') as f:
            metadata = pickle.load(f)

        # Create index instance
        index = cls(
            dimension=metadata['dimension'],
            index_type=metadata['index_type']
        )

        # Restore index
        index.index = faiss.read_index(f"{filepath}.index")
        index.is_trained = metadata['is_trained']
        index.vectors = metadata['vectors']
        index.ids = metadata['ids']

        return index

    def size(self) -> int:
        """
        Get number of vectors in index.

        Returns:
            Number of vectors
        """
        return self.index.ntotal

    def __repr__(self) -> str:
        return f"VectorIndex(type={self.index_type}, size={self.size()}, dimension={self.dimension})"


class CachedVectorIndex(VectorIndex):
    """
    Vector index with in-memory cache for frequently accessed vectors.
    """

    def __init__(self, *args, cache_size: int = 1000, **kwargs):
        """
        Initialize cached vector index.

        Args:
            cache_size: Maximum number of vectors to cache
        """
        super().__init__(*args, **kwargs)
        self.cache_size = cache_size
        self.cache = {}  # Map from ID to vector

    def get_cached(self, vector_id: str) -> Optional[np.ndarray]:
        """
        Get vector from cache.

        Args:
            vector_id: ID of vector

        Returns:
            Cached vector or None if not in cache
        """
        return self.cache.get(vector_id)

    def cache_vector(self, vector_id: str, vector: np.ndarray):
        """
        Cache a vector.

        Args:
            vector_id: ID of vector
            vector: Vector to cache
        """
        # Evict oldest if cache is full
        if len(self.cache) >= self.cache_size:
            # Simple FIFO eviction
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]

        self.cache[vector_id] = vector

    def clear_cache(self):
        """Clear the cache."""
        self.cache.clear()
