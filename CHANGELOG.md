# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- LSP connection pool (`lsp_session`) and tool `lsp_find_references`.
- `uv.lock` with CI using `uv sync --frozen --extra dev`.
- Dependabot updates for GitHub Actions and pip/uv lockfile.
- TUI Pilot tests, pre-commit + ruff in dev extras.

### Changed

- `lsp_goto_definition` reuses the pooled language server per workspace.

## [0.1.0]

Initial published layout: agent loop, tools, sessions, optional TUI and LSP tools.

[Unreleased]: https://github.com/chenhaodev/pyopencode/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/chenhaodev/pyopencode/releases/tag/v0.1.0
