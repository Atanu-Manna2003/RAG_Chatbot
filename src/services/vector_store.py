import logging
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
import os
from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings
from langchain_core.documents import Document as LangchainDocument



logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self, embeddings: Embeddings, persist_directory: str = "./storage/vector_store"):
        self.persist_directory = persist_directory
        os.makedirs(persist_directory, exist_ok=True)
        
        # Initialize LangChain Chroma
        self.vector_store = Chroma(
            persist_directory=persist_directory,
            embedding_function=embeddings,
            collection_name="document_chunks"
        )
        
        logger.info("Vector store initialized with LangChain Chroma")

    def add_documents(self, documents: List[Dict[str, Any]]) -> List[str]:
        """Add documents to vector store using LangChain"""
        try:
            # Convert to LangChain Document format
            langchain_docs = []
            for doc in documents:
                langchain_docs.append(
                    LangchainDocument(
                        page_content=doc["content"],
                        metadata={
                            "document_id": doc["document_id"],
                            "chunk_index": doc["chunk_index"],
                            "filename": doc["filename"],
                            "source": doc["filename"]
                        }
                    )
                )
            
            # Add to vector store
            ids = self.vector_store.add_documents(langchain_docs)
            
            logger.info(f"Added {len(documents)} documents to vector store")
            return ids
            
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {str(e)}")
            raise

    def search(self, query: str, top_k: int = 5, document_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Search for similar documents using LangChain with proper scoring"""
        try:
            # Build filter if document_ids provided
            filter_dict = None
            if document_ids:
                filter_dict = {"document_id": {"$in": document_ids}}
            
            # Use similarity_search_with_relevance_scores for better scoring
            results = self.vector_store.similarity_search_with_relevance_scores(
                query=query,
                k=top_k,
                filter=filter_dict
            )
            
            # Format results with proper scoring
            formatted_results = []
            for doc, score in results:
                # Chroma returns cosine similarity scores between 0-1
                # Higher score = more relevant
                formatted_results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": float(score),  # Direct similarity score
                    "similarity": float(score)
                })
            
            logger.info(f"Search returned {len(formatted_results)} results with scores: {[r['score'] for r in formatted_results]}")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching vector store: {str(e)}")
            raise

    def delete_documents(self, document_ids: List[str]):
        """Delete documents from vector store"""
        try:
            # Get all documents in the collection
            all_docs = self.vector_store.get()
            
            # Find IDs to delete
            ids_to_delete = []
            if all_docs and 'metadatas' in all_docs:
                for i, metadata in enumerate(all_docs['metadatas']):
                    if metadata and 'document_id' in metadata and metadata['document_id'] in document_ids:
                        if 'ids' in all_docs and i < len(all_docs['ids']):
                            ids_to_delete.append(all_docs['ids'][i])
            
            # Delete the documents
            if ids_to_delete:
                self.vector_store.delete(ids=ids_to_delete)
            
            logger.info(f"Deleted documents with IDs: {document_ids}")
        except Exception as e:
            logger.error(f"Error deleting documents from vector store: {str(e)}")
            raise

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store collection"""
        try:
            count = self.vector_store._collection.count()
            return {
                "total_chunks": count,
                "collection_name": "document_chunks",
                "vector_store": "ChromaDB with proper similarity scoring"
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {str(e)}")
            return {"error": str(e)}