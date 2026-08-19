"""
Central registry for external "tools" the chatbot can call via Gemini
function calling (weather now, more later — news, calculator, etc).

Owner: Rabia

Integration contract with core/chat_engine.py (Ghanwa):
- get_tool_declarations() returns the list Gemini needs to know what
  functions it may call (passed straight into gemini_client.get_model).
- dispatch(name, args) runs the matching function and returns a string
  result to feed back to Gemini.

To add a new tool:
1. Write it in its own file (see tools/weather_tool.py for the pattern).
2. Add its declaration to TOOL_DECLARATIONS below.
3. Add its name -> function mapping to TOOL_FUNCTIONS below.
"""

from tools.weather_tool import get_weather

TOOL_DECLARATIONS = [
    {
        "name": "get_weather",
        "description": "Get the current weather for a given city.",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "City name, e.g. 'Lahore' or 'Karachi'.",
                },
            },
            "required": ["city"],
        },
    },
    # TODO(Rabia): add more tool declarations here as you build them.
]

TOOL_FUNCTIONS = {
    "get_weather": get_weather,
    # TODO(Rabia): map new tool names to their functions here.
}


def get_tool_declarations() -> list[dict]:
    return TOOL_DECLARATIONS


def dispatch(name: str, args: dict) -> str:
    """Run the tool named `name` with `args`, return a string result."""
    if name not in TOOL_FUNCTIONS:
        return f"Error: unknown tool '{name}'"
    return TOOL_FUNCTIONS[name](**args)
