from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class DocumentUpload(BaseModel):
    filename: str
    file_size: int
    file_type: str

class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_size: int
    file_type: str
    page_count: Optional[int]
    chunk_count: Optional[int]
    processed: bool
    created_at: datetime

class QueryRequest(BaseModel):
    question: str
    document_ids: Optional[List[str]] = None
    top_k: int = 5

class QueryResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    confidence: float
    model_used: str

class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: datetime

class ErrorResponse(BaseModel):
    error: str
    details: Optional[str] = None