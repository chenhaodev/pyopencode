"""Optional LSP tools: go-to-definition and find-references via pooled language server."""

import json
import os
import shutil
from pathlib import Path
from typing import Optional

from pyopencode.tools.registry import registry


def _optional_pyright_js_cmd(language: str) -> Optional[list[str]]:
    """Match integration tests: node + PYOPENCODE_PYRIGHT_JS for Python when set."""
    if language != "python":
        return None
    js = os.environ.get("PYOPENCODE_PYRIGHT_JS")
    node = shutil.which("node")
    if js and Path(js).is_file() and node:
        return [node, js, "--stdio"]
    return None


async def _pooled_bridge(language: str, root: str):
    from pyopencode.tools.lsp_session import get_lsp_bridge

    cmd = _optional_pyright_js_cmd(language)
    return await get_lsp_bridge(language, root, server_cmd=cmd)


def _read_source_sync(abs_fp: str) -> str:
    return Path(abs_fp).read_text(encoding="utf-8")


async def _open_or_sync(bridge, language: str, abs_fp: str, *, sync: bool) -> str | None:
    try:
        text = _read_source_sync(abs_fp)
    except OSError as exc:
        return f"Error: cannot read file: {exc}"
    if sync:
        await bridge.did_change(abs_fp, text, language_id=language)
    else:
        await bridge.did_open(abs_fp, text, language_id=language)
    return None


@registry.register(
    name="lsp_goto_definition",
    description=(
        "Use the language server for this workspace to resolve go-to-definition "
        "at a position in a source file. Requires the matching server on PATH "
        "(e.g. pyright-langserver for python, typescript-language-server for "
        "typescript). Reuses one server process per workspace when possible."
    ),
    parameters={
        "type": "object",
        "properties": {
            "language": {
                "type": "string",
                "description": (
                    "One of: python, typescript, go, rust "
                    "(must match LSPBridge.SERVERS)"
                ),
            },
            "file_path": {
                "type": "string",
                "description": "Absolute or project-relative path to the file",
            },
            "line": {
                "type": "integer",
                "description": "0-based line number",
            },
            "character": {
                "type": "integer",
                "description": "0-based UTF-16 code unit offset on the line",
            },
        },
        "required": ["language", "file_path", "line", "character"],
    },
    category="always_ask",
)
async def lsp_goto_definition(
    language: str,
    file_path: str,
    line: int,
    character: int,
) -> str:
    root = str(Path.cwd().resolve())
    try:
        bridge = await _pooled_bridge(language, root)
    except ValueError as exc:
        return f"Error: {exc}"
    except RuntimeError as exc:
        return f"Error: {exc}"
    except (FileNotFoundError, OSError) as exc:
        return (
            f"Error: could not start LSP server for '{language}'. "
            f"Is it installed and on PATH? ({type(exc).__name__}: {exc})"
        )
    abs_fp = str(Path(file_path).expanduser().resolve())
    try:
        src = Path(abs_fp).read_text(encoding="utf-8")
    except OSError as exc:
        return f"Error: cannot read file: {exc}"
    await bridge.did_open(abs_fp, src)
    doc = await bridge.goto_definition(abs_fp, line, character)
    return json.dumps(doc, ensure_ascii=False, indent=2)


@registry.register(
    name="lsp_find_references",
    description=(
        "Use the language server to list references to the symbol at a position. "
        "Same server requirements as lsp_goto_definition; shares the pooled process."
    ),
    parameters={
        "type": "object",
        "properties": {
            "language": {
                "type": "string",
                "description": (
                    "One of: python, typescript, go, rust "
                    "(must match LSPBridge.SERVERS)"
                ),
            },
            "file_path": {
                "type": "string",
                "description": "Absolute or project-relative path to the file",
            },
            "line": {
                "type": "integer",
                "description": "0-based line number",
            },
            "character": {
                "type": "integer",
                "description": "0-based UTF-16 code unit offset on the line",
            },
        },
        "required": ["language", "file_path", "line", "character"],
    },
    category="always_ask",
)
async def lsp_find_references(
    language: str,
    file_path: str,
    line: int,
    character: int,
) -> str:
    root = str(Path.cwd().resolve())
    try:
        bridge = await _pooled_bridge(language, root)
    except ValueError as exc:
        return f"Error: {exc}"
    except RuntimeError as exc:
        return f"Error: {exc}"
    except (FileNotFoundError, OSError) as exc:
        return (
            f"Error: could not start LSP server for '{language}'. "
            f"Is it installed and on PATH? ({type(exc).__name__}: {exc})"
        )
    abs_fp = str(Path(file_path).expanduser().resolve())
    try:
        src = Path(abs_fp).read_text(encoding="utf-8")
    except OSError as exc:
        return f"Error: cannot read file: {exc}"
    await bridge.did_open(abs_fp, src)
    refs = await bridge.find_references(abs_fp, line, character)
    return json.dumps(refs, ensure_ascii=False, indent=2)


@registry.register(
    name="lsp_sync_document",
    description=(
        "After you edit a file on disk, notify the pooled language server via "
        "textDocument/didChange (full text) so diagnostics and other LSP "
        "features see the latest content."
    ),
    parameters={
        "type": "object",
        "properties": {
            "language": {
                "type": "string",
                "description": "python | typescript | go | rust",
            },
            "file_path": {"type": "string"},
        },
        "required": ["language", "file_path"],
    },
    category="always_allow",
)
async def lsp_sync_document(language: str, file_path: str) -> str:
    root = str(Path.cwd().resolve())
    try:
        bridge = await _pooled_bridge(language, root)
    except (ValueError, RuntimeError) as exc:
        return f"Error: {exc}"
    except (FileNotFoundError, OSError) as exc:
        return f"Error: could not start LSP server: {exc}"
    abs_fp = str(Path(file_path).expanduser().resolve())
    err = await _open_or_sync(bridge, language, abs_fp, sync=True)
    if err:
        return err
    return f"LSP synced (didChange) for {abs_fp}"


@registry.register(
    name="lsp_get_diagnostics",
    description=(
        "Return language-server diagnostics for a file (errors/warnings). "
        "Opens the file if needed; waits briefly for publishDiagnostics."
    ),
    parameters={
        "type": "object",
        "properties": {
            "language": {"type": "string"},
            "file_path": {"type": "string"},
        },
        "required": ["language", "file_path"],
    },
    category="always_allow",
)
async def lsp_get_diagnostics(language: str, file_path: str) -> str:
    root = str(Path.cwd().resolve())
    try:
        bridge = await _pooled_bridge(language, root)
    except (ValueError, RuntimeError) as exc:
        return f"Error: {exc}"
    except (FileNotFoundError, OSError) as exc:
        return f"Error: could not start LSP server: {exc}"
    abs_fp = str(Path(file_path).expanduser().resolve())
    try:
        src = _read_source_sync(abs_fp)
    except OSError as exc:
        return f"Error: cannot read file: {exc}"
    await bridge.did_open(abs_fp, src, language_id=language)
    await bridge.settle_diagnostics()
    diags = bridge.diagnostics_for_file(abs_fp)
    return json.dumps(diags, ensure_ascii=False, indent=2)


@registry.register(
    name="lsp_hover",
    description="Request hover / quick-info at a position from the language server.",
    parameters={
        "type": "object",
        "properties": {
            "language": {"type": "string"},
            "file_path": {"type": "string"},
            "line": {"type": "integer", "description": "0-based line"},
            "character": {
                "type": "integer",
                "description": "0-based UTF-16 code unit on the line",
            },
        },
        "required": ["language", "file_path", "line", "character"],
    },
    category="always_allow",
)
async def lsp_hover(
    language: str,
    file_path: str,
    line: int,
    character: int,
) -> str:
    root = str(Path.cwd().resolve())
    try:
        bridge = await _pooled_bridge(language, root)
    except (ValueError, RuntimeError) as exc:
        return f"Error: {exc}"
    except (FileNotFoundError, OSError) as exc:
        return f"Error: could not start LSP server: {exc}"
    abs_fp = str(Path(file_path).expanduser().resolve())
    try:
        src = _read_source_sync(abs_fp)
    except OSError as exc:
        return f"Error: cannot read file: {exc}"
    await bridge.did_open(abs_fp, src, language_id=language)
    doc = await bridge.hover(abs_fp, line, character)
    return json.dumps(doc, ensure_ascii=False, indent=2)


@registry.register(
    name="lsp_document_symbols",
    description=(
        "List symbols in a document (outline) from the language server "
        "(textDocument/documentSymbol)."
    ),
    parameters={
        "type": "object",
        "properties": {
            "language": {"type": "string"},
            "file_path": {"type": "string"},
        },
        "required": ["language", "file_path"],
    },
    category="always_allow",
)
async def lsp_document_symbols(language: str, file_path: str) -> str:
    root = str(Path.cwd().resolve())
    try:
        bridge = await _pooled_bridge(language, root)
    except (ValueError, RuntimeError) as exc:
        return f"Error: {exc}"
    except (FileNotFoundError, OSError) as exc:
        return f"Error: could not start LSP server: {exc}"
    abs_fp = str(Path(file_path).expanduser().resolve())
    try:
        src = _read_source_sync(abs_fp)
    except OSError as exc:
        return f"Error: cannot read file: {exc}"
    await bridge.did_open(abs_fp, src, language_id=language)
    doc = await bridge.document_symbols(abs_fp)
    return json.dumps(doc, ensure_ascii=False, indent=2)
