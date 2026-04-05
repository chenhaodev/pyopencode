# Roadmap

Short status vs the phase plan in [`TASK.md`](TASK.md). Release notes:
[`CHANGELOG.md`](CHANGELOG.md).

## Phases (summary)

| Phase | Intent | Status |
|-------|--------|--------|
| 1 | CLI, config (TOML merge), tools, ReAct loop | Done |
| 2 | Compaction, SQLite sessions, AGENT.md | Done |
| 3 | Subagents, `dispatch_subagents`, repomap (AST + optional tree-sitter) | Done |
| 4 | LSP pool (`lsp_session`), `lsp_*` tools, TUI (Textual + tests) | Done + polish |

## Near term (done / ongoing)

- **LSP:** `publishDiagnostics` handling, `didChange` via `lsp_sync_document`,
  `lsp_get_diagnostics`, `lsp_hover`, `lsp_document_symbols`.
- **TUI:** grouped tool batch panel, unified diff preview for writes/edits,
  `--tui-theme`, `--tui-high-contrast`, `--no-group-tools`.
- **Tools:** sync/async timeouts, retries (config), bash deny-list + max timeout cap.
- **Repomap:** optional `pyopencode[repomap]` (`prefer_tree_sitter` on `get_repomap`).
- **MCP:** stdio MCP bus (`mcp_list_tools`, `mcp_call_tool`) + `[mcp.servers]` in TOML.
- **Extras:** `[lsp]` → `pygls` for server-side experiments.

## Later

- Tool cancellation mid-flight; richer bash sandbox (allowlists).
- LSP: `didSave`, workspace symbols, richer notification draining.
- MCP: multi-transport (SSE/HTTP), OAuth for hosted MCP.
- TUI: true collapsible widgets inside transcript; side-by-side diff view.

Contributors: open an issue or PR scoped to one item above; keep this file in sync when scope shifts.
