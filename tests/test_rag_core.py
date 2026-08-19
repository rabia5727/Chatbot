import io
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import fitz
import pytest
from docx import Document

from config.settings import get_settings
from core.exceptions import DocumentProcessingError, EmbeddingError, UnsupportedDocumentTypeError
from db import documents
from rag import chunker, embeddings, rag_service, retriever, vector_store
from rag.document_loader import extract_text


@pytest.fixture
def rag_db(tmp_path, monkeypatch):
    monkeypatch.setenv("RAG_DB_PATH", str(tmp_path / "rag-test.db"))
    get_settings.cache_clear()
    yield tmp_path / "rag-test.db"
    get_settings.cache_clear()


def test_txt_extraction_and_validation():
    assert extract_text(b"First paragraph.\n\nSecond paragraph.", "notes.txt", "text/plain") == (
        "First paragraph.\n\nSecond paragraph."
    )
    with pytest.raises(DocumentProcessingError):
        extract_text(b"", "empty.txt", "text/plain")
    with pytest.raises(UnsupportedDocumentTypeError):
        extract_text(b"data", "unsafe.exe", "application/octet-stream")


def test_docx_extraction():
    buffer = io.BytesIO()
    document = Document()
    document.add_paragraph("DOCX heading")
    document.add_paragraph("Useful body text")
    document.save(buffer)
    assert "Useful body text" in extract_text(
        buffer.getvalue(),
        "sample.docx",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


def test_pdf_extraction():
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "Text from a PDF")
    data = document.tobytes()
    document.close()
    assert "Text from a PDF" in extract_text(data, "sample.pdf", "application/pdf")


def test_chunker_creates_overlap_without_empty_chunks():
    text = " ".join(f"word{i}" for i in range(80))
    chunks = chunker.chunk_text(text, chunk_size=100, overlap=20)
    assert len(chunks) > 1
    assert all(item.strip() for item in chunks)
    assert any(chunks[index][-10:].split()[-1] in chunks[index + 1] for index in range(len(chunks) - 1))
    assert chunker.chunk_text("   ") == []


async def test_embeddings_batch_and_provider_error():
    response = SimpleNamespace(
        embeddings=[SimpleNamespace(values=[1.0, 0.0]), SimpleNamespace(values=[0.0, 1.0])]
    )
    client = MagicMock()
    client.aio.models.embed_content = AsyncMock(return_value=response)
    with patch("rag.embeddings.get_client", return_value=client):
        assert await embeddings.embed_texts(["one", "two"]) == [[1.0, 0.0], [0.0, 1.0]]
        kwargs = client.aio.models.embed_content.await_args.kwargs
        assert kwargs["config"].task_type == "RETRIEVAL_DOCUMENT"

    client.aio.models.embed_content = AsyncMock(side_effect=RuntimeError("provider down"))
    with patch("rag.embeddings.get_client", return_value=client), pytest.raises(EmbeddingError):
        await embeddings.embed_text("question")


async def test_vector_store_scoping_filtering_and_delete(rag_db):
    for document_id, user_id in (("doc-a", "user-a"), ("doc-b", "user-b")):
        await documents.create_document({
            "document_id": document_id, "user_id": user_id, "filename": f"{document_id}.txt",
            "mime_type": "text/plain", "chunk_count": 1,
        })
    await vector_store.store_chunks([
        {"document_id": "doc-a", "user_id": "user-a", "filename": "a.txt", "chunk_index": 0,
         "page": None, "text": "alpha", "embedding": [1.0, 0.0]},
        {"document_id": "doc-b", "user_id": "user-b", "filename": "b.txt", "chunk_index": 0,
         "page": None, "text": "private", "embedding": [1.0, 0.0]},
    ])
    results = await vector_store.similarity_search("user-a", [1.0, 0.0], top_k=1)
    assert [item["document_id"] for item in results] == ["doc-a"]
    assert await vector_store.similarity_search("user-a", [1.0, 0.0], document_id="doc-b") == []
    assert await documents.delete_document("doc-a", "user-b") is False
    assert await documents.delete_document("doc-a", "user-a") is True
    assert await vector_store.similarity_search("user-a", [1.0, 0.0]) == []


async def test_retriever_top_k_and_user_scope():
    with patch("rag.retriever.embed_text", new=AsyncMock(return_value=[1.0])), patch(
        "rag.retriever.similarity_search", new=AsyncMock(return_value=[{"text": "match"}])
    ) as search:
        assert await retriever.retrieve("user-1", "question", document_id="doc-1", top_k=2)
        search.assert_awaited_once_with("user-1", [1.0], document_id="doc-1", top_k=2)


async def test_rag_service_ingestion_and_query_flow():
    with patch("rag.rag_service.extract_text", return_value="Useful document text"), patch(
        "rag.rag_service.chunk_text", return_value=["chunk one"]
    ), patch("rag.rag_service.embed_texts", new=AsyncMock(return_value=[[1.0, 0.0]])), patch(
        "rag.rag_service.documents.create_document", new=AsyncMock()
    ), patch("rag.rag_service.store_chunks", new=AsyncMock()) as store:
        result = await rag_service.ingest_document("user-1", "../safe.txt", "text/plain", b"text")
        assert result["filename"] == "safe.txt"
        assert result["chunks_created"] == 1
        assert "embedding" in store.await_args.args[0][0]

    model = MagicMock()
    model.generate = AsyncMock(return_value=SimpleNamespace(candidates=[SimpleNamespace(
        content=SimpleNamespace(parts=[SimpleNamespace(text="Grounded answer")])
    )]))
    hit = {"document_id": "doc-1", "filename": "safe.txt", "chunk_index": 0,
           "page": None, "text": "source text", "score": 0.9}
    with patch("rag.rag_service.retrieve", new=AsyncMock(return_value=[hit])), patch(
        "rag.rag_service.get_model", return_value=model
    ):
        response = await rag_service.query_documents("user-1", "What is it?")
        assert response["answer"] == "Grounded answer"
        assert response["sources"][0]["score"] == 0.9

    with patch("rag.rag_service.retrieve", new=AsyncMock(return_value=[])):
        response = await rag_service.query_documents("user-1", "Unknown?")
        assert response["sources"] == []
        assert "does not provide enough information" in response["answer"]
