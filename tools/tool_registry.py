"""Central registry that all callable tools register themselves into.

This module is deliberately Gemini-SDK-agnostic: tools are described with
a plain JSON-schema ``parameters`` dict, not a google-genai type. It is
``core/gemini_client.py``'s job to translate these specs into whatever the
Gemini SDK expects. This keeps tool_registry reusable if the LLM provider
ever changes, and keeps chat_engine.py from importing individual tools
directly.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable

from core.exceptions import ToolExecutionError, ToolNotFoundError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ToolSpec:
    """Describes one callable tool and how to invoke it."""

    name: str
    description: str
    parameters: dict[str, Any]
    handler: Callable[..., Any]


_REGISTRY: dict[str, ToolSpec] = {}


def register(name: str, description: str, parameters: dict[str, Any]):
    """Decorator that registers a function as a dispatchable tool.

    ``parameters`` must be a JSON-schema object describing the function's
    keyword arguments (this is what gets shown to Gemini as the function
    declaration).
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        if name in _REGISTRY:
            raise ValueError(f"Tool '{name}' is already registered.")
        _REGISTRY[name] = ToolSpec(
            name=name, description=description, parameters=parameters, handler=func
        )
        logger.debug("Registered tool '%s'", name)
        return func

    return decorator


def list_tool_specs() -> list[ToolSpec]:
    """Return all currently registered tool specs."""
    return list(_REGISTRY.values())


def dispatch(name: str, arguments: dict[str, Any]) -> Any:
    """Execute a registered tool by name with the given keyword arguments.

    Raises:
        ToolNotFoundError: if no tool with this name is registered.
        ToolExecutionError: if the tool raises, or is called with bad args.
    """
    spec = _REGISTRY.get(name)
    if spec is None:
        raise ToolNotFoundError(f"No tool named '{name}' is registered.")

    try:
        return spec.handler(**arguments)
    except TypeError as exc:
        logger.warning("Invalid arguments for tool '%s': %s", name, exc)
        raise ToolExecutionError(f"Invalid arguments for tool '{name}': {exc}") from exc
    except Exception as exc:  # noqa: BLE001 - deliberately broad: isolate tool failures
        logger.exception("Tool '%s' raised during execution", name)
        raise ToolExecutionError(f"Tool '{name}' failed: {exc}") from exc


def _reset_registry_for_tests() -> None:
    """Test-only helper to clear registrations between test modules."""
    _REGISTRY.clear()
