"""Route queries by complexity to optimize cost and latency."""
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain.schema.output_parser import StrOutputParser
from infra.config import Config
from pathlib import Path


class QueryRouter:
    def __init__(self):
        # Use a smaller/faster model for routing to minimize latency
        self.router_llm = ChatGroq(
            model="llama-3.1-8b-instant",
            api_key=Config.GROQ_API_KEY,
            temperature=0,
            max_tokens=20,
        )
        template = Path("prompts/router_prompt.txt").read_text()
        self.prompt = PromptTemplate(
            template=template, input_variables=["question"]
        )
        self.chain = self.prompt | self.router_llm | StrOutputParser()

    def classify(self, question: str) -> str:
        """Classify query complexity."""
        result = self.chain.invoke({"question": question}).strip().upper()
        # Extract just the category name if extra text is returned
        for category in ("FACTOID", "ANALYTICAL", "UNANSWERABLE"):
            if category in result:
                return category
        return "ANALYTICAL"  # default to more thorough retrieval

    def get_retrieval_params(self, query_type: str) -> dict:
        """Return retrieval parameters based on query type."""
        params = {
            "FACTOID": {"top_k": 3, "dense_weight": 0.5},
            "ANALYTICAL": {"top_k": 7, "dense_weight": 0.6},
            "UNANSWERABLE": {"top_k": 3, "dense_weight": 0.5},
        }
        return params.get(query_type, params["ANALYTICAL"])
