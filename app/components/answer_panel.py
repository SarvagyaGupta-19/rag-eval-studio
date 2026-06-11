"""Answer panel — user-friendly answer with clean source citations."""
import streamlit as st


def _confidence_badge(result: dict) -> str:
    """Derive a user-friendly confidence level from the result quality signals."""
    contexts = result.get("contexts", [])
    if not contexts:
        return "<span class='confidence-low'>⚠️ Low Confidence</span> — no sources found"

    # Count how many sources were retrieved by both dense AND sparse (stronger signal)
    both_methods = sum(
        1 for c in contexts
        if len(c.get("retrieval_methods", [])) >= 2
    )
    top_score = max(
        (c.get("rrf_score", 0) or c.get("score", 0) for c in contexts),
        default=0,
    )

    if both_methods >= 2 and top_score > 0.01:
        return "<span class='confidence-high'>🟢 High Confidence</span> — corroborated by multiple search methods"
    elif len(contexts) >= 3:
        return "<span class='confidence-medium'>🟡 Medium Confidence</span> — based on multiple sources"
    else:
        return "<span class='confidence-low'>🟠 Limited Confidence</span> — fewer sources available"


def _format_source_name(source: str) -> str:
    """Turn 'documents/AAPL_10K_2024_000123.pdf' into 'Apple 10-K (2024)'."""
    name_map = {
        "AAPL": "Apple", "TSLA": "Tesla",
        "NVDA": "NVIDIA", "JPM": "JPMorgan",
    }
    # Extract the filename part
    filename = source.split("/")[-1].replace(".pdf", "")
    parts = filename.split("_")
    if len(parts) >= 3:
        ticker = parts[0]
        filing_type = parts[1].replace("10K", "10-K").replace("10Q", "10-Q")
        year = parts[2]
        company = name_map.get(ticker, ticker)
        return f"{company} {filing_type} ({year})"
    return source


def render(result: dict, label: str = ""):
    """Render user-friendly answer with confidence badge and clean source citations."""
    if label:
        st.markdown(f"#### {label}")

    # Confidence badge + response time
    confidence_html = _confidence_badge(result)
    st.markdown(
        f"<div class='metric-container'>{confidence_html} <span style='color:#8b949e; margin-left: 10px;'>⏱️ {result['latency_seconds']:.2f}s</span></div>",
        unsafe_allow_html=True
    )

    # Answer in a clean container
    st.markdown(f"<div style='font-size: 16px; line-height: 1.6; margin-bottom: 20px;'>{result['answer']}</div>", unsafe_allow_html=True)

    # Source citations — clean format
    contexts = result.get("contexts", [])
    if not contexts:
        return

    # Deduplicate sources by document name
    seen_sources = {}
    for chunk in contexts:
        meta = chunk.get("metadata", chunk)
        source = meta.get("source", "unknown")
        page = meta.get("page_number", "?")
        friendly_name = _format_source_name(source)
        if friendly_name not in seen_sources:
            seen_sources[friendly_name] = []
        if page not in seen_sources[friendly_name]:
            seen_sources[friendly_name].append(page)

    # Show as clean citation list
    citation_parts = []
    for doc_name, pages in seen_sources.items():
        page_str = ", ".join(str(p) for p in sorted(pages)[:5])
        citation_parts.append(f"**{doc_name}** (p. {page_str})")

    st.markdown("##### 📄 Sources Used")
    st.markdown(f"<div style='color: #8b949e; font-size: 14px;'>{' · '.join(citation_parts)}</div>", unsafe_allow_html=True)
    st.write("")

    # Expandable detail for users who want to verify
    with st.expander("View exact source excerpts", expanded=False):
        for i, chunk in enumerate(contexts):
            meta = chunk.get("metadata", chunk)
            source = _format_source_name(meta.get("source", "unknown"))
            page = meta.get("page_number", "?")

            st.markdown(f"**{source}** — Page {page}")
            st.markdown(f"<div class='source-card'>{chunk['content'][:600]}...</div>", unsafe_allow_html=True)
