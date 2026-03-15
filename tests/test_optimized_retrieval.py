"""
Performance Tests for Optimized Retrieval

Tests FAISS-accelerated retrieval performance.
"""

import sys
import time
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent.parent / 'src'
sys.path.insert(0, str(src_path))

from skillgraph.graphrag import EntityExtractor, CommunityDetector
from skillgraph.graphrag.optimized_retrieval import OptimizedGraphRetriever
from skillgraph.parser import SkillParser


def test_retrieval_performance():
    """Test retrieval performance with and without FAISS."""
    print("=" * 60)
    print("Retrieval Performance Test")
    print("=" * 60)

    # Test with malicious skill
    example_file = Path(__file__).resolve().parent.parent.parent / 'examples' / 'malicious_skill.md'

    if not example_file.exists():
        example_file = Path.cwd() / 'examples' / 'malicious_skill.md'

    if not example_file.exists():
        print(f"\n[X] Example file not found: {example_file}")
        return

    print(f"\n[1] Parsing skill file...")

    try:
        parser = SkillParser()
        skill = parser.parse_file(str(example_file))
        print(f"   [OK] Parsed skill: {skill.name}")
    except Exception as e:
        print(f"   [ERROR] Parse error: {e}")
        return

    # Extract entities
    print("\n[2] Extracting entities...")

    try:
        extractor = EntityExtractor()
        entities = extractor.extract(
            '',
            skill.sections,
            skill.code_blocks
        )
        print(f"   [OK] Extracted {len(entities)} entities")

        # Generate embeddings
        print("\n[3] Generating embeddings...")

        from skillgraph.graphrag.embeddings import EmbeddingGenerator

        config = {'model': {'provider': 'openai'}}
        embedding_gen = EmbeddingGenerator(config)

        entities = embedding_gen.generate_entity_embeddings(entities)
        print(f"   [OK] Generated embeddings for {len(entities)} entities")

        # Create communities
        print("\n[4] Creating communities...")

        detector = CommunityDetector()
        relationships = extractor.extract_relationships(entities, '')
        communities = detector.detect(entities, relationships)
        communities = embedding_gen.generate_community_embeddings(communities)
        print(f"   [OK] Created {len(communities)} communities")

        # Create analysis
        from skillgraph.graphrag.models import GraphRAGAnalysis

        analysis = GraphRAGAnalysis(
            entities=entities,
            communities=communities,
            risk_findings=[]
        )

        # Test with FAISS enabled
        print("\n[5] Testing FAISS-accelerated retrieval...")

        config_with_faiss = {
            'retrieval': {
                'strategy': 'hybrid',
                'use_faiss': True,
                'top_k_entities': 10,
                'top_k_communities': 5
            }
        }

        retriever = OptimizedGraphRetriever(config_with_faiss)

        # Build indexes
        start_time = time.time()
        retriever.build_indexes(entities, communities)
        build_time = time.time() - start_time
        print(f"   [OK] Index build time: {build_time:.3f}s")

        # Perform retrieval
        queries = [
            "network requests",
            "file operations",
            "security risks"
        ]

        total_query_time = 0

        for query in queries:
            start_time = time.time()
            result = retriever.retrieve(query, analysis)
            query_time = time.time() - start_time
            total_query_time += query_time

            print(f"   Query: '{query}'")
            print(f"     Time: {query_time:.4f}s")
            print(f"     Results: {len(result.entities)} entities, {len(result.communities)} communities")

        avg_query_time = total_query_time / len(queries)
        print(f"   Average query time: {avg_query_time:.4f}s")

        # Test without FAISS
        print("\n[6] Testing linear retrieval (baseline)...")

        config_without_faiss = {
            'retrieval': {
                'strategy': 'hybrid',
                'use_faiss': False,
                'top_k_entities': 10,
                'top_k_communities': 5
            }
        }

        retriever_linear = OptimizedGraphRetriever(config_without_faiss)

        total_query_time_linear = 0

        for query in queries:
            start_time = time.time()
            result = retriever_linear.retrieve(query, analysis)
            query_time = time.time() - start_time
            total_query_time_linear += query_time

        avg_query_time_linear = total_query_time_linear / len(queries)
        print(f"   Average query time: {avg_query_time_linear:.4f}s")

        # Calculate speedup
        if avg_query_time_linear > 0:
            speedup = avg_query_time_linear / avg_query_time
            print(f"\n[7] Performance Summary:")
            print(f"   FAISS query time: {avg_query_time:.4f}s")
            print(f"   Linear query time: {avg_query_time_linear:.4f}s")
            print(f"   Speedup: {speedup:.2f}x")

            if speedup > 10:
                print(f"   [EXCELLENT] FAISS provides >10x speedup!")
            elif speedup > 5:
                print(f"   [GOOD] FAISS provides significant speedup")
            elif speedup > 2:
                print(f"   [OK] FAISS provides moderate speedup")
            else:
                print(f"   [INFO] Dataset may be too small for FAISS advantage")

    except Exception as e:
        print(f"   [ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # Final summary
    print("\n" + "=" * 60)
    print("[OK] Performance test complete!")
    print("=" * 60)


def test_index_persistence():
    """Test index save and load functionality."""
    print("\n" + "=" * 60)
    print("Index Persistence Test")
    print("=" * 60)

    try:
        from skillgraph.graphrag.optimized_retrieval import OptimizedGraphRetriever
        from skillgraph.graphrag.models import Entity, EntityType

        # Create dummy entities
        import numpy as np

        entities = [
            Entity(
                id="entity1",
                name="test1",
                type=EntityType.API,
                description="Test entity 1",
                embedding=np.random.rand(1536).astype(np.float32)
            ),
            Entity(
                id="entity2",
                name="test2",
                type=EntityType.API,
                description="Test entity 2",
                embedding=np.random.rand(1536).astype(np.float32)
            )
        ]

        # Create retriever and build index
        config = {'retrieval': {'use_faiss': True}}
        retriever = OptimizedGraphRetriever(config)

        from skillgraph.graphrag.models import Community, CommunityLevel

        communities = [
            Community(
                id="community1",
                description="Test community 1",
                level=CommunityLevel.LEVEL_1,
                entities=["entity1"],
                embedding=np.random.rand(1536).astype(np.float32)
            )
        ]

        retriever.build_indexes(entities, communities)

        # Save indexes
        output_dir = "output/test_indexes"
        print(f"\n[1] Saving indexes to {output_dir}...")
        retriever.save_indexes(output_dir)
        print(f"   [OK] Indexes saved")

        # Load indexes
        print(f"\n[2] Loading indexes from {output_dir}...")
        retriever_loaded = OptimizedGraphRetriever.load_indexes(config, output_dir)
        print(f"   [OK] Indexes loaded")
        print(f"   Entity index size: {retriever_loaded.entity_index.size()}")
        print(f"   Community index size: {retriever_loaded.community_index.size()}")

        print("\n" + "=" * 60)
        print("[OK] Persistence test complete!")
        print("=" * 60)

    except Exception as e:
        print(f"[ERROR] Persistence test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    test_retrieval_performance()
    test_index_persistence()
