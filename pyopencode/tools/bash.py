import subprocess

from pyopencode.tools.registry import registry
from pyopencode.utils.truncate import truncate_output


@registry.register(
    name="bash",
    description=(
        "Execute a bash command. Use for running tests, installing packages, "
        "git operations, exploring file system, etc."
    ),
    parameters={
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "The bash command to execute"},
            "timeout": {
                "type": "integer",
                "description": "Timeout in seconds (default 60)",
            },
        },
        "required": ["command"],
    },
    category="always_ask",
)
def bash(command: str, timeout: int = 60) -> str:
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=".",
        )
        output = ""
        if result.stdout:
            output += result.stdout
        if result.stderr:
            output += (
                ("\n--- STDERR ---\n" + result.stderr) if output else result.stderr
            )
        if not output:
            output = "(no output)"

        output = truncate_output(output)

        return f"[Exit code: {result.returncode}]\n{output}"

    except subprocess.TimeoutExpired:
        return f"Error: Command timed out after {timeout} seconds."
    except Exception as e:
        return f"Error: {type(e).__name__}: {e}"
