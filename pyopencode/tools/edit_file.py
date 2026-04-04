from pathlib import Path
from pyopencode.tools.registry import registry


@registry.register(
    name="edit_file",
    description=(
        "Edit a file by replacing an exact string match. "
        "You MUST read the file first to get the exact content to replace. "
        "The old_string must match EXACTLY including whitespace and indentation."
    ),
    parameters={
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Path to the file"},
            "old_string": {
                "type": "string",
                "description": "Exact string to find and replace",
            },
            "new_string": {"type": "string", "description": "Replacement string"},
        },
        "required": ["file_path", "old_string", "new_string"],
    },
    category="allow_once_then_remember",
)
def edit_file(file_path: str, old_string: str, new_string: str) -> str:
    path = Path(file_path)
    if not path.exists():
        return f"Error: File '{file_path}' does not exist. Use write_file to create new files."

    content = path.read_text(encoding="utf-8")

    count = content.count(old_string)
    if count == 0:
        return (
            f"Error: old_string not found in {file_path}. "
            f"Make sure you read the file first and the string matches exactly."
        )
    if count > 1:
        return (
            f"Error: old_string found {count} times in {file_path}. "
            f"Provide a more unique string to match exactly once."
        )

    new_content = content.replace(old_string, new_string, 1)
    path.write_text(new_content, encoding="utf-8")

    return f"Successfully edited {file_path}: replaced 1 occurrence."
