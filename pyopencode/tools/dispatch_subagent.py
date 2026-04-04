from pyopencode.tools.registry import registry

_llm_instance = None


def set_llm_instance(llm):
    global _llm_instance
    _llm_instance = llm


@registry.register(
    name="dispatch_subagents",
    description=(
        "Dispatch multiple sub-agents to work on tasks in parallel. "
        "Each sub-agent can read files and search but cannot write or execute commands. "
        "Use this for parallel information gathering."
    ),
    parameters={
        "type": "object",
        "properties": {
            "tasks": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of task descriptions for each sub-agent",
            },
        },
        "required": ["tasks"],
    },
    category="always_allow",
)
async def dispatch_subagents(tasks: list[str]) -> str:
    from pyopencode.core.subagent import run_subagents

    if _llm_instance is None:
        return "Error: LLM instance not configured for sub-agents."

    results = await run_subagents(_llm_instance, tasks)

    output = ""
    for i, (task, result) in enumerate(zip(tasks, results)):
        output += f"\n--- Sub-agent {i + 1}: {task} ---\n{result}\n"
    return output
