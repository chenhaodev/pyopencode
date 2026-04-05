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


def generate_repomap(
    root: str = ".",
    extensions: Optional[list[str]] = None,
    *,
    prefer_tree_sitter: bool = False,
) -> str:
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
                skeleton = ""
                if prefer_tree_sitter:
                    ts = _python_skeleton_tree_sitter(file_path)
                    if ts:
                        skeleton = ts
                if not skeleton:
                    skeleton = _python_skeleton(file_path)
                if skeleton:
                    output_parts.append(f"## {rel_path}\n{skeleton}")

    return "\n\n".join(output_parts)


def _python_skeleton_tree_sitter(file_path: Path) -> str:
    try:
        from tree_sitter_languages import get_parser
    except ImportError:
        return ""

    try:
        source = file_path.read_bytes()
    except OSError:
        return ""

    parser = get_parser("python")
    tree = parser.parse(source)
    lines: list[str] = []

    root = tree.root_node
    for child in root.children:
        t = child.type
        if t == "function_definition":
            name_node = child.child_by_field_name("name")
            if name_node:
                nm = source[name_node.start_byte : name_node.end_byte].decode(
                    "utf-8",
                    errors="replace",
                )
                lines.append(f"  def {nm}(...)")
        elif t == "class_definition":
            name_node = child.child_by_field_name("name")
            if name_node:
                nm = source[name_node.start_byte : name_node.end_byte].decode(
                    "utf-8",
                    errors="replace",
                )
                lines.append(f"  class {nm}:")
            body = child.child_by_field_name("body")
            if body is None:
                for ch in child.children:
                    if ch.type == "block":
                        body = ch
                        break
            if body:
                for item in body.children:
                    if item.type in (
                        "function_definition",
                        "async_function_definition",
                    ):
                        nn = item.child_by_field_name("name")
                        if nn:
                            fn = source[nn.start_byte : nn.end_byte].decode(
                                "utf-8",
                                errors="replace",
                            )
                            prefix = (
                                "async def"
                                if item.type == "async_function_definition"
                                else "def"
                            )
                            lines.append(f"    {prefix} {fn}(...)")

    return "\n".join(lines)


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
