"""Integration tests for Day 2: embedding, vector store, BM25, and hybrid retrieval."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.embedding import EmbeddingService
from services.chunker import Chunk
from services.bm25_store import BM25Store


# --- Embedding tests ---

class TestEmbeddingService:
    def test_embed_single_query(self):
        svc = EmbeddingService()
        vec = svc.embed_query("What is Apple's revenue?")
        assert isinstance(vec, list)
        assert len(vec) == svc.dimension
        assert all(isinstance(v, float) for v in vec)

    def test_embed_batch(self):
        svc = EmbeddingService()
        texts = ["revenue growth", "operating income", "net profit"]
        vecs = svc.embed_texts(texts)
        assert len(vecs) == 3
        assert all(len(v) == svc.dimension for v in vecs)

    def test_dimension_matches_config(self):
        from infra.config import Config
        svc = EmbeddingService()
        assert svc.dimension == Config.EMBEDDING_DIM


# --- BM25 tests ---

SAMPLE_CHUNKS = [
    Chunk(content="Apple reported revenue of 394 billion dollars in fiscal year 2024.",
          metadata={"source": "AAPL_10K_2024.pdf", "page": 1, "chunk_index": 0}),
    Chunk(content="Tesla delivered 1.8 million vehicles worldwide in 2024.",
          metadata={"source": "TSLA_10K_2024.pdf", "page": 1, "chunk_index": 0}),
    Chunk(content="JPMorgan Chase had total assets of 4.0 trillion dollars.",
          metadata={"source": "JPM_10K_2024.pdf", "page": 1, "chunk_index": 0}),
    Chunk(content="NVIDIA GPU revenue grew 122% driven by data center demand.",
          metadata={"source": "NVDA_10K_2024.pdf", "page": 1, "chunk_index": 0}),
    Chunk(content="Apple's operating expenses included research and development costs of 30 billion.",
          metadata={"source": "AAPL_10K_2024.pdf", "page": 5, "chunk_index": 1}),
]


class TestBM25Store:
    def test_index_and_search(self):
        bm25 = BM25Store()
        bm25.index(SAMPLE_CHUNKS)
        results = bm25.search("Apple revenue", top_k=2)
        assert len(results) > 0
        # The top result should mention Apple
        assert "apple" in results[0]["content"].lower()

    def test_keyword_exact_match(self):
        bm25 = BM25Store()
        bm25.index(SAMPLE_CHUNKS)
        results = bm25.search("Tesla vehicles delivered", top_k=1)
        assert len(results) > 0
        assert "tesla" in results[0]["content"].lower()

    def test_empty_query_returns_nothing(self):
        bm25 = BM25Store()
        bm25.index(SAMPLE_CHUNKS)
        results = bm25.search("zzzyyyxxx", top_k=3)
        assert len(results) == 0

    def test_save_and_load(self, tmp_path):
        bm25 = BM25Store()
        bm25.index(SAMPLE_CHUNKS)
        save_path = str(tmp_path / "test_bm25.json")
        bm25.save(save_path)

        bm25_loaded = BM25Store()
        bm25_loaded.load(save_path)
        results = bm25_loaded.search("NVIDIA GPU", top_k=1)
        assert len(results) > 0
        assert "nvidia" in results[0]["content"].lower()


# --- Hybrid retriever tests (offline, using mocked dense results) ---

class TestHybridRetrieverLogic:
    """Test the RRF fusion logic without needing a live Qdrant connection."""

    def test_rrf_fusion_combines_results(self):
        """Verify that RRF fusion merges dense and sparse and ranks correctly."""
        from services.hybrid_retriever import HybridRetriever

        # Create a mock dense store
        class MockDense:
            def search(self, query, top_k=5):
                return [
                    {"content": "Apple revenue was 394 billion.", "score": 0.95, "metadata": {}},
                    {"content": "NVIDIA GPU revenue grew 122%.", "score": 0.80, "metadata": {}},
                ]

        class MockSparse:
            def search(self, query, top_k=5):
                return [
                    {"content": "Apple revenue was 394 billion.", "score": 5.2, "metadata": {}},
                    {"content": "Tesla delivered 1.8 million vehicles.", "score": 2.1, "metadata": {}},
                ]

        hybrid = HybridRetriever(MockDense(), MockSparse())
        results = hybrid.retrieve("Apple revenue", top_k=3)

        # Apple result should be first since it appears in BOTH dense and sparse
        assert len(results) > 0
        assert "apple" in results[0]["content"].lower()
        # It should have both retrieval methods
        assert "dense" in results[0]["retrieval_methods"]
        assert "sparse" in results[0]["retrieval_methods"]

    def test_hybrid_retriever_empty_results(self):
        """When both dense and sparse return empty, hybrid returns empty."""
        from services.hybrid_retriever import HybridRetriever

        class EmptyDense:
            def search(self, query, top_k=5):
                return []

        class EmptySparse:
            def search(self, query, top_k=5):
                return []

        hybrid = HybridRetriever(EmptyDense(), EmptySparse())
        results = hybrid.retrieve("nonexistent topic", top_k=3)
        assert results == []


class TestBM25AddChunks:
    """Test the dynamic add_chunks feature added for PDF upload."""

    def test_add_chunks_appends_and_reindexes(self, tmp_path):
        bm25 = BM25Store()
        bm25.index(SAMPLE_CHUNKS)
        original_count = len(bm25.documents)

        new_chunk = Chunk(
            content="Microsoft Azure revenue exceeded 60 billion in 2024.",
            metadata={"source": "MSFT_10K_2024.pdf", "page": 1, "chunk_index": 0},
        )
        # Override save path for test isolation
        save_path = str(tmp_path / "bm25_append.json")
        bm25.save = lambda path=save_path: BM25Store.save(bm25, path)
        bm25.add_chunks([new_chunk])

        assert len(bm25.documents) == original_count + 1

        results = bm25.search("Microsoft Azure revenue", top_k=1)
        assert len(results) > 0
        assert "microsoft" in results[0]["content"].lower()

