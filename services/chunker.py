"""Multiple chunking strategies — configurable for comparison experiments."""
from dataclasses import dataclass
from enum import Enum
import tiktoken


class ChunkStrategy(Enum):
    FIXED_TOKEN = "fixed_token"
    RECURSIVE_CHARACTER = "recursive_character"
    PARAGRAPH = "paragraph"


@dataclass
class Chunk:
    content: str
    metadata: dict  # inherits from DocumentPage + adds chunk_index, chunk_strategy, token_count


class Chunker:
    def __init__(self, strategy: ChunkStrategy, chunk_size: int = 512, overlap: int = 50):
        self.strategy = strategy
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.tokenizer = tiktoken.get_encoding("cl100k_base")

    def chunk_pages(self, pages: list) -> list[Chunk]:
        """Chunk a list of DocumentPages."""
        all_chunks = []
        for page in pages:
            if self.strategy == ChunkStrategy.FIXED_TOKEN:
                chunks = self._fixed_token_chunk(page)
            elif self.strategy == ChunkStrategy.PARAGRAPH:
                chunks = self._paragraph_chunk(page)
            else:
                chunks = self._recursive_char_chunk(page)
            all_chunks.extend(chunks)
        return all_chunks

    def _fixed_token_chunk(self, page) -> list[Chunk]:
        tokens = self.tokenizer.encode(page.content)
        chunks = []
        start = 0
        idx = 0
        while start < len(tokens):
            end = min(start + self.chunk_size, len(tokens))
            chunk_tokens = tokens[start:end]
            text = self.tokenizer.decode(chunk_tokens)
            chunks.append(Chunk(
                content=text,
                metadata={
                    **page.metadata,
                    "chunk_index": idx,
                    "chunk_strategy": self.strategy.value,
                    "token_count": len(chunk_tokens),
                }
            ))
            start += self.chunk_size - self.overlap
            idx += 1
        return chunks

    def _paragraph_chunk(self, page) -> list[Chunk]:
        """Split on double newlines, merge small paragraphs."""
        paragraphs = [p.strip() for p in page.content.split("\n\n") if p.strip()]
        chunks, current, idx = [], "", 0
        for para in paragraphs:
            if len(self.tokenizer.encode(current + "\n\n" + para)) > self.chunk_size and current:
                token_count = len(self.tokenizer.encode(current))
                chunks.append(Chunk(
                    content=current.strip(),
                    metadata={**page.metadata, "chunk_index": idx,
                              "chunk_strategy": "paragraph", "token_count": token_count}
                ))
                current = para
                idx += 1
            else:
                current = current + "\n\n" + para if current else para
        if current.strip():
            token_count = len(self.tokenizer.encode(current))
            chunks.append(Chunk(
                content=current.strip(),
                metadata={**page.metadata, "chunk_index": idx,
                          "chunk_strategy": "paragraph", "token_count": token_count}
            ))
        return chunks

    def _recursive_char_chunk(self, page) -> list[Chunk]:
        """LangChain-style recursive character splitting."""
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size * 4,  # char-level approx
            chunk_overlap=self.overlap * 4,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        texts = splitter.split_text(page.content)
        chunks = []
        for idx, text in enumerate(texts):
            token_count = len(self.tokenizer.encode(text))
            chunks.append(Chunk(
                content=text,
                metadata={**page.metadata, "chunk_index": idx,
                          "chunk_strategy": "recursive_character", "token_count": token_count}
            ))
        return chunks
