import difflib


def generate_diff(original: str, modified: str, filename: str = "file") -> str:
    original_lines = original.splitlines(keepends=True)
    modified_lines = modified.splitlines(keepends=True)
    diff = difflib.unified_diff(
        original_lines,
        modified_lines,
        fromfile=f"a/{filename}",
        tofile=f"b/{filename}",
    )
    return "".join(diff)


def apply_patch(original: str, patch: str) -> str | None:
    lines = original.splitlines(keepends=True)
    patched = []
    i = 0
    patch_lines = patch.splitlines(keepends=True)
    pi = 0

    while pi < len(patch_lines):
        line = patch_lines[pi]
        if line.startswith("@@"):
            pi += 1
            continue
        if line.startswith("---") or line.startswith("+++"):
            pi += 1
            continue
        if line.startswith("+"):
            patched.append(line[1:])
            pi += 1
        elif line.startswith("-"):
            if i < len(lines):
                i += 1
            pi += 1
        else:
            if i < len(lines):
                patched.append(lines[i])
                i += 1
            pi += 1

    patched.extend(lines[i:])
    return "".join(patched)
