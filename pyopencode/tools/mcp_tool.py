"""Optional MCP tool bus: list and call tools on configured stdio servers."""

from __future__ import annotations

import json
from typing import Any

from pyopencode.tools.registry import registry

_mcp_servers: dict[str, dict[str, Any]] = {}


def configure_mcp_servers(config: dict) -> None:
    """Called from AgentLoop with merged config."""
    global _mcp_servers
    mcp = config.get("mcp") or {}
    servers = mcp.get("servers")
    if isinstance(servers, dict):
        _mcp_servers = {
            str(k): dict(v)
            for k, v in servers.items()
            if isinstance(v, dict)
        }
    else:
        _mcp_servers = {}


def _server_names() -> list[str]:
    return sorted(_mcp_servers.keys())


@registry.register(
    name="mcp_list_tools",
    description=(
        "List tools exposed by a configured MCP server (stdio). "
        "Configure under [mcp.servers] in config TOML with a command array."
    ),
    parameters={
        "type": "object",
        "properties": {
            "server": {
                "type": "string",
                "description": "Server name from mcp.servers config",
            },
        },
        "required": ["server"],
    },
    category="always_allow",
)
async def mcp_list_tools(server: str) -> str:
    if not _mcp_servers:
        return (
            "Error: no MCP servers configured. Add [mcp.servers.name] "
            "with command = [\"…\"] in ~/.pyopencode/config.toml or "
            ".pyopencode.toml."
        )
    if server not in _mcp_servers:
        return (
            f"Error: unknown MCP server '{server}'. "
            f"Known: {', '.join(_server_names())}"
        )
    from pathlib import Path

    from pyopencode.tools.mcp_session import get_mcp_bridge

    root = str(Path.cwd().resolve())
    try:
        bridge = await get_mcp_bridge(server, _mcp_servers[server], root)
        doc = await bridge.list_tools()
    except (ValueError, RuntimeError, OSError, FileNotFoundError) as exc:
        return f"Error: {type(exc).__name__}: {exc}"
    return json.dumps(doc, ensure_ascii=False, indent=2)


@registry.register(
    name="mcp_call_tool",
    description=(
        "Invoke a tool on an MCP server. Use mcp_list_tools first to see names "
        "and argument shapes."
    ),
    parameters={
        "type": "object",
        "properties": {
            "server": {"type": "string"},
            "tool_name": {"type": "string"},
            "arguments": {
                "type": "object",
                "description": "JSON object passed to the MCP tool",
            },
        },
        "required": ["server", "tool_name", "arguments"],
    },
    category="always_ask",
)
async def mcp_call_tool(
    server: str,
    tool_name: str,
    arguments: dict[str, Any],
) -> str:
    if server not in _mcp_servers:
        return (
            f"Error: unknown MCP server '{server}'. "
            f"Known: {', '.join(_server_names())}"
        )
    from pathlib import Path

    from pyopencode.tools.mcp_session import get_mcp_bridge

    root = str(Path.cwd().resolve())
    try:
        bridge = await get_mcp_bridge(server, _mcp_servers[server], root)
        doc = await bridge.call_tool(tool_name, arguments)
    except (ValueError, RuntimeError, OSError, FileNotFoundError) as exc:
        return f"Error: {type(exc).__name__}: {exc}"
    return json.dumps(doc, ensure_ascii=False, indent=2)
