"""Built-in tool loading.

The explicit loader makes registration independent of which application
entry point imports the chat engine.
"""

from __future__ import annotations

from importlib import import_module

from tools.tool_registry import ToolSpec, list_tool_specs

_BUILTIN_MODULES = ("tools.calculator", "tools.weather")
_BUILTIN_NAMES = {"calculator", "get_weather"}


def load_builtin_tools() -> list[ToolSpec]:
    """Import every built-in tool module and verify its decorator ran."""
    for module_name in _BUILTIN_MODULES:
        import_module(module_name)
    specs = list_tool_specs()
    missing = _BUILTIN_NAMES.difference(spec.name for spec in specs)
    if missing:
        raise RuntimeError(f"Built-in tools failed to register: {sorted(missing)}")
    return specs
