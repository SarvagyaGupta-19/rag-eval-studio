"""RAGAS evaluation runner with LangSmith logging."""
import argparse
import copy
import json
import math
import os
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from datasets import Dataset
from ragas import evaluate
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import (
    answer_relevancy,
    context_precision,
    context_recall,
    faithfulness,
)
from ragas.run_config import RunConfig

from langchain_groq import ChatGroq
from langchain_community.embeddings import HuggingFaceEmbeddings
from infra.config import Config


METRIC_NAMES = [
    "faithfulness",
    "answer_relevancy",
    "context_recall",
    "context_precision",
]


def load_dataset(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def _safe_score(value) -> float | None:
    """Return a JSON-safe rounded score, or None for NaN/inf/missing values."""
    try:
        score = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(score):
        return None
    return round(score, 4)


def _mean_valid(values: list[float | None]) -> float | None:
    valid = [value for value in values if value is not None]
    if not valid:
        return None
    return round(sum(valid) / len(valid), 4)


def _load_answer_cache(cache_path: Path) -> dict:
    if not cache_path.exists():
        return {}
    try:
        return json.loads(cache_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _save_answer_cache(cache_path: Path, cache: dict):
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(cache, indent=2), encoding="utf-8")


def _cache_key(qa: dict, rag_chain) -> str:
    prompt_version = getattr(rag_chain, "prompt_version", "unknown_prompt")
    model = getattr(rag_chain, "model_name", "unknown_model")
    return f"{qa.get('id', qa['question'])}|{prompt_version}|{model}|{qa['question']}"


def _build_evaluator(
    judge_provider: str,
    judge_model: str,
    answer_relevancy_strictness: int,
):
    if judge_provider != "groq":
        raise ValueError("Only judge_provider='groq' is supported by default.")
    if not Config.GROQ_API_KEY:
        raise ValueError("Please add GROQ_API_KEY to your .env file.")

    evaluator_llm = LangchainLLMWrapper(
        ChatGroq(
            model=judge_model,
            api_key=Config.GROQ_API_KEY,
            temperature=0,
            max_tokens=1024,
        )
    )
    evaluator_embeddings = LangchainEmbeddingsWrapper(
        HuggingFaceEmbeddings(model_name=Config.EMBEDDING_MODEL)
    )

    relevancy = copy.deepcopy(answer_relevancy)
    relevancy.strictness = answer_relevancy_strictness
    metrics = [faithfulness, relevancy, context_recall, context_precision]

    run_config = RunConfig(
        max_workers=1,
        timeout=120,
        max_retries=2,
        max_wait=5,
        thread_timeout=180,
    )
    return evaluator_llm, evaluator_embeddings, metrics, run_config


@contextmanager
def _judge_without_tracing():
    previous = os.environ.get("LANGCHAIN_TRACING_V2")
    os.environ["LANGCHAIN_TRACING_V2"] = "false"
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop("LANGCHAIN_TRACING_V2", None)
        else:
            os.environ["LANGCHAIN_TRACING_V2"] = previous


def _score_one_question(
    result: dict,
    evaluator_llm,
    evaluator_embeddings,
    metrics,
    run_config: RunConfig,
    raise_exceptions: bool,
) -> tuple[dict, str | None]:
    eval_dataset = Dataset.from_dict({
        "question": [result["question"]],
        "answer": [result["answer"]],
        "contexts": [result["contexts"]],
        "ground_truth": [result["ground_truth"]],
    })

    try:
        with _judge_without_tracing():
            scores = evaluate(
                eval_dataset,
                metrics=metrics,
                llm=evaluator_llm,
                embeddings=evaluator_embeddings,
                run_config=run_config,
                raise_exceptions=raise_exceptions,
            )
    except Exception as exc:
        if raise_exceptions:
            raise
        return {name: None for name in METRIC_NAMES}, str(exc)

    metric_scores = {
        name: _safe_score(scores.get(name))
        for name in METRIC_NAMES
    }
    error = None
    if any(value is None for value in metric_scores.values()):
        error = "One or more RAGAS metrics returned NaN or failed."
    return metric_scores, error


def run_evaluation(
    dataset_path: str,
    rag_chain,
    output_dir: str = "eval/results",
    limit: int = None,
    judge_provider: str = "groq",
    judge_model: str = "llama-3.3-70b-versatile",
    answer_relevancy_strictness: int = 1,
    raise_exceptions: bool = False,
    question_delay_seconds: float = 5.0,
):
    """Run RAGAS evaluation and save results."""
    qa_pairs = load_dataset(dataset_path)
    if limit:
        qa_pairs = qa_pairs[:limit]

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    cache_path = output_path / "answer_cache.json"
    answer_cache = _load_answer_cache(cache_path)

    print(f"Generating answers for {len(qa_pairs)} questions...")
    results = []
    for i, qa in enumerate(qa_pairs):
        print(f"  [{i+1}/{len(qa_pairs)}] {qa['question']}")

        key = _cache_key(qa, rag_chain)
        cached = answer_cache.get(key)
        response = cached
        if cached:
            print("    [cache] Reusing generated answer.")
        else:
            # Retry logic for transient Groq generation failures.
            for attempt in range(5):
                try:
                    response = rag_chain.query(qa["question"])
                    answer_cache[key] = response
                    _save_answer_cache(cache_path, answer_cache)
                    break
                except Exception as e:
                    wait_time = 2 ** attempt
                    print(f"    [!] Error: {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                
        if not response:
            print("    [!] Failed after 5 attempts. Skipping.")
            continue
            
        results.append({
            "question": qa["question"],
            "answer": response["answer"],
            "contexts": [c["content"] for c in response["contexts"]],
            "ground_truth": qa["ground_truth"],
            "metadata": {
                "id": qa["id"],
                "difficulty": qa["difficulty"],
                "category": qa["category"],
                "latency": response["latency_seconds"],
            }
        })

    print(f"Initializing RAGAS Judge ({judge_provider}: {judge_model})...")
    evaluator_llm, evaluator_embeddings, metrics, run_config = _build_evaluator(
        judge_provider=judge_provider,
        judge_model=judge_model,
        answer_relevancy_strictness=answer_relevancy_strictness,
    )

    print("Running RAGAS evaluation per question...")
    for i, result in enumerate(results):
        print(f"  [{i+1}/{len(results)}] Scoring {result['metadata']['id']}")
        metric_scores, error = _score_one_question(
            result=result,
            evaluator_llm=evaluator_llm,
            evaluator_embeddings=evaluator_embeddings,
            metrics=metrics,
            run_config=run_config,
            raise_exceptions=raise_exceptions,
        )
        result["metrics"] = metric_scores
        result["error"] = error
        if error:
            print(f"    [!] {error}")
        if question_delay_seconds and i < len(results) - 1:
            time.sleep(question_delay_seconds)

    aggregate_scores = {
        name: _mean_valid([r.get("metrics", {}).get(name) for r in results])
        for name in METRIC_NAMES
    }

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"{output_dir}/eval_{timestamp}.json"

    output = {
        "timestamp": timestamp,
        "dataset": dataset_path,
        "num_questions": len(qa_pairs),
        "judge": {
            "provider": judge_provider,
            "model": judge_model,
            "answer_relevancy_strictness": answer_relevancy_strictness,
        },
        "aggregate_scores": aggregate_scores,
        "per_question": results,
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, allow_nan=False)

    print(f"\n{'='*50}")
    print(f"RAGAS Evaluation Results")
    print(f"{'='*50}")
    for metric, score in aggregate_scores.items():
        display = "null" if score is None else f"{score:.4f}"
        print(f"  {metric}: {display}")
    print(f"\nResults saved to: {output_file}")

    return output

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="eval/datasets/qa_pairs.jsonl")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--judge-provider", choices=["groq"], default="groq")
    parser.add_argument("--judge-model", default="llama-3.3-70b-versatile")
    parser.add_argument("--answer-relevancy-strictness", type=int, default=1)
    parser.add_argument("--raise-exceptions", action="store_true")
    args = parser.parse_args()

    # Initialize pipeline
    from services.vector_store import VectorStore
    from services.bm25_store import BM25Store
    from services.hybrid_retriever import HybridRetriever
    from services.rag_chain import RAGChain
    from services.loader import load_all_documents
    from services.chunker import Chunker, ChunkStrategy

    print("Loading documents and indexing for evaluation...")
    pages = load_all_documents()
    chunks = Chunker(ChunkStrategy.FIXED_TOKEN).chunk_pages(pages)
    
    vs = VectorStore()
    vs.upsert_chunks(chunks)
    
    bm25 = BM25Store()
    bm25.index(chunks)
    
    hybrid = HybridRetriever(vs, bm25)
    chain = RAGChain(hybrid)

    run_evaluation(
        args.dataset,
        chain,
        limit=args.limit,
        judge_provider=args.judge_provider,
        judge_model=args.judge_model,
        answer_relevancy_strictness=args.answer_relevancy_strictness,
        raise_exceptions=args.raise_exceptions,
    )
