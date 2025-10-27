import pytest
from unittest.mock import Mock, patch
from src.services.llm_service import LLMService

@pytest.fixture
def mock_llm_service():
    with patch('src.services.llm_service.ChatGroq') as mock_groq:
        mock_llm = Mock()
        mock_groq.return_value = mock_llm
        service = LLMService(api_key="test-key")
        service.llm = mock_llm
        return service, mock_llm

def test_llm_service_initialization(mock_llm_service):
    service, mock_llm = mock_llm_service
    assert service.model_name == "llama-3.3-70b-versatile"
    assert service.llm is not None

@pytest.mark.asyncio
async def test_generate_response(mock_llm_service):
    service, mock_llm = mock_llm_service
    
    # Mock the chain
    mock_chain = Mock()
    mock_chain.ainvoke.return_value = "This is a test response."
    
    with patch('src.services.llm_service.ChatPromptTemplate') as mock_prompt:
        with patch('src.services.llm_service.StrOutputParser') as mock_parser:
            mock_prompt.from_messages.return_value = mock_chain
            mock_parser.return_value = mock_chain
            
            context_chunks = [
                {
                    "content": "Test content 1",
                    "score": 0.9,
                    "metadata": {"document_id": "1", "chunk_index": 0}
                }
            ]
            
            response = await service.agenerate_response(
                question="Test question",
                context_chunks=context_chunks
            )
            
            assert response["answer"] == "This is a test response."
            assert response["confidence"] == 0.9
            assert response["model_used"] == "llama-3.3-70b-versatile"