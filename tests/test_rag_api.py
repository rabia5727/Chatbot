from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from main import app
from config.settings import get_settings

client = TestClient(app)


def test_upload_valid_txt():
    result = {"document_id": "doc-1", "filename": "notes.txt", "chunks_created": 2}
    with patch("main.ingest_document", new=AsyncMock(return_value=result)) as ingest:
        response = client.post(
            "/documents/upload",
            data={"user_id": "user-1"},
            files={"file": ("notes.txt", b"hello", "text/plain")},
        )
    assert response.status_code == 200
    assert response.json() == result
    assert ingest.await_args.kwargs["file_bytes"] == b"hello"


def test_upload_unsupported_type():
    from core.exceptions import UnsupportedDocumentTypeError

    with patch("main.ingest_document", new=AsyncMock(
        side_effect=UnsupportedDocumentTypeError("Only PDF, DOCX, and TXT documents are supported.")
    )):
        response = client.post(
            "/documents/upload", data={"user_id": "user-1"},
            files={"file": ("bad.exe", b"bad", "application/octet-stream")},
        )
    assert response.status_code == 415


def test_query_list_and_delete_routes():
    query_result = {"answer": "grounded", "sources": [{"document_id": "doc-1"}]}
    with patch("main.query_documents", new=AsyncMock(return_value=query_result)):
        response = client.post("/rag/query", json={
            "user_id": "user-1", "question": "What?", "document_id": "doc-1"
        })
    assert response.status_code == 200
    assert response.json() == query_result

    with patch("main.list_documents", new=AsyncMock(return_value=[{"document_id": "doc-1"}])):
        response = client.get("/documents/user-1")
    assert response.json()["documents"][0]["document_id"] == "doc-1"

    with patch("main.delete_document", new=AsyncMock(return_value=True)):
        response = client.delete("/documents/doc-1", params={"user_id": "user-1"})
    assert response.status_code == 200
    assert response.json()["deleted"] is True


def test_complete_rag_route_flow_with_providers_mocked(tmp_path, monkeypatch):
    monkeypatch.setenv("RAG_DB_PATH", str(tmp_path / "api-rag.db"))
    monkeypatch.setenv("RAG_CHUNK_SIZE", "100")
    monkeypatch.setenv("RAG_CHUNK_OVERLAP", "10")
    get_settings.cache_clear()
    model = MagicMock()
    model.generate = AsyncMock(return_value=SimpleNamespace(candidates=[SimpleNamespace(
        content=SimpleNamespace(parts=[SimpleNamespace(text="The policy allows remote work.")])
    )]))
    try:
        with patch("rag.rag_service.embed_texts", new=AsyncMock(return_value=[[1.0, 0.0]])):
            uploaded = client.post(
                "/documents/upload", data={"user_id": "integration-user"},
                files={"file": ("policy.txt", b"The policy allows remote work.", "text/plain")},
            )
        assert uploaded.status_code == 200
        document_id = uploaded.json()["document_id"]

        with patch("rag.retriever.embed_text", new=AsyncMock(return_value=[1.0, 0.0])), patch(
            "rag.rag_service.get_model", return_value=model
        ):
            answered = client.post("/rag/query", json={
                "user_id": "integration-user", "question": "Is remote work allowed?",
                "document_id": document_id,
            })
        assert answered.status_code == 200
        assert answered.json()["answer"] == "The policy allows remote work."
        assert answered.json()["sources"][0]["document_id"] == document_id

        listed = client.get("/documents/integration-user")
        assert listed.json()["documents"][0]["document_id"] == document_id
        deleted = client.delete(f"/documents/{document_id}", params={"user_id": "integration-user"})
        assert deleted.status_code == 200
        assert client.get("/documents/integration-user").json()["documents"] == []
    finally:
        get_settings.cache_clear()
