import json
from typing import Callable, Any


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
        try:
            result = tool["func"](**arguments)
            if hasattr(result, "__await__"):
                result = await result
            return str(result)
        except Exception as e:
            return f"Error executing {name}: {type(e).__name__}: {e}"

    def get_category(self, name: str) -> str:
        return self._tools.get(name, {}).get("category", "always_ask")


registry = ToolRegistry()
