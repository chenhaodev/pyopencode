import litellm
from typing import AsyncIterator


class LLMClient:
    def __init__(self, config: dict):
        self.config = config
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    async def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        model: str | None = None,
        stream: bool = True,
    ) -> dict:
        model = model or self.config["model"]
        provider = self.config.get("provider", "anthropic")
        provider_config = self.config.get("providers", {}).get(provider, {})

        kwargs = {
            "model": model,
            "messages": messages,
            "temperature": self.config.get("temperature", 0),
            "max_tokens": self.config.get("max_tokens", 16384),
            "stream": stream,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        api_base = provider_config.get("api_base")
        if api_base:
            kwargs["api_base"] = api_base

        api_key_env = provider_config.get("api_key_env", "")
        if api_key_env and not api_key_env.replace("_", "").isupper():
            kwargs["api_key"] = api_key_env

        if stream:
            return await self._stream_chat(**kwargs)
        else:
            response = await litellm.acompletion(**kwargs)
            self._track_usage(response.usage)
            return self._parse_response(response)

    async def _stream_chat(self, **kwargs) -> dict:
        response = await litellm.acompletion(**kwargs)

        full_content = ""
        tool_calls = []

        async for chunk in response:
            delta = chunk.choices[0].delta

            if delta.content:
                full_content += delta.content
                print(delta.content, end="", flush=True)

            if delta.tool_calls:
                for tc in delta.tool_calls:
                    self._accumulate_tool_call(tool_calls, tc)

        print()

        if hasattr(response, "usage") and response.usage:
            self._track_usage(response.usage)

        return {
            "content": full_content,
            "tool_calls": tool_calls if tool_calls else None,
        }

    def _accumulate_tool_call(self, tool_calls: list, delta_tc):
        idx = delta_tc.index
        while len(tool_calls) <= idx:
            tool_calls.append({"id": "", "function": {"name": "", "arguments": ""}})
        if delta_tc.id:
            tool_calls[idx]["id"] = delta_tc.id
        if delta_tc.function:
            if delta_tc.function.name:
                tool_calls[idx]["function"]["name"] += delta_tc.function.name
            if delta_tc.function.arguments:
                tool_calls[idx]["function"]["arguments"] += delta_tc.function.arguments

    def _parse_response(self, response) -> dict:
        msg = response.choices[0].message
        tool_calls = None
        if msg.tool_calls:
            tool_calls = [
                {
                    "id": tc.id,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in msg.tool_calls
            ]
        return {
            "content": msg.content or "",
            "tool_calls": tool_calls,
        }

    def _track_usage(self, usage):
        if usage:
            self.total_input_tokens += getattr(usage, "prompt_tokens", 0)
            self.total_output_tokens += getattr(usage, "completion_tokens", 0)

    @property
    def total_cost_estimate(self) -> float:
        return (self.total_input_tokens * 3 + self.total_output_tokens * 15) / 1_000_000
