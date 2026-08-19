"""High-level document ingestion and grounded question answering."""

from __future__ import annotations

import re
import uuid
from pathlib import Path

from google.genai import types

from config.settings import get_settings
from core.exceptions import DocumentProcessingError, EmbeddingError, RAGError
from core.gemini_client import get_model
from core.prompts import RAG_GROUNDING_INSTRUCTIONS, build_rag_prompt
from db import documents
from rag.chunker import chunk_text
from rag.document_loader import extract_text
from rag.embeddings import embed_texts
from rag.retriever import retrieve
from rag.vector_store import store_chunks


def safe_filename(filename: str) -> str:
    name = Path(filename or "document").name
    name = re.sub(r"[^A-Za-z0-9._ -]", "_", name).strip(" .")
    return name or "document"


async def ingest_document(user_id: str, filename: str, mime_type: str, file_bytes: bytes) -> dict:
    if not user_id.strip():
        raise DocumentProcessingError("A user ID is required.")
    settings = get_settings()
    if len(file_bytes) > settings.max_upload_size_mb * 1024 * 1024:
        raise DocumentProcessingError(
            f"Document exceeds the {settings.max_upload_size_mb} MB upload limit."
        )
    clean_name = safe_filename(filename)
    text = extract_text(file_bytes, clean_name, mime_type)
    texts = chunk_text(text, settings.rag_chunk_size, settings.rag_chunk_overlap)
    if not texts:
        raise DocumentProcessingError("The document did not produce any useful text chunks.")
    vectors = await embed_texts(texts, task_type="RETRIEVAL_DOCUMENT")
    document_id = str(uuid.uuid4())
    metadata = {
        "document_id": document_id, "user_id": user_id, "filename": clean_name,
        "mime_type": mime_type, "chunk_count": len(texts),
    }
    try:
        await documents.create_document(metadata)
        await store_chunks([
            {
                **metadata, "chunk_index": index, "page": None,
                "text": chunk, "embedding": vector,
            }
            for index, (chunk, vector) in enumerate(zip(texts, vectors))
        ])
    except Exception as exc:
        await documents.delete_document(document_id, user_id)
        raise RAGError("Could not store the processed document.") from exc
    return {"document_id": document_id, "filename": clean_name, "chunks_created": len(texts)}


async def query_documents(user_id: str, question: str, document_id: str | None = None) -> dict:
    if not question.strip():
        raise RAGError("Question must not be empty.")
    if document_id:
        document = await documents.get_document(document_id)
        if not document or document["user_id"] != user_id:
            raise RAGError("Document was not found for this user.")
    results = await retrieve(user_id, question, document_id=document_id)
    if not results:
        return {
            "answer": "The uploaded document does not provide enough information to answer that question.",
            "sources": [],
        }
    blocks = []
    for item in results:
        page = f", page {item['page']}" if item.get("page") is not None else ""
        blocks.append(f"[Source: {item['filename']}, chunk {item['chunk_index']}{page}]\n{item['text']}")
    prompt = build_rag_prompt(question, blocks)
    try:
        response = await get_model().generate(
            [types.Content(role="user", parts=[types.Part.from_text(text=prompt)])],
            system_instruction=RAG_GROUNDING_INSTRUCTIONS,
        )
        candidates = getattr(response, "candidates", None)
        parts = candidates[0].content.parts if candidates and candidates[0].content else []
        answer = "".join(part.text for part in parts if getattr(part, "text", None)).strip()
        if not answer:
            raise RAGError("Gemini returned no grounded answer.")
    except RAGError:
        raise
    except Exception as exc:
        raise RAGError("Could not generate a grounded answer.") from exc
    sources = [
        {key: item.get(key) for key in ("document_id", "filename", "chunk_index", "score", "page")}
        for item in results
    ]
    return {"answer": answer, "sources": sources}
