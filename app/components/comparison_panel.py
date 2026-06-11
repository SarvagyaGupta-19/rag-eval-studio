"""Comparison panel — user-friendly side-by-side retrieval comparison."""
import streamlit as st
from app.components import answer_panel


def render(question: str, rag_chain, top_k: int):
    """Run the same query through dense-only and hybrid, show user-friendly comparison."""
    st.markdown("### 🔀 Comparing Search Engines")
    st.markdown(
        "<div style='color: #8b949e; margin-bottom: 20px;'>"
        "The same question is answered using two different search strategies "
        "to show how combining keyword and semantic search improves results."
        "</div>",
        unsafe_allow_html=True
    )

    col_dense, col_hybrid = st.columns(2)

    with col_dense:
        st.markdown("#### Semantic Search Only")
        with st.status("Searching...", expanded=True) as s1:
            st.write("Scanning vectors...")
            result_dense = rag_chain.query_with_routing(
                question,
                query_type="COMPARISON",
                params={"top_k": top_k, "dense_weight": 1.0},
            )
            s1.update(label="Complete", state="complete", expanded=False)
            
        answer_panel.render(result_dense)

    with col_hybrid:
        st.markdown("#### Semantic + Keyword Search")
        with st.status("Searching...", expanded=True) as s2:
            st.write("Scanning vectors & keywords...")
            result_hybrid = rag_chain.query_with_routing(
                question,
                query_type="COMPARISON",
                params={"top_k": top_k, "dense_weight": 0.6},
            )
            s2.update(label="Complete", state="complete", expanded=False)
            
        answer_panel.render(result_hybrid)

    # Source overlap — explained in user terms
    dense_sources = {c["content"][:100] for c in result_dense["contexts"]}
    hybrid_sources = {c["content"][:100] for c in result_hybrid["contexts"]}
    only_hybrid = hybrid_sources - dense_sources

    if only_hybrid:
        st.markdown(
            f"<div class='metric-container' style='border-color: #3fb950;'>"
            f"✅ <span style='color: #7ee787; font-weight: 500;'>The combined approach found {len(only_hybrid)} additional source(s)</span> "
            "that pure semantic search missed — these were matched by exact keywords."
            "</div>",
            unsafe_allow_html=True
        )
    else:
        st.info("Both approaches retrieved the same sources for this query.")
