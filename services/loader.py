"""PDF loading with page-level metadata extraction."""
import fitz  # PyMuPDF
from dataclasses import dataclass
from infra.s3_helpers import download_document, list_documents


@dataclass
class DocumentPage:
    content: str
    metadata: dict  # source_key, page_number, total_pages, char_count


def load_pdf_from_s3(s3_key: str) -> list[DocumentPage]:
    """Load a PDF from S3 and extract text with metadata."""
    pdf_bytes = download_document(s3_key)
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages = []
    for page_num, page in enumerate(doc):
        text = page.get_text("text").strip()
        if text:  # skip blank pages
            pages.append(DocumentPage(
                content=text,
                metadata={
                    "source": s3_key,
                    "page_number": page_num + 1,
                    "total_pages": len(doc),
                    "char_count": len(text),
                }
            ))
    doc.close()
    return pages


def load_all_documents() -> list[DocumentPage]:
    """Load all PDFs from S3."""
    keys = list_documents()
    all_pages = []
    for key in keys:
        all_pages.extend(load_pdf_from_s3(key))
    return all_pages
