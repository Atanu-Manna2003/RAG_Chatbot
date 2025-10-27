from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query, BackgroundTasks
from sqlalchemy.orm import Session
import os
from typing import List, Optional
import logging

from src.models.database import get_db, Document
from src.models.schemas import (
    DocumentResponse, QueryRequest, QueryResponse, 
    HealthResponse
)
from src.services.document_processor import DocumentProcessor
from src.services.embedding_service import EmbeddingService
from src.services.vector_store import VectorStore
from src.services.llm_service import LLMService
from src.config.settings import settings
from src.utils.file_handlers import save_uploaded_file, validate_file

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize services
document_processor = DocumentProcessor()
embedding_service = EmbeddingService(model_name=settings.embedding_model)
vector_store = VectorStore(embeddings=embedding_service.embeddings)
llm_service = LLMService(model=settings.groq_model, api_key=settings.groq_api_key)

def process_document_background(document_id: str, file_path: str, filename: str):
    """Background task to process document - metadata only in database, chunks in vector store"""
    try:
        from src.models.database import SessionLocal
        db = SessionLocal()
        
        logger.info(f"Starting to process document: {filename}")
        
        # Process document
        result = document_processor.process_document(file_path, filename)
        logger.info(f"Document processed: {len(result['chunks'])} chunks created")
        
        # Prepare documents for vector store
        documents_for_store = [
            {
                "content": chunk,
                "document_id": document_id,
                "chunk_index": i,
                "filename": filename
            }
            for i, chunk in enumerate(result["chunks"])
        ]
        
        # Add to vector store ONLY (no database storage for chunks)
        logger.info("Adding documents to vector store...")
        vector_store.add_documents(documents_for_store)
        logger.info("Documents added to vector store successfully")
        
        # Update document record with metadata only
        document = db.query(Document).filter(Document.id == document_id).first()
        if document:
            document.page_count = result.get("page_count")
            document.chunk_count = len(result["chunks"])  # Store count for reference
            document.processed = True
            db.commit()
            logger.info(f"Successfully processed document: {filename} with {len(result['chunks'])} chunks (metadata in database, chunks in vector store)")
        else:
            logger.error(f"Document {document_id} not found in database")
            
    except Exception as e:
        logger.error(f"Error processing document {document_id}: {str(e)}", exc_info=True)
        # Update document status to indicate failure
        try:
            document = db.query(Document).filter(Document.id == document_id).first()
            if document:
                document.processed = False
                db.commit()
                logger.info(f"Marked document {document_id} as failed")
        except Exception as db_error:
            logger.error(f"Error updating document status: {str(db_error)}")
    finally:
        db.close()

@router.post("/documents/upload", response_model=DocumentResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload and process a document - store metadata only in database"""
    try:
        logger.info(f"Received upload request for file: {file.filename}")
        
        # Validate file
        validate_file(file)
        logger.info("File validation passed")
        
        # Save file
        file_path = save_uploaded_file(file)
        logger.info(f"File saved to: {file_path}")
        
        # Create document record (metadata only)
        document = Document(
            filename=file.filename,
            file_path=file_path,
            file_size=os.path.getsize(file_path),
            file_type=file.content_type or "unknown"
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        logger.info(f"Document metadata stored with ID: {document.id}")
        
        # Process document in background (chunks go to vector store only)
        background_tasks.add_task(
            process_document_background, 
            document.id, 
            file_path, 
            file.filename
        )
        logger.info("Background processing task added")
        
        return DocumentResponse(
            id=document.id,
            filename=document.filename,
            file_size=document.file_size,
            file_type=document.file_type,
            page_count=document.page_count,
            chunk_count=document.chunk_count,
            processed=document.processed,
            created_at=document.created_at
        )
        
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error uploading document: {str(e)}")

@router.get("/documents", response_model=List[DocumentResponse])
async def get_documents(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get list of processed documents (metadata only)"""
    try:
        documents = db.query(Document).offset(skip).limit(limit).all()
        logger.info(f"Retrieved {len(documents)} documents from database")
        return [
            DocumentResponse(
                id=doc.id,
                filename=doc.filename,
                file_size=doc.file_size,
                file_type=doc.file_type,
                page_count=doc.page_count,
                chunk_count=doc.chunk_count,
                processed=doc.processed,
                created_at=doc.created_at
            )
            for doc in documents
        ]
    except Exception as e:
        logger.error(f"Error retrieving documents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving documents: {str(e)}")

@router.post("/query", response_model=QueryResponse)
async def query_documents(
    query_request: QueryRequest,
    db: Session = Depends(get_db)
):
    """Query the RAG system using Groq LLM"""
    try:
        logger.info(f"Received query: {query_request.question}")
        
        # Search vector store using text query
        search_results = vector_store.search(
            query=query_request.question,
            top_k=query_request.top_k,
            document_ids=query_request.document_ids
        )
        logger.info(f"Vector search returned {len(search_results)} results")
        
        if not search_results:
            logger.info("No relevant documents found for query")
            return QueryResponse(
                answer="I cannot find relevant information in the provided documents to answer this question.",
                sources=[],
                confidence=0.0,
                model_used=settings.groq_model
            )
        
        # Generate response using Groq LLM
        logger.info("Generating response with Groq LLM...")
        response = await llm_service.agenerate_response(
            question=query_request.question,
            context_chunks=search_results
        )
        logger.info("Response generated successfully")
        
        return QueryResponse(**response)
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    db: Session = Depends(get_db)
):
    """Delete a document and its chunks from the system"""
    try:
        logger.info(f"Deleting document: {document_id}")
        
        # Find document
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            logger.warning(f"Document {document_id} not found")
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Delete from vector store
        vector_store.delete_documents([document_id])
        logger.info("Document chunks deleted from vector store")
        
        # Delete document record (metadata only)
        db.delete(document)
        db.commit()
        logger.info("Document metadata deleted from database")
        
        # Delete file from storage
        try:
            if os.path.exists(document.file_path):
                os.remove(document.file_path)
                logger.info(f"File deleted: {document.file_path}")
        except Exception as e:
            logger.warning(f"Could not delete file {document.file_path}: {str(e)}")
        
        return {"message": f"Document {document_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")

@router.get("/vector-store/stats")
async def get_vector_store_stats():
    """Get vector store statistics"""
    try:
        stats = vector_store.get_collection_stats()
        logger.info(f"Vector store stats: {stats}")
        return {"vector_store": stats}
    except Exception as e:
        logger.error(f"Error getting vector store stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting vector store stats: {str(e)}")

@router.get("/debug/documents")
async def debug_documents(db: Session = Depends(get_db)):
    """Debug endpoint to see all documents in database (metadata only)"""
    try:
        documents = db.query(Document).all()
        return {
            "total_documents": len(documents),
            "storage_type": "Metadata only (chunks stored in vector store)",
            "documents": [
                {
                    "id": doc.id,
                    "filename": doc.filename,
                    "file_size": doc.file_size,
                    "file_type": doc.file_type,
                    "processed": doc.processed,
                    "page_count": doc.page_count,
                    "chunk_count": doc.chunk_count,
                    "created_at": doc.created_at.isoformat() if doc.created_at else None,
                    "file_path": doc.file_path
                }
                for doc in documents
            ]
        }
    except Exception as e:
        logger.error(f"Error getting documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/debug/database-stats")
async def debug_database_stats(db: Session = Depends(get_db)):
    """Debug endpoint to see database statistics"""
    try:
        total_documents = db.query(Document).count()
        processed_documents = db.query(Document).filter(Document.processed == True).count()
        failed_documents = db.query(Document).filter(Document.processed == False).count()
        
        # Calculate total chunks from processed documents
        total_chunks = sum(doc.chunk_count or 0 for doc in db.query(Document).filter(Document.processed == True).all())
        
        return {
            "database_stats": {
                "total_documents": total_documents,
                "processed_documents": processed_documents,
                "failed_documents": failed_documents,
                "total_chunks_in_vector_store": total_chunks,
                "database_file": "rag_pipeline.db",
                "storage_architecture": "Metadata in SQLite, chunks in ChromaDB vector store"
            }
        }
    except Exception as e:
        logger.error(f"Error getting database stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/debug/document/{document_id}")
async def debug_document_detail(document_id: str, db: Session = Depends(get_db)):
    """Debug endpoint to see detailed information about a specific document"""
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {
            "document": {
                "id": document.id,
                "filename": document.filename,
                "file_size": document.file_size,
                "file_type": document.file_type,
                "processed": document.processed,
                "page_count": document.page_count,
                "chunk_count": document.chunk_count,
                "file_path": document.file_path,
                "created_at": document.created_at.isoformat() if document.created_at else None,
                "updated_at": document.updated_at.isoformat() if document.updated_at else None
            },
            "storage_info": {
                "metadata_location": "SQLite database",
                "chunks_location": "ChromaDB vector store",
                "file_location": "storage/documents/ directory"
            }
        }
    except Exception as e:
        logger.error(f"Error getting document details: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check() -> HealthResponse:
    """Health check endpoint"""
    from datetime import datetime
    return HealthResponse(
        status="healthy",
        service="RAG Pipeline API with Groq & SQLite",
        timestamp=datetime.utcnow()
    )