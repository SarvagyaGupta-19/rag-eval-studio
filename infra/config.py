"""Centralized configuration — single source of truth for all settings."""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # AWS
    AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
    S3_BUCKET = os.getenv("S3_BUCKET_NAME")

    # Embedding
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", 384))

    # Chunking defaults
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 512))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 50))

    # Qdrant
    QDRANT_URL = os.getenv("QDRANT_URL")
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
    QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "rag_docs")

    # Groq
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")

    # LangSmith — auto-enabled via env vars
