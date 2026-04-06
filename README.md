# PyOpenCode

Terminal **AI coding agent** for Python **3.11+**. It targets the same problem
space as **OpenCode** and **Claude Code**: a small, hackable ReAct core with
disciplined tool use (read before edit, `todo_write`, tiered permissions,
string-replacement `edit_file`). Backends are unified through
[LiteLLM](https://github.com/BerriAI/litellm) (Claude, OpenAI, Gemini,
Qwen / DashScope, SiliconFlow), with an optional **Textual TUI** and LSP tools.

**Ultrawork (compact)** is an optional high-push mode: extra system instructions
for finishing tasks, todos, parallel exploration, and verification — enabled
with **`--ultrawork` / `-U`**, **`[agent] ultrawork = true`**, or a message prefix
`ulw ` / `ultrawork `. It is not the full oh-my-opencode Ultrawork stack (no
bundled sub-agents beyond `dispatch_subagents`).

---

## Install

**From this repository** (recommended until the package is on PyPI):

```bash
git clone https://github.com/chenhaodev/pyopencode.git
cd pyopencode
pip install -e .
```

### Using uv (recommended for this repo)

Locked install (matches CI — includes dev tools if you add `--extra dev`):

```bash
cd pyopencode
uv venv
uv sync --frozen --extra dev    # or: uv sync --extra dev
```

Runtime-only (no pytest/ruff in the lock group — still pulls **click** + **litellm**):

```bash
uv sync --frozen
```

Editable install with **pip** front-end (must target the venv’s Python explicitly
if the environment is not the project default):

```bash
uv venv
uv pip install --python .venv/bin/python -e .
# optional UI:  uv pip install --python .venv/bin/python -e ".[tui]"
```

**Trap — empty venv + `UV_PROJECT_ENVIRONMENT`:** if `UV_PROJECT_ENVIRONMENT`
points at a separate, empty environment and you run **`uv pip install -e .`**
without **`--python …/bin/python`**, uv may only link the editable package and
**skip dependencies**, leading to `ModuleNotFoundError: click` when you run
`pyopencode`. **Unset `UV_PROJECT_ENVIRONMENT`**, work from the repo root with
the default `.venv`, or always pass **`--python`** to `uv pip install` for your
target interpreter. After install, **`pyopencode doctor`** checks **litellm**
(and prints the interpreter path).

| Extra | Install | Purpose |
|-------|---------|---------|
| *(none)* | `pip install -e .` | CLI + agent core |
| **`[tui]`** | `pip install -e ".[tui]"` | Textual chat UI (`--tui`, themes, grouped tool panels) |
| **`[repomap]`** | `pip install -e ".[repomap]"` | `get_repomap` with `prefer_tree_sitter=true` (tree-sitter) |
| **`[lsp]`** | `pip install -e ".[lsp]"` | Optional `pygls` for building/extending language servers |
| **`[mcp]`** | `pip install -e ".[mcp]"` | Placeholder extra; MCP stdio uses stdlib (see [Config snippets](#config-snippets-pyopencodeconfigtoml-or-pyopencodetoml)) |
| **`[dev]`** | `pip install -e ".[dev]"` | pytest, ruff, pre-commit, Textual (Pilot tests) |

If `python -m pyopencode` fails with **No module named 'click'**, your venv is
missing dependencies — use **`uv sync`** or **`uv pip install --python … -e .`**
as above (not only the editable name).

**From PyPI:** `pip install pyopencode` / `pip install "pyopencode[tui]"` after
release ([RELEASING.md](RELEASING.md)). If `pip` reports *no matching
distribution*, use the clone flow above.

---

## Quick start

1. **API keys** — set env vars or run `pyopencode auth login` (see [API keys](#api-keys)).
2. **Sanity check:** `pyopencode doctor` (Python version, which keys are set,
   whether Textual is installed).
3. **Run:** `pyopencode "summarize this repo"`, `pyopencode -U "bigger task"` for
   [Ultrawork](#config-snippets-pyopencodeconfigtoml-or-pyopencodetoml), or
   `pyopencode --tui` for the UI (`--tui-theme light|dark`, `--tui-high-contrast`,
   `--no-group-tools` optional).

Entry points:

- `pyopencode …`
- `python -m pyopencode …` (same commands)

---

## API keys

The default provider is **Anthropic**. Use the key that matches your
`--provider` / config.

### Environment variables

| Provider | Variable |
|----------|----------|
| Anthropic | `ANTHROPIC_API_KEY` |
| OpenAI | `OPENAI_API_KEY` |
| Gemini | `GEMINI_API_KEY` |
| Qwen (DashScope) | `DASHSCOPE_API_KEY` |
| SiliconFlow | `SILICONFLOW_API_KEY` |

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
# … add others as needed for your providers
```

### `auth login` (credentials file)

Stores keys in **`~/.pyopencode/credentials.json`** (file mode `0600`). Values
are loaded into the process environment on each run (whitelist only; no extra
keys).

```bash
pyopencode auth login
pyopencode auth login --provider openai   # skip the interactive menu
```

Do **not** commit keys. See [SECURITY.md](SECURITY.md).

---

## CLI

Global options: **`pyopencode --help`**, **`pyopencode --version`**.

### Command overview

| Command | What it does |
|---------|----------------|
| **`run`** | Start the agent: interactive REPL, or one-shot if you pass a prompt. |
| **`auth login`** | Save API keys to `~/.pyopencode/credentials.json`. |
| **`sessions list`** | List saved chats for the **current working directory**. |
| **`sessions list --all`** | List recent sessions across **all** project paths. |
| **`sessions list --limit N`** | Cap rows (default 50). |
| **`sessions path`** | Print path to the **SQLite** session database. |
| **`config paths`** | Show global / project TOML, credentials, and DB paths (no secrets). |
| **`config show`** | Print effective `model`, `provider`, `max_tokens` after merge. |
| **`doctor`** | Python/OS, env key presence, `credentials.json`, Textual, `cwd`. |
| **`version`** | Package version (same as `--version`). |

**`run` flags (high level):** `--model` / `--provider`, `--resume` / `--session-id`,
`--list-sessions`, **`--ultrawork` / `-U`**, `--tui` with `--tui-theme`,
`--tui-high-contrast`, `--no-group-tools`. See **`pyopencode run --help`**.

### `run` (agent)

```bash
pyopencode run                          # interactive REPL
pyopencode run "your task"              # one-shot then REPL
pyopencode run --model gpt-4o --provider openai "task"

pyopencode run --list-sessions          # sessions for cwd, then exit
pyopencode run --resume                 # continue latest session for cwd
pyopencode run --session-id <uuid>      # continue a specific session
pyopencode run --tui                    # Textual UI (needs [tui])
pyopencode run --tui --resume
pyopencode run --tui --tui-theme light --tui-high-contrast
pyopencode run --tui --no-group-tools   # one Panel per tool instead of batch
pyopencode run -U "refactor X"          # Ultrawork (compact high-push mode)
```

**Shorthand:** if the first argument is **not** a known subcommand (`run`,
`auth`, `sessions`, `config`, `doctor`) and not `--help` / `--version`, the CLI
prepends **`run`**. So these are equivalent:

```bash
pyopencode "hello"
pyopencode run "hello"
pyopencode --model gpt-4o --provider openai "hello"
```

Use **`pyopencode run --help`** for the full option list.

### Config snippets (`~/.pyopencode/config.toml` or `.pyopencode.toml`)

**Ultrawork (compact “push to finish” mode)**

```toml
[agent]
ultrawork = true
```

Or per run: `pyopencode run -U "your task"` / `pyopencode run --ultrawork --tui`. You can also
start a message with `ulw ` or `ultrawork ` (similar to OpenCode’s keyword), which enables the
mode for that session and strips the prefix. This only appends extra system instructions — no
separate plugin agents. Shorthand works too: `pyopencode -U "task"` (CLI injects `run`).

**Tool timeouts / bash cap / retries**

```toml
[tools]
sync_timeout_sec = 120.0
async_timeout_sec = 180.0
bash_max_timeout_sec = 300
max_retries = 1
retry_delay_sec = 0.3
```

**MCP stdio servers** (then use agent tools `mcp_list_tools` / `mcp_call_tool`)

```toml
[mcp.servers.files]
command = ["npx", "-y", "@modelcontextprotocol/server-filesystem", "{root}"]
# optional: cwd = "/tmp", env = { KEY = "value" }
```

`{root}` expands to the absolute path of the current working directory when the
server is started.

### Sessions (persistence)

- State is stored in **`~/.pyopencode/sessions.db`** (SQLite), not a `sessions/`
  folder. Inspect the path with **`pyopencode sessions path`**.
- Sessions are **scoped by resolved project path** (the directory you run from).

---

## Textual TUI (`--tui`)

Requires the **`[tui]`** extra (`pip install -e ".[tui]"` or PyPI
`pyopencode[tui]`).

```bash
pyopencode --tui
pyopencode run --tui --resume
pyopencode run --tui -U "large refactor"   # Ultrawork + TUI
```

**Ultrawork in TUI:** use **`run --ultrawork`** / **`-U`**, set **`[agent] ultrawork`**
in TOML, or prefix the first (or any) message with **`ulw `** / **`ultrawork `**.

### Composer (bottom area)

- **Multiline `TextArea`** — **Enter** inserts a newline.
- **Send** — **Ctrl+Enter** or the **Send** button submits the message.
- Placeholder text summarizes shortcuts.

### Transcript (main log)

- **User** and **Assistant** turns appear as **panels** with **timestamps**
  (`You · HH:MM`, `Assistant · HH:MM`).
- **Assistant** final text is rendered as **Markdown** when possible (code
  blocks use a dark theme); on parse issues it falls back to plain text.
- A **narrow strip** under the log shows the **current stream** with an
  **“Assistant · typing…”** label while tokens arrive.
- **Tool calls / results** are grouped in **panels** (`Tool · name`); errors use
  a red border.
- **Welcome** panel on first open (no `--tui` initial prompt) explains
  send/focus shortcuts.
- **Dim rules** separate completed turns.

### Keyboard

| Key | Action |
|-----|--------|
| **F1** | Help overlay (shortcuts & UI notes). |
| **Ctrl+Enter** | Send message from the input area. |
| **Ctrl+L** | Clear transcript **and** in-memory conversation (new session). |
| **Ctrl+K** | Request context **compaction** (token saving). |
| **Ctrl+Shift+G** | Focus the chat log (scroll with PgUp/PgDn / arrows). |
| **Ctrl+C** | Quit. |

Dangerous tools open a **permission modal** (allow once / always / deny).

LSP / `PYOPENCODE_PYRIGHT_JS` notes for contributors: [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Configuration

Config is merged in order (later overrides earlier, deep merge where applicable):

1. Built-in defaults (`pyopencode/config.py`)
2. `~/.pyopencode/config.toml`
3. `.pyopencode.toml` in the **current working directory**

Environment-based API keys and `credentials.json` are applied as documented in
**[API keys](#api-keys)**.

Inspect resolved paths and non-secret values:

```bash
pyopencode config paths
pyopencode config show
```

---

## Documentation

| Doc | Contents |
|-----|----------|
| [CONTRIBUTING.md](CONTRIBUTING.md) | Dev setup, pytest, CI, pre-commit, LSP integration tests |
| [ROADMAP.md](ROADMAP.md) | Status vs [TASK.md](TASK.md), next steps |
| [CHANGELOG.md](CHANGELOG.md) | Release notes |
| [RELEASING.md](RELEASING.md) | PyPI / tags |
| [SECURITY.md](SECURITY.md) | Keys, `credentials.json`, staging checklist |
| [TASK.md](TASK.md) | Short design reference |
| [LICENSE](LICENSE) | MIT |
