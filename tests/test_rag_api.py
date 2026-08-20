from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_upload_processes_document_without_claiming_persistence():
    processed = {
        "metadata": {"document_id": "doc-1", "filename": "notes.txt", "chunk_count": 2},
        "chunks": [{"text": "one"}, {"text": "two"}],
    }
    with patch("main.process_document", new=AsyncMock(return_value=processed)):
        response = client.post(
            "/documents/upload", data={"user_id": "user-1"},
            files={"file": ("notes.txt", b"hello", "text/plain")},
        )
    assert response.status_code == 200
    assert response.json() == {
        "document_id": "doc-1", "filename": "notes.txt",
        "chunks_created": 2, "persisted": False,
    }


def test_upload_unsupported_type():
    from core.exceptions import UnsupportedDocumentTypeError

    with patch("main.process_document", new=AsyncMock(
        side_effect=UnsupportedDocumentTypeError("Unsupported")
    )):
        response = client.post(
            "/documents/upload", data={"user_id": "user-1"},
            files={"file": ("bad.exe", b"bad", "application/octet-stream")},
        )
    assert response.status_code == 415


def test_persistence_dependent_routes_are_not_exposed():
    paths = app.openapi()["paths"]
    assert "/rag/query" not in paths
    assert "/documents/{user_id}" not in paths
    assert "/documents/{document_id}" not in paths
