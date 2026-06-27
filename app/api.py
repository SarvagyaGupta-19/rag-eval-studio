import sys
import os
from pathlib import Path
from typing import List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from services.vector_store import VectorStore
from services.bm25_store import BM25Store
from services.hybrid_retriever import HybridRetriever
from services.rag_chain import RAGChain
from services.query_router import QueryRouter
from services.document_processor import DocumentProcessor
from services.reranker import Reranker

app = FastAPI(title="RAG Eval Studio API")

# Configure CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], # Restrict in production
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Initialize services
vs = VectorStore()
bm25 = BM25Store()
bm25_path = Path("data/bm25_index.json")
if bm25_path.exists():
    bm25.load(str(bm25_path))
hybrid = HybridRetriever(vs, bm25)
router = QueryRouter()
reranker = Reranker()
chain = RAGChain(hybrid, prompt_version="rag_v1", reranker=reranker)

judge = None
gemini_key = os.getenv("GEMINI_API_KEY")
if gemini_key:
    try:
        from services.faithfulness_judge import FaithfulnessJudge
        judge = FaithfulnessJudge()
    except Exception as e:
        print(f"Warning: Could not initialize FaithfulnessJudge: {e}")

class ChatRequest(BaseModel):
    prompt: str
    source_filter: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    sources: List[str]
    faithfulness_score: Optional[float] = None

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        query_type = router.classify(request.prompt)
        params = router.get_retrieval_params(query_type)
        params["top_k"] = 5
        if request.source_filter:
            params["source_filter"] = f"uploads/{request.source_filter}"

        result = chain.query_with_routing(request.prompt, query_type, params)

        faith_score = None
        if judge:
            context_text = "\n".join([c["content"] for c in result["contexts"]])
            faith_score = judge.score(result["answer"], context_text)

        sources = []
        for chunk in result["contexts"]:
            source_name = chunk['metadata'].get('source', 'Unknown Document')
            source_name = Path(source_name).stem
            if source_name not in sources:
                sources.append(source_name)

        return ChatResponse(
            answer=result["answer"],
            sources=sources,
            faithfulness_score=faith_score
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
        
    try:
        content = await file.read()
        if len(content) > 10 * 1024 * 1024: # 10MB limit
            raise HTTPException(status_code=400, detail="File size exceeds 10MB limit.")
            
        processor = DocumentProcessor()
        chunks = processor.process_pdf_stream(content, file.filename)
        
        vs.upsert_chunks(chunks)
        bm25.add_chunks(chunks)
        
        return {"message": f"Successfully processed {file.filename}", "chunks": len(chunks)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

import os
from fastapi.staticfiles import StaticFiles
if os.path.exists("public"):
    app.mount("/", StaticFiles(directory="public", html=True), name="public")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
