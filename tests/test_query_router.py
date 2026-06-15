"""Extended tests for QueryRouter edge cases."""
import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestQueryRouterEdgeCases:
    """Edge cases not covered by the existing test_rag_chain.py router tests."""

    def _make_router(self, llm_response: str):
        from services.query_router import QueryRouter

        router = QueryRouter.__new__(QueryRouter)
        router.chain = MagicMock()
        router.chain.invoke = MagicMock(return_value=llm_response)
        return router

    def test_unknown_query_type_defaults_in_params(self):
        """get_retrieval_params with an unknown type falls back to ANALYTICAL."""
        from services.query_router import QueryRouter

        router = QueryRouter.__new__(QueryRouter)
        params = router.get_retrieval_params("UNKNOWN_TYPE")
        # Should default to ANALYTICAL params
        assert params["top_k"] == 7
        assert params["dense_weight"] == 0.6

    def test_classify_handles_lowercase_response(self):
        """LLM might return 'factoid' in lowercase — router should normalise."""
        router = self._make_router("factoid")
        result = router.classify("What is revenue?")
        assert result == "FACTOID"

    def test_classify_handles_empty_response(self):
        """Empty LLM response should default to ANALYTICAL."""
        router = self._make_router("")
        result = router.classify("test?")
        assert result == "ANALYTICAL"

    def test_classify_handles_multiline_response(self):
        """LLM returning verbose multi-line text with the keyword embedded."""
        router = self._make_router(
            "Based on analysis, this is:\nANALYTICAL\nBecause it requires comparison."
        )
        result = router.classify("Compare Q1 and Q2 revenue")
        assert result == "ANALYTICAL"
