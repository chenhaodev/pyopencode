"""Reuse one LSP subprocess per (project root, language[, server_cmd]).

Avoids spawning pyright-langserver on every go-to-definition call. Processes are
terminated synchronously on interpreter exit via :mod:`atexit`.
"""

from __future__ import annotations

import asyncio
import atexit
from pathlib import Path
from typing import Optional

from pyopencode.tools.lsp_bridge import LSPBridge

_bridges: dict[str, LSPBridge] = {}
_pool_lock = asyncio.Lock()
_atexit_registered = False


def _session_key(
    language: str,
    root: str,
    server_cmd: Optional[tuple[str, ...]],
) -> str:
    root_resolved = str(Path(root).expanduser().resolve())
    cmd_part = "\x1e".join(server_cmd) if server_cmd else ""
    return f"{language}\x00{root_resolved}\x00{cmd_part}"


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
            proc.wait(timeout=3)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
    _bridges.clear()


async def get_lsp_bridge(
    language: str,
    project_root: str,
    *,
    server_cmd: Optional[list[str]] = None,
) -> LSPBridge:
    """Return a started bridge, creating or reviving the pooled process as needed."""
    root = str(Path(project_root).expanduser().resolve())
    cmd_t = tuple(server_cmd) if server_cmd else None
    key = _session_key(language, root, cmd_t)
    _ensure_atexit()

    async with _pool_lock:
        existing = _bridges.get(key)
        if existing is not None:
            proc = existing.process
            if proc is not None and proc.poll() is None:
                return existing
            await existing.stop()
            del _bridges[key]

        bridge = LSPBridge(language, root, server_cmd=server_cmd)
        await bridge.start()
        _bridges[key] = bridge
        return bridge


async def shutdown_all_lsp_sessions() -> None:
    """Stop every pooled LSP process (for tests)."""
    async with _pool_lock:
        for bridge in list(_bridges.values()):
            await bridge.stop()
        _bridges.clear()
