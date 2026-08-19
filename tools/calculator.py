"""Example tool: safe arithmetic evaluation.

Registered into tools.tool_registry so Gemini can call it via function
calling. Uses ast parsing (not eval()) so only arithmetic is possible.
"""

from __future__ import annotations

import ast
import operator

from tools.tool_registry import register

_OPERATORS: dict[type, object] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}


def _eval_node(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPERATORS:
        return _OPERATORS[type(node.op)](_eval_node(node.left), _eval_node(node.right))  # type: ignore[operator]
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPERATORS:
        return _OPERATORS[type(node.op)](_eval_node(node.operand))  # type: ignore[operator]
    raise ValueError(f"Unsupported expression element: {ast.dump(node)}")


@register(
    name="calculator",
    description=(
        "Evaluate a basic arithmetic expression using +, -, *, /, %, and ** "
        "(power). Example expression: '(2 + 3) * 4'."
    ),
    parameters={
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "The arithmetic expression to evaluate.",
            }
        },
        "required": ["expression"],
    },
)
def calculate(expression: str) -> float:
    """Safely evaluate an arithmetic expression string and return the result."""
    try:
        tree = ast.parse(expression, mode="eval")
        return _eval_node(tree.body)
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"Invalid expression '{expression}': {exc}") from exc
