"""Test chunking strategies produce expected output."""
from services.chunker import Chunker, ChunkStrategy
from services.loader import DocumentPage


def test_fixed_token_chunker_produces_chunks():
    page = DocumentPage(content="word " * 1000, metadata={"source": "test.pdf", "page_number": 1})
    chunker = Chunker(ChunkStrategy.FIXED_TOKEN, chunk_size=100, overlap=10)
    chunks = chunker.chunk_pages([page])
    assert len(chunks) > 1
    assert all(c.metadata["chunk_strategy"] == "fixed_token" for c in chunks)


def test_chunk_metadata_preserved():
    page = DocumentPage(content="Some test content.", metadata={"source": "doc.pdf", "page_number": 3})
    chunker = Chunker(ChunkStrategy.FIXED_TOKEN)
    chunks = chunker.chunk_pages([page])
    assert chunks[0].metadata["source"] == "doc.pdf"
    assert chunks[0].metadata["page_number"] == 3


def test_paragraph_chunker_splits_on_double_newline():
    text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
    page = DocumentPage(content=text, metadata={"source": "test.pdf", "page_number": 1})
    chunker = Chunker(ChunkStrategy.PARAGRAPH, chunk_size=10, overlap=0)
    chunks = chunker.chunk_pages([page])
    assert len(chunks) >= 1
    assert all(c.metadata["chunk_strategy"] == "paragraph" for c in chunks)


def test_recursive_character_chunker():
    page = DocumentPage(content="word " * 1000, metadata={"source": "test.pdf", "page_number": 1})
    chunker = Chunker(ChunkStrategy.RECURSIVE_CHARACTER, chunk_size=100, overlap=10)
    chunks = chunker.chunk_pages([page])
    assert len(chunks) >= 1
    assert all(c.metadata["chunk_strategy"] == "recursive_character" for c in chunks)


def test_chunk_token_count_present():
    page = DocumentPage(content="Hello world this is a test.", metadata={"source": "test.pdf", "page_number": 1})
    chunker = Chunker(ChunkStrategy.FIXED_TOKEN)
    chunks = chunker.chunk_pages([page])
    assert all("token_count" in c.metadata for c in chunks)
    assert all(c.metadata["token_count"] > 0 for c in chunks)
