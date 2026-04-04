# PyOpenCode Project Memory

## Project Overview
PyOpenCode is a Python-based lightweight AI coding agent built in 4 phases.

## Architecture
- `pyopencode/core/` — AgentLoop (ReAct), SubAgent, Compaction, ModelRouter
- `pyopencode/llm/` — LLMClient (litellm), providers config, token counting
- `pyopencode/tools/` — ToolRegistry, permissions, all tool implementations
- `pyopencode/memory/` — AGENT.md I/O, SQLite sessions, repomap (AST)
- `pyopencode/tui/` — Textual TUI (optional, requires `pip install pyopencode[tui]`)
- `pyopencode/utils/` — truncate, diff, project detection

## Key Design Decisions
- `edit_file` uses exact old_string/new_string replacement (not diffs)
- Always read before edit — enforced in system prompt
- Head+tail truncation for bash output
- TodoWrite for agent task tracking
- Tiered permissions: always_allow / allow_once_then_remember / always_ask
- Cheap model (qwen-turbo) for conversation compaction
- SQLite at `~/.pyopencode/sessions.db` for session persistence

## Running
```bash
pip install -e .
pyopencode "your task here"
pyopencode --model gpt-4o --provider openai
```

## Testing
```bash
pip install -e ".[dev]"
pytest tests/
```
