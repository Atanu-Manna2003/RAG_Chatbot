import os
import uuid
from fastapi import UploadFile, HTTPException
from typing import List
import magic
from src.config.settings import settings

# Allowed file types and their MIME types
ALLOWED_FILE_TYPES = {
    'application/pdf': '.pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
    'text/plain': '.txt',
    'text/markdown': '.md'
}

ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.doc', '.txt', '.md'}

def save_uploaded_file(file: UploadFile) -> str:
    """Save uploaded file to storage directory and return file path"""
    try:
        # Create storage directory if it doesn't exist
        os.makedirs("storage/documents", exist_ok=True)
        
        # Validate file type
        validate_file_type(file)
        
        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail="Unsupported file extension")
            
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join("storage/documents", unique_filename)
        
        # Save file
        with open(file_path, "wb") as buffer:
            content = file.file.read()
            buffer.write(content)
        
        return file_path
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")

def validate_file(file: UploadFile):
    """Validate uploaded file for size and type"""
    # Check file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Seek back to start
    
    if file_size > settings.max_file_size:
        raise HTTPException(status_code=400, detail=f"File too large. Maximum size is {settings.max_file_size} bytes")
    
    if file_size == 0:
        raise HTTPException(status_code=400, detail="File is empty")
    
    # Validate file type
    validate_file_type(file)

def validate_file_type(file: UploadFile):
    """Validate file type using python-magic"""
    try:
        # Read first 2048 bytes for MIME type detection
        file_content = file.file.read(2048)
        file.file.seek(0)  # Reset file pointer
        
        mime = magic.Magic(mime=True)
        mime_type = mime.from_buffer(file_content)
        
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        # Check if MIME type is allowed
        if mime_type not in ALLOWED_FILE_TYPES:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {mime_type}")
        
        # Check if extension matches MIME type
        expected_extension = ALLOWED_FILE_TYPES.get(mime_type)
        if expected_extension and not file_extension.endswith(expected_extension):
            raise HTTPException(
                status_code=400, 
                detail=f"File extension {file_extension} does not match MIME type {mime_type}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        # If magic fails, fall back to content type validation
        if file.content_type not in ALLOWED_FILE_TYPES:
            raise HTTPException(status_code=400, detail="Unsupported file type")
        file.file.seek(0)  # Reset file pointer

def get_file_extension(filename: str) -> str:
    """Get file extension in lowercase"""
    return os.path.splitext(filename)[1].lower()

def is_file_type_allowed(filename: str) -> bool:
    """Check if file type is allowed based on extension"""
    extension = get_file_extension(filename)
    return extension in ALLOWED_EXTENSIONS

def cleanup_file(file_path: str):
    """Delete file from storage"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        # Log warning but don't raise exception
        print(f"Warning: Could not delete file {file_path}: {str(e)}")