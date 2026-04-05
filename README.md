# PyOpenCode

Terminal AI coding agent for Python **3.11+**. Uses [LiteLLM](https://github.com/BerriAI/litellm) for Claude, OpenAI, Gemini, Qwen (DashScope), and SiliconFlow.

## Install

**From this repository** (works today):

```bash
git clone https://github.com/chenhaodev/pyopencode.git
cd pyopencode
pip install -e .
```

Optional Textual UI: `pip install -e ".[tui]"` (or `uv pip install -e ".[tui]"`).

**From PyPI:** `pip install pyopencode` / `pip install "pyopencode[tui]"` once the
package is published ([RELEASING.md](RELEASING.md)). If `pip` reports no matching
distribution, use the clone steps above.

## Usage

Set at least one provider API key first ([SECURITY.md](SECURITY.md)). Defaults
use Anthropic unless you pass `--model` / `--provider`.

```bash
pyopencode "your task"
pyopencode --model gpt-4o --provider openai "your task"
pyopencode --list-sessions
pyopencode --resume
pyopencode --session-id <uuid>
pyopencode --tui
```

Sessions live under `~/.pyopencode/sessions` (scoped by project path).

## Configuration

Optional TOML (later overrides earlier): `~/.pyopencode/config.toml`, then
`.pyopencode.toml` in the working directory. Defaults and schema:
`pyopencode/config.py`. Keys: [SECURITY.md](SECURITY.md).

## Documentation

[CONTRIBUTING.md](CONTRIBUTING.md) · [ROADMAP.md](ROADMAP.md) ·
[CHANGELOG.md](CHANGELOG.md) · [RELEASING.md](RELEASING.md) ·
[SECURITY.md](SECURITY.md) · [TASK.md](TASK.md)
