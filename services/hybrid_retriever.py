"""Hybrid retrieval: fuse dense (Qdrant) + sparse (BM25) using Reciprocal Rank Fusion."""
from services.vector_store import VectorStore
from services.bm25_store import BM25Store


class HybridRetriever:
    def __init__(self, vector_store: VectorStore, bm25_store: BM25Store):
        self.dense = vector_store
        self.sparse = bm25_store

    def retrieve(
        self, query: str, top_k: int = 5, dense_weight: float = 0.6, source_filter: str = None
    ) -> list[dict]:
        """
        Hybrid retrieval using Reciprocal Rank Fusion (RRF).
        dense_weight: weight for dense results (0-1). Sparse weight = 1 - dense_weight.
        """
        dense_results = self.dense.search(query, top_k=top_k * 2, source_filter=source_filter)
        sparse_results = self.sparse.search(query, top_k=top_k * 2, source_filter=source_filter)

        # RRF scoring: score = sum(weight / (k + rank)) across retrieval methods
        k = 60  # RRF constant
        fused_scores: dict[str, dict] = {}

        for rank, result in enumerate(dense_results):
            doc_key = result["content"][:100]  # use content prefix as key
            if doc_key not in fused_scores:
                fused_scores[doc_key] = {
                    **result,
                    "rrf_score": 0,
                    "retrieval_methods": [],
                }
            fused_scores[doc_key]["rrf_score"] += dense_weight * (
                1 / (k + rank + 1)
            )
            fused_scores[doc_key]["retrieval_methods"].append("dense")

        for rank, result in enumerate(sparse_results):
            doc_key = result["content"][:100]
            if doc_key not in fused_scores:
                fused_scores[doc_key] = {
                    **result,
                    "rrf_score": 0,
                    "retrieval_methods": [],
                }
            fused_scores[doc_key]["rrf_score"] += (1 - dense_weight) * (
                1 / (k + rank + 1)
            )
            if "sparse" not in fused_scores[doc_key]["retrieval_methods"]:
                fused_scores[doc_key]["retrieval_methods"].append("sparse")

        # Sort by fused score and return top_k
        ranked = sorted(
            fused_scores.values(), key=lambda x: x["rrf_score"], reverse=True
        )
        return ranked[:top_k]
