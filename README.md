# PyOpenCode

Terminal AI coding agent for Python **3.11+**. Uses [LiteLLM](https://github.com/BerriAI/litellm) for Claude, OpenAI, Gemini, Qwen (DashScope), and SiliconFlow.

## Install

```bash
pip install pyopencode
pip install "pyopencode[tui]"   # optional Textual UI
pip install -e .                # editable, from a clone (uv pip also works)
```

## Usage

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

Set provider keys in the environment — see [SECURITY.md](SECURITY.md).

Optional TOML (later overrides earlier): `~/.pyopencode/config.toml`, then
`.pyopencode.toml` in the working directory. Defaults and schema:
`pyopencode/config.py`.

## Documentation

[CONTRIBUTING.md](CONTRIBUTING.md) · [ROADMAP.md](ROADMAP.md) ·
[CHANGELOG.md](CHANGELOG.md) · [RELEASING.md](RELEASING.md) ·
[SECURITY.md](SECURITY.md) · [TASK.md](TASK.md)
