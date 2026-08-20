from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from core import chat_engine


def _fake_call(name, args):
    return SimpleNamespace(name=name, args=args)


def _fake_response(function_calls=None, text=None):
    parts = []
    for call in function_calls or []:
        parts.append(SimpleNamespace(function_call=call, text=None))
    if text is not None:
        parts.append(SimpleNamespace(function_call=None, text=text))
    return SimpleNamespace(
        candidates=[SimpleNamespace(content=SimpleNamespace(role="model", parts=parts))]
    )


def _patch_content_types():
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


def _settings(max_tool_calls=5):
    return SimpleNamespace(max_tool_calls=max_tool_calls)


async def test_send_message_rejects_empty_text():
    with pytest.raises(chat_engine.ChatEngineError):
        await chat_engine.send_message("user-1", "   ")


async def test_send_message_is_stateless_normal_chat():
    specs = [SimpleNamespace(name="calculator"), SimpleNamespace(name="get_weather")]
    p1, p2, p3 = _patch_content_types()
    with p1, p2, p3, patch("core.chat_engine.get_settings", return_value=_settings()), patch(
        "core.chat_engine.load_builtin_tools", return_value=specs
    ), patch("core.chat_engine.list_tool_specs", return_value=specs), patch(
        "core.chat_engine.get_model"
    ) as get_model:
        model = AsyncMock()
        model.generate = AsyncMock(return_value=_fake_response(text="Hello there"))
        get_model.return_value = model
        assert await chat_engine.send_message("user-1", "hi") == "Hello there"
        get_model.assert_called_once_with(tools=specs)
        sent = model.generate.await_args.args[0]
        assert len(sent) == 1
        assert sent[0].role == "user"
        assert sent[0].parts[0].text == "hi"


async def test_single_tool_call_uses_gemini_role_sequence():
    call = _fake_call("calculator", {"expression": "27 * 14 + 35"})
    first = _fake_response(function_calls=[call])
    model = AsyncMock()
    model.generate = AsyncMock(side_effect=[first, _fake_response(text="413")])
    p1, p2, p3 = _patch_content_types()
    with p1, p2, p3, patch("core.chat_engine.dispatch", return_value=413) as dispatch:
        assert await chat_engine._run_turn(
            model, [SimpleNamespace(role="user", parts=[])], 5
        ) == "413"
    dispatch.assert_called_once_with("calculator", {"expression": "27 * 14 + 35"})
    contents = model.generate.await_args_list[1].args[0]
    assert [item.role for item in contents] == ["user", "model", "user"]
    assert contents[1] is first.candidates[0].content
    assert all(item.role != "tool" for item in contents)


async def test_multiple_sequential_tool_calls():
    model = AsyncMock()
    model.generate = AsyncMock(side_effect=[
        _fake_response(function_calls=[_fake_call("calculator", {"expression": "2+2"})]),
        _fake_response(function_calls=[_fake_call("calculator", {"expression": "4*2"})]),
        _fake_response(text="8"),
    ])
    with patch("core.chat_engine.dispatch", side_effect=[4, 8]) as dispatch:
        assert await chat_engine._run_turn(model, [], 2) == "8"
    assert dispatch.call_count == 2


async def test_multiple_calls_in_one_response():
    calls = [
        _fake_call("get_weather", {"city": "Lahore"}),
        _fake_call("calculator", {"expression": "125 * 8"}),
    ]
    model = AsyncMock()
    model.generate = AsyncMock(
        side_effect=[_fake_response(function_calls=calls), _fake_response(text="done")]
    )
    with patch("core.chat_engine.dispatch", side_effect=[{"temperature_c": 30}, 1000]):
        assert await chat_engine._run_turn(model, [], 2) == "done"
    responses = model.generate.await_args_list[1].args[0][-1]
    assert responses.role == "user"
    assert len(responses.parts) == 2


@pytest.mark.parametrize(
    ("side_effect", "expected"),
    [
        (chat_engine.ToolNotFoundError("missing"), "error"),
        (chat_engine.ToolExecutionError("failed"), "error"),
    ],
)
async def test_tool_failures_become_structured_responses(side_effect, expected):
    with patch("core.chat_engine.dispatch", side_effect=side_effect):
        result = await chat_engine._execute_tool("broken", {})
    assert expected in result


async def test_max_tool_calls_prevents_extra_dispatch():
    calls = [_fake_call("a", {}), _fake_call("b", {})]
    model = AsyncMock()
    model.generate = AsyncMock(return_value=_fake_response(function_calls=calls))
    with patch("core.chat_engine.dispatch") as dispatch, pytest.raises(chat_engine.ChatEngineError):
        await chat_engine._run_turn(model, [], 1)
    dispatch.assert_not_called()


async def test_malformed_response_raises():
    model = AsyncMock()
    model.generate = AsyncMock(return_value=SimpleNamespace(candidates=[]))
    with pytest.raises(chat_engine.ChatEngineError):
        await chat_engine._run_turn(model, [], 1)


def test_history_conversion_helper_uses_only_gemini_roles():
    history = [
        {"role": "user", "content": "question"},
        {"role": "assistant", "content": "answer"},
        {"role": "system", "content": "ignored"},
        {"role": "tool", "content": "ignored"},
    ]
    contents = chat_engine._build_contents(history, "new")
    assert [content.role for content in contents] == ["user", "model", "user"]
