import ast
from pathlib import Path
from typing import Optional

_IGNORE_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    ".tox",
    "dist",
    "build",
}


def generate_repomap(root: str = ".", extensions: Optional[list[str]] = None) -> str:
    if extensions is None:
        extensions = [".py"]

    root_path = Path(root)
    output_parts = []

    for ext in extensions:
        for file_path in sorted(root_path.rglob(f"*{ext}")):
            if any(part in _IGNORE_DIRS for part in file_path.parts):
                continue

            rel_path = file_path.relative_to(root_path)

            if ext == ".py":
                skeleton = _python_skeleton(file_path)
                if skeleton:
                    output_parts.append(f"## {rel_path}\n{skeleton}")

    return "\n\n".join(output_parts)


def _python_skeleton(file_path: Path) -> str:
    try:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except (SyntaxError, UnicodeDecodeError):
        return ""

    lines = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            bases = ", ".join(
                ast.dump(b) if not isinstance(b, ast.Name) else b.id for b in node.bases
            )
            lines.append(f"  class {node.name}({bases}):")
            for item in ast.iter_child_nodes(node):
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    sig = _format_func_sig(item)
                    lines.append(f"    {sig}")

        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            sig = _format_func_sig(node)
            lines.append(f"  {sig}")

        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    lines.append(f"  {target.id} = ...")

    return "\n".join(lines)


def _format_func_sig(node) -> str:
    prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
    args = []
    for arg in node.args.args:
        annotation = ""
        if arg.annotation:
            try:
                annotation = f": {ast.unparse(arg.annotation)}"
            except Exception:
                pass
        args.append(f"{arg.arg}{annotation}")

    returns = ""
    if node.returns:
        try:
            returns = f" -> {ast.unparse(node.returns)}"
        except Exception:
            pass

    return f"{prefix} {node.name}({', '.join(args)}){returns}"
