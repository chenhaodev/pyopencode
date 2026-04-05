import asyncio

from pyopencode.llm.client import LLMClient
from pyopencode.tools.registry import registry

SUBAGENT_PROMPT = """You are a focused sub-agent. Complete the specific task assigned to you.
Be concise and return only the essential result. Do not explain your process unless asked.

Your task: {task}"""


class SubAgent:
    def __init__(
        self,
        llm: LLMClient,
        task: str,
        tools: list[str] = None,
        *,
        model: str | None = None,
        provider_id: str | None = None,
    ):
        self.llm = llm
        self.task = task
        self._model = model
        self._provider_id = provider_id
        self.allowed_tools = tools or ["read_file", "glob_search", "grep_search"]
        self.messages = [
            {"role": "system", "content": SUBAGENT_PROMPT.format(task=task)},
            {"role": "user", "content": task},
        ]

    def _get_tool_schemas(self) -> list[dict]:
        return [
            s
            for s in registry.get_schemas()
            if s["function"]["name"] in self.allowed_tools
        ]

    async def run(self, max_iterations: int = 10) -> str:
        for _ in range(max_iterations):
            chat_kw: dict = {
                "messages": self.messages,
                "tools": self._get_tool_schemas(),
                "stream": False,
            }
            if self._model is not None:
                chat_kw["model"] = self._model
            if self._provider_id is not None:
                chat_kw["provider_id"] = self._provider_id
            response = await self.llm.chat(**chat_kw)

            self.messages.append({"role": "assistant", **response})

            if not response.get("tool_calls"):
                return response.get("content", "")

            for tc in response["tool_calls"]:
                result = await registry.execute(
                    tc["function"]["name"],
                    tc["function"]["arguments"],
                )
                self.messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": result,
                    }
                )

        return "Sub-agent reached iteration limit."


async def run_subagents(llm: LLMClient, tasks: list[str]) -> list[str]:
    from pyopencode.core.router import ModelRouter
    from pyopencode.llm.client import infer_provider_id_for_model

    router = ModelRouter(llm.config)
    sub_model = router.select("subagent")
    sub_provider = infer_provider_id_for_model(sub_model, llm.config)
    agents = [
        SubAgent(
            llm,
            task,
            model=sub_model,
            provider_id=sub_provider,
        )
        for task in tasks
    ]
    results = await asyncio.gather(*[agent.run() for agent in agents])
    return list(results)
