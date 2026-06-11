"""Run RAGAS evaluation across different chunking strategies and compare."""
import argparse
import json
import time
from pathlib import Path

from services.loader import load_all_documents
from services.chunker import Chunker, ChunkStrategy
from services.vector_store import VectorStore
from services.bm25_store import BM25Store
from services.hybrid_retriever import HybridRetriever
from services.rag_chain import RAGChain
from eval.ragas_eval import run_evaluation


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="eval/datasets/qa_pairs.jsonl")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--judge-provider", choices=["groq"], default="groq")
    parser.add_argument("--judge-model", default="llama-3.3-70b-versatile")
    parser.add_argument("--answer-relevancy-strictness", type=int, default=1)
    parser.add_argument("--raise-exceptions", action="store_true")
    parser.add_argument("--strategy-delay-seconds", type=float, default=5.0)
    parser.add_argument("--question-delay-seconds", type=float, default=5.0)
    args = parser.parse_args()

    dataset_path = args.dataset
    output_dir = Path("eval/results")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    strategies = [
        ChunkStrategy.FIXED_TOKEN,
        ChunkStrategy.PARAGRAPH,
        ChunkStrategy.RECURSIVE_CHARACTER
    ]

    pages = None
    
    summary = {}

    for strategy in strategies:
        print(f"\n{'='*60}")
        print(f"EVALUATING STRATEGY: {strategy.name}")
        print(f"{'='*60}")
        
        # 1. & 2. Chunking and Indexing (with intelligent caching)
        collection_name = f"rag_eval_{strategy.name.lower()}"
        bm25_path = f"data/bm25_{strategy.name.lower()}.json"
        vs = VectorStore(collection_name=collection_name)
        bm25 = BM25Store()
        
        # Check if vectors already exist in the persistent database
        if vs.client.collection_exists(collection_name) and vs.count() > 0 and Path(bm25_path).exists():
            print(f"[{strategy.name}] Collection and BM25 index already exist. Skipping expensive embedding phase.")
            bm25.load(bm25_path)
        else:
            if pages is None:
                print("Loading PDFs...")
                pages = load_all_documents()
            print(f"[{strategy.name}] Data not found. Chunking and embedding from scratch...")
            chunker = Chunker(strategy)
            chunks = chunker.chunk_pages(pages)
            print(f"[{strategy.name}] Generated {len(chunks)} chunks.")
            
            print(f"[{strategy.name}] Indexing to Qdrant collection: {collection_name}")
            vs.upsert_chunks(chunks)
            
            print(f"[{strategy.name}] Indexing to BM25 store: {bm25_path}")
            bm25.index(chunks)
            bm25.save(bm25_path)
        
        # 3. Setup RAG Chain
        retriever = HybridRetriever(vs, bm25)
        chain = RAGChain(retriever)
        
        # 4. Evaluate
        strategy_output_dir = f"eval/results/{strategy.name.lower()}"
        print(f"[{strategy.name}] Starting RAGAS evaluation...")
        result = run_evaluation(
            dataset_path,
            chain,
            output_dir=strategy_output_dir,
            limit=args.limit,
            judge_provider=args.judge_provider,
            judge_model=args.judge_model,
            answer_relevancy_strictness=args.answer_relevancy_strictness,
            raise_exceptions=args.raise_exceptions,
            question_delay_seconds=args.question_delay_seconds,
        )
        
        # 5. Record aggregate scores
        summary[strategy.name] = result["aggregate_scores"]

        # 6. Close Qdrant client to release local file locks for the next strategy
        vs.client.close()

        # 7. Small delay to keep judge-provider rate limits stable.
        if args.strategy_delay_seconds and strategy != strategies[-1]:
            print(f"[{strategy.name}] Sleeping for {args.strategy_delay_seconds}s before next strategy...")
            time.sleep(args.strategy_delay_seconds)

    # Save summary
    summary_path = output_dir / "strategy_comparison.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
        
    print("\n\n" + "="*60)
    print("FINAL COMPARISON RESULTS")
    print("="*60)
    print(json.dumps(summary, indent=2))
    print(f"\nComparison saved to: {summary_path}")

if __name__ == "__main__":
    main()
