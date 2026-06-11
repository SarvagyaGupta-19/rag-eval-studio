"""Finance Insights — SEC Filing Document Q&A."""
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
from services.document_processor import DocumentProcessor

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

# Initialize session state for chat
if "messages" not in st.session_state:
    st.session_state.messages = []

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
def init_chain(_hybrid):
    # Hardcode safe defaults for enterprise use
    return RAGChain(_hybrid, prompt_version="rag_v1")

if "pipeline_loaded" not in st.session_state:
    with st.spinner("Initializing system..."):
        vs, bm25, hybrid, router = init_pipeline()
        chain = init_chain(hybrid)
        st.session_state["pipeline_loaded"] = True
else:
    vs, bm25, hybrid, router = init_pipeline()
    chain = init_chain(hybrid)


# ─── Sidebar ────────────────────────────────────────────────
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
    # Landing Page State
    st.markdown(
        """
        <div class="landing-header">
            <h2>Finance Insights</h2>
            <p>Query millions of data points across corporate filings instantly.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(
            '''
            <div class="glass-panel">
                <h3>Compare Tesla & Apple Revenue</h3>
                <p>What were the primary drivers of revenue growth for Tesla and Apple in their latest 10-K filings?</p>
            </div>
            ''', unsafe_allow_html=True
        )
        st.write("<br>", unsafe_allow_html=True)
        st.markdown(
            '''
            <div class="glass-panel">
                <h3>NVIDIA Risk Factors</h3>
                <p>Summarize the key supply chain risks mentioned in NVIDIA's latest annual report.</p>
            </div>
            ''', unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            '''
            <div class="glass-panel">
                <h3>JPMorgan Interest Rates</h3>
                <p>How did rising interest rates impact JPMorgan Chase's net interest income?</p>
            </div>
            ''', unsafe_allow_html=True
        )
        st.write("<br>", unsafe_allow_html=True)
        st.markdown(
            '''
            <div class="glass-panel">
                <h3>Deep Dive: Apple Services</h3>
                <p>Provide a detailed breakdown of Apple's Services segment performance and margins.</p>
            </div>
            ''', unsafe_allow_html=True
        )
else:
    # Chat State (Hide the big header once chatting)
    st.markdown("<h3>Finance Insights</h3><br>", unsafe_allow_html=True)

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat Input
if prompt := st.chat_input("Ask about SEC Filings (e.g., 'What were Apple's 2024 margins?')..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.status("Analyzing...", expanded=True) as status:
            st.write("Understanding query intent...")
            query_type = router.classify(prompt)
            params = router.get_retrieval_params(query_type)
            params["top_k"] = 5 # Hardcoded safe default
            
            st.write("Scanning semantic vectors and keyword indexes...")
            st.write("Synthesizing financial data...")
            
            result = chain.query_with_routing(prompt, query_type, params)
            
            status.update(label="Analysis complete", state="complete", expanded=False)
        
        st.markdown(result["answer"])
        
        st.write("")
        st.markdown("**Sources:**")
        html_sources = ""
        for i, chunk in enumerate(result["source_documents"]):
            source_name = chunk.metadata.get('source', 'Unknown Document')
            source_name = Path(source_name).stem
            html_sources += f'<span class="source-pill">{source_name}</span>'
            
        st.markdown(html_sources, unsafe_allow_html=True)
        
    st.session_state.messages.append({"role": "assistant", "content": result["answer"]})
