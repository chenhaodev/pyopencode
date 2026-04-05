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
