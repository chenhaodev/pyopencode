# PyOpenCode Project Memory

## Project Overview
PyOpenCode is a Python terminal AI coding agent: **OpenCode**-like minimal core
plus **Claude Code**-style workflow (todos, permissions, edit_file). Built in four
phases (MVP → memory → scale-out → TUI/LSP).

## Architecture
- `pyopencode/core/` — AgentLoop (ReAct), SubAgent, Compaction, ModelRouter
- `pyopencode/llm/` — LLMClient (litellm), providers config, token counting
- `pyopencode/tools/` — ToolRegistry, permissions, all tool implementations
- `pyopencode/memory/` — AGENT.md I/O, SQLite sessions, repomap (AST)
- `pyopencode/tui/` — Textual TUI (optional: `uv pip install -e '.[tui]'` or `pip install -e '.[tui]'` from clone)
- `pyopencode/utils/` — truncate, diff, project detection

## Key Design Decisions
- `edit_file` uses exact old_string/new_string replacement (not diffs)
- Always read before edit — enforced in system prompt
- Head+tail truncation for bash output
- TodoWrite for agent task tracking
- Tiered permissions: always_allow / allow_once_then_remember / always_ask
- ModelRouter: main chat vs long-context vs subagent vs cheap compaction;
  compaction `summary_model: "auto"` uses the cheap tier
- SQLite at `~/.pyopencode/sessions.db` for session persistence

## Running
```bash
uv pip install -e .
# or: pip install -e .
pyopencode "your task here"
pyopencode --model gpt-4o --provider openai
```

## Testing
```bash
uv pip install -e ".[dev]"
# or: pip install -e ".[dev]"
pytest tests/
```
