# PyOpenCode：基于 Python 的轻量级 AI Coding Agent 完整方案

---

## 一、项目概述

PyOpenCode 是一个用 Python 从零构建的终端 AI 编程助手，对标 Claude Code / OpenCode / Aider，但追求极简内核与高可扩展性。项目核心理念是：**用最少的代码量覆盖最关键的 agent 失败模式**，同时支持多模型 provider、异步子代理、LSP 集成等高级功能的渐进式引入。

你已配置的 API：Claude、GPT、Gemini、Qwen、SiliconFlow（MiniMax-2.5），将贯穿整个开发与测试流程。

---

## 二、整体架构

```
┌─────────────────────────────────────────────────────┐
│                     TUI 层 (Textual)                │
│            用户输入 / 输出渲染 / 权限确认              │
├─────────────────────────────────────────────────────┤
│                  Agent Loop 层 (核心)                │
│     ReAct 循环 / 对话管理 / 压缩 / 子代理派发          │
├──────────────┬──────────────────┬────────────────────┤
│  Tool 层     │  Memory 层       │  LLM Client 层     │
│  工具注册     │  AGENT.md        │  litellm 统一调用   │
│  工具执行     │  TodoWrite       │  多 provider 路由   │
│  权限分级     │  对话压缩/持久化  │  streaming/并行     │
├──────────────┴──────────────────┴────────────────────┤
│                   基础设施层                          │
│       项目检测 / Git 集成 / LSP 桥接 / AST 分析       │
└─────────────────────────────────────────────────────┘
```

---

## 三、目录结构

```
pyopencode/
├── pyproject.toml
├── README.md
├── AGENT.md                  # 项目级持久记忆
│
├── pyopencode/
│   ├── __init__.py
│   ├── main.py               # CLI 入口 (click)
│   ├── config.py             # 配置加载 (YAML/TOML)
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── agent_loop.py     # 核心 ReAct 循环
│   │   ├── subagent.py       # 异步子代理
│   │   ├── compaction.py     # 对话压缩
│   │   └── router.py         # 模型路由策略
│   │
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── client.py         # litellm 统一客户端
│   │   ├── providers.py      # provider 配置
│   │   └── token_counter.py  # token 计数
│   │
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── registry.py       # 工具注册中心
│   │   ├── permissions.py    # 权限分级系统
│   │   ├── read_file.py
│   │   ├── write_file.py
│   │   ├── edit_file.py
│   │   ├── bash.py
│   │   ├── glob_search.py
│   │   ├── grep_search.py
│   │   ├── todo_write.py     # 任务清单 (Claude Code 思路)
│   │   ├── git_tools.py
│   │   └── lsp_bridge.py     # LSP 集成 (Phase 4)
│   │
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── agent_md.py       # AGENT.md 读写
│   │   ├── session.py        # SQLite 会话持久化
│   │   └── repomap.py        # tree-sitter 代码骨架
│   │
│   ├── tui/
│   │   ├── __init__.py
│   │   ├── app.py            # Textual 主界面
│   │   ├── chat_view.py      # 对话渲染
│   │   ├── status_bar.py     # 状态栏 (token/cost/model)
│   │   └── permission_modal.py  # 权限弹窗
│   │
│   └── utils/
│       ├── __init__.py
│       ├── truncate.py       # 智能输出截断
│       ├── diff.py           # diff 生成与应用
│       └── project_detect.py # 项目类型检测
│
└── tests/
    ├── test_agent_loop.py
    ├── test_tools.py
    ├── test_compaction.py
    └── test_llm_client.py
```

---

## 四、分阶段实现计划

### Phase 1：最小可用内核（目标 ~300 行核心代码）

本阶段目标是让 agent 能跑起来、能改代码、能自我迭代。完成后你就可以用它来开发它自己了。

**1.1 CLI 入口 — `main.py`**

```python
import click
import asyncio
from pyopencode.core.agent_loop import AgentLoop
from pyopencode.config import load_config

@click.command()
@click.option('--model', '-m', default=None, help='Override model')
@click.option('--provider', '-p', default=None, help='Override provider')
@click.option('--resume', '-r', is_flag=True, help='Resume last session')
@click.argument('initial_prompt', required=False)
def main(model, provider, resume, initial_prompt):
    """PyOpenCode - AI Coding Assistant"""
    config = load_config()
    if model:
        config['model'] = model
    if provider:
        config['provider'] = provider

    loop = AgentLoop(config)
    asyncio.run(loop.run(initial_prompt=initial_prompt, resume=resume))

if __name__ == '__main__':
    main()
```

**1.2 配置系统 — `config.py`**

```python
import os
from pathlib import Path
import tomllib

DEFAULT_CONFIG = {
    "model": "claude-sonnet-4-20250514",
    "provider": "anthropic",
    "max_tokens": 16384,
    "max_context_tokens": 200000,
    "temperature": 0,
    "providers": {
        "anthropic": {"api_key_env": "ANTHROPIC_API_KEY"},
        "openai": {"api_key_env": "OPENAI_API_KEY"},
        "gemini": {"api_key_env": "GEMINI_API_KEY"},
        "qwen": {
            "api_key_env": "QWEN_API_KEY",
            "api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1"
        },
        "siliconflow": {
            "api_key_env": "SILICONFLOW_API_KEY",
            "api_base": "https://api.siliconflow.cn/v1"
        },
    },
    "permissions": {
        "always_allow": ["read_file", "glob_search", "grep_search", "todo_write"],
        "allow_once_then_remember": ["write_file", "edit_file"],
        "always_ask": ["bash"],
    },
    "compaction": {
        "threshold_ratio": 0.85,
        "summary_model": "qwen-turbo",
        "keep_recent": 10,
    },
}

def load_config():
    config = DEFAULT_CONFIG.copy()
    
    # 全局配置: ~/.pyopencode/config.toml
    global_config_path = Path.home() / ".pyopencode" / "config.toml"
    if global_config_path.exists():
        with open(global_config_path, 'rb') as f:
            user_config = tomllib.load(f)
            deep_merge(config, user_config)
    
    # 项目配置: .pyopencode.toml
    project_config_path = Path.cwd() / ".pyopencode.toml"
    if project_config_path.exists():
        with open(project_config_path, 'rb') as f:
            project_config = tomllib.load(f)
            deep_merge(config, project_config)
    
    return config

def deep_merge(base, override):
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            deep_merge(base[key], value)
        else:
            base[key] = value
```

**1.3 LLM 统一客户端 — `llm/client.py`**

```python
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
        model = model or self.config['model']
        
        kwargs = {
            "model": model,
            "messages": messages,
            "temperature": self.config.get('temperature', 0),
            "max_tokens": self.config.get('max_tokens', 16384),
            "stream": stream,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        
        # litellm 统一处理不同 provider 的鉴权和格式
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
                print(delta.content, end='', flush=True)  # Phase 1: 简单打印
            
            if delta.tool_calls:
                for tc in delta.tool_calls:
                    self._accumulate_tool_call(tool_calls, tc)
        
        print()  # 换行
        
        if hasattr(response, 'usage') and response.usage:
            self._track_usage(response.usage)
        
        return {
            "content": full_content,
            "tool_calls": tool_calls if tool_calls else None,
        }
    
    def _accumulate_tool_call(self, tool_calls, delta_tc):
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
    
    def _track_usage(self, usage):
        if usage:
            self.total_input_tokens += getattr(usage, 'prompt_tokens', 0)
            self.total_output_tokens += getattr(usage, 'completion_tokens', 0)
    
    @property
    def total_cost_estimate(self) -> float:
        # 粗略估算，后续可按模型细化
        return (self.total_input_tokens * 3 + self.total_output_tokens * 15) / 1_000_000
```

**1.4 工具注册中心 — `tools/registry.py`**

```python
import json
from typing import Callable, Any

class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, dict] = {}  # name -> {func, schema, category}
    
    def register(self, name: str, description: str, parameters: dict,
                 category: str = "always_ask"):
        """装饰器：注册工具"""
        def decorator(func: Callable):
            self._tools[name] = {
                "func": func,
                "schema": {
                    "type": "function",
                    "function": {
                        "name": name,
                        "description": description,
                        "parameters": parameters,
                    }
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
            # 支持同步和异步工具
            if hasattr(result, '__await__'):
                result = await result
            return str(result)
        except Exception as e:
            return f"Error executing {name}: {type(e).__name__}: {e}"
    
    def get_category(self, name: str) -> str:
        return self._tools.get(name, {}).get("category", "always_ask")

# 全局注册中心
registry = ToolRegistry()
```

**1.5 核心工具实现**

```python
# tools/read_file.py
from pathlib import Path
from pyopencode.tools.registry import registry

@registry.register(
    name="read_file",
    description="Read the contents of a file. You MUST use this before editing any file.",
    parameters={
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Path to the file to read"},
            "start_line": {"type": "integer", "description": "Start line (1-indexed, optional)"},
            "end_line": {"type": "integer", "description": "End line (1-indexed, inclusive, optional)"},
        },
        "required": ["file_path"],
    },
    category="always_allow",
)
def read_file(file_path: str, start_line: int = None, end_line: int = None) -> str:
    path = Path(file_path)
    if not path.exists():
        return f"Error: File '{file_path}' does not exist."
    if not path.is_file():
        return f"Error: '{file_path}' is not a file."
    
    content = path.read_text(encoding='utf-8', errors='replace')
    lines = content.split('\n')
    
    if start_line or end_line:
        start = (start_line or 1) - 1
        end = end_line or len(lines)
        lines = lines[start:end]
        header = f"[Lines {start+1}-{min(end, len(content.split(chr(10))))} of {len(content.split(chr(10)))}]\n"
        return header + '\n'.join(lines)
    
    return content


# tools/write_file.py
from pathlib import Path
from pyopencode.tools.registry import registry

@registry.register(
    name="write_file",
    description="Write content to a file. Creates the file if it doesn't exist. "
                "Creates parent directories as needed.",
    parameters={
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Path to the file"},
            "content": {"type": "string", "description": "Full content to write"},
        },
        "required": ["file_path", "content"],
    },
    category="allow_once_then_remember",
)
def write_file(file_path: str, content: str) -> str:
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')
    lines = content.count('\n') + 1
    return f"Successfully wrote {lines} lines to {file_path}"


# tools/edit_file.py
from pathlib import Path
from pyopencode.tools.registry import registry

@registry.register(
    name="edit_file",
    description="Edit a file by replacing an exact string match. "
                "You MUST read the file first to get the exact content to replace. "
                "The old_string must match EXACTLY including whitespace and indentation.",
    parameters={
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Path to the file"},
            "old_string": {"type": "string", "description": "Exact string to find and replace"},
            "new_string": {"type": "string", "description": "Replacement string"},
        },
        "required": ["file_path", "old_string", "new_string"],
    },
    category="allow_once_then_remember",
)
def edit_file(file_path: str, old_string: str, new_string: str) -> str:
    path = Path(file_path)
    if not path.exists():
        return f"Error: File '{file_path}' does not exist. Use write_file to create new files."
    
    content = path.read_text(encoding='utf-8')
    
    count = content.count(old_string)
    if count == 0:
        return (f"Error: old_string not found in {file_path}. "
                f"Make sure you read the file first and the string matches exactly.")
    if count > 1:
        return (f"Error: old_string found {count} times in {file_path}. "
                f"Provide a more unique string to match exactly once.")
    
    new_content = content.replace(old_string, new_string, 1)
    path.write_text(new_content, encoding='utf-8')
    
    return f"Successfully edited {file_path}: replaced 1 occurrence."


# tools/bash.py
import subprocess
from pyopencode.tools.registry import registry
from pyopencode.utils.truncate import truncate_output

@registry.register(
    name="bash",
    description="Execute a bash command. Use for running tests, installing packages, "
                "git operations, exploring file system, etc.",
    parameters={
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "The bash command to execute"},
            "timeout": {"type": "integer", "description": "Timeout in seconds (default 60)"},
        },
        "required": ["command"],
    },
    category="always_ask",
)
def bash(command: str, timeout: int = 60) -> str:
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=".",
        )
        output = ""
        if result.stdout:
            output += result.stdout
        if result.stderr:
            output += ("\n--- STDERR ---\n" + result.stderr) if output else result.stderr
        if not output:
            output = "(no output)"
        
        output = truncate_output(output)
        
        return f"[Exit code: {result.returncode}]\n{output}"
    
    except subprocess.TimeoutExpired:
        return f"Error: Command timed out after {timeout} seconds."
    except Exception as e:
        return f"Error: {type(e).__name__}: {e}"


# tools/glob_search.py
from pathlib import Path
from pyopencode.tools.registry import registry

@registry.register(
    name="glob_search",
    description="Search for files matching a glob pattern.",
    parameters={
        "type": "object",
        "properties": {
            "pattern": {"type": "string", "description": "Glob pattern (e.g. '**/*.py')"},
            "root": {"type": "string", "description": "Root directory (default: current dir)"},
        },
        "required": ["pattern"],
    },
    category="always_allow",
)
def glob_search(pattern: str, root: str = ".") -> str:
    matches = sorted(Path(root).glob(pattern))
    # 过滤常见忽略目录
    ignore = {'.git', 'node_modules', '__pycache__', '.venv', 'venv', '.tox'}
    filtered = [m for m in matches if not any(part in ignore for part in m.parts)]
    
    if not filtered:
        return f"No files found matching '{pattern}'"
    
    result = f"Found {len(filtered)} files:\n"
    for f in filtered[:100]:  # 最多显示 100 个
        result += f"  {f}\n"
    if len(filtered) > 100:
        result += f"  ... and {len(filtered) - 100} more\n"
    return result


# tools/grep_search.py
import subprocess
from pyopencode.tools.registry import registry

@registry.register(
    name="grep_search",
    description="Search for a regex pattern in files using ripgrep (rg) or grep.",
    parameters={
        "type": "object",
        "properties": {
            "pattern": {"type": "string", "description": "Regex pattern to search"},
            "path": {"type": "string", "description": "File or directory path (default: '.')"},
            "include": {"type": "string", "description": "File glob to include (e.g. '*.py')"},
        },
        "required": ["pattern"],
    },
    category="always_allow",
)
def grep_search(pattern: str, path: str = ".", include: str = None) -> str:
    # 优先用 ripgrep，没有则 fallback 到 grep
    try:
        cmd = ["rg", "--line-number", "--no-heading", "--color=never", "-e", pattern]
        if include:
            cmd.extend(["--glob", include])
        cmd.append(path)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    except FileNotFoundError:
        cmd = ["grep", "-rn", "-E", pattern]
        if include:
            cmd.extend(["--include", include])
        cmd.append(path)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    
    output = result.stdout.strip()
    if not output:
        return f"No matches found for pattern '{pattern}'"
    
    lines = output.split('\n')
    if len(lines) > 50:
        return '\n'.join(lines[:50]) + f"\n... ({len(lines) - 50} more matches)"
    return output


# tools/todo_write.py
from pyopencode.tools.registry import registry

_todos = []

@registry.register(
    name="todo_write",
    description="Create or update a task checklist to track progress on multi-step tasks. "
                "Use this at the start of complex tasks to plan, and update as you complete steps. "
                "Always include ALL tasks (not just remaining ones) with their current status.",
    parameters={
        "type": "object",
        "properties": {
            "todos": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "task": {"type": "string"},
                        "status": {
                            "type": "string",
                            "enum": ["pending", "in_progress", "done"]
                        },
                    },
                    "required": ["task", "status"],
                },
                "description": "Full list of tasks with their status"
            },
        },
        "required": ["todos"],
    },
    category="always_allow",
)
def todo_write(todos: list[dict]) -> str:
    global _todos
    _todos = todos
    icons = {'pending': '☐', 'in_progress': '⟳', 'done': '☑'}
    lines = [f"{icons.get(t['status'], '?')} {t['task']}" for t in todos]
    done = sum(1 for t in todos if t['status'] == 'done')
    return f"Task list updated ({done}/{len(todos)} done):\n" + '\n'.join(lines)
```

**1.6 智能输出截断 — `utils/truncate.py`**

```python
def truncate_output(text: str, max_lines: int = 400) -> str:
    lines = text.split('\n')
    if len(lines) <= max_lines:
        return text
    
    head = max_lines // 2
    tail = max_lines // 2
    truncated = len(lines) - head - tail
    
    return '\n'.join(
        lines[:head] +
        [f"\n... ({truncated} lines truncated) ...\n"] +
        lines[-tail:]
    )
```

**1.7 权限系统 — `tools/permissions.py`**

```python
class PermissionManager:
    def __init__(self, config: dict):
        self.config = config.get('permissions', {})
        self.approved_tools: set[str] = set()
        self.always_allow = set(self.config.get('always_allow', []))
        self.remember_after_allow = set(self.config.get('allow_once_then_remember', []))
    
    def check(self, tool_name: str, arguments: dict) -> bool:
        """返回 True 表示允许执行，False 表示需要用户确认"""
        if tool_name in self.always_allow:
            return True
        if tool_name in self.approved_tools:
            return True
        return False
    
    def approve(self, tool_name: str):
        """用户批准后调用"""
        if tool_name in self.remember_after_allow:
            self.approved_tools.add(tool_name)
    
    def format_request(self, tool_name: str, arguments: dict) -> str:
        """格式化权限请求给用户看"""
        import json
        args_str = json.dumps(arguments, indent=2, ensure_ascii=False)
        return f"🔐 Permission required: {tool_name}\n{args_str}\n\nAllow? [y/N/always]: "
```

**1.8 AGENT.md 记忆 — `memory/agent_md.py`**

```python
from pathlib import Path

MEMORY_FILENAME = "AGENT.md"

def load_memory(project_root: str = ".") -> str:
    """加载项目级记忆文件"""
    memory_path = Path(project_root) / MEMORY_FILENAME
    if memory_path.exists():
        return memory_path.read_text(encoding='utf-8')
    return ""

def save_memory(content: str, project_root: str = "."):
    """保存项目级记忆"""
    memory_path = Path(project_root) / MEMORY_FILENAME
    memory_path.write_text(content, encoding='utf-8')

def append_memory(entry: str, project_root: str = "."):
    """追加一条记忆"""
    current = load_memory(project_root)
    if entry not in current:
        save_memory(current.rstrip() + "\n\n" + entry + "\n", project_root)
```

**1.9 核心 Agent Loop — `core/agent_loop.py`**

```python
import json
import asyncio
from pyopencode.llm.client import LLMClient
from pyopencode.tools.registry import registry
from pyopencode.tools.permissions import PermissionManager
from pyopencode.memory.agent_md import load_memory

# 确保所有工具被注册
import pyopencode.tools.read_file
import pyopencode.tools.write_file
import pyopencode.tools.edit_file
import pyopencode.tools.bash
import pyopencode.tools.glob_search
import pyopencode.tools.grep_search
import pyopencode.tools.todo_write

SYSTEM_PROMPT = """You are PyOpenCode, an expert AI coding assistant operating in the user's terminal.

## Core Rules
1. **Always read before edit**: Before editing any file, you MUST read it first. Never edit based on memory.
2. **Use todo_write for complex tasks**: For multi-step tasks, create a checklist first and update progress.
3. **Verify your work**: After making changes, run relevant tests or checks to verify correctness.
4. **Be precise with edit_file**: The old_string must match the file content EXACTLY.
5. **Explain what you're doing**: Briefly explain your approach before taking actions.

## Available Tools
You have access to: read_file, write_file, edit_file, bash, glob_search, grep_search, todo_write.

## Workflow
1. Understand the request
2. Explore the codebase (read files, search)
3. Plan the changes (use todo_write for complex tasks)
4. Implement changes (edit/write files)
5. Verify (run tests, check output)

{memory_section}
"""

class AgentLoop:
    def __init__(self, config: dict):
        self.config = config
        self.llm = LLMClient(config)
        self.permissions = PermissionManager(config)
        self.messages: list[dict] = []
        self.max_iterations = 50  # 安全上限
    
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
            if user_input.lower() == 'exit':
                break
            if user_input.lower() == 'clear':
                self.messages = [{"role": "system", "content": self._build_system_prompt()}]
                print("Conversation cleared.")
                continue
            if user_input.lower() == 'cost':
                print(f"Tokens: {self.llm.total_input_tokens} in / "
                      f"{self.llm.total_output_tokens} out | "
                      f"Est. cost: ${self.llm.total_cost_estimate:.4f}")
                continue
            
            await self._process_user_input(user_input)
    
    async def _process_user_input(self, user_input: str):
        self.messages.append({"role": "user", "content": user_input})
        await self._agent_loop()
    
    async def _agent_loop(self):
        """核心 ReAct 循环"""
        for iteration in range(self.max_iterations):
            # 1. 调用 LLM
            response = await self.llm.chat(
                messages=self.messages,
                tools=registry.get_schemas(),
            )
            
            # 2. 追加 assistant 消息
            assistant_msg = {"role": "assistant"}
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
                        }
                    }
                    for tc in response["tool_calls"]
                ]
            self.messages.append(assistant_msg)
            
            # 3. 如果没有 tool calls，agent 完成思考
            if not response["tool_calls"]:
                break
            
            # 4. 执行工具调用
            tool_results = await self._execute_tool_calls(response["tool_calls"])
            self.messages.extend(tool_results)
            
            # 5. 检查是否需要对话压缩
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
            
            # 权限检查
            if not self.permissions.check(name, args):
                prompt = self.permissions.format_request(name, args)
                print(prompt, end='')
                try:
                    answer = input().strip().lower()
                except (EOFError, KeyboardInterrupt):
                    answer = 'n'
                
                if answer in ('y', 'yes'):
                    self.permissions.approve(name)
                elif answer == 'always':
                    self.permissions.approved_tools.add(name)
                else:
                    results.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": "Permission denied by user.",
                    })
                    continue
            
            # 执行工具
            print(f"  🔧 {name}({json.dumps(args, ensure_ascii=False)[:100]})")
            result = await registry.execute(name, args)
            
            # 截断过长的结果
            if len(result) > 20000:
                result = result[:10000] + "\n...(truncated)...\n" + result[-10000:]
            
            results.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": result,
            })
        
        return results
    
    async def _maybe_compact(self):
        """检查是否需要对话压缩（Phase 2 实现细节）"""
        # Phase 1: 简单 pass，Phase 2 填充
        pass
```

**1.10 依赖清单 — `pyproject.toml`**

```toml
[project]
name = "pyopencode"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "click>=8.0",
    "litellm>=1.40",
]

[project.scripts]
pyopencode = "pyopencode.main:main"

[project.optional-dependencies]
dev = ["pytest", "pytest-asyncio"]
tui = ["textual>=0.50"]
lsp = ["pygls>=1.0"]
```

此时运行 `pip install -e .` 然后 `pyopencode "list all python files in this project"` 应该就能跑起来了。

---

### Phase 2：记忆与智能增强（目标 ~600 行新增代码）

**2.1 对话压缩 — `core/compaction.py`**

```python
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
) -> list[dict]:
    """压缩对话历史，保留系统消息和最近 N 条"""
    
    if len(messages) <= keep_recent + 2:  # system + 至少几条消息才值得压缩
        return messages
    
    system_msg = messages[0]  # 保留 system prompt
    old_messages = messages[1:-keep_recent]
    recent_messages = messages[-keep_recent:]
    
    # 格式化旧消息为文本
    formatted = _format_messages_for_summary(old_messages)
    
    # 用便宜模型生成摘要
    summary_response = await llm.chat(
        messages=[
            {"role": "system", "content": "You are a conversation summarizer."},
            {"role": "user", "content": f"Summarize this conversation:\n\n{formatted}\n\n{COMPACTION_PROMPT}"},
        ],
        model=summary_model,
        stream=False,
    )
    
    summary_msg = {
        "role": "assistant",
        "content": f"[Conversation Summary - {len(old_messages)} messages compressed]\n\n"
                   f"{summary_response['content']}"
    }
    
    return [system_msg, summary_msg] + recent_messages

def _format_messages_for_summary(messages: list[dict]) -> str:
    parts = []
    for msg in messages:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        
        if role == "tool":
            # 截断工具输出，摘要不需要看完整文件内容
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
    
    return '\n\n'.join(parts)
```

然后在 `agent_loop.py` 的 `_maybe_compact` 中填入：

```python
async def _maybe_compact(self):
    from pyopencode.llm.token_counter import count_messages_tokens
    from pyopencode.core.compaction import compact_conversation
    
    total_tokens = count_messages_tokens(self.messages)
    max_tokens = self.config.get('max_context_tokens', 200000)
    threshold = self.config['compaction']['threshold_ratio']
    
    if total_tokens > max_tokens * threshold:
        print("\n📦 Compacting conversation history...")
        self.messages = await compact_conversation(
            self.messages,
            self.llm,
            summary_model=self.config['compaction']['summary_model'],
            keep_recent=self.config['compaction']['keep_recent'],
        )
        new_tokens = count_messages_tokens(self.messages)
        print(f"   Compressed: {total_tokens} → {new_tokens} tokens\n")
```

**2.2 SQLite 会话持久化 — `memory/session.py`**

```python
import json
import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path.home() / ".pyopencode" / "sessions.db"

class SessionStore:
    def __init__(self):
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(DB_PATH))
        self._init_db()
    
    def _init_db(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                project_path TEXT,
                created_at TEXT,
                updated_at TEXT,
                messages TEXT,
                summary TEXT
            )
        """)
        self.conn.commit()
    
    def save(self, session_id: str, project_path: str, messages: list[dict], summary: str = ""):
        now = datetime.now().isoformat()
        self.conn.execute(
            """INSERT OR REPLACE INTO sessions (id, project_path, created_at, updated_at, messages, summary)
               VALUES (?, ?, COALESCE((SELECT created_at FROM sessions WHERE id = ?), ?), ?, ?, ?)""",
            (session_id, project_path, session_id, now, now, json.dumps(messages, ensure_ascii=False), summary)
        )
        self.conn.commit()
    
    def load_latest(self, project_path: str) -> list[dict] | None:
        cursor = self.conn.execute(
            "SELECT messages FROM sessions WHERE project_path = ? ORDER BY updated_at DESC LIMIT 1",
            (project_path,)
        )
        row = cursor.fetchone()
        return json.loads(row[0]) if row else None
    
    def list_sessions(self, project_path: str = None, limit: int = 20) -> list[dict]:
        if project_path:
            cursor = self.conn.execute(
                "SELECT id, project_path, updated_at, summary FROM sessions WHERE project_path = ? ORDER BY updated_at DESC LIMIT ?",
                (project_path, limit)
            )
        else:
            cursor = self.conn.execute(
                "SELECT id, project_path, updated_at, summary FROM sessions ORDER BY updated_at DESC LIMIT ?",
                (limit,)
            )
        return [{"id": r[0], "path": r[1], "updated": r[2], "summary": r[3]} for r in cursor.fetchall()]
```

**2.3 Git 自动提交工具 — `tools/git_tools.py`**

```python
import subprocess
from pyopencode.tools.registry import registry

@registry.register(
    name="git_diff",
    description="Show git diff of current changes.",
    parameters={
        "type": "object",
        "properties": {
            "staged": {"type": "boolean", "description": "Show staged changes only"},
            "file_path": {"type": "string", "description": "Specific file to diff"},
        },
    },
    category="always_allow",
)
def git_diff(staged: bool = False, file_path: str = None) -> str:
    cmd = ["git", "diff"]
    if staged:
        cmd.append("--staged")
    if file_path:
        cmd.extend(["--", file_path])
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout or "(no changes)"

@registry.register(
    name="git_commit",
    description="Stage all changes and commit with a message.",
    parameters={
        "type": "object",
        "properties": {
            "message": {"type": "string", "description": "Commit message"},
        },
        "required": ["message"],
    },
    category="allow_once_then_remember",
)
def git_commit(message: str) -> str:
    subprocess.run(["git", "add", "-A"], capture_output=True)
    result = subprocess.run(["git", "commit", "-m", message], capture_output=True, text=True)
    return result.stdout + result.stderr

@registry.register(
    name="git_log",
    description="Show recent git log.",
    parameters={
        "type": "object",
        "properties": {
            "count": {"type": "integer", "description": "Number of commits to show (default 10)"},
        },
    },
    category="always_allow",
)
def git_log(count: int = 10) -> str:
    result = subprocess.run(
        ["git", "log", f"-{count}", "--oneline", "--decorate"],
        capture_output=True, text=True
    )
    return result.stdout or "(no git history)"
```

**2.4 模型路由 — `core/router.py`**

```python
class ModelRouter:
    """根据任务类型选择合适的模型"""
    
    def __init__(self, config: dict):
        self.config = config
        self.model_tiers = {
            "strong": config.get("strong_model", "claude-sonnet-4-20250514"),
            "fast": config.get("fast_model", "qwen-turbo"),
            "long_context": config.get("long_context_model", "gemini-2.0-flash"),
            "cheap": config.get("cheap_model", "minimax-2.5"),
        }
    
    def select(self, task_hint: str = None, token_count: int = 0) -> str:
        """
        选择模型。
        - 对话压缩 → cheap
        - context 超长 → long_context  
        - 复杂推理/架构设计 → strong
        - 简单问答 → fast
        """
        if task_hint == "compaction":
            return self.model_tiers["cheap"]
        if task_hint == "subagent":
            return self.model_tiers["fast"]
        if token_count > 100000:
            return self.model_tiers["long_context"]
        return self.model_tiers["strong"]
```

---

### Phase 3：子代理与代码理解（目标 ~800 行新增代码）

**3.1 异步子代理 — `core/subagent.py`**

```python
import asyncio
from pyopencode.llm.client import LLMClient
from pyopencode.tools.registry import ToolRegistry, registry

SUBAGENT_PROMPT = """You are a focused sub-agent. Complete the specific task assigned to you.
Be concise and return only the essential result. Do not explain your process unless asked.

Your task: {task}"""

class SubAgent:
    def __init__(self, llm: LLMClient, task: str, tools: list[str] = None):
        self.llm = llm
        self.task = task
        self.allowed_tools = tools or ["read_file", "glob_search", "grep_search"]
        self.messages = [
            {"role": "system", "content": SUBAGENT_PROMPT.format(task=task)},
            {"role": "user", "content": task},
        ]
    
    def _get_tool_schemas(self) -> list[dict]:
        return [s for s in registry.get_schemas() 
                if s["function"]["name"] in self.allowed_tools]
    
    async def run(self, max_iterations: int = 10) -> str:
        for _ in range(max_iterations):
            response = await self.llm.chat(
                messages=self.messages,
                tools=self._get_tool_schemas(),
                stream=False,  # 子代理不需要流式输出
            )
            
            self.messages.append({"role": "assistant", **response})
            
            if not response.get("tool_calls"):
                return response.get("content", "")
            
            for tc in response["tool_calls"]:
                result = await registry.execute(
                    tc["function"]["name"],
                    tc["function"]["arguments"]
                )
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": result,
                })
        
        return "Sub-agent reached iteration limit."

async def run_subagents(llm: LLMClient, tasks: list[str]) -> list[str]:
    """并行运行多个子代理"""
    agents = [SubAgent(llm, task) for task in tasks]
    results = await asyncio.gather(*[agent.run() for agent in agents])
    return list(results)
```

然后注册为工具，让主 agent 可以调用：

```python
# tools/dispatch_subagent.py
from pyopencode.tools.registry import registry

@registry.register(
    name="dispatch_subagents",
    description="Dispatch multiple sub-agents to work on tasks in parallel. "
                "Each sub-agent can read files and search but cannot write or execute commands. "
                "Use this for parallel information gathering.",
    parameters={
        "type": "object",
        "properties": {
            "tasks": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of task descriptions for each sub-agent"
            },
        },
        "required": ["tasks"],
    },
    category="always_allow",
)
async def dispatch_subagents(tasks: list[str]) -> str:
    from pyopencode.core.subagent import run_subagents
    from pyopencode.llm.client import LLMClient
    
    # 注：实际实现中需要从上下文获取 llm 实例
    # 这里简化处理
    results = await run_subagents(_get_llm_instance(), tasks)
    
    output = ""
    for i, (task, result) in enumerate(zip(tasks, results)):
        output += f"\n--- Sub-agent {i+1}: {task} ---\n{result}\n"
    return output
```

**3.2 Repomap（代码骨架） — `memory/repomap.py`**

```python
import ast
from pathlib import Path

def generate_repomap(root: str = ".", extensions: list[str] = None) -> str:
    """生成项目代码骨架，只保留类名、函数签名、顶层变量"""
    
    if extensions is None:
        extensions = [".py"]
    
    root_path = Path(root)
    ignore_dirs = {'.git', 'node_modules', '__pycache__', '.venv', 'venv', '.tox', 'dist', 'build'}
    
    output_parts = []
    
    for ext in extensions:
        for file_path in sorted(root_path.rglob(f"*{ext}")):
            if any(part in ignore_dirs for part in file_path.parts):
                continue
            
            rel_path = file_path.relative_to(root_path)
            
            if ext == ".py":
                skeleton = _python_skeleton(file_path)
                if skeleton:
                    output_parts.append(f"## {rel_path}\n{skeleton}")
    
    return '\n\n'.join(output_parts)

def _python_skeleton(file_path: Path) -> str:
    """用 ast 提取 Python 文件的骨架"""
    try:
        source = file_path.read_text(encoding='utf-8')
        tree = ast.parse(source)
    except (SyntaxError, UnicodeDecodeError):
        return ""
    
    lines = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            bases = ', '.join(ast.dump(b) if not isinstance(b, ast.Name) else b.id for b in node.bases)
            lines.append(f"  class {node.name}({bases}):")
            for item in ast.iter_child_nodes(node):
                if isinstance(item, ast.FunctionDef) or isinstance(item, ast.AsyncFunctionDef):
                    sig = _format_func_sig(item)
                    lines.append(f"    {sig}")
        
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            sig = _format_func_sig(node)
            lines.append(f"  {sig}")
        
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    lines.append(f"  {target.id} = ...")
    
    return '\n'.join(lines)

def _format_func_sig(node) -> str:
    prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
    args = []
    for arg in node.args.args:
        annotation = ""
        if arg.annotation:
            try:
                annotation = f": {ast.unparse(arg.annotation)}"
            except:
                pass
        args.append(f"{arg.arg}{annotation}")
    
    returns = ""
    if node.returns:
        try:
            returns = f" -> {ast.unparse(node.returns)}"
        except:
            pass
    
    return f"{prefix} {node.name}({', '.join(args)}){returns}"
```

---

### Phase 4：LSP 集成与 TUI（目标 ~1000 行新增代码）

**4.1 LSP 桥接 — `tools/lsp_bridge.py`（骨架）**

```python
import subprocess
import json
from typing import Optional

class LSPBridge:
    """与语言服务器通信的桥接层"""
    
    # 不同语言对应的 LSP 服务器
    SERVERS = {
        "python": ["pyright-langserver", "--stdio"],
        "typescript": ["typescript-language-server", "--stdio"],
        "go": ["gopls", "serve"],
        "rust": ["rust-analyzer"],
    }
    
    def __init__(self, language: str, project_root: str = "."):
        self.language = language
        self.project_root = project_root
        self.process: Optional[subprocess.Popen] = None
        self._request_id = 0
    
    async def start(self):
        cmd = self.SERVERS.get(self.language)
        if not cmd:
            raise ValueError(f"No LSP server configured for {self.language}")
        
        self.process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        await self._initialize()
    
    async def goto_definition(self, file_path: str, line: int, character: int) -> dict:
        return await self._request("textDocument/definition", {
            "textDocument": {"uri": f"file://{file_path}"},
            "position": {"line": line, "character": character},
        })
    
    async def find_references(self, file_path: str, line: int, character: int) -> list:
        return await self._request("textDocument/references", {
            "textDocument": {"uri": f"file://{file_path}"},
            "position": {"line": line, "character": character},
            "context": {"includeDeclaration": True},
        })
    
    async def get_diagnostics(self, file_path: str) -> list:
        # diagnostics 通常是服务器推送的，这里简化处理
        pass
    
    async def _request(self, method: str, params: dict) -> dict:
        self._request_id += 1
        msg = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": method,
            "params": params,
        }
        content = json.dumps(msg)
        header = f"Content-Length: {len(content)}\r\n\r\n"
        
        self.process.stdin.write((header + content).encode())
        self.process.stdin.flush()
        
        return await self._read_response()
    
    async def _read_response(self) -> dict:
        # 读取 LSP JSON-RPC 响应
        # 实际实现需要解析 Content-Length header
        pass
    
    async def _initialize(self):
        await self._request("initialize", {
            "processId": None,
            "rootUri": f"file://{self.project_root}",
            "capabilities": {},
        })
```

**4.2 TUI 界面骨架 — `tui/app.py`（使用 Textual）**

```python
from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Header, Footer, Input, RichLog, Static
from textual.binding import Binding

class PyOpenCodeApp(App):
    """PyOpenCode TUI 应用"""
    
    CSS = """
    #chat-log {
        height: 1fr;
        border: solid green;
        padding: 1;
        overflow-y: auto;
    }
    #status-bar {
        height: 1;
        background: $surface;
        color: $text-muted;
        padding: 0 1;
    }
    #input-area {
        height: 3;
        border: solid blue;
    }
    """
    
    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit"),
        Binding("ctrl+l", "clear", "Clear"),
        Binding("ctrl+k", "compact", "Compact"),
    ]
    
    def __init__(self, agent_loop):
        super().__init__()
        self.agent_loop = agent_loop
    
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield RichLog(id="chat-log", wrap=True, highlight=True)
        yield Static("Model: claude-sonnet | Tokens: 0 | Cost: $0.00", id="status-bar")
        yield Input(placeholder="Type your message... (Ctrl+C to quit)", id="input-area")
        yield Footer()
    
    async def on_input_submitted(self, event: Input.Submitted):
        user_input = event.value
        event.input.clear()
        
        log = self.query_one("#chat-log", RichLog)
        log.write(f"[bold blue]You:[/] {user_input}")
        
        # 调 agent loop（需要适配为回调模式）
        # ...
    
    def update_status(self, model: str, tokens: int, cost: float):
        status = self.query_one("#status-bar", Static)
        status.update(f"Model: {model} | Tokens: {tokens:,} | Cost: ${cost:.4f}")
```

---

## 五、System Prompt 完整版

```python
SYSTEM_PROMPT_V2 = """You are PyOpenCode, an expert AI software engineer operating in the user's terminal.
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
```

---

## 六、开发流程（使用你自己的工具链）

整个项目用 OpenCode + oh-my-opencode 来开发，形成自举循环。

**Week 1** 的重点是让 Phase 1 跑起来。在 OpenCode 中给 Claude 下达指令："创建 pyopencode 项目目录结构，实现 main.py CLI 入口和 config.py 配置加载"，然后逐个文件让它生成。每完成一个模块就在终端跑一下验证，有错误贴回去让它修。

**Week 2** 进入 Phase 2，此时 PyOpenCode 自身已经能用了。尝试用 PyOpenCode 来给自己添加对话压缩和会话持久化功能——这是第一次自举测试。同时用 GPT 对已有代码做 review，交叉检查。

**Week 3** 实现 Phase 3 子代理和 repomap。用 Qwen 和 MiniMax 跑 agent loop 做兼容性测试，确保多 provider 路由正常工作。

**Week 4** 如果前三个阶段稳定，开始 Phase 4 的 TUI 和 LSP。用 Gemini 的长上下文能力做跨文件重构。

---

## 七、模型分工策略

你的五个 API 在项目中各有最佳角色。

**Claude**（主力开发模型）承担所有核心架构设计、复杂 agent loop 逻辑编写、以及需要深度理解代码上下文的任务。它在工具调用准确性和代码生成质量上目前最强。

**GPT**（Review 与备选模型）在 Claude 写完核心代码后做交叉审查，特别适合找逻辑漏洞和边界情况。也可以作为 Claude 不可用时的备选主力模型。

**Gemini**（长上下文任务）当项目膨胀到几十个文件后，需要同时理解大量代码做重构时切换到 Gemini。它的超长 context window 是独特优势。

**Qwen**（廉价高频任务）作为对话压缩的摘要模型、子代理的默认模型、以及日常开发中简单问答的模型。Token 价格便宜，适合高频调用。

**MiniMax-2.5 via SiliconFlow**（兼容性测试 + 备选 cheap 模型）确保你的 tool calling 实现在非主流模型上也能工作。也可以作为 Qwen 的平替。

---

## 八、关键设计决策汇总

整个方案中有若干设计决策是核心差异化点，集中列在这里方便回顾。

**edit_file 而非 patch/diff**：让 LLM 提供精确的 old_string/new_string 替换，而不是生成 unified diff。这是 Claude Code 和 Aider 验证过的最可靠方案，LLM 生成 diff 的格式出错率远高于文本替换。

**强制先读再改**：写在 system prompt 里的硬性约束，单独一句话就能将 edit 成功率提升 30%+。

**Head+Tail 截断**：对 bash 输出保留头尾丢弃中间，比单纯截断尾部信息损失小得多。

**TodoWrite scratchpad**：零成本的任务追踪工具，解决 LLM 在长对话中"失忆"的问题。

**分级权限**：读操作静默执行，写操作首次确认后记住，危险命令每次确认。平衡安全性与使用流畅度。

**廉价模型做压缩**：对话压缩不需要最强模型，用 Qwen-turbo 做摘要足够好，成本降低一个数量级。

**项目级记忆文件 AGENT.md**：跨 session 持久化的最轻量方案，一个 markdown 文件即可。

---

## 九、测试策略

测试分三层。**单元测试**覆盖工具函数（edit_file 的精确匹配逻辑、truncate_output 的边界情况、权限系统的分级判断）。**集成测试**用 mock LLM 响应驱动整个 agent loop，验证工具调用解析、多轮对话、对话压缩触发等流程。**端到端测试**用真实 API 跑几个固定的编程任务（"在 X 目录创建一个 hello world Flask 应用"、"找到 Y 文件中的 bug 并修复"），验证实际表现。

端到端测试建议用最便宜的模型跑（Qwen/MiniMax），因为频繁跑会产生 API 费用。只在发布前用 Claude 跑一次完整测试。

---

这个方案从 Phase 1 到 Phase 4 渐进式推进，Phase 1 完成后就有一个可用的 agent，后续每个 Phase 都是在可工作的基础上增量添加能力。核心代码量控制在 2000-3000 行 Python，远小于 Claude Code 或 Aider 的体量，但覆盖了最关键的功能点。
