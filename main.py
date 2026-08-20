"""FastAPI application entry point.

Run with:
    uvicorn main:app --reload
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel

from core.chat_engine import send_message
from core.exceptions import (
    ChatEngineError,
    DocumentProcessingError,
    EmbeddingError,
    GeminiConfigurationError,
    RAGError,
    SpeechSynthesisError,
    SpeechTranscriptionError,
    UnsupportedDocumentTypeError,
)
from core.stt import transcribe
from core.tts import synthesize
from config.settings import get_settings
from rag.rag_service import process_document
from tools import load_builtin_tools

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

startup_tools = load_builtin_tools()
logger.info("Registered tools at startup: %s", [spec.name for spec in startup_tools])

app = FastAPI(title="Chatbot API")


class ChatRequest(BaseModel):
    user_id: str
    message: str


class ChatResponse(BaseModel):
    reply: str


class TTSRequest(BaseModel):
    text: str


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    try:
        reply = await send_message(request.user_id, request.message)
        return ChatResponse(reply=reply)
    except GeminiConfigurationError as exc:
        logger.error("Gemini configuration error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except ChatEngineError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/stt")
async def speech_to_text(audio: UploadFile = File(...)) -> dict:
    audio_bytes = await audio.read()
    try:
        transcript = await transcribe(audio_bytes, mime_type=audio.content_type)
        return {"transcript": transcript}
    except SpeechTranscriptionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/tts")
async def text_to_speech(request: TTSRequest) -> Response:
    try:
        audio_bytes = await synthesize(request.text)
        return Response(content=audio_bytes, media_type="audio/mpeg")
    except SpeechSynthesisError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/documents/upload")
async def upload_document(user_id: str = Form(...), file: UploadFile = File(...)) -> dict:
    limit = get_settings().max_upload_size_mb * 1024 * 1024
    file_bytes = await file.read(limit + 1)
    try:
        processed = await process_document(
            user_id=user_id,
            filename=file.filename or "document",
            mime_type=file.content_type or "application/octet-stream",
            file_bytes=file_bytes,
        )
        metadata = processed["metadata"]
        return {
            "document_id": metadata["document_id"],
            "filename": metadata["filename"],
            "chunks_created": metadata["chunk_count"],
            "persisted": False,
        }
    except UnsupportedDocumentTypeError as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc
    except DocumentProcessingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (EmbeddingError, RAGError) as exc:
        logger.error("Document ingestion failed: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc

