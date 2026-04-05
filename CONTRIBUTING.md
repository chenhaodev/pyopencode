# 参与贡献

产品阶段规划与 `TASK.md` 对照见根目录 **[ROADMAP.md](ROADMAP.md)**。

## 环境

- Python **3.11+**（与 `pyproject.toml` 一致）
- 推荐使用 **[uv](https://docs.astral.sh/uv/)** 作为 pip 前端；经典 **pip** 亦可

## 安装开发依赖

推荐使用 **uv** 与仓库中的 **`uv.lock`**（与 CI 一致）：

```bash
uv sync --extra dev
# 或仅检查锁是否最新: uv lock --check
```

也可沿用 **pip** 可编辑安装：

```bash
uv pip install -e ".[dev]"
# 或: pip install -e ".[dev]"
```

修改 `pyproject.toml` 依赖后请执行 **`uv lock`** 并提交更新后的 **`uv.lock`**。

可选 TUI：

```bash
uv pip install -e ".[tui]"
```

## 本地检查

```bash
ruff check pyopencode/ tests/
pytest tests/ -q -m "not integration"
```

其中包含 **`tests/test_tui_app.py`**（Textual `run_test` / Pilot；依赖 `[dev]` 里的 **textual**）。
仅跑 TUI 相关：`pytest tests/test_tui_app.py -m tui`。

集成测试（真机 LSP，按需）：

```bash
export PYOPENCODE_RUN_LSP_INTEGRATION=1
pytest tests/test_lsp_integration.py -q -m integration
```

**LSP / pyright：** Agent 工具 `lsp_goto_definition`、`lsp_find_references` 依赖本机
language server（如 Python 的 `pyright-langserver --stdio`）。若 shim 异常或找不到可执行文件，可设置环境变量 **`PYOPENCODE_PYRIGHT_JS`** 为 npm 包 `pyright` 里 **`pyright-langserver.js` 的绝对路径**（需 `node` 在 `PATH`）。每个 workspace 复用一条连接，直至进程结束。

## pre-commit（可选）

`[dev]` 已包含 **pre-commit**。在暂存文件上跑 **ruff**（与 CI 全量检查互补）：

```bash
pre-commit install
pre-commit run --all-files
```

钩子定义见仓库根目录 `.pre-commit-config.yaml`。

## CI

推送至 `main` / `master` 或打开 PR 会运行：**`uv lock --check`**、**`uv sync --frozen --extra dev`**、**`uv run ruff`**、**`uv run pytest`**（不含 `integration`），以及单独的 **pyright** LSP 集成 job。

Dependabot：见 `.github/dependabot.yml`（Actions 与 pip/锁文件）。
