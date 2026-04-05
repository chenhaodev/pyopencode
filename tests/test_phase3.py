"""Phase 3: repomap, SubAgent, dispatch_subagents (LLM mocked)."""

import pytest
from unittest.mock import AsyncMock, patch

from pyopencode.memory.repomap import generate_repomap


def test_generate_repomap_includes_defs_and_class(tmp_path):
    (tmp_path / "sample.py").write_text(
        "def hello():\n"
        "    return 1\n"
        "\n"
        "class SampleCls:\n"
        "    def method(self):\n"
        "        pass\n",
        encoding="utf-8",
    )
    text = generate_repomap(str(tmp_path))
    assert "sample.py" in text
    assert "def hello" in text
    assert "class SampleCls" in text
    assert "def method" in text


@pytest.mark.asyncio
async def test_subagent_returns_content_without_tools():
    from pyopencode.core.subagent import SubAgent

    llm = AsyncMock()
    llm.chat = AsyncMock(
        return_value={"content": "plain answer", "tool_calls": None}
    )
    agent = SubAgent(llm, "do something")
    result = await agent.run()
    assert result == "plain answer"
    llm.chat.assert_awaited()


@pytest.mark.asyncio
async def test_subagent_runs_tool_then_finishes():
    from pyopencode.core.subagent import SubAgent

    llm = AsyncMock()
    first = {
        "content": "",
        "tool_calls": [
            {
                "id": "tc1",
                "function": {
                    "name": "read_file",
                    "arguments": '{"file_path": "x.py"}',
                },
            }
        ],
    }
    second = {"content": "after tool", "tool_calls": None}
    llm.chat = AsyncMock(side_effect=[first, second])

    with patch(
        "pyopencode.core.subagent.registry.execute",
        new_callable=AsyncMock,
    ) as mock_exec:
        mock_exec.return_value = "file body"
        agent = SubAgent(llm, "read x.py")
        result = await agent.run()

    assert result == "after tool"
    mock_exec.assert_awaited()
    call_kw = mock_exec.await_args
    assert call_kw[0][0] == "read_file"


@pytest.mark.asyncio
async def test_get_repomap_tool_registered(tmp_path):
    import pyopencode.tools.repomap_tool  # noqa: F401
    from pyopencode.tools.registry import registry

    (tmp_path / "a.py").write_text("def foo():\n    pass\n", encoding="utf-8")
    out = await registry.execute(
        "get_repomap",
        {"root": str(tmp_path), "extensions": [".py"]},
    )
    assert "foo" in out
    assert "a.py" in out


@pytest.mark.asyncio
async def test_dispatch_subagents_formats_output():
    from pyopencode.tools.dispatch_subagent import (
        dispatch_subagents,
        set_llm_instance,
    )

    llm = AsyncMock()
    llm.chat = AsyncMock(
        return_value={"content": "sub result", "tool_calls": None}
    )
    set_llm_instance(llm)
    try:
        out = await dispatch_subagents(["alpha task", "beta task"])
    finally:
        set_llm_instance(None)

    assert "alpha task" in out
    assert "beta task" in out
    assert "sub result" in out
    assert "Sub-agent" in out
