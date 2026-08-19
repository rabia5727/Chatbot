"""Main chat orchestration layer: one complete user turn, including
multi-step Gemini tool calling, history loading, and persistence.

Flow: validate input -> load history -> build Gemini conversation ->
send to Gemini -> if a tool call is requested, dispatch it via
tools.tool_registry.dispatch and feed the result back -> repeat until
Gemini returns final text -> persist the turn -> return the reply.
"""

from __future__ import annotations

import asyncio
import logging

from google.genai import types

from config.settings import get_settings
from core.exceptions import ChatEngineError, ToolExecutionError, ToolNotFoundError
from core.gemini_client import get_model
from core.prompts import build_system_instruction
from db import chat_history
from tools import load_builtin_tools
from tools.tool_registry import dispatch, list_tool_specs

logger = logging.getLogger(__name__)


async def send_message(user_id: str, user_text: str) -> str:
    """Run one full chat turn for ``user_id`` and return the assistant's reply.

    Raises:
        ChatEngineError: on invalid input, history failure, tool-call limit
            exceeded, or an unusable Gemini response.
    """
    if not user_text or not user_text.strip():
        raise ChatEngineError("Message text must not be empty.")

    settings = get_settings()

    history = await _load_history(user_id, settings.max_chat_history)
    contents = _build_contents(history, user_text)

    load_builtin_tools()
    tool_specs = list_tool_specs()
    logger.info("Tool specs passed to Gemini: %s", [spec.name for spec in tool_specs])
    model = get_model(tools=tool_specs)
    final_text = await _run_turn(model, contents, settings.max_tool_calls)

    await _save_turn(user_id, user_text, final_text)
    return final_text


async def _load_history(user_id: str, limit: int) -> list[dict]:
    try:
        return await chat_history.get_recent_messages(user_id, limit)
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to load chat history for user %s: %s", user_id, exc)
        raise ChatEngineError("Could not load conversation history.") from exc


def _build_contents(history: list[dict], user_text: str) -> list[types.Content]:
    """Convert stored history + the new user message into Gemini Content objects."""
    contents: list[types.Content] = []
    for message in history:
        stored_role = message["role"]
        if stored_role in {"assistant", "model"}:
            role = "model"
        elif stored_role == "user":
            role = "user"
        else:
            logger.warning("Skipping unsupported stored conversation role '%s'", stored_role)
            continue
        contents.append(
            types.Content(role=role, parts=[types.Part.from_text(text=message["content"])])
        )
    contents.append(types.Content(role="user", parts=[types.Part.from_text(text=user_text)]))
    return contents


async def _run_turn(model, contents: list[types.Content], max_tool_calls: int) -> str:
    """Drive the Gemini <-> tool-call loop until a final text answer appears."""
    tool_calls_used = 0
    while True:
        response = await model.generate(contents, system_instruction=build_system_instruction())

        function_calls = _extract_function_calls(response)
        if not function_calls:
            return _extract_final_text(response)

        if tool_calls_used + len(function_calls) > max_tool_calls:
            raise ChatEngineError(
                f"Maximum tool calls ({max_tool_calls}) exceeded without a final answer."
            )
        tool_calls_used += len(function_calls)

        for call in function_calls:
            logger.info(
                "Gemini requested function '%s' with arguments %s",
                call.name,
                dict(call.args or {}),
            )

        # Preserve Gemini's original model content (including function_call parts),
        # followed by user-role function_response parts as required by Gemini.
        contents.append(_extract_model_content(response))
        contents.append(await _build_tool_response_content(function_calls))


def _extract_model_content(response: types.GenerateContentResponse) -> types.Content:
    candidates = getattr(response, "candidates", None)
    if not candidates or candidates[0].content is None:
        raise ChatEngineError("Gemini returned no usable candidate content.")
    return candidates[0].content


def _extract_function_calls(response: types.GenerateContentResponse) -> list:
    candidates = getattr(response, "candidates", None)
    if not candidates:
        raise ChatEngineError("Gemini returned no candidates.")

    content = candidates[0].content
    if content is None or not content.parts:
        return []

    return [part.function_call for part in content.parts if getattr(part, "function_call", None)]


def _extract_final_text(response: types.GenerateContentResponse) -> str:
    candidates = getattr(response, "candidates", None)
    if not candidates:
        raise ChatEngineError("Gemini returned no usable response.")

    content = candidates[0].content
    if content is None or not content.parts:
        raise ChatEngineError("Gemini returned an empty response.")

    text_parts = [part.text for part in content.parts if getattr(part, "text", None)]
    if not text_parts:
        raise ChatEngineError("Gemini did not return a text response.")

    return "".join(text_parts).strip()


async def _build_tool_response_content(function_calls: list) -> types.Content:
    """Execute every requested tool call and package the results for Gemini."""
    response_parts = []
    for call in function_calls:
        result = await _execute_tool(call.name, dict(call.args or {}))
        response_parts.append(types.Part.from_function_response(name=call.name, response=result))
    return types.Content(role="user", parts=response_parts)


async def _execute_tool(name: str, arguments: dict) -> dict:
    """Dispatch one tool call, converting failures into a structured result
    Gemini can reason about instead of crashing the turn."""
    try:
        logger.info("Dispatching tool '%s' with arguments %s", name, arguments)
        result = await asyncio.to_thread(dispatch, name, arguments)
        logger.info("Tool '%s' result: %s", name, result)
        return {"result": result}
    except ToolNotFoundError as exc:
        logger.warning("Gemini requested an unknown tool: %s", name)
        return {"error": str(exc)}
    except ToolExecutionError as exc:
        logger.error("Tool '%s' failed: %s", name, exc)
        return {"error": str(exc)}
    except Exception:  # noqa: BLE001 - last-resort guard, must never crash the turn
        logger.exception("Unexpected error executing tool '%s'", name)
        return {"error": f"Tool '{name}' failed unexpectedly."}


async def _save_turn(user_id: str, user_text: str, assistant_text: str) -> None:
    try:
        await chat_history.add_message(user_id, "user", user_text)
        await chat_history.add_message(user_id, "assistant", assistant_text)
    except Exception as exc:  # noqa: BLE001
        # Persistence failure shouldn't erase the reply the user already got,
        # but it must not be silently swallowed either.
        logger.error("Failed to persist chat turn for user %s: %s", user_id, exc)
