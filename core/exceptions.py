"""Application-level exception hierarchy.

Raw SDK / provider exceptions (Gemini SDK errors, requests
exceptions, etc.) should be caught close to their source and re-raised as
one of these, so upper layers (FastAPI routes, callers) never need to know
which provider is behind a given feature.
"""


class ChatbotError(Exception):
    """Base class for all application-level errors in this project."""


class GeminiConfigurationError(ChatbotError):
    """Raised when required Gemini configuration (e.g. API key) is missing."""


class ChatEngineError(ChatbotError):
    """Raised for errors during a chat turn (validation, orchestration, limits)."""


class ToolNotFoundError(ChatbotError):
    """Raised when Gemini requests a tool that is not registered."""


class ToolExecutionError(ChatbotError):
    """Raised when a registered tool raises during execution or gets bad args."""


class SpeechTranscriptionError(ChatbotError):
    """Raised when speech-to-text transcription fails."""


class SpeechSynthesisError(ChatbotError):
    """Raised when text-to-speech synthesis fails."""


class DocumentProcessingError(ChatbotError):
    """Raised when an uploaded document cannot be validated or parsed."""


class UnsupportedDocumentTypeError(DocumentProcessingError):
    """Raised when an uploaded document type is not supported."""


class EmbeddingError(ChatbotError):
    """Raised when embedding generation fails or returns invalid data."""


class RetrievalError(ChatbotError):
    """Raised when stored document chunks cannot be searched."""


class RAGError(ChatbotError):
    """Raised when document ingestion or grounded question answering fails."""
