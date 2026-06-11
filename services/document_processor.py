"""PDF Processing — load streams, extract text, and chunk."""
import fitz  # PyMuPDF
from services.chunker import Chunker, Chunk, ChunkStrategy
from dataclasses import dataclass

@dataclass
class SimplePage:
    content: str
    metadata: dict

class DocumentProcessor:
    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        self.chunker = Chunker(
            strategy=ChunkStrategy.FIXED_TOKEN,
            chunk_size=chunk_size,
            overlap=chunk_overlap,
        )

    def process_pdf_stream(self, file_bytes: bytes, filename: str) -> list[Chunk]:
        """Extract text from a PDF byte stream and chunk it."""
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
        except Exception as e:
            raise ValueError(f"Failed to read PDF: {e}")

        pages_to_chunk = []
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text()
            if not text.strip():
                continue

            metadata = {
                "source": f"uploads/{filename}",
                "page_number": page_num + 1,
            }
            pages_to_chunk.append(SimplePage(content=text, metadata=metadata))

        return self.chunker.chunk_pages(pages_to_chunk)
