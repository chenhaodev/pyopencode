import subprocess
from typing import Optional

from pyopencode.tools.registry import registry


@registry.register(
    name="grep_search",
    description="Search for a regex pattern in files using ripgrep (rg) or grep.",
    parameters={
        "type": "object",
        "properties": {
            "pattern": {"type": "string", "description": "Regex pattern to search"},
            "path": {
                "type": "string",
                "description": "File or directory path (default: '.')",
            },
            "include": {
                "type": "string",
                "description": "File glob to include (e.g. '*.py')",
            },
        },
        "required": ["pattern"],
    },
    category="always_allow",
)
def grep_search(pattern: str, path: str = ".", include: Optional[str] = None) -> str:
    try:
        cmd = ["rg", "--line-number", "--no-heading", "--color=never", "-e", pattern]
        if include:
            cmd.extend(["--glob", include])
        cmd.append(path)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    except FileNotFoundError:
        cmd = ["grep", "-rn", "-E", pattern]
        if include:
            cmd.extend(["--include", include])
        cmd.append(path)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

    output = result.stdout.strip()
    if not output:
        return f"No matches found for pattern '{pattern}'"

    lines = output.split("\n")
    if len(lines) > 50:
        return "\n".join(lines[:50]) + f"\n... ({len(lines) - 50} more matches)"
    return output
