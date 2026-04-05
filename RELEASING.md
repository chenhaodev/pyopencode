# 发布流程（PyPI）

## 前置

- 安装 [uv](https://docs.astral.sh/uv/)
- PyPI 账号与 token（或 `~/.pypirc`）

## 步骤

1. **版本号**：在 `pyproject.toml` 的 `[project]` 里更新 `version`（遵循 [SemVer](https://semver.org/)）。
2. **更新日志**：在 `CHANGELOG.md` 把 `[Unreleased]` 下的条目移到新版本标题下，并写上日期。
3. **锁定依赖**（若改过 `pyproject.toml` 依赖）：执行 `uv lock`，提交 `uv.lock`。
4. **检查锁定**：`uv lock --check`。
5. **测试**：`uv sync --frozen --extra dev` 后 `uv run pytest tests/ -m "not integration"`。
6. **构建**：`uv build`（产物在 `dist/`）。
7. **上传**：`uv publish`（需配置 `UV_PUBLISH_TOKEN` 等），或使用 `python -m twine upload dist/*`。

## 标签

```bash
git tag -s "vX.Y.Z" -m "vX.Y.Z"
git push origin "vX.Y.Z"
```

将上述仓库 URL 换成你的 fork 时，请同步修改 `pyproject.toml` 中的 `[project.urls]` 与 `CHANGELOG.md` 底部链接。
