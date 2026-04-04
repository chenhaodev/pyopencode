import json
import asyncio
from pyopencode.llm.client import LLMClient
from pyopencode.tools.registry import registry
from pyopencode.tools.permissions import PermissionManager
from pyopencode.memory.agent_md import load_memory

import pyopencode.tools.read_file
import pyopencode.tools.write_file
import pyopencode.tools.edit_file
import pyopencode.tools.bash
import pyopencode.tools.glob_search
import pyopencode.tools.grep_search
import pyopencode.tools.todo_write
import pyopencode.tools.git_tools
import pyopencode.tools.dispatch_subagent
from pyopencode.tools.dispatch_subagent import set_llm_instance

SYSTEM_PROMPT = """You are PyOpenCode, an expert AI software engineer operating in the user's terminal.
You have direct access to the filesystem and can execute commands.

## Identity
- You are autonomous: you explore, plan, implement, and verify without asking for permission at every step.
- You are thorough: you read before editing, test after changing, and verify your assumptions.
- You communicate concisely: explain what you'll do, do it, report the result.

## Mandatory Rules
1. **ALWAYS read before edit**: Never edit a file based on memory. Always read_file first.
2. **Use todo_write for complex tasks**: Any task requiring 3+ steps → create a checklist first.
3. **Verify changes**: After modifying code, run tests or at minimum re-read the file.
4. **Atomic edits**: Make one logical change at a time. Don't combine unrelated changes.
5. **Exact matching**: edit_file's old_string must match the file EXACTLY, including all whitespace.
6. **No hallucinated paths**: Always use glob_search or bash(ls) to discover file paths. Never guess.

## Workflow
For complex tasks, follow this pattern:
1. EXPLORE: Use glob_search, grep_search, read_file to understand the codebase
2. PLAN: Use todo_write to create a step-by-step plan
3. IMPLEMENT: Make changes one file at a time, updating todo after each step
4. VERIFY: Run tests (bash), re-read files, check for errors
5. COMMIT: If using git, suggest a commit with a clear message

## Parallel Work
When you need to gather information from multiple files, use dispatch_subagents to read them in parallel.

## Communication Style
- Start with a brief plan (1-3 sentences)
- During work, print minimal status updates
- End with a summary of what was done

{memory_section}
"""


class AgentLoop:
    def __init__(self, config: dict):
        self.config = config
        self.llm = LLMClient(config)
        set_llm_instance(self.llm)
        self.permissions = PermissionManager(config)
        self.messages: list[dict] = []
        self.max_iterations = 50

    def _build_system_prompt(self) -> str:
        memory = load_memory()
        memory_section = ""
        if memory:
            memory_section = f"## Project Memory (from AGENT.md)\n{memory}"
        return SYSTEM_PROMPT.format(memory_section=memory_section)

    async def run(self, initial_prompt: str = None, resume: bool = False):
        print("🤖 PyOpenCode ready. Type 'exit' to quit, 'clear' to reset.\n")

        self.messages = [{"role": "system", "content": self._build_system_prompt()}]

        if initial_prompt:
            await self._process_user_input(initial_prompt)

        while True:
            try:
                user_input = input("\n> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nBye!")
                break

            if not user_input:
                continue
            if user_input.lower() == "exit":
                break
            if user_input.lower() == "clear":
                self.messages = [
                    {"role": "system", "content": self._build_system_prompt()}
                ]
                print("Conversation cleared.")
                continue
            if user_input.lower() == "cost":
                print(
                    f"Tokens: {self.llm.total_input_tokens} in / "
                    f"{self.llm.total_output_tokens} out | "
                    f"Est. cost: ${self.llm.total_cost_estimate:.4f}"
                )
                continue

            await self._process_user_input(user_input)

    async def _process_user_input(self, user_input: str):
        self.messages.append({"role": "user", "content": user_input})
        await self._agent_loop()

    async def _agent_loop(self):
        for iteration in range(self.max_iterations):
            response = await self.llm.chat(
                messages=self.messages,
                tools=registry.get_schemas(),
            )

            assistant_msg: dict = {"role": "assistant"}
            if response["content"]:
                assistant_msg["content"] = response["content"]
            if response["tool_calls"]:
                assistant_msg["tool_calls"] = [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {
                            "name": tc["function"]["name"],
                            "arguments": tc["function"]["arguments"],
                        },
                    }
                    for tc in response["tool_calls"]
                ]
            self.messages.append(assistant_msg)

            if not response["tool_calls"]:
                break

            tool_results = await self._execute_tool_calls(response["tool_calls"])
            self.messages.extend(tool_results)

            await self._maybe_compact()

        else:
            print("\n⚠️  Reached maximum iterations. Stopping.")

    async def _execute_tool_calls(self, tool_calls: list[dict]) -> list[dict]:
        results = []

        for tc in tool_calls:
            name = tc["function"]["name"]
            try:
                args = json.loads(tc["function"]["arguments"])
            except json.JSONDecodeError:
                args = {}

            if not self.permissions.check(name, args):
                prompt = self.permissions.format_request(name, args)
                print(prompt, end="")
                try:
                    answer = input().strip().lower()
                except (EOFError, KeyboardInterrupt):
                    answer = "n"

                if answer in ("y", "yes"):
                    self.permissions.approve(name)
                elif answer == "always":
                    self.permissions.approved_tools.add(name)
                else:
                    results.append(
                        {
                            "role": "tool",
                            "tool_call_id": tc["id"],
                            "content": "Permission denied by user.",
                        }
                    )
                    continue

            print(f"  🔧 {name}({json.dumps(args, ensure_ascii=False)[:100]})")
            result = await registry.execute(name, args)

            if len(result) > 20000:
                result = result[:10000] + "\n...(truncated)...\n" + result[-10000:]

            results.append(
                {
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": result,
                }
            )

        return results

    async def _maybe_compact(self):
        from pyopencode.llm.token_counter import count_messages_tokens
        from pyopencode.core.compaction import compact_conversation

        total_tokens = count_messages_tokens(self.messages)
        max_tokens = self.config.get("max_context_tokens", 200000)
        threshold = self.config["compaction"]["threshold_ratio"]

        if total_tokens > max_tokens * threshold:
            print("\n📦 Compacting conversation history...")
            self.messages = await compact_conversation(
                self.messages,
                self.llm,
                summary_model=self.config["compaction"]["summary_model"],
                keep_recent=self.config["compaction"]["keep_recent"],
            )
            new_tokens = count_messages_tokens(self.messages)
            print(f"   Compressed: {total_tokens} → {new_tokens} tokens\n")
