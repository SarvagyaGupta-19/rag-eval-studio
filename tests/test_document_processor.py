"""Tests for the DocumentProcessor PDF upload feature."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.document_processor import DocumentProcessor

# A minimal valid PDF byte stream (1 page with "Hello World" text).
# Generated via: fitz.open(); page = doc.new_page(); page.insert_text((72,72), "Hello World"); doc.tobytes()
import fitz


def _make_tiny_pdf(text: str = "Hello World from test PDF.") -> bytes:
    """Create a minimal valid PDF in memory."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


class TestDocumentProcessor:

    def test_process_valid_pdf_stream(self):
        """A valid PDF byte stream is chunked successfully."""
        pdf_bytes = _make_tiny_pdf("Apple reported $394 billion in revenue for fiscal year 2024.")
        processor = DocumentProcessor()
        chunks = processor.process_pdf_stream(pdf_bytes, "test_report.pdf")

        assert len(chunks) >= 1
        assert any("394" in c.content for c in chunks)

    def test_process_empty_pdf_raises(self):
        """Corrupt/empty bytes should raise a ValueError."""
        processor = DocumentProcessor()
        with pytest.raises(ValueError, match="Failed to read PDF"):
            processor.process_pdf_stream(b"not a real pdf", "bad.pdf")

    def test_chunks_have_upload_source_metadata(self):
        """Chunks from uploaded PDFs should have 'uploads/' prefix in source."""
        pdf_bytes = _make_tiny_pdf("Test content for metadata check.")
        processor = DocumentProcessor()
        chunks = processor.process_pdf_stream(pdf_bytes, "quarterly_report.pdf")

        assert len(chunks) >= 1
        for chunk in chunks:
            assert chunk.metadata["source"].startswith("uploads/")
            assert "quarterly_report.pdf" in chunk.metadata["source"]
