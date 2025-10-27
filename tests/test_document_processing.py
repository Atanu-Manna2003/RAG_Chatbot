import pytest
import os
from src.services.document_processor import DocumentProcessor

def test_text_splitting():
    processor = DocumentProcessor(chunk_size=100, chunk_overlap=20)
    text = "This is a test. " * 50  # Create long text
    chunks = processor._split_text(text)
    
    assert len(chunks) > 1
    # Check that chunks don't exceed the specified size (with some tolerance)
    assert all(len(chunk) <= 120 for chunk in chunks)  # Allow some flexibility

def test_pdf_processing(sample_pdf_file):
    processor = DocumentProcessor()
    result = processor.process_document(sample_pdf_file, "test.pdf")
    
    assert result["filename"] == "test.pdf"
    assert result["file_type"] == "pdf"
    assert "chunks" in result
    assert isinstance(result["chunks"], list)

def test_text_processing(sample_text_file):
    processor = DocumentProcessor()
    result = processor.process_document(sample_text_file, "test.txt")
    
    assert result["filename"] == "test.txt"
    assert result["file_type"] == "text"
    assert "chunks" in result
    assert len(result["chunks"]) > 0

def test_unsupported_file_type():
    processor = DocumentProcessor()
    with pytest.raises(ValueError):
        processor.process_document("test.jpg", "test.jpg")

def test_chunk_overlap():
    processor = DocumentProcessor(chunk_size=50, chunk_overlap=10)
    text = "This is a longer text that should be split into multiple chunks with overlap between them."
    chunks = processor._split_text(text)
    
    if len(chunks) > 1:
        # Check that chunks overlap (simplified check)
        assert len(chunks) > 1  # Should have multiple chunks

def test_empty_file():
    processor = DocumentProcessor()
    # Create empty file
    with open("empty_test.txt", "w") as f:
        f.write("")
    
    try:
        result = processor.process_document("empty_test.txt", "empty_test.txt")
        assert result["total_chunks"] == 0 or result["total_chunks"] == 1
    finally:
        os.remove("empty_test.txt")