from tools import load_builtin_tools
from tools.tool_registry import dispatch, list_tool_specs


def test_builtin_tools_are_registered():
    loaded = load_builtin_tools()
    assert {spec.name for spec in loaded} == {"calculator", "get_weather"}
    assert {spec.name for spec in list_tool_specs()} == {"calculator", "get_weather"}


def test_calculator_dispatches_through_registry():
    load_builtin_tools()
    assert dispatch("calculator", {"expression": "27 * 14 + 35"}) == 413
