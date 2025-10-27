import os
import logging
from typing import List, Dict, Any
from PyPDF2 import PdfReader
from docx import Document as DocxDocument
import chardet
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""]
        )
        
    def process_document(self, file_path: str, filename: str) -> Dict[str, Any]:
        """Process a document and return chunks and metadata"""
        file_ext = os.path.splitext(filename)[1].lower()
        
        try:
            if file_ext == '.pdf':
                return self._process_pdf(file_path, filename)
            elif file_ext in ['.docx', '.doc']:
                return self._process_docx(file_path, filename)
            elif file_ext in ['.txt', '.md']:
                return self._process_text(file_path, filename)
            else:
                raise ValueError(f"Unsupported file type: {file_ext}")
        except Exception as e:
            logger.error(f"Error processing document {filename}: {str(e)}")
            raise

    def _process_pdf(self, file_path: str, filename: str) -> Dict[str, Any]:
        """Process PDF document using PyPDF2"""
        reader = PdfReader(file_path)
        text_chunks = []
        page_count = len(reader.pages)
        
        full_text = ""
        for page_num, page in enumerate(reader.pages):
            try:
                page_text = page.extract_text()
                if page_text.strip():
                    full_text += f"Page {page_num + 1}:\n{page_text}\n\n"
            except Exception as e:
                logger.warning(f"Error extracting text from page {page_num + 1}: {str(e)}")
                continue
        
        # Use LangChain text splitter
        chunks = self.text_splitter.split_text(full_text)
        
        return {
            "filename": filename,
            "file_type": "pdf",
            "page_count": page_count,
            "chunks": chunks,
            "total_chunks": len(chunks)
        }

    def _process_docx(self, file_path: str, filename: str) -> Dict[str, Any]:
        """Process DOCX document"""
        doc = DocxDocument(file_path)
        full_text = ""
        
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                full_text += paragraph.text + "\n"
        
        # Use LangChain text splitter
        chunks = self.text_splitter.split_text(full_text)
        
        return {
            "filename": filename,
            "file_type": "docx",
            "page_count": None,
            "chunks": chunks,
            "total_chunks": len(chunks)
        }

    def _process_text(self, file_path: str, filename: str) -> Dict[str, Any]:
        """Process text document"""
        with open(file_path, 'rb') as file:
            raw_data = file.read()
            encoding = chardet.detect(raw_data)['encoding'] or 'utf-8'
            
        with open(file_path, 'r', encoding=encoding) as file:
            full_text = file.read()
        
        # Use LangChain text splitter
        chunks = self.text_splitter.split_text(full_text)
        
        return {
            "filename": filename,
            "file_type": "text",
            "page_count": None,
            "chunks": chunks,
            "total_chunks": len(chunks)
        }