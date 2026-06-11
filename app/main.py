"""RAG Eval Studio — SEC Filing Document Q&A."""
import sys
from pathlib import Path

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
    page_title="Terminal | SEC Filings",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── Inject Custom CSS ────────────────────────────────────────────────────────
def load_css():
    css_path = Path(__file__).parent / "styles.css"
    if css_path.exists():
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# ─── Pipeline initialization ─────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def init_pipeline():
    vs = VectorStore()
    bm25 = BM25Store()
    bm25.load("data/bm25_index.json")
    hybrid = HybridRetriever(vs, bm25)
    router = QueryRouter()
    return vs, bm25, hybrid, router


@st.cache_resource(show_spinner=False)
def init_chain(_hybrid, prompt_version: str):
    return RAGChain(_hybrid, prompt_version=prompt_version)


# ─── Sidebar (Developer Tools) ────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Settings")

    prompt_version = st.selectbox(
        "Response style",
        ["rag_v1", "rag_v2_cot"],
        format_func=lambda x: "Direct Answer" if x == "rag_v1" else "Step-by-Step Reasoning",
    )
    top_k = st.slider("Sources depth", 1, 10, 5)
    comparison_mode = st.toggle("Compare search engines", value=False)

    st.divider()
    dev_mode = st.toggle("🛠️ Developer Mode", value=False)

    if dev_mode:
        st.divider()
        metrics_panel.render_dev_tools(
            result=st.session_state.get("last_result")
        )


# ─── Initialize pipeline ─────────────────────────────────────────────────────
# We use a skeleton loader while the models load into memory.
if "pipeline_loaded" not in st.session_state:
    with st.spinner("Waking up semantic engines..."):
        vs, bm25, hybrid, router = init_pipeline()
        chain = init_chain(hybrid, prompt_version)
        st.session_state["pipeline_loaded"] = True
else:
    vs, bm25, hybrid, router = init_pipeline()
    chain = init_chain(hybrid, prompt_version)


# ─── Main area ────────────────────────────────────────────────────────────────
st.markdown("## ⚡ SEC Intelligence Terminal")
st.markdown(
    "<span style='color:#8b949e;'>Query millions of data points across Apple, Tesla, "
    "NVIDIA, and JPMorgan Chase filings instantly.</span>",
    unsafe_allow_html=True
)
st.write("") # Spacer

question = query_panel.render()

if question:
    if comparison_mode:
        comparison_panel.render(question, chain, top_k)
    else:
        # Active Loading States
        with st.status("Analyzing...", expanded=True) as status:
            st.write("🧠 Understanding query intent...")
            query_type = router.classify(question)
            params = router.get_retrieval_params(query_type)
            params["top_k"] = top_k
            
            st.write("🔍 Scanning semantic vectors and keyword indexes...")
            # The RAG chain handles both retrieval and generation internally right now.
            st.write("⚡ Synthesizing financial data...")
            
            result = chain.query_with_routing(question, query_type, params)
            
            status.update(label="Analysis complete", state="complete", expanded=False)

        # Store for dev mode access
        st.session_state["last_result"] = result

        # Display answer
        answer_panel.render(result)
