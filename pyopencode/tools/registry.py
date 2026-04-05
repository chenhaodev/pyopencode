import asyncio
import inspect
import json
from typing import Callable

from pyopencode.tools.tool_runtime import get_settings


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, dict] = {}

    def register(
        self,
        name: str,
        description: str,
        parameters: dict,
        category: str = "always_ask",
    ):
        def decorator(func: Callable):
            self._tools[name] = {
                "func": func,
                "schema": {
                    "type": "function",
                    "function": {
                        "name": name,
                        "description": description,
                        "parameters": parameters,
                    },
                },
                "category": category,
            }
            return func

        return decorator

    def get_schemas(self) -> list[dict]:
        return [t["schema"] for t in self._tools.values()]

    async def execute(self, name: str, arguments: str | dict) -> str:
        if name not in self._tools:
            return f"Error: Unknown tool '{name}'"

        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError as e:
                return f"Error: Invalid JSON arguments: {e}"

        tool = self._tools[name]
        func = tool["func"]
        settings = get_settings()
        timeout_async = float(settings["async_timeout_sec"])
        timeout_sync = float(settings["sync_timeout_sec"])
        max_retries = int(settings["max_retries"])
        retry_delay = float(settings["retry_delay_sec"])

        for attempt in range(max_retries + 1):
            try:
                if inspect.iscoroutinefunction(func):
                    out = await asyncio.wait_for(
                        func(**arguments),
                        timeout=timeout_async,
                    )
                else:
                    out = await asyncio.wait_for(
                        asyncio.to_thread(lambda: func(**arguments)),
                        timeout=timeout_sync,
                    )
                return str(out)
            except asyncio.TimeoutError:
                return f"Error: tool '{name}' timed out"
            except Exception as e:
                if attempt < max_retries:
                    await asyncio.sleep(retry_delay)
                    continue
                return f"Error executing {name}: {type(e).__name__}: {e}"

    def get_category(self, name: str) -> str:
        return self._tools.get(name, {}).get("category", "always_ask")


registry = ToolRegistry()
