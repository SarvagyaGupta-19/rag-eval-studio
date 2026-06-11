"""Comparison panel — dense-only vs hybrid retrieval side by side."""
import streamlit as st
from app.components import answer_panel


def render(question: str, rag_chain, prompt_version: str, top_k: int):
    """Run the same query through dense-only and hybrid retrieval, display side by side."""
    st.markdown("### 🔀 Comparison: Dense vs Hybrid Retrieval")

    col_dense, col_hybrid = st.columns(2)

    with col_dense:
        st.markdown("##### Dense Only (Qdrant)")
        with st.spinner("Running dense-only..."):
            # Dense-only: set dense_weight=1.0 so sparse contributes nothing
            result_dense = rag_chain.query_with_routing(
                question,
                query_type="COMPARISON",
                params={"top_k": top_k, "dense_weight": 1.0},
            )
        answer_panel.render(result_dense, label="")

    with col_hybrid:
        st.markdown("##### Hybrid (RRF: Dense + BM25)")
        with st.spinner("Running hybrid..."):
            # Hybrid: balanced dense+sparse weights
            result_hybrid = rag_chain.query_with_routing(
                question,
                query_type="COMPARISON",
                params={"top_k": top_k, "dense_weight": 0.6},
            )
        answer_panel.render(result_hybrid, label="")

    # Source overlap analysis
    dense_sources = set()
    hybrid_sources = set()
    for c in result_dense["contexts"]:
        dense_sources.add(c["content"][:100])
    for c in result_hybrid["contexts"]:
        hybrid_sources.add(c["content"][:100])

    overlap = dense_sources & hybrid_sources
    only_dense = dense_sources - hybrid_sources
    only_hybrid = hybrid_sources - dense_sources

    st.markdown("---")
    st.markdown("##### Source Overlap")
    c1, c2, c3 = st.columns(3)
    c1.metric("Shared", str(len(overlap)))
    c2.metric("Dense Only", str(len(only_dense)))
    c3.metric("Hybrid Only", str(len(only_hybrid)))

    if only_hybrid:
        st.info(
            f"Hybrid retrieval surfaced **{len(only_hybrid)} unique chunk(s)** "
            "that dense-only missed — these came from BM25 keyword matching."
        )
