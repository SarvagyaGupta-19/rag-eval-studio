"""Qdrant Cloud vector store — upsert, search, and manage collections."""
from qdrant_client import QdrantClient, models
from infra.config import Config
from services.chunker import Chunk
from services.embedding import EmbeddingService
import uuid


class VectorStore:
    def __init__(self):
        self.client = QdrantClient(url=Config.QDRANT_URL, api_key=Config.QDRANT_API_KEY)
        self.collection = Config.QDRANT_COLLECTION
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
