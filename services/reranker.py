"""Dummy reranker for free tier memory limits."""
from __future__ import annotations


class Reranker:
    """Pass-through reranker since local CrossEncoders exceed Render free tier memory limits."""

    def __init__(self, model_name: str = "disabled"):
        pass

    def rerank(self, query: str, results: list[dict], top_k: int = 5) -> list[dict]:
        """Skip reranking and return the top_k results."""
        if not results:
            return results

        # Just return the top_k from the original retrieval
        return results[:top_k]
