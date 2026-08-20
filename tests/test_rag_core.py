import io
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import fitz
import pytest
from docx import Document

from core.exceptions import DocumentProcessingError, EmbeddingError, UnsupportedDocumentTypeError
from rag import chunker, embeddings, rag_service, retriever
from rag.document_loader import extract_text
from rag.vector_store import cosine_similarity


def test_txt_extraction_and_validation():
    assert extract_text(b"First.\n\nSecond.", "notes.txt", "text/plain") == "First.\n\nSecond."
    with pytest.raises(DocumentProcessingError):
        extract_text(b"", "empty.txt", "text/plain")
    with pytest.raises(UnsupportedDocumentTypeError):
        extract_text(b"data", "unsafe.exe", "application/octet-stream")


def test_docx_extraction():
    buffer = io.BytesIO()
    document = Document()
    document.add_paragraph("Useful DOCX text")
    document.save(buffer)
    assert "Useful DOCX text" in extract_text(
        buffer.getvalue(), "sample.docx",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


def test_pdf_extraction():
    document = fitz.open()
    document.new_page().insert_text((72, 72), "Text from a PDF")
    data = document.tobytes()
    document.close()
    assert "Text from a PDF" in extract_text(data, "sample.pdf", "application/pdf")


def test_chunker_and_cosine_similarity():
    chunks = chunker.chunk_text(" ".join(f"word{i}" for i in range(80)), 100, 20)
    assert len(chunks) > 1 and all(item.strip() for item in chunks)
    assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == pytest.approx(1.0)
    assert cosine_similarity([1.0], [1.0, 0.0]) == 0.0


async def test_embeddings_batch_and_provider_error():
    client = MagicMock()
    client.aio.models.embed_content = AsyncMock(return_value=SimpleNamespace(
        embeddings=[SimpleNamespace(values=[1.0]), SimpleNamespace(values=[2.0])]
    ))
    with patch("rag.embeddings.get_client", return_value=client):
        assert await embeddings.embed_texts(["one", "two"]) == [[1.0], [2.0]]
    client.aio.models.embed_content = AsyncMock(side_effect=RuntimeError("down"))
    with patch("rag.embeddings.get_client", return_value=client), pytest.raises(EmbeddingError):
        await embeddings.embed_text("question")


async def test_process_document_returns_unpersisted_integration_payload():
    with patch("rag.rag_service.extract_text", return_value="Useful text"), patch(
        "rag.rag_service.chunk_text", return_value=["chunk one"]
    ), patch("rag.rag_service.embed_texts", new=AsyncMock(return_value=[[1.0, 0.0]])):
        processed = await rag_service.process_document(
            "user-1", "../safe.txt", "text/plain", b"text"
        )
    assert processed["metadata"]["filename"] == "safe.txt"
    assert processed["metadata"]["chunk_count"] == 1
    assert processed["chunks"][0]["embedding"] == [1.0, 0.0]


async def test_storage_integration_boundary_receives_processed_document():
    storage = MagicMock()
    storage.store_document = AsyncMock()
    processed = {"metadata": {"document_id": "doc-1"}, "chunks": [{"text": "chunk"}]}
    await rag_service.store_processed_document(processed, storage)
    storage.store_document.assert_awaited_once_with(processed["metadata"], processed["chunks"])


async def test_retriever_uses_injected_storage_and_user_scope():
    storage = MagicMock()
    storage.search_chunks = AsyncMock(return_value=[{"text": "match"}])
    with patch("rag.retriever.embed_text", new=AsyncMock(return_value=[1.0])):
        result = await retriever.retrieve("user-1", "question", storage, "doc-1", 2)
    assert result == [{"text": "match"}]
    storage.search_chunks.assert_awaited_once_with(
        "user-1", [1.0], document_id="doc-1", top_k=2
    )


async def test_query_flow_uses_injected_storage():
    storage = MagicMock()
    hit = {"document_id": "doc-1", "filename": "safe.txt", "chunk_index": 0,
           "page": None, "text": "source", "score": 0.9}
    model = MagicMock()
    model.generate = AsyncMock(return_value=SimpleNamespace(candidates=[SimpleNamespace(
        content=SimpleNamespace(parts=[SimpleNamespace(text="Grounded answer")])
    )]))
    with patch("rag.rag_service.retrieve", new=AsyncMock(return_value=[hit])) as retrieve_mock, patch(
        "rag.rag_service.get_model", return_value=model
    ):
        result = await rag_service.query_documents("user-1", "What?", storage, "doc-1")
    retrieve_mock.assert_awaited_once_with("user-1", "What?", storage, document_id="doc-1")
    assert result["answer"] == "Grounded answer"
