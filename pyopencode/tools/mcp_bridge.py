"""Minimal MCP client over stdio (Content-Length JSON-RPC, like LSP)."""

from __future__ import annotations

import asyncio
import json
import subprocess
from pathlib import Path
from typing import Any, Optional


class McpStdioBridge:
    """One subprocess speaking MCP over stdin/stdout."""

    def __init__(
        self,
        command: list[str],
        *,
        cwd: Optional[str] = None,
        env: Optional[dict[str, str]] = None,
    ):
        self.command = list(command)
        self.cwd = cwd
        self.env = env
        self.process: Optional[subprocess.Popen] = None
        self._request_id = 0

    async def start(self) -> None:
        popen_env = None
        if self.env:
            import os

            popen_env = {**os.environ, **self.env}
        self.process = subprocess.Popen(
            self.command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=self.cwd or None,
            env=popen_env,
        )
        await asyncio.sleep(0.05)
        self._ensure_alive("startup")
        init = await self._request(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "pyopencode", "version": "0.1.0"},
            },
        )
        if init.get("error"):
            raise RuntimeError(f"MCP initialize error: {init.get('error')!r}")
        await self._send_notification("notifications/initialized", {})

    async def stop(self) -> None:
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None

    async def list_tools(self) -> dict[str, Any]:
        return await self._request("tools/list", {})

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        return await self._request(
            "tools/call",
            {"name": name, "arguments": arguments},
        )

    def _ensure_alive(self, phase: str) -> None:
        if not self.process:
            raise RuntimeError(f"MCP not running ({phase})")
        code = self.process.poll()
        if code is not None:
            err = self._read_stderr_tail()
            raise RuntimeError(
                f"MCP process exited (code={code}) during {phase}. stderr: {err!r}"
            )

    def _read_stderr_tail(self) -> str:
        if not self.process or not self.process.stderr:
            return ""
        if self.process.poll() is None:
            return ""
        try:
            raw = self.process.stderr.read()
        except OSError:
            return ""
        return raw.decode("utf-8", errors="replace")[:8000]

    async def _read_one_message(self) -> dict[str, Any]:
        if not self.process or not self.process.stdout:
            return {}
        header_line = self.process.stdout.readline()
        if not header_line:
            return {}
        try:
            header_text = header_line.decode("utf-8").strip()
        except UnicodeDecodeError:
            return {}
        if not header_text.startswith("Content-Length:"):
            return {}
        length = int(header_text.split(":", 1)[1].strip())
        self.process.stdout.readline()
        raw = self.process.stdout.read(length)
        if len(raw) < length:
            return {}
        try:
            return json.loads(raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {}

    def _handle_incoming_message(self, msg: dict[str, Any]) -> None:
        # Server-initiated requests could be handled here later.
        _ = msg

    async def _read_until_response_id(self, req_id: int) -> dict[str, Any]:
        for _ in range(512):
            msg = await self._read_one_message()
            if not msg:
                return {}
            mid = msg.get("id")
            if mid is not None and mid == req_id:
                return msg
            self._handle_incoming_message(msg)
        return {}

    async def _send_notification(self, method: str, params: dict[str, Any]) -> None:
        if not self.process or not self.process.stdin:
            return
        self._ensure_alive(f"notification {method}")
        nmsg = {"jsonrpc": "2.0", "method": method, "params": params}
        body_bytes = json.dumps(
            nmsg,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        header = f"Content-Length: {len(body_bytes)}\r\n\r\n".encode("ascii")
        self.process.stdin.write(header + body_bytes)
        self.process.stdin.flush()

    async def _request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        if not self.process or not self.process.stdin:
            return {}
        self._ensure_alive(f"request {method}")
        self._request_id += 1
        rid = self._request_id
        msg = {
            "jsonrpc": "2.0",
            "id": rid,
            "method": method,
            "params": params,
        }
        body = json.dumps(msg, ensure_ascii=False, separators=(",", ":"))
        body_bytes = body.encode("utf-8")
        header = f"Content-Length: {len(body_bytes)}\r\n\r\n".encode("ascii")
        self.process.stdin.write(header + body_bytes)
        self.process.stdin.flush()
        return await self._read_until_response_id(rid)


def expand_mcp_command(command: list[str], project_root: str) -> list[str]:
    """Replace ``{root}`` placeholders in command argv with project path."""
    root = str(Path(project_root).expanduser().resolve())
    return [part.replace("{root}", root) for part in command]
