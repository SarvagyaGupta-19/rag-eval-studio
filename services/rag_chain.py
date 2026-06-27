"""RAG chain with Groq LLM, cross-encoder reranking, and LangSmith tracing."""
from __future__ import annotations

from services.retry import retry_with_backoff

from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain_core.tracers.context import tracing_v2_enabled
from infra.config import Config
from services.hybrid_retriever import HybridRetriever
from pathlib import Path
import time


class RAGChain:
    def __init__(self, retriever: HybridRetriever, prompt_version: str = "rag_v1", reranker=None):
        self.retriever = retriever
        self.reranker = reranker
        self.model_name = "llama-3.1-8b-instant"
        self.llm = ChatGroq(
            model=self.model_name,
            api_key=Config.GROQ_API_KEY,
            temperature=0,
            max_tokens=1024,
        )
        self.prompt_version = prompt_version
        self.prompt_template = self._load_prompt(prompt_version)

    def _load_prompt(self, version: str) -> PromptTemplate:
        prompt_path = Path(f"prompts/{version}.txt")
        template = prompt_path.read_text()
        return PromptTemplate(template=template, input_variables=["context", "question"])

    @staticmethod
    def _format_context(retrieved: list[dict]) -> str:
        """Format retrieved chunks into a context string for the LLM prompt."""
        return "\n\n---\n\n".join(
            [
                f"[Source: {r['metadata'].get('source', 'unknown')}, "
                f"Page: {r['metadata'].get('page_number', '?')}]\n{r['content']}"
                for r in retrieved
            ]
        )

    @retry_with_backoff(max_retries=3, base_delay=2.0)
    def _generate(self, context: str, question: str) -> str:
        """Run LLM generation with LangSmith tracing."""
        chain = self.prompt_template | self.llm | StrOutputParser()
        with tracing_v2_enabled(project_name="rag-eval-studio"):
            return chain.invoke({"context": context, "question": question})

    def query(self, question: str, top_k: int = 5) -> dict:
        """Run full RAG pipeline: retrieve -> rerank -> format -> generate."""
        start_time = time.time()

        candidates = self.retriever.retrieve(question, top_k=top_k * 2)
        if self.reranker:
            retrieved = self.reranker.rerank(question, candidates, top_k=top_k)
        else:
            retrieved = candidates[:top_k]
        context = self._format_context(retrieved)
        answer = self._generate(context, question)

        elapsed = time.time() - start_time

        return {
            "question": question,
            "answer": answer,
            "contexts": retrieved,
            "prompt_version": self.prompt_version,
            "model": self.model_name,
            "latency_seconds": round(elapsed, 2),
            "top_k": top_k,
        }

    def query_with_routing(self, question: str, query_type: str, params: dict) -> dict:
        """Run RAG pipeline with pre-determined routing params."""
        start_time = time.time()

        top_k = params.get("top_k", 5)
        dense_weight = params.get("dense_weight", 0.6)
        source_filter = params.get("source_filter")

        candidates = self.retriever.retrieve(
            question, top_k=top_k * 2, dense_weight=dense_weight, source_filter=source_filter
        )
        if self.reranker:
            retrieved = self.reranker.rerank(question, candidates, top_k=top_k)
        else:
            retrieved = candidates[:top_k]
        context = self._format_context(retrieved)
        answer = self._generate(context, question)

        elapsed = time.time() - start_time

        return {
            "question": question,
            "answer": answer,
            "contexts": retrieved,
            "prompt_version": self.prompt_version,
            "model": self.model_name,
            "latency_seconds": round(elapsed, 2),
            "top_k": top_k,
            "query_type": query_type,
            "dense_weight": dense_weight,
        }
