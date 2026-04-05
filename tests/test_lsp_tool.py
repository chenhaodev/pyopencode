"""LSP tools (pooled bridge mocked via get_lsp_bridge)."""

import json
from pathlib import Path

import pytest

import pyopencode.tools.lsp_tool  # noqa: F401
from pyopencode.tools.registry import registry


@pytest.mark.asyncio
async def test_lsp_goto_definition_uses_pooled_bridge(monkeypatch, tmp_path):
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

        async def find_references(self, file_path: str, line: int, character: int):
            trace.append(f"refs:{file_path}:{line}:{character}")
            return [{"uri": "file:///y.py"}]

    async def fake_get(
        language: str,
        project_root: str,
        *,
        server_cmd=None,
    ):
        b = FakeBridge(language, project_root)
        await b.start()
        return b

    monkeypatch.setattr(
        "pyopencode.tools.lsp_session.get_lsp_bridge",
        fake_get,
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
    assert "stop" not in trace
    assert any(x.startswith("goto:") for x in trace)
    assert any(x.startswith("did_open:") for x in trace)


@pytest.mark.asyncio
async def test_lsp_find_references_uses_pooled_bridge(monkeypatch, tmp_path):
    foo = tmp_path / "bar.py"
    foo.write_text("def f():\n  pass\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    trace: list[str] = []

    class FakeBridge:
        def __init__(self, language: str, project_root: str):
            self.language = language
            self.root = project_root

        async def start(self) -> None:
            trace.append("start")

        async def did_open(self, file_path: str, text: str) -> None:
            trace.append("did_open")

        async def find_references(self, file_path: str, line: int, character: int):
            trace.append("refs")
            return [{"uri": "file:///ref.py"}]

    async def fake_get(language: str, project_root: str, *, server_cmd=None):
        b = FakeBridge(language, project_root)
        await b.start()
        return b

    monkeypatch.setattr(
        "pyopencode.tools.lsp_session.get_lsp_bridge",
        fake_get,
    )
    payload = {
        "language": "python",
        "file_path": str(foo),
        "line": 0,
        "character": 0,
    }
    out = await registry.execute("lsp_find_references", json.dumps(payload))
    data = json.loads(out)
    assert data[0]["uri"] == "file:///ref.py"
    assert "refs" in trace
    assert "stop" not in trace


@pytest.mark.asyncio
async def test_lsp_pool_reuses_bridge(monkeypatch, tmp_path):
    foo = tmp_path / "z.py"
    foo.write_text("x = 1\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    from pyopencode.tools import lsp_session

    await lsp_session.shutdown_all_lsp_sessions()
    inits: list[int] = []

    class CountBridge:
        def __init__(
            self,
            language: str,
            project_root: str,
            *,
            server_cmd=None,
        ):
            inits.append(1)
            self.language = language
            self.project_root = project_root
            self.process = None

        async def start(self) -> None:
            class P:
                def poll(self_inner):
                    return None

            self.process = P()

        async def stop(self) -> None:
            self.process = None

    monkeypatch.setattr(lsp_session, "LSPBridge", CountBridge)

    root = str(Path(tmp_path).resolve())
    a = await lsp_session.get_lsp_bridge("python", root)
    b = await lsp_session.get_lsp_bridge("python", root)
    assert a is b
    assert len(inits) == 1
    await lsp_session.shutdown_all_lsp_sessions()
