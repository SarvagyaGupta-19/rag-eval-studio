"""Tests for the cross-encoder reranker."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.reranker import Reranker


class TestReranker:
    """Test reranker scoring and ordering."""

    def test_rerank_returns_top_k(self):
        reranker = Reranker()
        results = [
            {"content": "Apple revenue was 394 billion in 2024.", "metadata": {}},
            {"content": "Tesla makes electric vehicles.", "metadata": {}},
            {"content": "Apple's gross margin was 46%.", "metadata": {}},
            {"content": "Weather in New York is rainy.", "metadata": {}},
        ]
        reranked = reranker.rerank("What was Apple's revenue?", results, top_k=2)
        assert len(reranked) == 2

    def test_rerank_adds_score(self):
        reranker = Reranker()
        results = [
            {"content": "NVIDIA earnings exceeded expectations.", "metadata": {}},
        ]
        reranked = reranker.rerank("NVIDIA earnings", results, top_k=1)
        assert "rerank_score" in reranked[0]

    def test_rerank_empty_input(self):
        reranker = Reranker()
        reranked = reranker.rerank("any query", [], top_k=5)
        assert reranked == []

    def test_rerank_relevance_ordering(self):
        reranker = Reranker()
        results = [
            {"content": "The weather is sunny today.", "metadata": {}},
            {"content": "Apple's total revenue in 2024 was $394 billion.", "metadata": {}},
        ]
        reranked = reranker.rerank("What was Apple's 2024 revenue?", results, top_k=2)
        assert "Apple" in reranked[0]["content"]
