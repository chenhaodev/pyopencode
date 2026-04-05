from typing import Optional


class ModelRouter:
    """Pick a model id per task kind (compaction, subagent) or context size.

    Tiers mirror the ORIGIN plan: strong default chat, fast subagents, cheap
    compaction summaries, long-context when the estimated window is huge.
    """

    def __init__(self, config: dict):
        self.config = config
        default_strong = config.get("strong_model") or config.get(
            "model",
            "claude-sonnet-4-20250514",
        )
        self.model_tiers = {
            "strong": default_strong,
            "fast": config.get("fast_model", "qwen-turbo"),
            "long_context": config.get("long_context_model", "gemini-2.0-flash"),
            "cheap": config.get("cheap_model", "minimax-2.5"),
        }

    def select(self, task_hint: Optional[str] = None, token_count: int = 0) -> str:
        if task_hint == "compaction":
            return self.model_tiers["cheap"]
        if task_hint == "subagent":
            return self.model_tiers["fast"]
        if token_count > 100000:
            return self.model_tiers["long_context"]
        return self.model_tiers["strong"]
