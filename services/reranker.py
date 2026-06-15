"""Cross-encoder reranker for improving retrieval precision."""
from __future__ import annotations

from sentence_transformers import CrossEncoder


class Reranker:
    """Rerank retrieved chunks using a cross-encoder model."""

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model = CrossEncoder(model_name)

    def rerank(self, query: str, results: list[dict], top_k: int = 5) -> list[dict]:
        """Rescore results with the cross-encoder and return the top_k.

        Args:
            query: The user question.
            results: List of dicts with at least a 'content' key.
            top_k: Number of top results to return after reranking.

        Returns:
            The top_k results sorted by cross-encoder relevance score.
        """
        if not results:
            return results

        pairs = [(query, r["content"]) for r in results]
        scores = self.model.predict(pairs)

        for result, score in zip(results, scores):
            result["rerank_score"] = float(score)

        reranked = sorted(results, key=lambda x: x["rerank_score"], reverse=True)
        return reranked[:top_k]
