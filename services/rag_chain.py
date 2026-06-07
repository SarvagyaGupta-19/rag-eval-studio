"""RAG chain with Groq LLM and LangSmith tracing."""
from __future__ import annotations

from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain_core.tracers.context import tracing_v2_enabled
from infra.config import Config
from pathlib import Path
import time


class RAGChain:
    def __init__(self, retriever: HybridRetriever, prompt_version: str = "rag_v1"):
        self.retriever = retriever
        self.llm = ChatGroq(
            model=Config.GROQ_MODEL,
            api_key=Config.GROQ_API_KEY,
            temperature=0.1,
            max_tokens=1024,
        )
        self.prompt_version = prompt_version
        self.prompt_template = self._load_prompt(prompt_version)

    def _load_prompt(self, version: str) -> PromptTemplate:
        prompt_path = Path(f"prompts/{version}.txt")
        template = prompt_path.read_text()
        return PromptTemplate(template=template, input_variables=["context", "question"])

    def query(self, question: str, top_k: int = 5) -> dict:
        """Run full RAG pipeline: retrieve -> format -> generate."""
        start_time = time.time()

        # Retrieve
        retrieved = self.retriever.retrieve(question, top_k=top_k)
        context = "\n\n---\n\n".join(
            [
                f"[Source: {r['metadata'].get('source', 'unknown')}, "
                f"Page: {r['metadata'].get('page_number', '?')}]\n{r['content']}"
                for r in retrieved
            ]
        )

        # Generate with LangSmith tracing
        chain = self.prompt_template | self.llm | StrOutputParser()

        with tracing_v2_enabled(project_name="rag-eval-studio"):
            answer = chain.invoke({"context": context, "question": question})

        elapsed = time.time() - start_time

        return {
            "question": question,
            "answer": answer,
            "contexts": retrieved,
            "prompt_version": self.prompt_version,
            "model": Config.GROQ_MODEL,
            "latency_seconds": round(elapsed, 2),
            "top_k": top_k,
        }

    def query_with_routing(self, question: str, query_type: str, params: dict) -> dict:
        """Run RAG pipeline with pre-determined routing params."""
        start_time = time.time()

        top_k = params.get("top_k", 5)
        dense_weight = params.get("dense_weight", 0.6)

        # Retrieve with routed params
        retrieved = self.retriever.retrieve(
            question, top_k=top_k, dense_weight=dense_weight
        )
        context = "\n\n---\n\n".join(
            [
                f"[Source: {r['metadata'].get('source', 'unknown')}, "
                f"Page: {r['metadata'].get('page_number', '?')}]\n{r['content']}"
                for r in retrieved
            ]
        )

        # Generate with tracing
        chain = self.prompt_template | self.llm | StrOutputParser()

        with tracing_v2_enabled(project_name="rag-eval-studio"):
            answer = chain.invoke({"context": context, "question": question})

        elapsed = time.time() - start_time

        return {
            "question": question,
            "answer": answer,
            "contexts": retrieved,
            "prompt_version": self.prompt_version,
            "model": Config.GROQ_MODEL,
            "latency_seconds": round(elapsed, 2),
            "top_k": top_k,
            "query_type": query_type,
            "dense_weight": dense_weight,
        }
