from pyopencode.llm.client import LLMClient

COMPACTION_PROMPT = """Summarize the conversation above concisely. You MUST preserve:
1. What files were read, created, or modified, and a brief description of changes
2. Key technical decisions made and why
3. Current task status and any remaining work
4. Any errors encountered and how they were resolved
5. Important context about the codebase discovered

Format as a structured summary. Be concise but don't lose important details."""


async def compact_conversation(
    messages: list[dict],
    llm: LLMClient,
    summary_model: str = "qwen-turbo",
    keep_recent: int = 10,
    *,
    summary_provider_id: str | None = None,
) -> list[dict]:
    if len(messages) <= keep_recent + 2:
        return messages

    system_msg = messages[0]
    old_messages = messages[1:-keep_recent]
    recent_messages = messages[-keep_recent:]

    formatted = _format_messages_for_summary(old_messages)

    summary_response = await llm.chat(
        messages=[
            {"role": "system", "content": "You are a conversation summarizer."},
            {
                "role": "user",
                "content": f"Summarize this conversation:\n\n{formatted}\n\n{COMPACTION_PROMPT}",
            },
        ],
        model=summary_model,
        stream=False,
        provider_id=summary_provider_id,
    )

    summary_msg = {
        "role": "assistant",
        "content": (
            f"[Conversation Summary - {len(old_messages)} messages compressed]\n\n"
            f"{summary_response['content']}"
        ),
    }

    return [system_msg, summary_msg] + recent_messages


def _format_messages_for_summary(messages: list[dict]) -> str:
    parts = []
    for msg in messages:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")

        if role == "tool":
            if len(content) > 500:
                content = content[:250] + "\n...\n" + content[-250:]
            parts.append(f"[Tool Result]: {content}")
        elif role == "assistant":
            if msg.get("tool_calls"):
                calls = [tc["function"]["name"] for tc in msg["tool_calls"]]
                parts.append(f"Assistant: {content or ''} [Called: {', '.join(calls)}]")
            else:
                parts.append(f"Assistant: {content}")
        elif role == "user":
            parts.append(f"User: {content}")

    return "\n\n".join(parts)
