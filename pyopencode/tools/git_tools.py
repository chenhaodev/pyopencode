import subprocess
from pyopencode.tools.registry import registry


@registry.register(
    name="git_diff",
    description="Show git diff of current changes.",
    parameters={
        "type": "object",
        "properties": {
            "staged": {"type": "boolean", "description": "Show staged changes only"},
            "file_path": {"type": "string", "description": "Specific file to diff"},
        },
    },
    category="always_allow",
)
def git_diff(staged: bool = False, file_path: str = None) -> str:
    cmd = ["git", "diff"]
    if staged:
        cmd.append("--staged")
    if file_path:
        cmd.extend(["--", file_path])
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout or "(no changes)"


@registry.register(
    name="git_commit",
    description="Stage all changes and commit with a message.",
    parameters={
        "type": "object",
        "properties": {
            "message": {"type": "string", "description": "Commit message"},
        },
        "required": ["message"],
    },
    category="allow_once_then_remember",
)
def git_commit(message: str) -> str:
    subprocess.run(["git", "add", "-A"], capture_output=True)
    result = subprocess.run(
        ["git", "commit", "-m", message], capture_output=True, text=True
    )
    return result.stdout + result.stderr


@registry.register(
    name="git_log",
    description="Show recent git log.",
    parameters={
        "type": "object",
        "properties": {
            "count": {
                "type": "integer",
                "description": "Number of commits to show (default 10)",
            },
        },
    },
    category="always_allow",
)
def git_log(count: int = 10) -> str:
    result = subprocess.run(
        ["git", "log", f"-{count}", "--oneline", "--decorate"],
        capture_output=True,
        text=True,
    )
    return result.stdout or "(no git history)"
