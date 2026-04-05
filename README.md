# PyOpenCode

Terminal **AI coding agent** for Python **3.11+**. It runs a ReAct-style loop with
tools (read/edit files, bash, search, Git, optional LSP), multiple LLM backends
via [LiteLLM](https://github.com/BerriAI/litellm) (Claude, OpenAI, Gemini,
Qwen / DashScope, SiliconFlow), and an optional **Textual TUI**.

---

## Install

**From this repository** (recommended until the package is on PyPI):

```bash
git clone https://github.com/chenhaodev/pyopencode.git
cd pyopencode
pip install -e .
# or: uv pip install -e .
```

| Extra | Install | Purpose |
|-------|---------|---------|
| *(none)* | `pip install -e .` | CLI + agent core |
| **`[tui]`** | `pip install -e ".[tui]"` | Textual chat UI (`--tui`) |
| **`[dev]`** | `pip install -e ".[dev]"` | pytest, ruff, pre-commit, Textual (Pilot tests) |

**From PyPI:** `pip install pyopencode` / `pip install "pyopencode[tui]"` after
release ([RELEASING.md](RELEASING.md)). If `pip` reports *no matching
distribution*, use the clone flow above.

---

## Quick start

1. **API keys** — set env vars or run `pyopencode auth login` (see [API keys](#api-keys)).
2. **Sanity check:** `pyopencode doctor` (Python version, which keys are set,
   whether Textual is installed).
3. **Run:** `pyopencode "summarize this repo"` or `pyopencode --tui` for the UI.

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
```

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
