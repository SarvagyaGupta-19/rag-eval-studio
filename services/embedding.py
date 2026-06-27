"""Provider-agnostic embedding wrapper. Swap models without touching downstream code."""
import os
from google import genai
from infra.config import Config


class EmbeddingService:
    def __init__(self, model_name: str = None):
        # Default to Gemini embedding model if not specified in config
        self.model_name = model_name or os.getenv("EMBEDDING_MODEL", "text-embedding-004")
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        # Gemini text-embedding-004 has dimension 768
        self.dimension = int(os.getenv("EMBEDDING_DIM", "768"))

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts. Returns list of float vectors."""
        if not texts:
            return []
            
        response = self.client.models.embed_content(
            model=self.model_name,
            contents=texts
        )
        return [e.values for e in response.embeddings]

    def embed_query(self, query: str) -> list[float]:
        """Embed a single query."""
        if not query:
            return []
            
        response = self.client.models.embed_content(
            model=self.model_name,
            contents=query
        )
        return response.embeddings[0].values
