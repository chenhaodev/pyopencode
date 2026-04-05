from typing import Optional

from pyopencode.memory.repomap import generate_repomap
from pyopencode.tools.registry import registry


@registry.register(
    name="get_repomap",
    description=(
        "Generate a compact code skeleton map of the project: file paths, "
        "top-level classes, functions, and signatures. Uses Python AST by default; "
        "set prefer_tree_sitter=true when pyopencode[repomap] (tree-sitter) is "
        "installed for grammar-based parsing."
    ),
    parameters={
        "type": "object",
        "properties": {
            "root": {
                "type": "string",
                "description": "Root directory to scan (default: current project)",
                "default": ".",
            },
            "extensions": {
                "type": "array",
                "items": {"type": "string"},
                "description": "File extensions to include, e.g. [\".py\"]",
            },
            "prefer_tree_sitter": {
                "type": "boolean",
                "description": (
                    "If true, use tree-sitter for .py when tree-sitter-languages "
                    "is installed; otherwise fall back to AST"
                ),
                "default": False,
            },
        },
        "required": [],
    },
    category="always_allow",
)
def get_repomap(
    root: str = ".",
    extensions: Optional[list[str]] = None,
    prefer_tree_sitter: bool = False,
) -> str:
    return generate_repomap(
        root=root,
        extensions=extensions,
        prefer_tree_sitter=prefer_tree_sitter,
    )
