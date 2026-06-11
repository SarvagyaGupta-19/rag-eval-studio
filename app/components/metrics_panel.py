"""Sidebar metrics panel — RAGAS scores, eval results, and LangSmith link."""
import json
import math
import time
import streamlit as st
from pathlib import Path


def _safe(val) -> str:
    if val is None:
        return "—"
    try:
        v = float(val)
        return "—" if not math.isfinite(v) else f"{v:.4f}"
    except (TypeError, ValueError):
        return "—"


def render_live_eval(result: dict):
    """Run single-question RAGAS evaluation and display scores."""
    btn = st.button("⚡ Evaluate This Answer", use_container_width=True)
    if not btn:
        return

    with st.spinner("Running RAGAS judge (this takes ~15s)..."):
        try:
            from eval.ragas_eval import (
                _build_evaluator,
                _score_one_question,
                _judge_without_tracing,
            )

            evaluator_llm, evaluator_embeddings, metrics, run_config = (
                _build_evaluator(
                    judge_provider="groq",
                    judge_model="llama-3.3-70b-versatile",
                    answer_relevancy_strictness=1,
                )
            )

            eval_input = {
                "question": result["question"],
                "answer": result["answer"],
                "contexts": [c["content"] for c in result["contexts"]],
                "ground_truth": "No ground truth available for live queries.",
            }

            scores, error = _score_one_question(
                eval_input,
                evaluator_llm,
                evaluator_embeddings,
                metrics,
                run_config,
                raise_exceptions=False,
            )

            if error:
                st.warning(f"Partial scores — {error}")

            st.markdown("##### Live RAGAS Scores")
            cols = st.columns(2)
            cols[0].metric("Faithfulness", _safe(scores.get("faithfulness")))
            cols[1].metric("Relevancy", _safe(scores.get("answer_relevancy")))

        except Exception as e:
            st.error(f"Evaluation failed: {e}")


def render_precomputed_scores():
    """Display aggregate scores from the most recent evaluation run."""
    results_dir = Path("eval/results/fixed_token")
    if not results_dir.exists():
        return

    eval_files = sorted(results_dir.glob("eval_*.json"), reverse=True)
    if not eval_files:
        return

    with open(eval_files[0], encoding="utf-8") as f:
        data = json.load(f)

    st.markdown("##### Latest Eval Run")
    scores = data.get("aggregate_scores", {})
    st.metric("Faithfulness", _safe(scores.get("faithfulness")))
    st.metric("Answer Relevancy", _safe(scores.get("answer_relevancy")))
    st.metric("Context Recall", _safe(scores.get("context_recall")))
    st.metric("Context Precision", _safe(scores.get("context_precision")))
    st.caption(
        f"Questions: {data.get('num_questions', '?')} · "
        f"Judge: {data.get('judge', {}).get('model', '?')}"
    )


def render_langsmith_link():
    """Show clickable LangSmith dashboard link."""
    st.markdown("##### 🔗 Observability")
    st.link_button(
        "Open LangSmith Dashboard",
        "https://smith.langchain.com/",
        use_container_width=True,
    )
