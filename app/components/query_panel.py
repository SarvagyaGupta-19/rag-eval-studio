"""Query input panel with example queries dropdown."""
import streamlit as st

EXAMPLE_QUERIES = [
    "What was Apple's total net sales for fiscal year 2024?",
    "What was NVIDIA's revenue from the Data Center segment in fiscal year 2025?",
    "How many vehicles did Tesla deliver in 2024?",
    "Compare the total R&D expenses of Apple and NVIDIA.",
    "What are the key risk factors associated with Tesla's Gigafactory?",
    "What is the exact recipe for the cafeteria food at Apple Park?",
]


def render(key_prefix: str = "main") -> str | None:
    """Render query input and return the submitted question, or None."""
    example = st.selectbox(
        "Example queries",
        ["— type your own —"] + EXAMPLE_QUERIES,
        key=f"{key_prefix}_example",
    )

    default_text = "" if example == "— type your own —" else example
    question = st.text_area(
        "Ask a question about SEC filings",
        value=default_text,
        height=80,
        key=f"{key_prefix}_input",
        placeholder="e.g. What was Apple's total revenue in 2024?",
    )

    submitted = st.button("🔍 Submit", key=f"{key_prefix}_submit", use_container_width=True)

    if submitted and question.strip():
        return question.strip()
    return None
