from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from src.models.database import get_db
from src.config.settings import settings

def get_embedding_service():
    from src.services.embedding_service import EmbeddingService
    return EmbeddingService(model_name=settings.embedding_model)

def get_vector_store():
    from src.services.vector_store import VectorStore
    from src.services.embedding_service import EmbeddingService
    embedding_service = EmbeddingService(model_name=settings.embedding_model)
    return VectorStore(embeddings=embedding_service.embeddings)

def get_llm_service():
    from src.services.llm_service import LLMService
    return LLMService(model=settings.groq_model, api_key=settings.groq_api_key)

def get_document_processor():
    from src.services.document_processor import DocumentProcessor
    return DocumentProcessor(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap
    )