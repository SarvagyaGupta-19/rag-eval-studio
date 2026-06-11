"""Query input — sleek search bar with dynamic example queries."""
import streamlit as st

EXAMPLE_QUERIES = [
    "What was Apple's total revenue in 2024?",
    "What was NVIDIA's Data Center revenue in 2025?",
    "How many vehicles did Tesla deliver in 2024?",
    "Compare the R&D expenses of Apple and NVIDIA.",
    "What are the key risk factors for Tesla's manufacturing?",
]

def render(key_prefix: str = "main") -> str | None:
    """Render a clean search interface. Returns the submitted question or None."""
    
    # Hero Search Bar
    question = st.text_input(
        "Ask a question",
        key=f"{key_prefix}_input",
        placeholder="e.g. What was Apple's total revenue in 2024?",
        label_visibility="collapsed",
    )
    
    col_spacer, col_btn = st.columns([5, 1])
    with col_btn:
        submitted = st.button("Search →", key=f"{key_prefix}_submit", use_container_width=True)

    # Example queries as clickable pills
    st.markdown("<div style='margin-top: -10px; margin-bottom: 20px;'><span style='color: #8b949e; font-size: 13px;'>Try an example:</span></div>", unsafe_allow_html=True)
    
    pill_cols = st.columns(3)
    for i, example in enumerate(EXAMPLE_QUERIES[:3]):
        with pill_cols[i]:
            if st.button(
                example[:40] + "…" if len(example) > 40 else example,
                key=f"{key_prefix}_ex_{i}",
                use_container_width=True,
            ):
                # In Streamlit, setting session state for a widget requires a rerun
                # or assigning it directly if the widget hasn't rendered yet.
                # Here, we update a secondary state and rerun.
                st.session_state[f"{key_prefix}_override"] = example
                st.rerun()

    # If an example was clicked, we override the question
    if st.session_state.get(f"{key_prefix}_override"):
        question = st.session_state.pop(f"{key_prefix}_override")
        submitted = True

    if submitted and question.strip():
        return question.strip()
    return None
