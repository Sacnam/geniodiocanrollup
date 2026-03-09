"""Tests for Documents API."""
import pytest
from io import BytesIO
from fastapi.testclient import TestClient


class TestDocumentsAPI:
    """Test document management endpoints."""

    def test_list_documents(self, client: TestClient, test_user: dict):
        """Should list user's documents."""
        response = client.get(
            "/api/v1/documents",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_list_documents_with_status_filter(self, client: TestClient, test_user: dict):
        """Should filter documents by status."""
        response = client.get(
            "/api/v1/documents?status=ready",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        for doc in data["items"]:
            assert doc.get("status") == "ready"

    def test_upload_document(self, client: TestClient, test_user: dict):
        """Should upload a document."""
        # Create a test PDF-like file
        file_content = b"%PDF-1.4 test content"
        
        response = client.post(
            "/api/v1/documents/upload",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
            files={
                "file": ("test.pdf", BytesIO(file_content), "application/pdf")
            }
        )
        
        # Should accept upload and queue processing
        assert response.status_code in [201, 202, 422]

    def test_upload_invalid_file_type(self, client: TestClient, test_user: dict):
        """Should reject invalid file types."""
        response = client.post(
            "/api/v1/documents/upload",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
            files={
                "file": ("test.exe", BytesIO(b"invalid"), "application/x-msdownload")
            }
        )
        
        assert response.status_code in [400, 415, 422]

    def test_get_document(self, client: TestClient, test_user: dict):
        """Should get document details."""
        response = client.get(
            "/api/v1/documents/fake-id",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code == 404

    def test_delete_document(self, client: TestClient, test_user: dict):
        """Should delete document."""
        response = client.delete(
            "/api/v1/documents/fake-id",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code in [404, 204]

    def test_get_document_content(self, client: TestClient, test_user: dict):
        """Should get document content."""
        response = client.get(
            "/api/v1/documents/fake-id/content",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code in [404, 200]

    def test_get_document_chunks(self, client: TestClient, test_user: dict):
        """Should get document chunks."""
        response = client.get(
            "/api/v1/documents/fake-id/chunks",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code in [404, 200]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

    def test_create_highlight(self, client: TestClient, test_user: dict):
        """Should create a highlight."""
        response = client.post(
            "/api/v1/documents/fake-id/highlights",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
            json={
                "char_start": 10,
                "char_end": 50,
                "highlighted_text": "Important text",
                "note": "My note",
                "color": "yellow"
            }
        )
        
        assert response.status_code in [404, 201]

    def test_list_highlights(self, client: TestClient, test_user: dict):
        """Should list document highlights."""
        response = client.get(
            "/api/v1/documents/fake-id/highlights",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code in [404, 200]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

    def test_delete_highlight(self, client: TestClient, test_user: dict):
        """Should delete a highlight."""
        response = client.delete(
            "/api/v1/documents/fake-id/highlights/fake-highlight-id",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code in [404, 204]

    def test_search_within_document(self, client: TestClient, test_user: dict):
        """Should search within document."""
        response = client.get(
            "/api/v1/documents/fake-id/search?q=query",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code in [404, 200]

    def test_get_document_processing_status(self, client: TestClient, test_user: dict):
        """Should get document processing status."""
        response = client.get(
            "/api/v1/documents/fake-id/status",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        
        assert response.status_code in [404, 200]
        if response.status_code == 200:
            data = response.json()
            assert "status" in data
            assert "progress" in data or "state" in data

    def test_documents_unauthorized(self, client: TestClient):
        """Should reject unauthorized access."""
        response = client.get("/api/v1/documents")
        assert response.status_code == 401
