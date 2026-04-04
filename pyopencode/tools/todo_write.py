from pyopencode.tools.registry import registry

_todos: list[dict] = []


@registry.register(
    name="todo_write",
    description=(
        "Create or update a task checklist to track progress on multi-step tasks. "
        "Use this at the start of complex tasks to plan, and update as you complete steps. "
        "Always include ALL tasks (not just remaining ones) with their current status."
    ),
    parameters={
        "type": "object",
        "properties": {
            "todos": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "task": {"type": "string"},
                        "status": {
                            "type": "string",
                            "enum": ["pending", "in_progress", "done"],
                        },
                    },
                    "required": ["task", "status"],
                },
                "description": "Full list of tasks with their status",
            },
        },
        "required": ["todos"],
    },
    category="always_allow",
)
def todo_write(todos: list[dict]) -> str:
    global _todos
    _todos = todos
    icons = {"pending": "☐", "in_progress": "⟳", "done": "☑"}
    lines = [f"{icons.get(t['status'], '?')} {t['task']}" for t in todos]
    done = sum(1 for t in todos if t["status"] == "done")
    return f"Task list updated ({done}/{len(todos)} done):\n" + "\n".join(lines)


def get_todos() -> list[dict]:
    return _todos
