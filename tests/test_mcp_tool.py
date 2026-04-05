"""MCP tool registration (no live server)."""

import pytest

from pyopencode.tools import mcp_tool


@pytest.mark.asyncio
async def test_mcp_list_tools_no_servers_configured() -> None:
    mcp_tool.configure_mcp_servers({})
    out = await mcp_tool.mcp_list_tools("any")
    assert "no mcp servers" in out.lower()


@pytest.mark.asyncio
async def test_mcp_list_tools_unknown_server() -> None:
    mcp_tool.configure_mcp_servers(
        {"mcp": {"servers": {"a": {"command": ["true"]}}}},
    )
    out = await mcp_tool.mcp_list_tools("missing")
    assert "unknown" in out.lower()
