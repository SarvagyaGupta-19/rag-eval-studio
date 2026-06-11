"""Answer display panel with expandable source chunks."""
import streamlit as st


def render(result: dict, label: str = ""):
    """Render a RAG result dict with answer, metadata, and expandable sources."""
    if label:
        st.markdown(f"#### {label}")

    # Answer
    st.markdown(result["answer"])

    # Metadata row
    cols = st.columns(3)
    cols[0].metric("Latency", f"{result['latency_seconds']}s")
    cols[1].metric("Model", result.get("model", "—"))
    cols[2].metric("Sources", str(len(result["contexts"])))

    if result.get("query_type"):
        st.caption(
            f"Route: **{result['query_type']}** · "
            f"Top-K: {result.get('top_k', '?')} · "
            f"Dense weight: {result.get('dense_weight', '?')}"
        )

    # Expandable sources
    with st.expander(f"📄 Retrieved Chunks ({len(result['contexts'])})", expanded=False):
        for i, chunk in enumerate(result["contexts"]):
            meta = chunk.get("metadata", chunk)
            source = meta.get("source", "unknown")
            page = meta.get("page_number", "?")
            score = chunk.get("rrf_score") or chunk.get("score", "—")
            methods = chunk.get("retrieval_methods", [])

            method_tag = ""
            if methods:
                method_tag = " · ".join(f"`{m}`" for m in methods)
            else:
                method_tag = "`dense`"

            if isinstance(score, float):
                score = f"{score:.4f}"

            st.markdown(
                f"**[{i+1}]** `{source}` p.{page} — score: {score} — {method_tag}"
            )
            st.text(chunk["content"][:500])
            if len(chunk["content"]) > 500:
                st.caption(f"... ({len(chunk['content'])} chars total)")
            st.divider()
