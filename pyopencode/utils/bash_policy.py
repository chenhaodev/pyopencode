"""Conservative checks before running shell commands."""

from __future__ import annotations

import re

# Patterns that are almost always unsafe in an agent context.
_DENY_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"^\s*:\s*\(\)\s*\{"), "fork bombs / self-replicating shell"),
    (re.compile(r"rm\s+[^\n]*\s+/\s*$"), "rm targeting filesystem root"),
    (re.compile(r"rm\s+[^\n]*\s+/\s+"), "rm with root path segment"),
    (re.compile(r">\s*/dev/sd[a-z]"), "direct block device overwrite"),
    (re.compile(r"mkfs\."), "filesystem format"),
    (re.compile(r"dd\s+.*\bof=/dev/"), "dd to device nodes"),
    (re.compile(r"\|\s*bash\b"), "piped execution into bash"),
    (re.compile(r"\|\s*sh\b"), "piped execution into sh"),
    (re.compile(r"curl\s+[^\n]*\|\s*"), "curl pipe (download & execute)"),
    (re.compile(r"wget\s+[^\n]*\|\s*"), "wget pipe (download & execute)"),
    (re.compile(r"chmod\s+[^\n]*\s+777\s+"), "world-writable chmod"),
)


def bash_command_blocked_reason(command: str) -> str | None:
    """Return a short reason if the command must not run, else None."""
    line = command.strip()
    if not line:
        return "empty command"
    lower = line.lower()
    if "rm -rf /" in lower or re.search(r"rm\s+-rf\s+/\s*$", lower):
        return "recursive delete of filesystem root"
    for pat, label in _DENY_PATTERNS:
        if pat.search(line):
            return label
    return None
