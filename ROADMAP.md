# Roadmap

本文档对照 [`TASK.md`](TASK.md) 中的分阶段计划，总结**当前已落地能力**与**后续方向**。`TASK.md` 仍是设计与历史方案全文；路线图只回答「做到了哪、接下来做什么」。

---

## 与 TASK.md 四阶段的对照

| 阶段 | TASK.md 目标 | 当前状态 |
|------|----------------|----------|
| **Phase 1** | 最小可用内核：CLI、配置、工具、ReAct 循环 | **已完成**（并扩展：`config.info.py` 合并、流式输出等） |
| **Phase 2** | 压缩、SQLite 会话、AGENT.md | **已完成**（`compaction`、`SessionStore`、`--resume` / `--session-id` / `--list-sessions`） |
| **Phase 3** | 子代理、`dispatch_subagents`、repomap | **已完成**（`get_repomap` 工具；repomap 为 **AST 骨架**，与 TASK 中 tree-sitter 设想不同） |
| **Phase 4** | LSP 桥 + TUI 骨架 | **已超出骨架**：完整 JSON-RPC（UTF-8、`initialized`、`did_open`）、**连接池**（`lsp_session`）、工具 **`lsp_goto_definition` / `lsp_find_references`**、集成测试与 `PYOPENCODE_PYRIGHT_JS`；TUI 含流式区、权限弹窗、**F1 帮助**、工具 **Panel**、RichLog 截断与 **Textual Pilot 测试** |

---

## 已实现但未在 TASK 细述的工程能力

- **CI**：`uv.lock`、`uv lock --check`、`uv sync --frozen --extra dev`、`uv run` 执行 ruff/pytest；LSP 集成 job（pyright）。
- **本地质量**：`pre-commit` + ruff（版本与 `[dev]` 对齐）、`pytest` markers（`integration` / `tui`）。
- **文档与发布**：`CONTRIBUTING.md`、`RELEASING.md`、`CHANGELOG.md`、`pyproject` 的 `readme` / `[project.urls]`。
- **依赖治理**：Dependabot（GitHub Actions + pip/锁文件）。

---

## 近期（建议优先）

1. **`ModelRouter` 真正接入主路径**  
   `core/router.py` 已实现 `select()`，但 **尚未**在 `AgentLoop` / `LLMClient` 中按任务类型或 token 阈值切换模型；与 TASK「模型分工策略」对齐。

2. **LSP 加深（在现有池化桥接上增量做）**  
   - `get_diagnostics` 仍为占位；可接 **`textDocument/publishDiagnostics`** 或轮询式工具 **`lsp_diagnostics`**。  
   - **`textDocument/didChange`**：减少重复全量 `did_open`、贴近编辑器行为。  
   - 可选工具：**hover**、`documentSymbol` / `workspaceSymbol`（按语言与成本逐步加）。

3. **TUI**  
   - **Collapsible** 或等价折叠：多轮工具输出成组，减轻刷屏。  
   - **主题 / 高对比** 与可配置项（环境变量或 `config.toml`）。

4. **TASK.md / 仓库结构同步**  
   更新 `TASK.md` 目录树与 Phase 4 描述，使之反映 `lsp_session.py`、`help_modal.py`、`install_hint.py`、`test_tui_app.py`、`uv.lock` 等现实布局（避免新人只看 TASK 产生偏差）。

---

## 中期

- **工具执行治理**：超时、取消、可配置重试；危险命令二次确认策略与审计日志（可选）。
- **Repomap**：TASK 中的 **tree-sitter** 或多语言骨架（TS/Go 等）；与 `get_repomap` 参数扩展一并设计。
- **PyPI 与自动化**：`RELEASING.md` 流程 + 可选 **GitHub Action**（tag 触发 `uv build` / `uv publish`）。
- **可选 `[project.optional-dependencies] lsp`**：评估是否引入 **pygls** 等库（TASK 曾列 `pygls`；当前仍为占位 extra）。

---

## 长期 / 探索

- **MCP 或其它工具总线**：将外部能力以统一工具接口暴露（需安全模型与权限分级延伸）。
- **TUI 内联 diff / 补丁预览**：编辑类工具结果的可视化，而不只依赖日志 Panel。
- **更激进的 LSP**：语言服务器生命周期策略（多工作区、版本协商、崩溃自动重启与池淘汰策略细化）。

---

## 如何贡献某一栏

优先在 **Issue** 里对应到上表中的一条（或拆成更小 PR），并更新本文件勾选或移动条目。发布与版本说明仍以 [`CHANGELOG.md`](CHANGELOG.md) 为准。
