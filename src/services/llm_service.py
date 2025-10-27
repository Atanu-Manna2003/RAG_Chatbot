import logging
from typing import List, Dict, Any, Optional
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser


logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self, model: str = "llama-3.3-70b-versatile", api_key: Optional[str] = None):
        self.model_name = model
        self.api_key = api_key
        
        if not self.api_key:
            raise ValueError("Groq API key is required")
            
        self.llm = self._initialize_llm()
        logger.info(f"Initialized LLM service with model: {model}")

    def _initialize_llm(self) -> ChatGroq:
        """Initialize Groq LLM"""
        try:
            return ChatGroq(
                groq_api_key=self.api_key,
                model_name=self.model_name,
                temperature=0.1,
                max_tokens=1000
            )
        except Exception as e:
            logger.error(f"Error initializing Groq LLM: {str(e)}")
            raise

    async def agenerate_response(self, question: str, context_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate response using Groq LLM with context"""
        try:
            # Filter out low-relevance chunks and fix negative scores
            relevant_chunks = []
            for chunk in context_chunks:
                # Fix negative scores - ensure they're positive
                score = max(chunk.get('score', 0), 0)  # Ensure score is not negative
                if score > 0.1:  # Only use chunks with reasonable relevance
                    chunk['score'] = score
                    relevant_chunks.append(chunk)
            
            if not relevant_chunks:
                relevant_chunks = context_chunks[:3]  # Use top 3 if none meet threshold
                # Fix scores for the fallback chunks
                for chunk in relevant_chunks:
                    chunk['score'] = max(chunk.get('score', 0), 0.3)
                
            logger.info(f"Using {len(relevant_chunks)} relevant chunks for response generation")

            # Prepare context from retrieved chunks
            context = "\n\n".join([
                f"--- Document: {chunk['metadata'].get('filename', 'Unknown')} ---\n{chunk['content']}"
                for chunk in relevant_chunks
            ])
            
            # Create clean prompt template
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a helpful AI assistant that answers questions based ONLY on the provided document context.

IMPORTANT INSTRUCTIONS:
1. Answer the question concisely using ONLY the information from the provided context
2. Do not mention that you are using context or documents in your answer
3. If the context doesn't contain information to answer the question, say "I don't have information about that in the documents."
4. Be natural and conversational in your response
5. Do not include citations, references, or source mentions in your main answer
6. If different documents have conflicting information, provide the most relevant information

CONTEXT:
{context}

QUESTION: {question}

Provide a clear, concise answer:""")
            ])
            
            # Create chain
            chain = prompt | self.llm | StrOutputParser()
            
            # Generate response
            answer = await chain.ainvoke({
                "context": context,
                "question": question
            })
            
            # Clean up the answer - remove any source references
            clean_answer = self._clean_answer(answer)
            
            # Calculate average confidence
            avg_confidence = sum(chunk['score'] for chunk in relevant_chunks) / len(relevant_chunks) if relevant_chunks else 0
            
            return {
                "answer": clean_answer,
                "sources": [
                    {
                        "content": chunk["content"][:150] + "..." if len(chunk["content"]) > 150 else chunk["content"],
                        "metadata": chunk["metadata"],
                        "score": chunk["score"],
                        "relevance_percentage": f"{(chunk['score'] * 100):.1f}%"
                    }
                    for chunk in relevant_chunks
                ],
                "confidence": avg_confidence,
                "model_used": self.model_name,
                "chunks_used": len(relevant_chunks)
            }
            
        except Exception as e:
            logger.error(f"Error generating LLM response: {str(e)}")
            raise

    def _clean_answer(self, answer: str) -> str:
        """Remove source references from the answer"""
        import re
        # Remove phrases that reference sources
        patterns = [
            r'According to (?:the |this )?document[^.]*\.',
            r'Based on (?:the |this )?(?:context|document|information provided)[^.]*\.',
            r'As mentioned in (?:the |this )?(?:document|source|context)[^.]*\.',
            r'In the (?:provided |given )?(?:context|document)[^.]*\.',
            r'\[.*?\]',  # Remove citation brackets
            r'\(Source:.*?\)',  # Remove source references
        ]
        
        clean_answer = answer
        for pattern in patterns:
            clean_answer = re.sub(pattern, '', clean_answer, flags=re.IGNORECASE)
        
        # Clean up extra spaces and periods
        clean_answer = re.sub(r'\s+', ' ', clean_answer)
        clean_answer = re.sub(r'\.\.+', '.', clean_answer)
        clean_answer = clean_answer.strip()
        
        # Ensure the answer ends with proper punctuation
        if clean_answer and not clean_answer.endswith(('.', '!', '?')):
            clean_answer += '.'
            
        return clean_answer