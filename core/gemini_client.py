"""
Thin wrapper around the Gemini API.

Owner: Ghanwa

Responsibilities:
- Configure the google-generativeai SDK with GEMINI_API_KEY.
- Expose one function other modules call to get a model/chat session.
- Keep Gemini-specific setup (model name, generation config, safety
  settings) in this one file so nobody else has to touch the SDK directly.
"""

import google.generativeai as genai

from config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)

MODEL_NAME = "gemini-2.0-flash"  # TODO(Ghanwa): pick the model/version you want


def get_model(tools=None):
    """
    Return a configured genai.GenerativeModel.

    `tools` should be the Gemini function-declaration list built by
    tools.tool_registry.get_tool_declarations() — pass it through
    untouched, don't reshape it here.
    """
    return genai.GenerativeModel(model_name=MODEL_NAME, tools=tools)
