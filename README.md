# PyOpenCode

A lightweight Python AI coding agent. Supports Claude, GPT, Gemini, Qwen, and SiliconFlow.

## Install

From a clone (editable). If you use [uv](https://docs.astral.sh/uv/) as a pip front-end:

```bash
uv pip install -e .
```

Or with classic pip:

```bash
pip install -e .
```

## Usage

```bash
pyopencode "list all python files in this project"
pyopencode --model gpt-4o --provider openai "refactor the auth module"

# Session (project-scoped under ~/.pyopencode/sessions)
pyopencode --resume              # resume latest session for cwd
pyopencode --session-id <uuid>  # resume a specific session
pyopencode --list-sessions       # list sessions for cwd, then exit

# TUI (Textual)
pyopencode --tui                 # optional: uv pip / pip install extra [tui]
pyopencode --tui --resume
```

## Config merge order

Later steps override earlier ones (deep merge for nested dicts):

1. Built-in defaults in code
2. `~/.pyopencode/config.toml`
3. `.pyopencode.toml` in the current working directory
4. `~/.pyopencode/config.info.py` (optional: define `DEFAULT_CONFIG` dict)
5. `./config.info.py` in the current working directory (same shape as above)

Environment API keys are applied after TOML/Python overlays (see `pyopencode/config.py`).

## Optional tools

```bash
uv pip install -e '.[tui]'       # Textual TUI (from clone)
uv pip install -e '.[dev]'      # pytest, ruff, pre-commit, textual (TUI Pilot tests)
# Or: pip install -e '.[tui]' / pip install -e '.[dev]'
# From PyPI: uv pip install "pyopencode[tui]"
```

### LSP tools (`lsp_goto_definition`, `lsp_find_references`)

Registered in the agent tool registry (category `always_ask`). They talk to the local
language server (e.g. `pyright-langserver --stdio` for Python). **One server process
per workspace is reused** until the Python process exits (see `lsp_session`).

If the server is missing or your `pyright-langserver` is a broken pyenv shim, set:

- `PYOPENCODE_PYRIGHT_JS` — absolute path to `pyright-langserver.js` from the npm
  `pyright` package; used as `node <path> --stdio` when `node` is on `PATH`.

**Phase 4** means ongoing UX and editor parity (TUI polish, richer LSP usage).

PyPI release steps: [RELEASING.md](RELEASING.md). Changelog: [CHANGELOG.md](CHANGELOG.md).

## Example `config.toml`

```toml
model = "claude-sonnet-4-20250514"
provider = "anthropic"
max_tokens = 16384
```

## Development and CI

贡献流程与本地命令见 [CONTRIBUTING.md](CONTRIBUTING.md)。可选：安装 **pre-commit**
后在提交前自动跑 **ruff**（`pre-commit install`）。

```bash
uv sync --extra dev
uv run ruff check pyopencode/ tests/
uv run pytest tests/ -q -m "not integration"
```

仓库含 **`uv.lock`**。CI 使用 **`uv lock --check`** 与 **`uv sync --frozen --extra dev`**（见 `.github/workflows/ci.yml`）。仅 pip 时仍可用 `uv pip install -e '.[dev]'`。

Integration test (real `pyright-langserver` or `PYOPENCODE_PYRIGHT_JS`):

```bash
export PYOPENCODE_RUN_LSP_INTEGRATION=1
pytest tests/test_lsp_integration.py -q -m integration
```

GitHub Actions runs `ruff check`, default pytest (excludes `integration`), and a separate
job that installs `pyright` via npm and runs the LSP integration test.

---

**中文摘要：** 安装可用 **uv** 或 **pip**；开发说明见 **CONTRIBUTING.md**，可选
**pre-commit**。GitHub **CI 已用 uv** 装依赖。TUI 中 **Ctrl+Shift+G** 聚焦聊天日志、
**F1** 帮助；工具调用与结果以 **Panel** 成块显示。配置合并顺序见上文；CLI 支持
`--resume` / `--session-id` / `--list-sessions` / `--tui`。LSP 工具
`lsp_goto_definition` / `lsp_find_references`、**LSP 连接池** 与 `PYOPENCODE_PYRIGHT_JS`
见上文；**uv.lock** 与 CI **`uv sync --frozen`**；发布见 **RELEASING.md**。CI 含 `ruff`、pytest 与
可选 LSP 集成 job。
