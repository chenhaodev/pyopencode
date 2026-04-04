from pathlib import Path
from pyopencode.tools.registry import registry


@registry.register(
    name="read_file",
    description="Read the contents of a file. You MUST use this before editing any file.",
    parameters={
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Path to the file to read"},
            "start_line": {
                "type": "integer",
                "description": "Start line (1-indexed, optional)",
            },
            "end_line": {
                "type": "integer",
                "description": "End line (1-indexed, inclusive, optional)",
            },
        },
        "required": ["file_path"],
    },
    category="always_allow",
)
def read_file(file_path: str, start_line: int = None, end_line: int = None) -> str:
    path = Path(file_path)
    if not path.exists():
        return f"Error: File '{file_path}' does not exist."
    if not path.is_file():
        return f"Error: '{file_path}' is not a file."

    content = path.read_text(encoding="utf-8", errors="replace")
    lines = content.split("\n")

    if start_line or end_line:
        start = (start_line or 1) - 1
        end = end_line or len(lines)
        lines = lines[start:end]
        total = len(content.split("\n"))
        header = f"[Lines {start + 1}-{min(end, total)} of {total}]\n"
        return header + "\n".join(lines)

    return content
