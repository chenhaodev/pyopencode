"""Real language server (opt-in: pyright-langserver on PATH)."""

import os
import shutil
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration


def _pyright_stdio_cmd() -> list[str] | None:
    """Resolve a working pyright stdio command (npm global or node + bundle)."""
    js = os.environ.get("PYOPENCODE_PYRIGHT_JS")
    node = shutil.which("node")
    if js and Path(js).is_file() and node:
        return [node, js, "--stdio"]
    exe = shutil.which("pyright-langserver")
    if exe:
        return [exe, "--stdio"]
    return None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_pyright_initialize_and_goto_definition(tmp_path: Path) -> None:
    if os.environ.get("PYOPENCODE_RUN_LSP_INTEGRATION") != "1":
        pytest.skip(
            "Set PYOPENCODE_RUN_LSP_INTEGRATION=1 to run (needs pyright-langserver "
            "or PYOPENCODE_PYRIGHT_JS)"
        )
    cmd = _pyright_stdio_cmd()
    if cmd is None:
        pytest.skip(
            "No pyright-langserver on PATH and PYOPENCODE_PYRIGHT_JS unset "
            "(try: npm install -g pyright)"
        )

    mod = tmp_path / "mod.py"
    mod.write_text(
        "def foo():\n"
        "    return 42\n"
        "\n"
        "v = foo()\n",
        encoding="utf-8",
    )

    from pyopencode.tools.lsp_bridge import LSPBridge

    bridge = LSPBridge("python", str(tmp_path), server_cmd=cmd)
    try:
        await bridge.start()
    except RuntimeError as exc:
        pytest.skip(f"LSP did not start (broken shim or missing server): {exc}")

    try:
        await bridge.did_open(str(mod), mod.read_text(encoding="utf-8"))
        # "v = foo()" is line index 3; 'f' of foo at character 4
        res = await bridge.goto_definition(str(mod), 3, 4)
    finally:
        await bridge.stop()

    assert "error" not in res or res.get("error") is None, res
    r = res.get("result")
    assert r is not None, res

    if isinstance(r, dict):
        start = r.get("range", {}).get("start", {})
        assert start.get("line") == 0
    elif isinstance(r, list) and len(r) > 0:
        item = r[0]
        if "targetRange" in item:
            start = item["targetRange"]["start"]
        else:
            start = item.get("range", {}).get("start", {})
        assert start.get("line") == 0
    else:
        pytest.fail(f"Unexpected result shape: {r!r}")
