class ModelRouter:
    def __init__(self, config: dict):
        self.config = config
        self.model_tiers = {
            "strong": config.get("strong_model", "claude-sonnet-4-20250514"),
            "fast": config.get("fast_model", "qwen-turbo"),
            "long_context": config.get("long_context_model", "gemini-2.0-flash"),
            "cheap": config.get("cheap_model", "minimax-2.5"),
        }

    def select(self, task_hint: str = None, token_count: int = 0) -> str:
        if task_hint == "compaction":
            return self.model_tiers["cheap"]
        if task_hint == "subagent":
            return self.model_tiers["fast"]
        if token_count > 100000:
            return self.model_tiers["long_context"]
        return self.model_tiers["strong"]
