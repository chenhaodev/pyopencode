# Design reference (TASK)

Concise architecture and phase intent. **Source of truth is the code**; this
file avoids duplicating snippets that drift.

## Product

Terminal AI coding agent: ReAct loop, tool registry, LiteLLM-backed providers,
optional Textual TUI and LSP tools. Goal: small core, clear failure modes (read
before edit, permissions, compaction, sessions).

## Layout (mental map)

- `pyopencode/main.py` — CLI (`click`).
- `pyopencode/config.py` — defaults + `~/.pyopencode/config.toml` +
  `.pyopencode.toml` + env key wiring.
- `pyopencode/core/` — `agent_loop`, `compaction`, `subagent`, `router`
  (`ModelRouter` not yet wired into the main path).
- `pyopencode/llm/` — client, providers, token counting.
- `pyopencode/tools/` — registry, permissions, filesystem/git/search/LSP/repomap
  / subagent dispatch.
- `pyopencode/memory/` — `AGENT.md`, SQLite sessions, repomap generation.
- `pyopencode/tui/` — Textual app, modals, help.
- `pyopencode/utils/` — diff, truncate, project detect.
- `tests/` — pytest (see [`CONTRIBUTING.md`](CONTRIBUTING.md)).

## Phases (original plan)

1. **MVP** — Runnable agent, config, tools, loop.  
2. **Memory** — Compaction, persistent sessions, project memory file.  
3. **Scale-out** — Subagents, parallel dispatch, repo map tool.  
4. **UX / IDE** — LSP bridge + TUI.

## Design choices (stable)

- **edit_file** via exact `old_string` / `new_string` (not raw unified diffs).
- **Read before write** enforced in prompts and workflow.
- **Truncation** for large tool output (head/tail style where applicable).
- **todo_write** for multi-step work; **tiered permissions** for tools.
- **Cheaper model** for compaction when configured; **AGENT.md** for durable
  project hints.

## Prompts

System and subagent instructions live in code, e.g. `SYSTEM_PROMPT` in
`pyopencode/core/agent_loop.py` and `SUBAGENT_PROMPT` in
`pyopencode/core/subagent.py`—edit there, not in this doc.

## Testing

Layered tests under `tests/`; CI and optional LSP integration:
[`CONTRIBUTING.md`](CONTRIBUTING.md).

## Roadmap

Current status and next steps: [`ROADMAP.md`](ROADMAP.md).
