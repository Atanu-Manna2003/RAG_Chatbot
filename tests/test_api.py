import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_upload_document_invalid_type():
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.jpg", b"fake content", "image/jpeg")}
    )
    assert response.status_code == 400

def test_query_no_documents():
    response = client.post(
        "/api/v1/query",
        json={"question": "What is AI?"}
    )
    assert response.status_code == 200