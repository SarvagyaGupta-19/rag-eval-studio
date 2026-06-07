# 🔍 RAG Eval Studio

> A production-grade Retrieval-Augmented Generation pipeline with hybrid search,
> automated RAGAS evaluation, and LangSmith observability.
> Built on SEC financial filings (10-K, 10-Q) for real-world document QA.

## 🎯 Key Features

- **Hybrid Retrieval**: Dense (Qdrant) + Sparse (BM25) with Reciprocal Rank Fusion
- **3 Chunking Strategies**: Fixed-token, paragraph-aware, recursive character
- **Query Routing**: Automatic complexity classification for cost optimization
- **RAGAS Evaluation**: Faithfulness, relevancy, context recall, context precision
- **LangSmith Observability**: Full trace logging for every query
- **CI/CD Pipeline**: Automated evaluation on every push

## 🚀 Quick Start

```bash
# Clone
git clone https://github.com/SarvagyaGupta-19/rag-eval-studio.git
cd rag-eval-studio

# Setup
python -m venv .venv
.venv\Scripts\activate       # Windows
pip install -r requirements.txt

# Configure
cp .env.example .env
# Fill in your API keys in .env

# Run
make pipeline                 # End-to-End Pipeline test
make test                     # Unit tests
make eval                     # RAGAS evaluation
make run                      # Streamlit UI
```

## 🏗️ Architecture

```
S3 (PDFs) → Loader → Chunker → Embeddings → Qdrant (Dense)
                                           → BM25 (Sparse)
                                           → Hybrid (RRF)
                                           → RAG Chain (Groq LLM)
                                           → LangSmith Traces
```

## 📊 Evaluation Results

*RAGAS evaluation metrics across different chunking strategies will be published here.*

## 📝 Design Decisions

*Detailed writeup of architectural choices will be added here.*

## License

MIT
