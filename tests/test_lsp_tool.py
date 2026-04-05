"""lsp_goto_definition tool (LSPBridge mocked)."""

import json

import pytest

import pyopencode.tools.lsp_tool  # noqa: F401
from pyopencode.tools.registry import registry


@pytest.mark.asyncio
async def test_lsp_goto_definition_calls_bridge(monkeypatch, tmp_path):
    foo = tmp_path / "foo.py"
    foo.write_text("# x\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    trace: list[str] = []

    class FakeBridge:
        def __init__(self, language: str, project_root: str):
            self.language = language
            self.root = project_root
            trace.append(f"init:{language}")

        async def start(self) -> None:
            trace.append("start")

        async def stop(self) -> None:
            trace.append("stop")

        async def did_open(self, file_path: str, text: str) -> None:
            trace.append(f"did_open:{file_path}:{len(text)}")

        async def goto_definition(self, file_path: str, line: int, character: int):
            trace.append(f"goto:{file_path}:{line}:{character}")
            return {"result": [{"uri": "file:///x.py"}]}

    monkeypatch.setattr(
        "pyopencode.tools.lsp_bridge.LSPBridge",
        FakeBridge,
    )

    payload = {
        "language": "python",
        "file_path": str(foo),
        "line": 0,
        "character": 0,
    }
    out = await registry.execute("lsp_goto_definition", json.dumps(payload))
    data = json.loads(out)
    assert data["result"][0]["uri"] == "file:///x.py"
    assert "start" in trace
    assert "stop" in trace
    assert any(x.startswith("goto:") for x in trace)
    assert any(x.startswith("did_open:") for x in trace)
