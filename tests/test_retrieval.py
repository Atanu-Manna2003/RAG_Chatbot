import pytest
from unittest.mock import Mock, patch
from src.services.vector_store import VectorStore
from src.services.embedding_service import EmbeddingService

@pytest.fixture
def mock_embeddings():
    embeddings = Mock()
    embeddings.embed_documents.return_value = [[0.1] * 384]  # Mock embedding
    return embeddings

@pytest.fixture
def vector_store(mock_embeddings):
    with patch('src.services.vector_store.Chroma') as mock_chroma:
        with patch('src.services.vector_store.chromadb.PersistentClient'):
            store = VectorStore(embeddings=mock_embeddings)
            store.vector_store = mock_chroma.return_value
            return store

def test_add_documents(vector_store):
    documents = [
        {
            "content": "Test document content 1",
            "document_id": "doc1",
            "chunk_index": 0,
            "filename": "test1.pdf"
        },
        {
            "content": "Test document content 2", 
            "document_id": "doc1",
            "chunk_index": 1,
            "filename": "test1.pdf"
        }
    ]
    
    with patch.object(vector_store.vector_store, 'add_documents') as mock_add:
        mock_add.return_value = ["id1", "id2"]
        result = vector_store.add_documents(documents)
        
        assert result == ["id1", "id2"]
        mock_add.assert_called_once()

def test_search(vector_store):
    query = "test query"
    
    mock_doc = Mock()
    mock_doc.page_content = "Test content"
    mock_doc.metadata = {"document_id": "doc1", "chunk_index": 0}
    
    with patch.object(vector_store.vector_store, 'similarity_search_with_score') as mock_search:
        mock_search.return_value = [(mock_doc, 0.1)]
        
        results = vector_store.search(query, top_k=3)
        
        assert len(results) == 1
        assert results[0]["content"] == "Test content"
        assert results[0]["score"] == 0.9  # 1 - distance

def test_search_with_filter(vector_store):
    query = "test query"
    document_ids = ["doc1", "doc2"]
    
    with patch.object(vector_store.vector_store, 'similarity_search_with_score') as mock_search:
        vector_store.search(query, top_k=5, document_ids=document_ids)
        
        # Check that filter was passed
        call_args = mock_search.call_args
        assert call_args[1]['filter'] == {"document_id": {"$in": document_ids}}

def test_delete_documents(vector_store):
    document_ids = ["doc1", "doc2"]
    
    with patch('src.services.vector_store.chromadb.PersistentClient') as mock_client:
        mock_collection = Mock()
        mock_client.return_value.get_collection.return_value = mock_collection
        
        vector_store.delete_documents(document_ids)
        
        mock_collection.delete.assert_called_once_with(
            where={"document_id": {"$in": document_ids}}
        )