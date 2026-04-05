"""Pool MCP stdio subprocesses per server definition."""

from __future__ import annotations

import asyncio
import atexit
from typing import Any, Optional

from pyopencode.tools.mcp_bridge import McpStdioBridge, expand_mcp_command

_bridges: dict[str, McpStdioBridge] = {}
_pool_lock = asyncio.Lock()
_atexit_registered = False


def _key(server_name: str, command: tuple[str, ...], cwd: Optional[str]) -> str:
    cwd_part = cwd or ""
    return f"{server_name}\x00{command!r}\x00{cwd_part}"


def _ensure_atexit() -> None:
    global _atexit_registered
    if not _atexit_registered:
        atexit.register(_shutdown_all_sync)
        _atexit_registered = True


def _shutdown_all_sync() -> None:
    for bridge in list(_bridges.values()):
        proc = bridge.process
        if proc is None:
            continue
        try:
            proc.terminate()
            proc.wait(timeout=2)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
    _bridges.clear()


async def get_mcp_bridge(
    server_name: str,
    definition: dict[str, Any],
    project_root: str,
) -> McpStdioBridge:
    raw_cmd = definition.get("command")
    if not raw_cmd or not isinstance(raw_cmd, list):
        raise ValueError(f"MCP server '{server_name}' needs a command list")
    command = expand_mcp_command([str(x) for x in raw_cmd], project_root)
    cwd = definition.get("cwd")
    env = definition.get("env")
    if env is not None and not isinstance(env, dict):
        env = None
    env_s = {str(k): str(v) for k, v in env.items()} if env else None
    cmd_t = tuple(command)
    cwd_s = str(cwd) if cwd else None
    k = _key(server_name, cmd_t, cwd_s)
    _ensure_atexit()

    async with _pool_lock:
        existing = _bridges.get(k)
        if existing is not None:
            proc = existing.process
            if proc is not None and proc.poll() is None:
                return existing
            await existing.stop()
            del _bridges[k]

        bridge = McpStdioBridge(command, cwd=cwd_s, env=env_s)
        await bridge.start()
        _bridges[k] = bridge
        return bridge


async def shutdown_all_mcp_sessions() -> None:
    async with _pool_lock:
        for bridge in list(_bridges.values()):
            await bridge.stop()
        _bridges.clear()
