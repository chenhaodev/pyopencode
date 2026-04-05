# Roadmap

Short status vs the phase plan in [`TASK.md`](TASK.md). Release notes:
[`CHANGELOG.md`](CHANGELOG.md).

## Phases (summary)

| Phase | Intent | Status |
|-------|--------|--------|
| 1 | CLI, config (TOML merge), tools, ReAct loop | Done |
| 2 | Compaction, SQLite sessions, AGENT.md | Done |
| 3 | Subagents, `dispatch_subagents`, repomap (AST sketch) | Done |
| 4 | LSP pool (`lsp_session`), `lsp_*` tools, TUI (Textual + tests) | Done + ongoing polish |

## Near term

- Wire **`ModelRouter`** (`core/router.py`) into `AgentLoop` / `LLMClient`.
- LSP: diagnostics / `didChange`, optional hover & symbols.
- TUI: group or fold tool output; theme / contrast options.

## Later

- Tool timeouts, cancellation, retries; safer bash policy.
- Richer repomap (e.g. tree-sitter); optional `lsp` extra deps.
- MCP or other tool buses; TUI diff preview.

Contributors: open an issue or PR scoped to one item above; keep this file in sync when scope shifts.
