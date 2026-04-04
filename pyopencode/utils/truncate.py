def truncate_output(text: str, max_lines: int = 400) -> str:
    lines = text.split("\n")
    if len(lines) <= max_lines:
        return text

    head = max_lines // 2
    tail = max_lines // 2
    truncated = len(lines) - head - tail

    return "\n".join(
        lines[:head] + [f"\n... ({truncated} lines truncated) ...\n"] + lines[-tail:]
    )
