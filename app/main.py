"""RAG Eval Studio — SEC Filing Document Q&A."""
import sys
import os
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
from services.document_processor import DocumentProcessor
from services.reranker import Reranker

# ─── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Finance Insights",
    layout="wide",
    initial_sidebar_state="expanded",
)

def load_css():
    css_path = Path(__file__).parent / "styles.css"
    if css_path.exists():
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

if "messages" not in st.session_state:
    st.session_state.messages = []

# ─── Pipeline initialization ─────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def init_pipeline():
    vs = VectorStore()
    bm25 = BM25Store()
    bm25_path = Path("data/bm25_index.json")
    if bm25_path.exists():
        bm25.load(str(bm25_path))
    hybrid = HybridRetriever(vs, bm25)
    router = QueryRouter()
    reranker = Reranker()
    return vs, bm25, hybrid, router, reranker

@st.cache_resource(show_spinner=False)
def init_chain(_hybrid, _reranker):
    return RAGChain(_hybrid, prompt_version="rag_v1", reranker=_reranker)

@st.cache_resource(show_spinner=False)
def init_judge():
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        return None
    try:
        from services.faithfulness_judge import FaithfulnessJudge
        return FaithfulnessJudge()
    except Exception:
        return None

if "pipeline_loaded" not in st.session_state:
    with st.spinner("Initializing system..."):
        vs, bm25, hybrid, router, reranker = init_pipeline()
        chain = init_chain(hybrid, reranker)
        judge = init_judge()
        st.session_state["pipeline_loaded"] = True
else:
    vs, bm25, hybrid, router, reranker = init_pipeline()
    chain = init_chain(hybrid, reranker)
    judge = init_judge()


# ─── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Document Upload")
    uploaded_file = st.file_uploader("Upload custom PDF for analysis", type=["pdf"])
    if uploaded_file is not None:
        if st.button("Add to Knowledge Base", use_container_width=True):
            with st.status("Processing Document...", expanded=True) as status:
                st.write("Extracting text and generating chunks...")
                processor = DocumentProcessor()
                chunks = processor.process_pdf_stream(uploaded_file.read(), uploaded_file.name)
                st.write(f"Generating embeddings for {len(chunks)} chunks...")
                vs.upsert_chunks(chunks)
                st.write("Updating Keyword Index...")
                bm25.add_chunks(chunks)
                status.update(label=f"Successfully added '{uploaded_file.name}'", state="complete", expanded=False)

    st.divider()
    
    if st.button("New Session"):
        st.session_state.messages = []
        st.rerun()


# ─── Main area ────────────────────────────────────────────────────────────────
if not st.session_state.messages:
    st.markdown(
        """
        <div class="landing-header">
            <h2>Finance Insights</h2>
            <p>Query millions of data points across corporate filings instantly.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    st.markdown("<h3>Finance Insights</h3><br>", unsafe_allow_html=True)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"], unsafe_allow_html=True)

if prompt := st.chat_input("Ask about SEC Filings (e.g., 'What were Apple's 2024 margins?')..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        thinking_placeholder = st.empty()
        thinking_placeholder.markdown("""
        <div class="grid-dots-container">
            <div class="grid-dot"></div>
            <div class="grid-dot"></div>
            <div class="grid-dot"></div>
            <span class="thinking-text">Analyzing corporate filings...</span>
        </div>
        """, unsafe_allow_html=True)

        try:
            query_type = router.classify(prompt)
            params = router.get_retrieval_params(query_type)
            params["top_k"] = 5

            result = chain.query_with_routing(prompt, query_type, params)

            thinking_placeholder.empty()

            st.markdown(result["answer"])

            # Faithfulness scoring
            faith_score = None
            if judge:
                context_text = "\n".join([c["content"] for c in result["contexts"]])
                faith_score = judge.score(result["answer"], context_text)

            st.write("")

            # Sources + Trust Score row
            html_sources = ""
            for chunk in result["contexts"]:
                source_name = chunk['metadata'].get('source', 'Unknown Document')
                source_name = Path(source_name).stem
                html_sources += f'<span class="source-pill">{source_name}</span>'

            if faith_score is not None:
                if faith_score >= 0.7:
                    badge_color = "#22c55e"
                elif faith_score >= 0.4:
                    badge_color = "#eab308"
                else:
                    badge_color = "#ef4444"
                trust_badge = (
                    f'<span style="display:inline-block;background:{badge_color};'
                    f'color:#fff;padding:4px 12px;border-radius:12px;font-size:0.85rem;'
                    f'font-weight:600;margin-left:8px;">'
                    f'Faithfulness: {faith_score}</span>'
                )
            else:
                trust_badge = ""

            st.markdown("**Sources:**")
            st.markdown(html_sources + trust_badge, unsafe_allow_html=True)

            display_content = result["answer"]
            if trust_badge:
                display_content += f"\n\n{trust_badge}"
            st.session_state.messages.append({"role": "assistant", "content": display_content})

        except Exception as e:
            thinking_placeholder.empty()
            error_msg = f"An error occurred while processing your request. Please try again.\n\n`{type(e).__name__}: {e}`"
            st.error(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
