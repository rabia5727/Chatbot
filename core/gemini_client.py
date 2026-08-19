"""Gemini SDK setup, isolated from the rest of the application.

Uses the official ``google-genai`` SDK. Nothing outside this file should
import ``google.genai`` directly for chat/text generation -- other modules
should go through ``get_model()`` (for chat + tool calling) or
``get_client()`` (for lower-level multimodal calls, used by stt.py/tts.py).

No database logic, RAG logic, tool execution, or route logic belongs here.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Iterable, Optional

from google import genai
from google.genai import types

from config.settings import get_settings
from core.exceptions import GeminiConfigurationError

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_client() -> genai.Client:
    """Return a configured, cached Gemini SDK client.

    Raises:
        GeminiConfigurationError: if GEMINI_API_KEY is not set.
    """
    api_key = get_settings().gemini_api_key
    if not api_key:
        raise GeminiConfigurationError(
            "GEMINI_API_KEY is not configured. Set it in your environment or .env file."
        )
    return genai.Client(api_key=api_key)


def _build_tool(tool_specs: Optional[Iterable]) -> Optional[types.Tool]:
    """Convert tool_registry.ToolSpec objects into a Gemini Tool declaration."""
    specs = list(tool_specs) if tool_specs else []
    if not specs:
        return None

    declarations = [
        types.FunctionDeclaration(
            name=spec.name,
            description=spec.description,
            parameters=spec.parameters,
        )
        for spec in specs
    ]
    logger.info("Gemini tool declarations: %s", [declaration.name for declaration in declarations])
    return types.Tool(function_declarations=declarations)


class GeminiModel:
    """Thin wrapper around a configured Gemini model + optional tool config.

    Keeps SDK-specific request construction in one place so chat_engine.py
    only has to deal with a plain ``generate(contents, system_instruction)``
    call.
    """

    def __init__(self, client: genai.Client, model_name: str, tool: Optional[types.Tool] = None):
        self._client = client
        self._model_name = model_name
        self._tool = tool

    async def generate(
        self, contents: list, system_instruction: Optional[str] = None
    ) -> types.GenerateContentResponse:
        """Send ``contents`` (a list of google.genai.types.Content) to Gemini."""
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=[self._tool] if self._tool else None,
        )
        tool_names = (
            [declaration.name for declaration in self._tool.function_declarations or []]
            if self._tool
            else []
        )
        logger.debug("Sending Gemini request with tools: %s", tool_names)
        try:
            return await self._client.aio.models.generate_content(
                model=self._model_name,
                contents=contents,
                config=config,
            )
        except Exception as exc:  # noqa: BLE001 - re-raised, just logged here
            logger.error("Gemini generate_content request failed: %s", exc)
            raise


def get_model(tools: Optional[Iterable] = None) -> GeminiModel:
    """Return a Gemini model wrapper, optionally configured for tool calling.

    Args:
        tools: optional iterable of tools.tool_registry.ToolSpec. When
            provided, Gemini is told it may call these functions. When
            None, the model is created without any tool declarations.
    """
    client = get_client()
    settings = get_settings()
    tool = _build_tool(tools)
    return GeminiModel(client=client, model_name=settings.gemini_model, tool=tool)
