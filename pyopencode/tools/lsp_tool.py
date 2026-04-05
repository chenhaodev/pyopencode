"""Optional LSP tool: go-to-definition via local language server."""

import json
from pathlib import Path

from pyopencode.tools.registry import registry


@registry.register(
    name="lsp_goto_definition",
    description=(
        "Use the language server for this workspace to resolve go-to-definition "
        "at a position in a source file. Requires the matching server on PATH "
        "(e.g. pyright-langserver for python, typescript-language-server for "
        "typescript). Spawns a short-lived LSP process; can be slow."
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
    from pyopencode.tools.lsp_bridge import LSPBridge

    root = str(Path.cwd().resolve())
    bridge = LSPBridge(language, root)
    try:
        await bridge.start()
    except ValueError as exc:
        return f"Error: {exc}"
    except RuntimeError as exc:
        return f"Error: {exc}"
    except (FileNotFoundError, OSError) as exc:
        return (
            f"Error: could not start LSP server for '{language}'. "
            f"Is it installed and on PATH? ({type(exc).__name__}: {exc})"
        )
    try:
        abs_fp = str(Path(file_path).expanduser().resolve())
        try:
            src = Path(abs_fp).read_text(encoding="utf-8")
        except OSError as exc:
            return f"Error: cannot read file: {exc}"
        await bridge.did_open(abs_fp, src)
        doc = await bridge.goto_definition(abs_fp, line, character)
    finally:
        await bridge.stop()
    return json.dumps(doc, ensure_ascii=False, indent=2)
