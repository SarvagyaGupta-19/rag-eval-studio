"""
Day 3 integration test: run 10 queries through the full pipeline.
Tests RAG chain + query router + LangSmith tracing.
"""
import sys
import json
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from services.vector_store import VectorStore
from services.bm25_store import BM25Store
from services.hybrid_retriever import HybridRetriever
from services.rag_chain import RAGChain
from services.query_router import QueryRouter


# 10 test queries - mix of factoid, analytical, and unanswerable
TEST_QUERIES = [
    # Factoid queries
    "What was Apple's total net sales in the most recent fiscal year?",
    "How many vehicles did Tesla deliver in 2024?",
    "What is NVIDIA's primary source of revenue?",
    # Analytical queries
    "Compare Apple's revenue growth trends across the last two years.",
    "What are the key risk factors mentioned by Tesla in their annual report?",
    "How has JPMorgan's total assets changed over time?",
    "What is NVIDIA's strategy for the data center market?",
    # Keyword-specific queries (BM25 should help)
    "What was Apple's research and development expense?",
    "What is Tesla's automotive gross margin?",
    # Edge case
    "What is the weather forecast for tomorrow?",
]


def main():
    print("=" * 70)
    print("Day 3 Integration Test: RAG Chain + Query Router + LangSmith")
    print("=" * 70)

    # Initialize components
    print("\n[1/3] Initializing components...")
    vs = VectorStore()
    bm25 = BM25Store()
    bm25.load("data/bm25_index.json")
    hybrid = HybridRetriever(vs, bm25)
    rag = RAGChain(hybrid, prompt_version="rag_v1")
    router = QueryRouter()
    print("  [OK] All components initialized")

    results = []

    print(f"\n[2/3] Running {len(TEST_QUERIES)} queries...\n")

    for i, question in enumerate(TEST_QUERIES, 1):
        print(f"--- Query {i}/{len(TEST_QUERIES)} ---")
        print(f"Q: {question}")

        # Step 1: Route the query
        query_type = router.classify(question)
        params = router.get_retrieval_params(query_type)
        print(f"Router: {query_type} (top_k={params['top_k']}, dense_weight={params['dense_weight']})")

        # Step 2: Run RAG with routed params
        result = rag.query_with_routing(question, query_type, params)
        print(f"A: {result['answer'][:200]}...")
        print(f"Latency: {result['latency_seconds']}s | Sources: {len(result['contexts'])}")
        print()

        results.append({
            "query_index": i,
            "question": result["question"],
            "answer": result["answer"],
            "query_type": query_type,
            "top_k": params["top_k"],
            "latency_seconds": result["latency_seconds"],
            "num_contexts": len(result["contexts"]),
            "sources": [c["metadata"].get("source", "?") for c in result["contexts"]],
        })

    # Save results
    output_path = Path("data/day3_test_results.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(results, indent=2), encoding="utf-8")

    # Summary
    print(f"\n[3/3] Summary")
    print(f"{'=' * 70}")
    avg_latency = sum(r["latency_seconds"] for r in results) / len(results)
    print(f"  Queries run:     {len(results)}")
    print(f"  Avg latency:     {avg_latency:.2f}s")
    print(f"  Route breakdown:")
    for qt in ("FACTOID", "ANALYTICAL", "UNANSWERABLE"):
        count = sum(1 for r in results if r["query_type"] == qt)
        if count:
            print(f"    {qt}: {count}")
    print(f"\n  Results saved to: {output_path}")
    print(f"  Check LangSmith: https://smith.langchain.com/")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
