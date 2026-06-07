"""Unit tests for Day 3: RAG chain and query router."""
import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestQueryRouter:
    """Test query classification logic (mocked LLM calls)."""

    def test_factoid_classification(self):
        from services.query_router import QueryRouter

        router = QueryRouter.__new__(QueryRouter)
        router.chain = MagicMock()
        router.chain.invoke = MagicMock(return_value="FACTOID")
        assert router.classify("What was Apple's revenue?") == "FACTOID"

    def test_analytical_classification(self):
        from services.query_router import QueryRouter

        router = QueryRouter.__new__(QueryRouter)
        router.chain = MagicMock()
        router.chain.invoke = MagicMock(return_value="ANALYTICAL")
        assert router.classify("Compare Apple and Tesla revenue trends") == "ANALYTICAL"

    def test_unanswerable_classification(self):
        from services.query_router import QueryRouter

        router = QueryRouter.__new__(QueryRouter)
        router.chain = MagicMock()
        router.chain.invoke = MagicMock(return_value="UNANSWERABLE")
        assert router.classify("What is the weather?") == "UNANSWERABLE"

    def test_unknown_response_defaults_to_analytical(self):
        from services.query_router import QueryRouter

        router = QueryRouter.__new__(QueryRouter)
        router.chain = MagicMock()
        router.chain.invoke = MagicMock(return_value="SOMETHING_RANDOM")
        assert router.classify("test question") == "ANALYTICAL"

    def test_extracts_category_from_verbose_response(self):
        """Router should extract category even if LLM returns extra text."""
        from services.query_router import QueryRouter

        router = QueryRouter.__new__(QueryRouter)
        router.chain = MagicMock()
        router.chain.invoke = MagicMock(return_value="The category is FACTOID because...")
        assert router.classify("What is X?") == "FACTOID"

    def test_retrieval_params_factoid(self):
        from services.query_router import QueryRouter

        router = QueryRouter.__new__(QueryRouter)
        params = router.get_retrieval_params("FACTOID")
        assert params["top_k"] == 3
        assert params["dense_weight"] == 0.5

    def test_retrieval_params_analytical(self):
        from services.query_router import QueryRouter

        router = QueryRouter.__new__(QueryRouter)
        params = router.get_retrieval_params("ANALYTICAL")
        assert params["top_k"] == 7
        assert params["dense_weight"] == 0.6

    def test_retrieval_params_unanswerable(self):
        from services.query_router import QueryRouter

        router = QueryRouter.__new__(QueryRouter)
        params = router.get_retrieval_params("UNANSWERABLE")
        assert params["top_k"] == 3


class TestRAGChain:
    """Test RAG chain response structure (fully mocked, no qdrant needed)."""

    def _make_chain(self):
        """Create a RAGChain instance with all dependencies mocked."""
        from services.rag_chain import RAGChain

        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = [
            {
                "content": "Apple revenue was $394 billion",
                "score": 0.95,
                "metadata": {"source": "AAPL_10K.pdf", "page_number": 1},
                "rrf_score": 0.01,
                "retrieval_methods": ["dense", "sparse"],
            }
        ]

        chain = RAGChain.__new__(RAGChain)
        chain.retriever = mock_retriever
        chain.prompt_version = "rag_v1"
        chain.llm = MagicMock()

        # Build a mock prompt template that supports the | operator chain
        mock_prompt = MagicMock()
        mock_composed = MagicMock()
        mock_final = MagicMock(return_value="Apple's revenue was $394 billion.")
        mock_prompt.__or__ = MagicMock(return_value=mock_composed)
        mock_composed.__or__ = MagicMock(return_value=mock_final)
        chain.prompt_template = mock_prompt

        return chain

    @patch("services.rag_chain.tracing_v2_enabled")
    def test_query_returns_expected_structure(self, mock_tracing):
        chain = self._make_chain()
        result = chain.query("What was Apple revenue?")

        assert result["question"] == "What was Apple revenue?"
        assert "answer" in result
        assert "contexts" in result
        assert "latency_seconds" in result
        assert result["prompt_version"] == "rag_v1"

    @patch("services.rag_chain.tracing_v2_enabled")
    def test_query_with_routing_includes_routing_fields(self, mock_tracing):
        chain = self._make_chain()
        result = chain.query_with_routing(
            "test?", "FACTOID", {"top_k": 3, "dense_weight": 0.5}
        )

        assert result["query_type"] == "FACTOID"
        assert result["top_k"] == 3
        assert result["dense_weight"] == 0.5
        assert "answer" in result
