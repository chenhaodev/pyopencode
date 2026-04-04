import json


def count_messages_tokens(messages: list[dict]) -> int:
    total = 0
    for msg in messages:
        total += _count_message_tokens(msg)
    return total


def _count_message_tokens(msg: dict) -> int:
    role = msg.get("role", "")
    content = msg.get("content", "") or ""
    tool_calls = msg.get("tool_calls", []) or []

    tokens = _estimate_tokens(role) + _estimate_tokens(content)

    for tc in tool_calls:
        fn = tc.get("function", {})
        tokens += _estimate_tokens(fn.get("name", ""))
        tokens += _estimate_tokens(fn.get("arguments", ""))

    return tokens + 4


def _estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, len(text) // 4)
