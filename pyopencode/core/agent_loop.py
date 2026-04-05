import json
import uuid
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Optional

import pyopencode.tools.bash
import pyopencode.tools.dispatch_subagent
import pyopencode.tools.edit_file
import pyopencode.tools.git_tools
import pyopencode.tools.glob_search
import pyopencode.tools.grep_search
import pyopencode.tools.lsp_tool  # noqa: F401 - tool registration
import pyopencode.tools.mcp_tool  # noqa: F401 - tool registration
import pyopencode.tools.read_file
import pyopencode.tools.repomap_tool  # noqa: F401 - tool registration
import pyopencode.tools.todo_write
import pyopencode.tools.write_file  # noqa: F401 - imported for tool registration
from pyopencode.core.router import ModelRouter
from pyopencode.llm.client import LLMClient, infer_provider_id_for_model
from pyopencode.llm.token_counter import count_messages_tokens
from pyopencode.memory.agent_md import load_memory
from pyopencode.memory.session import SessionStore
from pyopencode.tools.dispatch_subagent import set_llm_instance
from pyopencode.tools.mcp_tool import configure_mcp_servers
from pyopencode.tools.permissions import PermissionManager
from pyopencode.tools.registry import registry
from pyopencode.tools.tool_runtime import configure_from_config
from pyopencode.utils.diff import generate_diff

PermissionHandler = Callable[[str, dict], Awaitable[str]]


def _read_file_text_if_exists(file_path: str) -> str | None:
    p = Path(file_path).expanduser()
    if not p.is_file():
        return None
    try:
        return p.read_text(encoding="utf-8")
    except OSError:
        return None


def _build_edit_diff(name: str, args: dict, before: str | None) -> str | None:
    fp = args.get("file_path")
    if not fp or name not in ("edit_file", "write_file"):
        return None
    p = Path(str(fp)).expanduser()
    after = ""
    if p.is_file():
        try:
            after = p.read_text(encoding="utf-8")
        except OSError:
            return None
    b = before if before is not None else ""
    diff = generate_diff(b, after, p.name)
    if not diff.strip():
        return None
    if len(diff) > 12000:
        return diff[:12000] + "\n…\n"
    return diff

SYSTEM_PROMPT = """You are PyOpenCode, an expert AI software engineer \
operating in the user's terminal. You have direct access to the filesystem \
and can execute commands.

Product stance: like **OpenCode** (small, hackable agent core) plus **Claude Code**-style \
discipline — read before edit, todo_write for multi-step work, tiered tool permissions, \
and reliable string-replacement edits.

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
Use get_repomap for a quick skeleton of the Python tree (AST; optional tree-sitter). \
After editing files, call lsp_sync_document so the language server sees updates; use \
lsp_get_diagnostics to read issues. MCP tools (mcp_*) are available when configured in TOML.

## Communication Style
- Start with a brief plan (1-3 sentences)
- During work, print minimal status updates
- End with a summary of what was done

{memory_section}
"""


class AgentLoop:
    def __init__(self, config: dict):
        self.config = config
        configure_from_config(config)
        configure_mcp_servers(config)
        self.router = ModelRouter(config)
        self.llm = LLMClient(config)
        set_llm_instance(self.llm)
        self.permissions = PermissionManager(config)
        self.messages: list[dict] = []
        self.max_iterations = 50
        self._project_path = ""
        self._session_id = ""
        self._session_store: SessionStore | None = None
        self._chat_stream = True
        self._stream_sink: Optional[Callable[[str], None]] = None
        self._notify: Optional[Callable[[str], None]] = None
        self._tool_echo: Optional[Callable[[str, dict], None]] = None
        self._tool_result_echo: Optional[
            Callable[[str, str, str | None], None]
        ] = None
        self._tool_wave_echo: Optional[
            Callable[[list[dict]], None]
        ] = None
        self._llm_idle_hook: Optional[Callable[[], None]] = None
        self._llm_busy_hook: Optional[Callable[[], None]] = None
        self._permission_handler: Optional[PermissionHandler] = None

    def _emit(self, message: str) -> None:
        if self._notify:
            self._notify(message)
        else:
            print(message)

    def _build_system_prompt(self) -> str:
        memory = load_memory()
        memory_section = ""
        if memory:
            memory_section = f"## Project Memory (from AGENT.md)\n{memory}"
        return SYSTEM_PROMPT.format(memory_section=memory_section)

    def _refresh_system_prompt_in_messages(self) -> None:
        content = self._build_system_prompt()
        if self.messages and self.messages[0].get("role") == "system":
            self.messages[0] = {"role": "system", "content": content}
        else:
            self.messages.insert(0, {"role": "system", "content": content})

    def _save_session(self) -> None:
        if not self._session_store:
            return
        self._session_store.save(
            self._session_id,
            self._project_path,
            self.messages,
        )

    def _setup_session(
        self,
        *,
        resume_latest: bool = False,
        resume_session_id: Optional[str] = None,
    ) -> None:
        self._project_path = str(Path.cwd().resolve())
        session_cfg = self.config.get("session", {})
        session_enabled = session_cfg.get("enabled", True)
        self._session_store = SessionStore() if session_enabled else None
        self._session_id = str(uuid.uuid4())

        if not session_enabled or not self._session_store:
            self.messages = [
                {"role": "system", "content": self._build_system_prompt()}
            ]
            return

        loaded: Optional[list[dict]] = None
        sid: Optional[str] = None

        if resume_session_id:
            loaded = self._session_store.load_by_id(
                resume_session_id, self._project_path
            )
            if loaded is not None:
                sid = resume_session_id
            else:
                print(
                    f"No session '{resume_session_id}' for this project. "
                    "Starting fresh.\n"
                )
        elif resume_latest:
            sid, loaded = self._session_store.load_latest_session(
                self._project_path
            )
            if sid is None or loaded is None:
                print(
                    "No saved session for this project. Starting fresh.\n"
                )

        if loaded is not None and sid is not None:
            self._session_id = sid
            self.messages = list(loaded)
            self._refresh_system_prompt_in_messages()
        else:
            self.messages = [
                {"role": "system", "content": self._build_system_prompt()}
            ]

    def clear_conversation(self) -> None:
        self._session_id = str(uuid.uuid4())
        self.messages = [
            {"role": "system", "content": self._build_system_prompt()}
        ]
        self._save_session()

    async def run(
        self,
        initial_prompt: str = None,
        resume: bool = False,
        resume_session_id: Optional[str] = None,
    ):
        print("🤖 PyOpenCode ready. Type 'exit' to quit, 'clear' to reset.\n")

        self._setup_session(
            resume_latest=resume and resume_session_id is None,
            resume_session_id=resume_session_id,
        )

        try:
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
                    self.clear_conversation()
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
        finally:
            self._save_session()

    async def _process_user_input(self, user_input: str):
        self.messages.append({"role": "user", "content": user_input})
        try:
            await self._agent_loop()
        except Exception as exc:
            self._emit(f"\n❌ Agent error: {type(exc).__name__}: {exc}\n")
        self._save_session()

    async def _agent_loop(self):
        for iteration in range(self.max_iterations):
            if self._llm_idle_hook:
                self._llm_idle_hook()
            try:
                token_estimate = count_messages_tokens(self.messages)
                main_model = self.router.select(token_count=token_estimate)
                main_provider = infer_provider_id_for_model(
                    main_model,
                    self.config,
                )
                response = await self.llm.chat(
                    messages=self.messages,
                    tools=registry.get_schemas(),
                    stream=self._chat_stream,
                    stream_sink=self._stream_sink if self._chat_stream else None,
                    model=main_model,
                    provider_id=main_provider,
                )
            except Exception as exc:
                self._emit(f"\n❌ LLM error: {type(exc).__name__}: {exc}\n")
                break
            finally:
                if self._llm_busy_hook:
                    self._llm_busy_hook()

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
            self._emit("\n⚠️  Reached maximum iterations. Stopping.")

    async def _execute_tool_calls(self, tool_calls: list[dict]) -> list[dict]:
        results = []
        wave: list[dict] = []

        for tc in tool_calls:
            name = tc["function"]["name"]
            try:
                args = json.loads(tc["function"]["arguments"])
            except json.JSONDecodeError:
                args = {}

            snapshot = None
            fp_arg = args.get("file_path")
            if name in ("edit_file", "write_file") and fp_arg:
                snapshot = _read_file_text_if_exists(str(fp_arg))

            if not self.permissions.check(name, args):
                if self._permission_handler:
                    try:
                        answer = (
                            await self._permission_handler(name, args)
                        ).strip().lower()
                    except (EOFError, KeyboardInterrupt):
                        answer = "n"
                else:
                    prompt = self.permissions.format_request(name, args)
                    if self._notify:
                        self._notify(prompt)
                    else:
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

            preview = json.dumps(args, ensure_ascii=False)[:100]
            if self._tool_wave_echo is None:
                if self._tool_echo:
                    self._tool_echo(name, args)
                elif self._notify:
                    self._notify(f"  🔧 {name}({preview})")
                else:
                    print(f"  🔧 {name}({preview})")
            result = await registry.execute(name, args)
            diff = _build_edit_diff(name, args, snapshot)

            cap = 480
            prev = result if len(result) <= cap else result[:cap] + "…"
            wave.append(
                {
                    "name": name,
                    "args": args,
                    "result": result,
                    "preview": prev,
                    "diff": diff,
                }
            )

            if self._tool_wave_echo is None and self._tool_result_echo:
                self._tool_result_echo(name, prev, diff)

            if len(result) > 20000:
                result = result[:10000] + "\n...(truncated)...\n" + result[-10000:]

            results.append(
                {
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": result,
                }
            )

        if self._tool_wave_echo and wave:
            self._tool_wave_echo(wave)

        return results

    async def _maybe_compact(self):
        from pyopencode.core.compaction import compact_conversation

        total_tokens = count_messages_tokens(self.messages)
        max_tokens = self.config.get("max_context_tokens", 200000)
        threshold = self.config["compaction"]["threshold_ratio"]

        if total_tokens > max_tokens * threshold:
            self._emit("\n📦 Compacting conversation history...")
            raw_summary = self.config["compaction"].get("summary_model", "auto")
            if raw_summary == "auto":
                summary_model = self.router.select("compaction")
            else:
                summary_model = raw_summary
            summary_provider = infer_provider_id_for_model(
                summary_model,
                self.config,
            )
            self.messages = await compact_conversation(
                self.messages,
                self.llm,
                summary_model=summary_model,
                keep_recent=self.config["compaction"]["keep_recent"],
                summary_provider_id=summary_provider,
            )
            new_tokens = count_messages_tokens(self.messages)
            self._emit(
                f"   Compressed: {total_tokens} → {new_tokens} tokens\n"
            )
