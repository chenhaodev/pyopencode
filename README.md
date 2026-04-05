# PyOpenCode

A lightweight Python AI coding agent. Supports Claude, GPT, Gemini, Qwen, and SiliconFlow.

## Install

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
pyopencode --tui                 # optional: pip install 'pyopencode[tui]'
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
pip install "pyopencode[tui]"    # Textual TUI
pip install "pyopencode[dev]"    # pytest, ruff (pinned in pyproject)
```

### LSP tool (`lsp_goto_definition`)

Registered in the agent tool registry (category `always_ask`). It spawns a short-lived
language server (e.g. `pyright-langserver --stdio` for Python) and runs go-to-definition.

If the server is missing or your `pyright-langserver` is a broken pyenv shim, set:

- `PYOPENCODE_PYRIGHT_JS` — absolute path to `pyright-langserver.js` from the npm
  `pyright` package; used as `node <path> --stdio` when `node` is on `PATH`.

**Phase 4** here means ongoing UX and editor parity (TUI polish, richer LSP usage).
The bridge and `lsp_goto_definition` tool are wired; deeper editor features are not.

## Example `config.toml`

```toml
model = "claude-sonnet-4-20250514"
provider = "anthropic"
max_tokens = 16384
```

## Development and CI

```bash
pip install -e '.[dev]'
ruff check pyopencode/ tests/
pytest tests/ -q -m "not integration"
```

Integration test (real `pyright-langserver` or `PYOPENCODE_PYRIGHT_JS`):

```bash
export PYOPENCODE_RUN_LSP_INTEGRATION=1
pytest tests/test_lsp_integration.py -q -m integration
```

GitHub Actions runs `ruff check`, default pytest (excludes `integration`), and a separate
job that installs `pyright` via npm and runs the LSP integration test.

---

**中文摘要：** 配置按「内置 → 用户 `config.toml` → 项目 `.pyopencode.toml` →
`~/.pyopencode/config.info.py` → 项目 `config.info.py`」覆盖合并。CLI 支持
`--resume` / `--session-id` / `--list-sessions` / `--tui`。LSP 工具
`lsp_goto_definition` 已接入；可选环境变量 `PYOPENCODE_PYRIGHT_JS` 用于绕过失效的
`pyright-langserver` shim。CI 含 `ruff` 与可选真机 LSP 集成测试。
