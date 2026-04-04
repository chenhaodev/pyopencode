from pathlib import Path
from pyopencode.tools.registry import registry

_IGNORE_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", ".tox"}


@registry.register(
    name="glob_search",
    description="Search for files matching a glob pattern.",
    parameters={
        "type": "object",
        "properties": {
            "pattern": {
                "type": "string",
                "description": "Glob pattern (e.g. '**/*.py')",
            },
            "root": {
                "type": "string",
                "description": "Root directory (default: current dir)",
            },
        },
        "required": ["pattern"],
    },
    category="always_allow",
)
def glob_search(pattern: str, root: str = ".") -> str:
    matches = sorted(Path(root).glob(pattern))
    filtered = [m for m in matches if not any(part in _IGNORE_DIRS for part in m.parts)]

    if not filtered:
        return f"No files found matching '{pattern}'"

    result = f"Found {len(filtered)} files:\n"
    for f in filtered[:100]:
        result += f"  {f}\n"
    if len(filtered) > 100:
        result += f"  ... and {len(filtered) - 100} more\n"
    return result
