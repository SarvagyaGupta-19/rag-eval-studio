"""BM25 sparse retrieval for keyword-heavy queries."""
from rank_bm25 import BM25Okapi
from services.chunker import Chunk
import json
import re
from pathlib import Path


class BM25Store:
    def __init__(self):
        self.documents: list[Chunk] = []
        self.bm25: BM25Okapi | None = None

    def index(self, chunks: list[Chunk]):
        """Build BM25 index from chunks."""
        self.documents = chunks
        tokenized = [self._tokenize(c.content) for c in chunks]
        self.bm25 = BM25Okapi(tokenized)

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """Sparse retrieval using BM25."""
        if not self.bm25:
            raise ValueError("BM25 index not built. Call index() first.")
        tokenized_query = self._tokenize(query)
        scores = self.bm25.get_scores(tokenized_query)
        top_indices = scores.argsort()[-top_k:][::-1]
        return [
            {
                "content": self.documents[i].content,
                "score": float(scores[i]),
                "metadata": self.documents[i].metadata,
            }
            for i in top_indices
            if scores[i] > 0
        ]

    def save(self, path: str = "data/bm25_index.json"):
        """Persist chunks to disk so BM25 can be rebuilt without re-loading PDFs."""
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        data = [
            {"content": c.content, "metadata": c.metadata} for c in self.documents
        ]
        out.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def load(self, path: str = "data/bm25_index.json"):
        """Load chunks from disk and rebuild BM25 index."""
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        chunks = [Chunk(content=d["content"], metadata=d["metadata"]) for d in data]
        self.index(chunks)

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return re.findall(r"\w+", text.lower())
