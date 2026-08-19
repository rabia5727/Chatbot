from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from core import chat_engine


def _fake_call(name, args):
    return SimpleNamespace(name=name, args=args)


def _fake_response(function_calls=None, text=None):
    parts = []
    if function_calls:
        for call in function_calls:
            parts.append(SimpleNamespace(function_call=call, text=None))
    if text is not None:
        parts.append(SimpleNamespace(function_call=None, text=text))
    content = SimpleNamespace(role="model", parts=parts)
    candidate = SimpleNamespace(content=content)
    return SimpleNamespace(candidates=[candidate])


def _patch_content_types():
    """Patch google.genai types used by chat_engine with simple passthrough
    stand-ins, so tests don't depend on exact SDK object construction."""
    return (
        patch(
            "core.chat_engine.types.Content",
            side_effect=lambda role, parts: SimpleNamespace(role=role, parts=parts),
        ),
        patch(
            "core.chat_engine.types.Part.from_text",
            side_effect=lambda *, text: SimpleNamespace(text=text),
        ),
        patch(
            "core.chat_engine.types.Part.from_function_response",
            side_effect=lambda name, response: SimpleNamespace(name=name, response=response),
        ),
    )


async def test_send_message_rejects_empty_text():
    with pytest.raises(chat_engine.ChatEngineError):
        await chat_engine.send_message("user-1", "   ")


async def test_send_message_plain_text_response():
    p1, p2, p3 = _patch_content_types()
    with p1, p2, p3, patch(
        "core.chat_engine.chat_history.get_recent_messages", new=AsyncMock(return_value=[])
    ), patch(
        "core.chat_engine.chat_history.add_message", new=AsyncMock()
    ) as mock_add, patch(
        "core.chat_engine.list_tool_specs", return_value=[]
    ), patch(
        "core.chat_engine.get_model"
    ) as mock_get_model:
        mock_model = AsyncMock()
        mock_model.generate = AsyncMock(return_value=_fake_response(text="Hello there"))
        mock_get_model.return_value = mock_model

        reply = await chat_engine.send_message("user-1", "hi")

        assert reply == "Hello there"
        assert mock_add.call_count == 2  # user message + assistant message


async def test_send_message_with_single_tool_call():
    call = _fake_call("calculator", {"expression": "2+2"})
    first_response = _fake_response(function_calls=[call])
    second_response = _fake_response(text="The answer is 4")

    p1, p2, p3 = _patch_content_types()
    with p1, p2, p3, patch(
        "core.chat_engine.chat_history.get_recent_messages", new=AsyncMock(return_value=[])
    ), patch(
        "core.chat_engine.chat_history.add_message", new=AsyncMock()
    ), patch(
        "core.chat_engine.list_tool_specs", return_value=[]
    ), patch(
        "core.chat_engine.dispatch", return_value=4
    ) as mock_dispatch, patch(
        "core.chat_engine.get_model"
    ) as mock_get_model:
        mock_model = AsyncMock()
        mock_model.generate = AsyncMock(side_effect=[first_response, second_response])
        mock_get_model.return_value = mock_model

        reply = await chat_engine.send_message("user-1", "what is 2+2?")

        assert reply == "The answer is 4"
        mock_dispatch.assert_called_once_with("calculator", {"expression": "2+2"})
        second_request = mock_model.generate.await_args_list[1].args[0]
        assert [content.role for content in second_request] == ["user", "model", "user"]
        assert all(content.role != "tool" for content in second_request)
        assert second_request[1] is first_response.candidates[0].content
        assert second_request[2].parts[0].name == "calculator"


async def test_send_message_multiple_sequential_tool_calls():
    call_a = _fake_call("tool_a", {})
    call_b = _fake_call("tool_b", {})
    response_1 = _fake_response(function_calls=[call_a])
    response_2 = _fake_response(function_calls=[call_b])
    response_3 = _fake_response(text="done")

    p1, p2, p3 = _patch_content_types()
    with p1, p2, p3, patch(
        "core.chat_engine.chat_history.get_recent_messages", new=AsyncMock(return_value=[])
    ), patch(
        "core.chat_engine.chat_history.add_message", new=AsyncMock()
    ), patch(
        "core.chat_engine.list_tool_specs", return_value=[]
    ), patch(
        "core.chat_engine.dispatch", side_effect=["result_a", "result_b"]
    ) as mock_dispatch, patch(
        "core.chat_engine.get_model"
    ) as mock_get_model:
        mock_model = AsyncMock()
        mock_model.generate = AsyncMock(side_effect=[response_1, response_2, response_3])
        mock_get_model.return_value = mock_model

        reply = await chat_engine.send_message("user-1", "do two things")

        assert reply == "done"
        assert mock_dispatch.call_count == 2


async def test_send_message_unknown_tool_returns_structured_error_to_gemini():
    call = _fake_call("nonexistent", {})
    first_response = _fake_response(function_calls=[call])
    second_response = _fake_response(text="I could not find that tool.")

    p1, p2, p3 = _patch_content_types()
    with p1, p2, p3, patch(
        "core.chat_engine.chat_history.get_recent_messages", new=AsyncMock(return_value=[])
    ), patch(
        "core.chat_engine.chat_history.add_message", new=AsyncMock()
    ), patch(
        "core.chat_engine.list_tool_specs", return_value=[]
    ), patch(
        "core.chat_engine.dispatch",
        side_effect=chat_engine.ToolNotFoundError("no such tool"),
    ), patch(
        "core.chat_engine.get_model"
    ) as mock_get_model:
        mock_model = AsyncMock()
        mock_model.generate = AsyncMock(side_effect=[first_response, second_response])
        mock_get_model.return_value = mock_model

        reply = await chat_engine.send_message("user-1", "use a fake tool")

        assert reply == "I could not find that tool."


async def test_send_message_tool_raises_exception_is_handled():
    call = _fake_call("broken_tool", {})
    first_response = _fake_response(function_calls=[call])
    second_response = _fake_response(text="Something went wrong with that tool.")

    p1, p2, p3 = _patch_content_types()
    with p1, p2, p3, patch(
        "core.chat_engine.chat_history.get_recent_messages", new=AsyncMock(return_value=[])
    ), patch(
        "core.chat_engine.chat_history.add_message", new=AsyncMock()
    ), patch(
        "core.chat_engine.list_tool_specs", return_value=[]
    ), patch(
        "core.chat_engine.dispatch",
        side_effect=chat_engine.ToolExecutionError("boom"),
    ), patch(
        "core.chat_engine.get_model"
    ) as mock_get_model:
        mock_model = AsyncMock()
        mock_model.generate = AsyncMock(side_effect=[first_response, second_response])
        mock_get_model.return_value = mock_model

        reply = await chat_engine.send_message("user-1", "use a broken tool")

        assert reply == "Something went wrong with that tool."


async def test_send_message_max_tool_calls_exceeded():
    call = _fake_call("loop_tool", {})
    looping_response = _fake_response(function_calls=[call])

    p1, p2, p3 = _patch_content_types()
    with p1, p2, p3, patch(
        "core.chat_engine.chat_history.get_recent_messages", new=AsyncMock(return_value=[])
    ), patch(
        "core.chat_engine.chat_history.add_message", new=AsyncMock()
    ), patch(
        "core.chat_engine.list_tool_specs", return_value=[]
    ), patch(
        "core.chat_engine.dispatch", return_value="ok"
    ), patch(
        "core.chat_engine.get_model"
    ) as mock_get_model, patch(
        "core.chat_engine.get_settings"
    ) as mock_get_settings:
        mock_get_settings.return_value.max_chat_history = 20
        mock_get_settings.return_value.max_tool_calls = 2

        mock_model = AsyncMock()
        mock_model.generate = AsyncMock(return_value=looping_response)
        mock_get_model.return_value = mock_model

        with pytest.raises(chat_engine.ChatEngineError):
            await chat_engine.send_message("user-1", "loop please")


async def test_send_message_raises_on_malformed_response():
    p1, p2, p3 = _patch_content_types()
    with p1, p2, p3, patch(
        "core.chat_engine.chat_history.get_recent_messages", new=AsyncMock(return_value=[])
    ), patch(
        "core.chat_engine.chat_history.add_message", new=AsyncMock()
    ), patch(
        "core.chat_engine.list_tool_specs", return_value=[]
    ), patch(
        "core.chat_engine.get_model"
    ) as mock_get_model:
        mock_model = AsyncMock()
        mock_model.generate = AsyncMock(return_value=SimpleNamespace(candidates=[]))
        mock_get_model.return_value = mock_model

        with pytest.raises(chat_engine.ChatEngineError):
            await chat_engine.send_message("user-1", "hello")


async def test_history_is_loaded_and_included_in_contents():
    history = [
        {"role": "user", "content": "earlier question"},
        {"role": "assistant", "content": "earlier reply"},
    ]

    p1, p2, p3 = _patch_content_types()
    with p1, p2, p3, patch(
        "core.chat_engine.chat_history.get_recent_messages", new=AsyncMock(return_value=history)
    ) as mock_get, patch(
        "core.chat_engine.chat_history.add_message", new=AsyncMock()
    ), patch(
        "core.chat_engine.list_tool_specs", return_value=[]
    ), patch(
        "core.chat_engine.get_model"
    ) as mock_get_model:
        mock_model = AsyncMock()
        mock_model.generate = AsyncMock(return_value=_fake_response(text="ok"))
        mock_get_model.return_value = mock_model

        await chat_engine.send_message("user-1", "new message")

        mock_get.assert_called_once()
        sent_contents = mock_model.generate.call_args[0][0]
        assert len(sent_contents) == 3  # 2 history messages + the new one
        assert [content.role for content in sent_contents] == ["user", "model", "user"]


def test_history_roles_are_normalized_for_gemini():
    history = [
        {"role": "assistant", "content": "assistant reply"},
        {"role": "model", "content": "model reply"},
        {"role": "system", "content": "must not become conversation content"},
        {"role": "tool", "content": "must not become conversation content"},
    ]
    contents = chat_engine._build_contents(history, "new question")
    assert [content.role for content in contents] == ["model", "model", "user"]
    assert all(content.role in {"user", "model"} for content in contents)


async def test_user_and_assistant_messages_are_persisted():
    p1, p2, p3 = _patch_content_types()
    with p1, p2, p3, patch(
        "core.chat_engine.chat_history.get_recent_messages", new=AsyncMock(return_value=[])
    ), patch(
        "core.chat_engine.chat_history.add_message", new=AsyncMock()
    ) as mock_add, patch(
        "core.chat_engine.list_tool_specs", return_value=[]
    ), patch(
        "core.chat_engine.get_model"
    ) as mock_get_model:
        mock_model = AsyncMock()
        mock_model.generate = AsyncMock(return_value=_fake_response(text="reply text"))
        mock_get_model.return_value = mock_model

        await chat_engine.send_message("user-1", "user text")

        mock_add.assert_any_call("user-1", "user", "user text")
        mock_add.assert_any_call("user-1", "assistant", "reply text")


@pytest.mark.parametrize(
    ("prompt", "calls", "results", "final_text"),
    [
        (
            "Calculate 27 * 14 + 35",
            [_fake_call("calculator", {"expression": "27 * 14 + 35"})],
            [413],
            "The answer is 413.",
        ),
        (
            "What is the current weather in Lahore?",
            [_fake_call("get_weather", {"city": "Lahore"})],
            [{"city": "Lahore", "temperature_c": 30}],
            "Lahore is currently 30°C.",
        ),
        (
            "Tell me the weather in Lahore and calculate 125 * 8.",
            [
                _fake_call("get_weather", {"city": "Lahore"}),
                _fake_call("calculator", {"expression": "125 * 8"}),
            ],
            [{"city": "Lahore", "temperature_c": 30}, 1000],
            "Lahore is 30°C, and 125 * 8 is 1000.",
        ),
    ],
)
async def test_expected_prompts_dispatch_gemini_selected_tools(prompt, calls, results, final_text):
    first_response = _fake_response(function_calls=calls)
    second_response = _fake_response(text=final_text)
    specs = [SimpleNamespace(name="calculator"), SimpleNamespace(name="get_weather")]
    p1, p2, p3 = _patch_content_types()
    with p1, p2, p3, patch(
        "core.chat_engine.chat_history.get_recent_messages", new=AsyncMock(return_value=[])
    ), patch("core.chat_engine.chat_history.add_message", new=AsyncMock()), patch(
        "core.chat_engine.load_builtin_tools", return_value=specs
    ), patch("core.chat_engine.list_tool_specs", return_value=specs), patch(
        "core.chat_engine.dispatch", side_effect=results
    ) as mock_dispatch, patch("core.chat_engine.get_model") as mock_get_model:
        model = AsyncMock()
        model.generate = AsyncMock(side_effect=[first_response, second_response])
        mock_get_model.return_value = model

        assert await chat_engine.send_message("user-1", prompt) == final_text
        mock_get_model.assert_called_once_with(tools=specs)
        assert [call.args[0] for call in mock_dispatch.call_args_list] == [call.name for call in calls]


async def test_explanation_prompt_does_not_dispatch_a_tool():
    specs = [SimpleNamespace(name="calculator"), SimpleNamespace(name="get_weather")]
    p1, p2, p3 = _patch_content_types()
    with p1, p2, p3, patch(
        "core.chat_engine.chat_history.get_recent_messages", new=AsyncMock(return_value=[])
    ), patch("core.chat_engine.chat_history.add_message", new=AsyncMock()), patch(
        "core.chat_engine.load_builtin_tools", return_value=specs
    ), patch("core.chat_engine.list_tool_specs", return_value=specs), patch(
        "core.chat_engine.dispatch"
    ) as mock_dispatch, patch("core.chat_engine.get_model") as mock_get_model:
        model = AsyncMock()
        model.generate = AsyncMock(
            return_value=_fake_response(text="Machine learning lets systems learn patterns from data.")
        )
        mock_get_model.return_value = model

        reply = await chat_engine.send_message(
            "user-1", "Explain machine learning in one sentence."
        )
        assert "learn patterns" in reply
        mock_dispatch.assert_not_called()


async def test_multiple_calls_in_one_response_use_one_user_function_response_content():
    calls = [
        _fake_call("get_weather", {"city": "Lahore"}),
        _fake_call("calculator", {"expression": "125 * 8"}),
    ]
    model = AsyncMock()
    model.generate = AsyncMock(
        side_effect=[_fake_response(function_calls=calls), _fake_response(text="done")]
    )
    with patch("core.chat_engine.dispatch", side_effect=[{"temperature_c": 30}, 1000]):
        assert await chat_engine._run_turn(model, [_fake_response(text="question").candidates[0].content], 2) == "done"
    second_request = model.generate.await_args_list[1].args[0]
    assert [content.role for content in second_request] == ["model", "model", "user"]
    assert len(second_request[-1].parts) == 2
    assert all(part.function_response is not None for part in second_request[-1].parts)
    assert all(content.role != "tool" for content in second_request)


async def test_max_tool_calls_counts_calls_not_model_rounds():
    calls = [
        _fake_call("get_weather", {"city": "Lahore"}),
        _fake_call("calculator", {"expression": "125 * 8"}),
    ]
    model = AsyncMock()
    model.generate = AsyncMock(return_value=_fake_response(function_calls=calls))
    with patch("core.chat_engine.dispatch") as mock_dispatch, pytest.raises(chat_engine.ChatEngineError):
        await chat_engine._run_turn(model, [], max_tool_calls=1)
    mock_dispatch.assert_not_called()
