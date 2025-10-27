from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database - SQLite by default
    database_url: str = "sqlite:///./rag_pipeline.db"
    
    # Redis (optional for development)
    redis_url: Optional[str] = None
    
    # Groq
    groq_api_key: Optional[str] = None
    groq_model: str = "llama-3.3-70b-versatile"
    
    # Embeddings
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Vector Database
    vector_store_path: str = "./storage/vector_store"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    
    # RAG Configuration
    top_k: int = 5
    temperature: float = 0.1
    max_tokens: int = 1000
    
    # API
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    max_documents: int = 20
    
    class Config:
        env_file = ".env"

settings = Settings()