"""LSP JSON-RPC framing (mock process, no real language server)."""

import io
import json
from unittest.mock import MagicMock

import pytest

from pyopencode.tools.lsp_bridge import LSPBridge


def _framed_response(obj: dict) -> bytes:
    body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
    return header + body


@pytest.mark.asyncio
async def test_request_uses_utf8_byte_length_for_content_length():
    stdin = io.BytesIO()
    resp = {"jsonrpc": "2.0", "id": 1, "result": {"capabilities": {}}}
    stdout = io.BytesIO(_framed_response(resp))

    proc = MagicMock()
    proc.stdin = stdin
    proc.stdout = stdout

    bridge = LSPBridge("python", "/tmp/proj")
    bridge._request_id = 0
    bridge.process = proc

    out = await bridge._request(
        "initialize",
        {"rootUri": "file:///x", "note": "日本"},
    )
    assert out["result"]["capabilities"] == {}

    raw = stdin.getvalue()
    sep = b"\r\n\r\n"
    sep_i = raw.index(sep) + len(sep)
    payload = raw[sep_i:]
    header_line = raw[: raw.index(b"\r\n")].decode("ascii")
    declared = int(header_line.split(":")[1].strip())
    assert declared == len(payload)
    parsed = json.loads(payload.decode("utf-8"))
    assert parsed["method"] == "initialize"
    assert parsed["params"]["note"] == "日本"


@pytest.mark.asyncio
async def test_read_response_invalid_json_returns_empty_dict():
    bad = b"Content-Length: 2\r\n\r\nxx"
    stdout = io.BytesIO(bad)
    proc = MagicMock()
    proc.stdin = io.BytesIO()
    proc.stdout = stdout
    bridge = LSPBridge("python", ".")
    bridge._request_id = 0
    bridge.process = proc
    out = await bridge._request("x", {})
    assert out == {}
