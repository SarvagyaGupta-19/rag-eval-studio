"""Qdrant vector store (local persistent) — upsert, search, and manage collections."""
from qdrant_client import QdrantClient, models
from infra.config import Config
from services.chunker import Chunk
from services.embedding import EmbeddingService
from services.retry import retry_with_backoff
import uuid


class VectorStore:
    def __init__(self, collection_name: str = None):
        self.client = QdrantClient(path="qdrant_data")  # local persistent storage
        self.collection = collection_name or Config.QDRANT_COLLECTION
        self.embedder = EmbeddingService()

    def create_collection(self):
        """Create collection if it doesn't exist."""
        collections = [c.name for c in self.client.get_collections().collections]
        if self.collection not in collections:
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=models.VectorParams(
                    size=self.embedder.dimension,
                    distance=models.Distance.COSINE,
                ),
            )

    @retry_with_backoff(max_retries=3, base_delay=1.0)
    def upsert_chunks(self, chunks: list[Chunk], batch_size: int = 64):
        """Embed and upsert chunks in batches."""
        self.create_collection()
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            texts = [c.content for c in batch]
            vectors = self.embedder.embed_texts(texts)
            points = [
                models.PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vec,
                    payload={"content": chunk.content, **chunk.metadata},
                )
                for chunk, vec in zip(batch, vectors)
            ]
            self.client.upsert(collection_name=self.collection, points=points)

    @retry_with_backoff(max_retries=3, base_delay=1.0)
    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """Dense retrieval — embed query and search Qdrant."""
        query_vector = self.embedder.embed_query(query)
        results = self.client.search(
            collection_name=self.collection,
            query_vector=query_vector,
            limit=top_k,
        )
        return [
            {"content": r.payload["content"], "score": r.score, "metadata": r.payload}
            for r in results
        ]

    def count(self) -> int:
        """Return number of points in the collection."""
        info = self.client.get_collection(collection_name=self.collection)
        return info.points_count
