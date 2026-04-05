from typing import Optional

from pyopencode.memory.repomap import generate_repomap
from pyopencode.tools.registry import registry


@registry.register(
    name="get_repomap",
    description=(
        "Generate a compact code skeleton map of the project: file paths, "
        "top-level classes, functions, and signatures (Python AST). "
        "Use before large refactors to see structure without reading every file."
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
        },
        "required": [],
    },
    category="always_allow",
)
def get_repomap(root: str = ".", extensions: Optional[list[str]] = None) -> str:
    return generate_repomap(root=root, extensions=extensions)
