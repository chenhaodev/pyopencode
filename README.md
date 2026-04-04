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
pyopencode --resume   # resume last session
```

## Config

Global config: `~/.pyopencode/config.toml`  
Project config: `.pyopencode.toml`

```toml
model = "claude-sonnet-4-20250514"
provider = "anthropic"
max_tokens = 16384
```

## Optional

```bash
pip install "pyopencode[tui]"    # Textual TUI
pip install "pyopencode[dev]"    # pytest
```
