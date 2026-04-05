from pathlib import Path

from pyopencode.tools.registry import registry


@registry.register(
    name="write_file",
    description=(
        "Write content to a file. Creates the file if it doesn't exist. "
        "Creates parent directories as needed."
    ),
    parameters={
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Path to the file"},
            "content": {"type": "string", "description": "Full content to write"},
        },
        "required": ["file_path", "content"],
    },
    category="allow_once_then_remember",
)
def write_file(file_path: str, content: str) -> str:
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    lines = content.count("\n") + 1
    return f"Successfully wrote {lines} lines to {file_path}"
