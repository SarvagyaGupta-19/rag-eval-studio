"""PDF Processing — load streams, extract text, and chunk."""
import fitz  # PyMuPDF
from services.chunker import Chunker, Chunk


class DocumentProcessor:
    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        self.chunker = Chunker(
            strategy="fixed_token",
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    def process_pdf_stream(self, file_bytes: bytes, filename: str) -> list[Chunk]:
        """Extract text from a PDF byte stream and chunk it."""
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
        except Exception as e:
            raise ValueError(f"Failed to read PDF: {e}")

        all_chunks = []
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text()
            if not text.strip():
                continue

            # Standardize metadata matching our ingestion script
            metadata = {
                "source": f"uploads/{filename}",
                "page_number": page_num + 1,
            }

            chunks = self.chunker.chunk(text, metadata=metadata)
            all_chunks.extend(chunks)

        return all_chunks
