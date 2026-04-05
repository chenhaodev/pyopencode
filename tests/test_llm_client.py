import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from pyopencode.llm.client import LLMClient
from pyopencode.llm.token_counter import count_messages_tokens, _estimate_tokens


class TestTokenCounter:
    def test_empty_messages(self):
        assert count_messages_tokens([]) == 0

    def test_single_message(self):
        messages = [{"role": "user", "content": "hello world"}]
        tokens = count_messages_tokens(messages)
        assert tokens > 0

    def test_estimate_tokens_empty(self):
        assert _estimate_tokens("") == 0

    def test_estimate_tokens_scales_with_length(self):
        short = _estimate_tokens("hi")
        long = _estimate_tokens("a" * 100)
        assert long > short

    def test_messages_with_tool_calls(self):
        messages = [
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": "tc_1",
                        "function": {
                            "name": "read_file",
                            "arguments": '{"file_path": "foo.py"}',
                        },
                    }
                ],
            }
        ]
        tokens = count_messages_tokens(messages)
        assert tokens > 0


class TestLLMClientCostEstimate:
    def test_cost_estimate_zero_at_start(self):
        client = LLMClient({"model": "test", "temperature": 0, "max_tokens": 100})
        assert client.total_cost_estimate == 0.0

    def test_cost_estimate_increases_with_tokens(self):
        client = LLMClient({"model": "test", "temperature": 0, "max_tokens": 100})
        client.total_input_tokens = 1000
        client.total_output_tokens = 500
        assert client.total_cost_estimate > 0.0

    def test_track_usage(self):
        client = LLMClient({"model": "test", "temperature": 0, "max_tokens": 100})
        usage = MagicMock()
        usage.prompt_tokens = 100
        usage.completion_tokens = 50
        client._track_usage(usage)
        assert client.total_input_tokens == 100
        assert client.total_output_tokens == 50

    def test_accumulate_tool_call(self):
        client = LLMClient({"model": "test", "temperature": 0, "max_tokens": 100})
        tool_calls = []

        delta = MagicMock()
        delta.index = 0
        delta.id = "tc_1"
        delta.function.name = "read_file"
        delta.function.arguments = '{"file_path":'

        client._accumulate_tool_call(tool_calls, delta)
        assert len(tool_calls) == 1
        assert tool_calls[0]["id"] == "tc_1"
        assert tool_calls[0]["function"]["name"] == "read_file"

        delta2 = MagicMock()
        delta2.index = 0
        delta2.id = None
        delta2.function.name = ""
        delta2.function.arguments = ' "foo.py"}'

        client._accumulate_tool_call(tool_calls, delta2)
        assert tool_calls[0]["function"]["arguments"] == '{"file_path": "foo.py"}'


@pytest.mark.asyncio
async def test_chat_passes_api_key_from_env(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-from-env")
    config = {
        "model": "gpt-4o-mini",
        "provider": "openai",
        "temperature": 0,
        "max_tokens": 100,
        "providers": {
            "openai": {"api_key_env": "OPENAI_API_KEY"},
        },
    }
    client = LLMClient(config)
    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock()]
    mock_resp.choices[0].message = MagicMock()
    mock_resp.choices[0].message.content = "hi"
    mock_resp.choices[0].message.tool_calls = None
    mock_resp.usage = MagicMock(prompt_tokens=1, completion_tokens=1)
    with patch(
        "pyopencode.llm.client.litellm.acompletion",
        new_callable=AsyncMock,
    ) as ac:
        ac.return_value = mock_resp
        await client.chat([{"role": "user", "content": "x"}], stream=False)
    ac.assert_awaited_once()
    assert ac.await_args.kwargs.get("api_key") == "sk-test-from-env"
