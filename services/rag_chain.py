"""RAG chain with Groq LLM and LangSmith tracing."""
from __future__ import annotations

from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain_core.tracers.context import tracing_v2_enabled
from infra.config import Config
from services.hybrid_retriever import HybridRetriever
from pathlib import Path
import time


class RAGChain:
    def __init__(self, retriever: HybridRetriever, prompt_version: str = "rag_v1"):
        self.retriever = retriever
        # Use a smaller/different model for generation to split the rate limit load.
        # The evaluator (judge) will still use the more powerful Config.GROQ_MODEL.
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

    def _generate(self, context: str, question: str) -> str:
        """Run LLM generation with LangSmith tracing."""
        chain = self.prompt_template | self.llm | StrOutputParser()
        with tracing_v2_enabled(project_name="rag-eval-studio"):
            return chain.invoke({"context": context, "question": question})

    def query(self, question: str, top_k: int = 5) -> dict:
        """Run full RAG pipeline: retrieve -> format -> generate."""
        start_time = time.time()

        retrieved = self.retriever.retrieve(question, top_k=top_k)
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

        retrieved = self.retriever.retrieve(
            question, top_k=top_k, dense_weight=dense_weight
        )
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
