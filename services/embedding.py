"""Provider-agnostic embedding wrapper. Swap models without touching downstream code."""
from sentence_transformers import SentenceTransformer
from infra.config import Config


class EmbeddingService:
    def __init__(self, model_name: str = None):
        self.model_name = model_name or Config.EMBEDDING_MODEL
        self.model = SentenceTransformer(self.model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts. Returns list of float vectors."""
        embeddings = self.model.encode(
            texts, show_progress_bar=True, normalize_embeddings=True
        )
        return embeddings.tolist()

    def embed_query(self, query: str) -> list[float]:
        """Embed a single query."""
        return self.model.encode(query, normalize_embeddings=True).tolist()
