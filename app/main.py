"""RAG Eval Studio — Streamlit UI for interactive RAG queries and evaluation."""
import sys
from pathlib import Path

# Ensure project root is on path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from services.vector_store import VectorStore
from services.bm25_store import BM25Store
from services.hybrid_retriever import HybridRetriever
from services.rag_chain import RAGChain
from services.query_router import QueryRouter

from app.components import query_panel, answer_panel, metrics_panel, comparison_panel

# ─── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="RAG Eval Studio",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ─── Pipeline initialization (cached) ────────────────────────────────────────
@st.cache_resource(show_spinner="Loading RAG pipeline...")
def init_pipeline():
    vs = VectorStore()
    bm25 = BM25Store()
    bm25.load("data/bm25_index.json")
    hybrid = HybridRetriever(vs, bm25)
    router = QueryRouter()
    return vs, bm25, hybrid, router


@st.cache_resource(show_spinner="Initializing RAG chain...")
def init_chain(_hybrid, prompt_version: str):
    return RAGChain(_hybrid, prompt_version=prompt_version)


# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🔍 RAG Eval Studio")
    st.caption("SEC Filing Document QA")
    st.divider()

    # Config controls
    st.markdown("##### ⚙️ Configuration")
    prompt_version = st.selectbox(
        "Prompt Template",
        ["rag_v1", "rag_v2_cot"],
        help="v1 = direct answer, v2 = chain-of-thought reasoning",
    )
    top_k = st.slider("Top-K Results", min_value=1, max_value=10, value=5)
    comparison_mode = st.toggle("🔀 Comparison Mode", value=False)

    st.divider()

    # Pre-computed eval scores
    metrics_panel.render_precomputed_scores()
    st.divider()

    # LangSmith link
    metrics_panel.render_langsmith_link()


# ─── Initialize pipeline ─────────────────────────────────────────────────────
vs, bm25, hybrid, router = init_pipeline()
chain = init_chain(hybrid, prompt_version)

# ─── Main area ────────────────────────────────────────────────────────────────
st.header("Ask a question about SEC filings")
st.caption("Powered by hybrid retrieval (Qdrant + BM25 + RRF) with Groq LLM")

question = query_panel.render()

if question:
    if comparison_mode:
        # ── Comparison mode ───────────────────────────────────────────────
        comparison_panel.render(question, chain, prompt_version, top_k)
    else:
        # ── Standard mode ─────────────────────────────────────────────────
        with st.spinner("Retrieving and generating..."):
            query_type = router.classify(question)
            params = router.get_retrieval_params(query_type)
            params["top_k"] = top_k  # override with user's slider value
            result = chain.query_with_routing(question, query_type, params)

        answer_panel.render(result)

        # Live eval button
        st.divider()
        metrics_panel.render_live_eval(result)

elif not question and st.session_state.get("main_submit"):
    st.warning("Please enter a question.")
