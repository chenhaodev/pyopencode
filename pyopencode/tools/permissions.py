import json


class PermissionManager:
    def __init__(self, config: dict):
        self.config = config.get("permissions", {})
        self.approved_tools: set[str] = set()
        self.always_allow = set(self.config.get("always_allow", []))
        self.remember_after_allow = set(self.config.get("allow_once_then_remember", []))

    def check(self, tool_name: str, arguments: dict) -> bool:
        if tool_name in self.always_allow:
            return True
        if tool_name in self.approved_tools:
            return True
        return False

    def approve(self, tool_name: str):
        if tool_name in self.remember_after_allow:
            self.approved_tools.add(tool_name)

    def format_request(self, tool_name: str, arguments: dict) -> str:
        args_str = json.dumps(arguments, indent=2, ensure_ascii=False)
        return (
            f"🔐 Permission required: {tool_name}\n{args_str}\n\nAllow? [y/N/always]: "
        )
