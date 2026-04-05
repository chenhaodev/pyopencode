# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `ROADMAP.md`: future work vs `TASK.md` and current implementation.
- LSP connection pool (`lsp_session`) and tool `lsp_find_references`.
- `uv.lock` with CI using `uv sync --frozen --extra dev`.
- Dependabot updates for GitHub Actions and pip/uv lockfile.
- TUI Pilot tests, pre-commit + ruff in dev extras.

### Changed

- `lsp_goto_definition` reuses the pooled language server per workspace.
- README: tighter structure; PyPI install; move dev/CI/LSP detail to
  CONTRIBUTING and other linked docs; English only; drop duplicate summary.
- README: clarify config is optional layered files (not “four configs” required).
- README: minimal layout; LSP/pyright notes moved to CONTRIBUTING.
- ROADMAP, SECURITY, TASK: shortened; TASK no longer embeds large code/prompt
  drafts (see source tree).
- README: install from clone first; note PyPI may be unavailable until publish;
  mention API keys before first run.
- Default Qwen `api_key_env` aligned to `DASHSCOPE_API_KEY` (matches
  `SECURITY.md` and LiteLLM env wiring).
- SECURITY: drop `config.info.py` guidance; align with TOML + env keys.

### Removed

- Root `test_phase2_e2e.py` (manual Phase 2 script; coverage lives in `tests/`).
- `config.info.example.py` (sample overlay).
- Loading `~/.pyopencode/config.info.py` and `./config.info.py`: configuration
  is built-in defaults + TOML + environment API keys only.

## [0.1.0]

Initial published layout: agent loop, tools, sessions, optional TUI and LSP tools.

[Unreleased]: https://github.com/chenhaodev/pyopencode/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/chenhaodev/pyopencode/releases/tag/v0.1.0
