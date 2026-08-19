from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core import gemini_client
from core.exceptions import GeminiConfigurationError


@pytest.fixture(autouse=True)
def _clear_client_cache():
    gemini_client.get_client.cache_clear()
    yield
    gemini_client.get_client.cache_clear()


def test_get_model_raises_without_api_key():
    with patch("core.gemini_client.get_settings") as mock_settings:
        mock_settings.return_value.gemini_api_key = ""
        with pytest.raises(GeminiConfigurationError):
            gemini_client.get_model()


def test_get_model_without_tools_has_no_tool_config():
    with patch("core.gemini_client.get_settings") as mock_settings, patch(
        "core.gemini_client.genai.Client"
    ) as mock_client_cls:
        mock_settings.return_value.gemini_api_key = "fake-key"
        mock_settings.return_value.gemini_model = "gemini-test"
        mock_client_cls.return_value = object()

        model = gemini_client.get_model(tools=None)

        assert model._tool is None
        assert model._model_name == "gemini-test"


def test_get_model_with_tools_builds_function_declarations():
    class DummySpec:
        name = "dummy_tool"
        description = "a dummy tool"
        parameters = {"type": "object", "properties": {}}

    with patch("core.gemini_client.get_settings") as mock_settings, patch(
        "core.gemini_client.genai.Client"
    ) as mock_client_cls:
        mock_settings.return_value.gemini_api_key = "fake-key"
        mock_settings.return_value.gemini_model = "gemini-test"
        mock_client_cls.return_value = object()

        model = gemini_client.get_model(tools=[DummySpec()])

        assert model._tool is not None
        assert model._tool.function_declarations[0].name == "dummy_tool"


async def test_generate_sends_tool_declarations_in_current_sdk_config():
    declaration = gemini_client.types.FunctionDeclaration(
        name="calculator",
        description="Calculate arithmetic",
        parameters={"type": "object", "properties": {}},
    )
    tool = gemini_client.types.Tool(function_declarations=[declaration])
    client = MagicMock()
    client.aio.models.generate_content = AsyncMock(return_value=object())
    model = gemini_client.GeminiModel(client, "gemini-test", tool)

    await model.generate(["Calculate 2 + 2"], system_instruction="Use tools when needed")

    config = client.aio.models.generate_content.await_args.kwargs["config"]
    assert config.tools[0].function_declarations[0].name == "calculator"
