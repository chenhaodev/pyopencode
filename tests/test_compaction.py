from unittest.mock import AsyncMock, MagicMock

import pytest

from pyopencode.core.compaction import (
    _format_messages_for_summary,
    compact_conversation,
)


class TestFormatMessagesForSummary:
    def test_user_message(self):
        messages = [{"role": "user", "content": "hello"}]
        result = _format_messages_for_summary(messages)
        assert "User: hello" in result

    def test_assistant_message(self):
        messages = [{"role": "assistant", "content": "hi there"}]
        result = _format_messages_for_summary(messages)
        assert "Assistant: hi there" in result

    def test_tool_result_truncated(self):
        long_content = "x" * 1000
        messages = [{"role": "tool", "content": long_content}]
        result = _format_messages_for_summary(messages)
        assert "[Tool Result]:" in result
        assert len(result) < len(long_content)

    def test_assistant_with_tool_calls(self):
        messages = [
            {
                "role": "assistant",
                "content": "I'll read the file",
                "tool_calls": [{"function": {"name": "read_file"}}],
            }
        ]
        result = _format_messages_for_summary(messages)
        assert "read_file" in result
        assert "Called:" in result


class TestCompactConversation:
    @pytest.mark.asyncio
    async def test_no_compaction_when_few_messages(self):
        messages = [{"role": "system", "content": "sys"}] + [
            {"role": "user", "content": f"msg{i}"} for i in range(5)
        ]
        mock_llm = MagicMock()

        result = await compact_conversation(messages, mock_llm, keep_recent=10)
        assert result == messages
        mock_llm.chat.assert_not_called()

    @pytest.mark.asyncio
    async def test_compaction_when_many_messages(self):
        system = {"role": "system", "content": "system prompt"}
        old_messages = [{"role": "user", "content": f"old{i}"} for i in range(20)]
        recent = [{"role": "user", "content": f"recent{i}"} for i in range(5)]
        messages = [system] + old_messages + recent

        mock_llm = AsyncMock()
        mock_llm.chat.return_value = {"content": "summary of old messages"}

        result = await compact_conversation(
            messages, mock_llm, summary_model="test-model", keep_recent=5
        )

        assert result[0] == system
        assert any("summary" in str(m.get("content", "")).lower() for m in result)
        assert result[-5:] == recent
        mock_llm.chat.assert_called_once()
