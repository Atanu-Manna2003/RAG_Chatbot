import logging
from typing import List
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.embeddings import Embeddings


logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.embeddings = self._initialize_embeddings()
        logger.info(f"Initialized embedding service with model: {model_name}")

    def _initialize_embeddings(self) -> Embeddings:
        """Initialize HuggingFace embeddings"""
        try:
            model_kwargs = {'device': 'cpu'}
            encode_kwargs = {'normalize_embeddings': True}
            
            embeddings = HuggingFaceEmbeddings(
                model_name=self.model_name,
                model_kwargs=model_kwargs,
                encode_kwargs=encode_kwargs
            )
            return embeddings
        except Exception as e:
            logger.error(f"Error initializing embeddings: {str(e)}")
            raise

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts"""
        try:
            return self.embeddings.embed_documents(texts)
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise

    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings"""
        # Test with a small text to get embedding dimension
        test_embedding = self.get_embeddings(["test"])[0]
        return len(test_embedding)