"""
Index all SEC filings: load from S3 -> chunk -> embed -> upsert to Qdrant + build BM25.
Run this once after uploading documents to S3.
"""
import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from services.loader import load_all_documents
from services.chunker import Chunker, ChunkStrategy
from services.vector_store import VectorStore
from services.bm25_store import BM25Store


def main():
    print("=" * 60)
    print("RAG Eval Studio - Document Indexer")
    print("=" * 60)

    # Step 1: Load PDFs from S3
    print("\n[1/4] Loading documents from S3...")
    pages = load_all_documents()
    print(f"  Loaded {len(pages)} pages from S3")

    if not pages:
        print("  [FAIL] No pages loaded. Check S3 bucket and credentials.")
        sys.exit(1)

    # Step 2: Chunk with fixed-token strategy (best for embedding consistency)
    print("\n[2/4] Chunking documents (fixed_token, 512 tokens, 50 overlap)...")
    chunker = Chunker(ChunkStrategy.FIXED_TOKEN, chunk_size=512, overlap=50)
    chunks = chunker.chunk_pages(pages)
    print(f"  Created {len(chunks)} chunks")
    print(f"  Sample metadata: {chunks[0].metadata}")

    # Step 3: Upsert to Qdrant
    print("\n[3/4] Embedding and upserting to Qdrant Cloud...")
    print("  (This will take a few minutes for the first run)")
    vs = VectorStore()
    vs.upsert_chunks(chunks, batch_size=64)
    count = vs.count()
    print(f"  [OK] Qdrant collection '{vs.collection}' now has {count} vectors")

    # Step 4: Build and save BM25 index
    print("\n[4/4] Building BM25 index...")
    bm25 = BM25Store()
    bm25.index(chunks)
    bm25.save("data/bm25_index.json")
    print(f"  [OK] BM25 index built ({len(chunks)} documents) and saved to data/bm25_index.json")

    print(f"\n{'=' * 60}")
    print("Indexing complete! You can now run queries.")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
